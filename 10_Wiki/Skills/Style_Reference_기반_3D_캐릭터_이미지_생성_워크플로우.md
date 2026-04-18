---
id: 70afd646
category: "[[10_Wiki/Skills]]"
confidence_score: 0.98
tags: ["Image Generation", "3D Art", "Character Design", "Style Transfer", "AI Workflow"]
last_reinforced: 2026-04-18
github_commit: "{{commit_hash}}" 
---

# [[Style Reference 기반 3D 캐릭터 이미지 생성 워크플로우]]

## 📌 한 줄 통찰 (The Karpathy Summary)
> 본 에이전트는 사용자의 묘사나 사진을 받아, 사전에 정의된 시그니처 스타일(스튜디오 조명, 흰 배경)과 지식 참조 파일을 결합하여 일관성 있는 고품질 3D 캐릭터 이미지를 생성하는 전문 워크플로우입니다.

## 📖 구조화된 지식 (Synthesized Content)
- **역할 및 목표:** 햄로그의 3D 시그니처 캐릭터 아티스트 역할을 수행하며, 사용자의 요청을 기반으로 이미지 생성을 담당합니다.
- **핵심 작동 원리 (Style Reference):** 사용자가 제공한 지식 파일(Knowledge)에 담긴 고유 스타일을 참조하여 모든 생성 과정에서 일관성을 유지하는 것이 핵심입니다.
- **입력 및 출력:** 사용자로부터 외모, 의상, 행동 등의 자연어 묘사 또는 첨부 파일을 입력받아, 부드러운 스튜디오 조명과 깔끔한 흰색 배경이 적용된 완성 이미지를 출력합니다.
- **사용자 경험 (UX):** 이 기능은 AI 에이전트(Gemini Gems) 형태로 구현되어 쉽게 공유하고 접근할 수 있습니다.

## ⚠️ 모순 및 업데이트 (Contradictions & RL Update)
- **과거 데이터와의 충돌:** 없음.
- **정책 변화:** 해당 폴더로 분류됨 (Confidence: 0.98)

## 🔗 지식 연결 (Graph)
- **Parent:** [[10_Wiki]]
- **Related:** [[Prompt Engineering Best Practices]], [[Visual Style Consistency Models]]
- **Raw Source:** [[00_Raw/햄로그_Group.md]]
