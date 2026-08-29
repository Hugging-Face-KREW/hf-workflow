# Quality Skill Builder

`skills/quality`(HF 블로그 번역 품질 검사)처럼 특정 문서 유형을 대상으로 하는
번역 품질 검사 스킬을, **다른 문서 유형**에 맞게 다시 빌드하는 과정을 정리한
메타 스킬이다. 실제 사용자가 아니라 **이 저장소에서 새로운 quality 스킬을
만드는 에이전트**가 대상 독자다.

## 언제 쓰는가

- 새 문서 유형(기술 문서, 코스 자료, README, 릴리즈 노트 등)의 한국어 번역
  품질을 검사하는 스킬이 필요할 때.
- 기존 quality 스킬 하나를 통째로 복사해서 손대는 대신, 무엇을 유지하고 무엇을
  바꿀지 근거를 남기며 진행하고 싶을 때.

## 파일 구조

```
SKILL.md              진입점(라우터) — 원칙·Phase 목차만, 실행에 필요한 것만
RATIONALE.md           "왜"만 모아둔 문서 — 실행에는 불필요, 규칙이 의아할 때만 읽는다
phases/00~06-*.md      Phase별 실행 지침 — 해당 Phase를 시작할 때 그 시점에 읽는다
templates/*.template.md  Phase 1/3/5 산출물의 빈 템플릿
```

`SKILL.md`는 한 번 읽고 전체 맥락만 잡는 용도다. Phase 4에서 Phase 1 내용이
가물가물해지는 걸 막기 위해, **각 Phase의 세부 지침은 그 Phase를 시작하는
시점에 `phases/0N-*.md`를 다시 읽도록** 설계했다 — 기억에 의존하지 않는다.
"왜 이 체크가 있는가"(실제 사례, 배경)는 작업 자체에는 필요 없는 메타
정보라 `RATIONALE.md`로 분리했다.

`SKILL.md`의 Phase 목차 표에 각 Phase의 목표·체크포인트 유무·해당 파일
경로가 정리돼 있다.

## 실제 예제

`skills/quality` → `skills/quality-docs`를 만든 실제 작업이 이 스킬의 근거다.
결과물을 그대로 참고할 수 있다:

- `skills/quality-docs/docs/blog-vs-technical-docs-differences.md` — Phase 1 산출물 예시
- `skills/quality-docs/docs/blog-quality-harness-architecture.md` — Phase 2 산출물 예시(도구 자체 문서라 문서 유형이 바뀌어도 재사용됨)
- `skills/quality-docs/` 전체 — Phase 3~4 결과물

이 스킬 자체(`SKILL.md`/`RATIONALE.md`/`phases/*.md` 분리 구조)도 위 작업을
진행하면서 나온 피드백(분량이 길다, Phase 4쯤 되면 초반 내용을 잊는다)을
반영해 나온 결과물이다 — `RATIONALE.md` 상단에 그 배경이 있다.

## 템플릿

`templates/` 아래에 Phase 1/3/5 산출물의 빈 템플릿이 있다. Phase 2 산출물은
문서 유형별로 새로 만드는 게 아니라 도구 자체에 대한 문서이므로 템플릿이
없다 — 이미 있으면 재사용하고, 없으면
`skills/quality-docs/docs/blog-quality-harness-architecture.md`의 구조를
그대로 본떠서 만든다.
