import os
import time
import json
import uuid
from datetime import datetime
import subprocess
import sys
import fitz  # PyMuPDF for PDF decoding
from watchdog.observers import Observer

# Set stdout to utf-8 to prevent Windows cp949 errors
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from watchdog.events import FileSystemEventHandler
from openai import OpenAI

# ==========================================
# ⚙️ Configuration
# ==========================================
RAW_DIR = "00_Raw"
WIKI_DIR = "10_Wiki"
META_DIR = "20_Meta"
LM_STUDIO_API_BASE = "http://localhost:1234/v1"
MODEL_NAME = "gemma4:e4b"

# Ensure base directories exist
for d in [RAW_DIR, WIKI_DIR, META_DIR, ".github"]:
    os.makedirs(d, exist_ok=True)

# Connect to Local LM Studio (Gemma 4)
client = OpenAI(base_url=LM_STUDIO_API_BASE, api_key="lm-studio")

# Cache to prevent repetitive processing on renames
PROCESSED_FILES = set()

# ==========================================
# 🧠 LLM System Prompt Template
# ==========================================
PROMPT_TEMPLATE = """You are P-Reinforce Architect, an autonomous knowledge agent.
Your task is to analyze the user's raw fragmented note and organize it into our Wiki system.

Follow these strict rules:
1. Determine the most appropriate category folder inside `10_Wiki` out of: `Projects`, `Topics`, `Decisions`, `Skills`.
   If a specific sub-topic is needed, create it as a subfolder (e.g., `10_Wiki/Topics/Psychology`).
2. Extract a concise, clear document title.
3. Write a one-line core insight (The Karpathy Summary).
4. Organize the details and patterns as bullet points.
5. Identify 2 related concepts for graph connectivity.
6. Provide a list of relevant tags.

You MUST respond strictly with the following JSON format. Do not use Markdown JSON tags or any other text around it.
{
  "category": "10_Wiki/Topics/SubTopic",
  "title": "Document Title",
  "summary": "This is a single core insight sentence.",
  "content": "- Extracted pattern 1\\n- Detail point 2",
  "tags": ["tag1", "tag2"],
  "related": ["RelatedConcept1", "RelatedConcept2"],
  "confidence_score": 0.95
}

User's Raw Note:
"""

# ==========================================
# 🚀 Processing Logic
# ==========================================
def process_file(filepath):
    if filepath in PROCESSED_FILES:
        return
    PROCESSED_FILES.add(filepath)
    
    # Wait briefly to ensure file copying is complete before reading
    time.sleep(1)
    
    filename = os.path.basename(filepath)
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    parent_dir = os.path.basename(os.path.dirname(filepath))
    raw_source_path = f"{RAW_DIR}/{parent_dir}/{filename}" if parent_dir != RAW_DIR else f"{RAW_DIR}/{filename}"

    print(f"\n[👀 File Detected] Processing: {filename}...")
    
    raw_text = ""
    try:
        if filepath.lower().endswith('.pdf'):
            doc = fitz.open(filepath)
            for page in doc:
                raw_text += page.get_text()
            
            # Context length protection for Gemma (truncate to ~30,000 characters)
            if len(raw_text) > 30000:
                print("[⚠️ Warning] PDF is very long. Truncating text to prevent context overload.")
                raw_text = raw_text[:30000] + "\n...[TRUNCATED_DUE_TO_LENGTH]..."
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                raw_text = f.read()
                
        # Auto-rename .txt to .md locally in 00_Raw for Obsidian compatibility
        if filepath.lower().endswith('.txt'):
            new_filepath = filepath[:-4] + '.md'
            PROCESSED_FILES.add(new_filepath) # Prevent watchdog recursion
            new_filename = os.path.basename(new_filepath)
            os.rename(filepath, new_filepath)
            print(f"[🔄 Auto-Rename] {filename} -> {new_filename} (For Obsidian)")
            filepath = new_filepath
            filename = new_filename
            if raw_source_path.endswith(".txt"):
                raw_source_path = raw_source_path[:-4] + ".md"
                
    except Exception as read_ex:
        print(f"[❌ Error] Failed to read {filename}: {read_ex}")
        return

    try:
        # Call Gemma 4 via Local LM Studio API
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a direct JSON output engine. Output only valid JSON."},
                {"role": "user", "content": PROMPT_TEMPLATE + raw_text}
            ],
            temperature=0.3
        )
        
        msg_content = response.choices[0].message.content.strip()
        
        # Strip codeblock wrapping if Gemma accidentally includes it
        if msg_content.startswith("```"):
            msg_content = msg_content.strip("` \n")
            if msg_content.lower().startswith("json"):
                msg_content = msg_content[4:].strip()
                
        # Parse output
        data = json.loads(msg_content)
        
        # Resolve destination path
        wiki_content_path = data.get("category", "10_Wiki/Topics/Unsorted")
        if not wiki_content_path.startswith("10_Wiki"):
            wiki_content_path = f"10_Wiki/{wiki_content_path}"
        
        wiki_path = os.path.join(os.getcwd(), wiki_content_path)
        os.makedirs(wiki_path, exist_ok=True)
        
        # Generate Metadata for Markdown
        doc_uuid = str(uuid.uuid4())[:8]
        doc_title = data.get("title", "Untitled Knowledge")
        safe_filename = "".join([c for c in doc_title if c.isalnum() or c in [' ', '-', '_']]).rstrip().replace(" ", "_")
        
        # Build Standardized Markdown Template
        md_text = f"""---
id: {doc_uuid}
category: "[[{wiki_content_path}]]"
confidence_score: {data.get("confidence_score", 0.9)}
tags: {json.dumps(data.get("tags", []))}
last_reinforced: {date_str}
github_commit: "{{{{commit_hash}}}}" 
---

# [[{doc_title}]]

## 📌 한 줄 통찰 (The Karpathy Summary)
> {data.get("summary", "No summary provided.")}

## 📖 구조화된 지식 (Synthesized Content)
{data.get("content", "- No parsed content.")}

## ⚠️ 모순 및 업데이트 (Contradictions & RL Update)
- **과거 데이터와의 충돌:** 없음.
- **정책 변화:** 해당 폴더로 분류됨 (Confidence: {data.get("confidence_score", 0.9)})

## 🔗 지식 연결 (Graph)
- **Parent:** [[{os.path.dirname(wiki_content_path).replace("\\", "/")}]]
- **Related:** {', '.join([f"[[{r}]]" for r in data.get('related', [])])}
- **Raw Source:** [[{raw_source_path}]]
"""
        
        # Write to 10_Wiki/...
        out_filepath = os.path.join(wiki_path, f"{safe_filename}.md")
        with open(out_filepath, "w", encoding="utf-8") as out_f:
            out_f.write(md_text)
            
        print(f"[✅ Synthesized] Generated: {out_filepath}")
        
        # Git Auto-Sync
        print(f"[🚀 Git Sync] Pushing changes to GitHub...")
        subprocess.run(["git", "add", "."], check=False)
        commit_msg = f"[P-Reinforce] reinforce: '{wiki_content_path}' 폴더 최적화 및 문서('{doc_title}') 추가"
        subprocess.run(["git", "commit", "-m", commit_msg], check=False)
        push_result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, check=False)
        
        if push_result.returncode == 0:
            print("[✅ Git Sync] Successfully pushed to origin/main.")
        else:
            print(f"[⚠️ Git Sync Warning] Ensure 'git init' and remote 'origin' are set up properly.\nDetails: {push_result.stderr}")
            
    except json.JSONDecodeError:
        print("[❌ Error] The LM Studio response was not valid JSON.")
        print(f"Raw Output: {msg_content}")
    except Exception as e:
        print(f"[❌ Error] Processing failed: {e}")

# ==========================================
# 📡 Directory Watcher
# ==========================================
class RawFolderWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            filepath = event.src_path
            # Analyze text, markdown, and pdf files
            if filepath.lower().endswith((".md", ".txt", ".pdf")):
                process_file(filepath)

if __name__ == "__main__":
    event_handler = RawFolderWatcher()
    observer = Observer()
    
    # Path to "00_Raw"
    raw_path = os.path.join(os.getcwd(), RAW_DIR)
    
    observer.schedule(event_handler, raw_path, recursive=True)
    observer.start()
    
    print("=====================================================")
    print("🌿 P-Reinforce Agent Is Online 🌿")
    print(f"📡 AI Source   : LM Studio ({MODEL_NAME}) @ {LM_STUDIO_API_BASE}")
    print(f"📂 Monitoring  : {RAW_DIR}/ directory for new notes")
    print("=====================================================")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Agent...")
        observer.stop()
    observer.join()
