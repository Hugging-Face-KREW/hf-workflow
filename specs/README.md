# HF Blog Workflow Specs

이 디렉터리는 HF Blog translation PR workflow를 유지·확장할 때 필요한 Spec만
모은다. 현재 구현 상태는 `hf-blog-workflow-spec.md`를 먼저 읽는다.

| 문서 | 용도 |
|---|---|
| [HF Blog Workflow Spec](hf-blog-workflow-spec.md) | 현재 구현, 병합 PR, WIP, 안전 조건, 검증 방법의 기준 문서 |
| [PR Agent Implementation Spec](pr-agent-implementation-spec.md) | GitHub Actions 기반 PR lifecycle/repair의 MVP 결정과 세부 정책 |
| [Agent Workflow Design](agent-workflow-design.md) | 장기 아키텍처와 설계 근거. 구현 전 가정이 있으므로 기준 문서를 대체하지는 않음 |
| [Skill Integration Guide](pr-agent-skill-integration-guide.md) | SEO/quality skill 입력·출력 및 repair-friendly finding 계약 |
| [SEO Metadata I/O](seo-metadata-module-io.md) | SEO gate와 metadata suggestion/apply를 분리하는 JSON 및 frontmatter 계약 |
| [Quality Skill Refactoring Plan](quality-skill-refactoring-plan.md) | `skills/quality`에서 core를 분리하고 문서 유형·repo별 부분을 profile로 빼는 리팩토링 계획. `quality-skill-builder` 스킬의 방향 전환 근거 |

다음 자료는 구현 Spec이 아니거나 현재 contract와 중복·불일치할 수 있어 포함하지
않는다: 발표 초안, HTML workflow 개요, E2E 스크린샷 중심 팀 리뷰 문서, 그리고
그 문서 전용 이미지 asset. 필요한 경우 Git history에서 별도로 참조한다.
