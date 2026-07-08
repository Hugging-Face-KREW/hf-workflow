# Render Signal Audit for Real HFKREW Fixtures

이 리포트는 Jekyll full build가 아니라 `_layouts/post.html`의 핵심 구조(`page.title` -> layout H1)를 반영한 근사 렌더 신호입니다.

## Summary

| File | Body H1 | Layout title H1 | Effective H1 | Meta description | H1 sample |
|---|---:|---|---:|---|---|
| `2024-09-16-how-to-contribute.md` | 0 | True | 1 | False | 🤗 어떻게 기여하나요? |
| `2025-05-31-2025-PseudoCon-recap.md` | 3 | True | 4 | False | HuggingFace KREW in 2025 PseudoCon<br>👩🏻‍🍳 Hugging Face 쿡북요리사<br>🚀 Hugging Face Beyond First PR |
| `2025-06-22-HuggingFace-Docs-Translation-Guide.md` | 0 | True | 1 | False | Hugging Face transformers 기술 문서 번역 가이드 |
| `2025-09-14-Implementing-MCP-Servers-in-Python.md` | 1 | True | 2 | False | Python으로 구현하는 MCP 서버: Gradio를 활용한 AI 쇼핑 어시스턴트<br>Python으로 구현하는 MCP 서버: Gradio를 활용한 AI 쇼핑 어시스턴트 |
| `2025-09-14-python-tiny-agents-ko.md` | 1 | True | 2 | False | 파이썬 Tiny Agents: 약 70줄의 코드로 MCP 기반 에이전트 구현하기<br>파이썬 Tiny Agents: 약 70줄의 코드로 MCP 기반 에이전트 구현하기 |
| `2025-10-12-vlm-explained-ko.md` | 1 | True | 2 | False | 비전 언어 모델 쉽게 이해하기<br>비전 언어 모델 쉽게 이해하기 |
| `2025-10-20-2025-VLM.md` | 0 | True | 1 | False | 2025년의 VLM : 더 좋아지고, 더 빠르고, 더 강해진 비전 언어 모델 |
| `2025-11-17-hf_translation_hub_mcp_design_and_tooling.md` | 1 | True | 2 | False | MCP 서버 설계 전략 및 개발 도구 선정<br>1. MCP 서버 의사결정 흐름에 따른 설계 전략 |
| `2025-12-01-rteb.md` | 1 | True | 2 | False | RTEB: 검색 평가의 새로운 표준<br>RTEB: 검색 평가의 새로운 표준 |
| `2025-12-15-ai-agents-are-here.md` | 6 | True | 7 | False | AI Agents의 도래: 그래서, 이제는?<br>서론<br>AI 에이전트란 무엇인가? |
| `2025-12-22-smolvla.md` | 1 | True | 2 | False | SmolVLA: Lerobot 커뮤니티 데이터로 학습된 효율적인 Vision-Language-Action 모델<br>SmolVLA: Lerobot 커뮤니티 데이터로 학습된 효율적인 Vision-Language-Action 모델 |
| `2025-12-28-translation-mcp-project-overview.md` | 0 | True | 1 | False | Hugging Face 번역 MCP 서버 총정리 |
| `2026-01-05-hf-translation-mcp-n8n.md` | 0 | True | 1 | False | n8n으로 번역 MCP Server 워크플로우 구축하기: 실전 트러블슈팅과 실행 방식 비교 |

## Interpretation

- `Body H1 = 0`이더라도 `Layout title H1 = True`이면 실제 post layout에서는 page title이 H1로 렌더링됩니다.
- `Effective H1 > 1`이면 frontmatter title H1에 더해 본문 H1이 추가되어 최종 HTML에서 H1 과다 가능성이 있습니다.
- 따라서 raw markdown 기준 `h1_count == 1` 규칙은 HFKREW post layout과 맞지 않습니다.
- H1 관련 gate는 rendered signal 기준으로 바꾸거나 advisory로 낮춰야 합니다.
