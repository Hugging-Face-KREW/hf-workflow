# SEO Gold Label Review Worksheet

목적: 현재 fixture의 라벨은 내부 평가용 가설이다. 이 문서는 HFKREW 콘텐츠/SEO 팀이 실제 gold label을 확정하기 위한 검토표다.

사용 방법:

1. 각 샘플을 읽고 `team_label`을 `gold_positive`, `acceptable`, `needs_changes`, `negative`, `blocker`, `exclude` 중 하나로 정한다.
2. `reason`에는 자동 검사 결과가 아니라 사람이 판단한 이유를 적는다.
3. title, description, opening, rendered H1의 의미 정합성을 반드시 같이 본다.
4. 정책형 항목은 SEO 팀 단독으로 확정하지 말고 콘텐츠/번역 정책 결정자를 적는다.

## 우선 검토 대상

| priority | fixture | current label | proposed review focus | team_label | owner | reason |
|---:|---|---|---|---|---|---|
| 1 | `curated/realistic-positive-no-image.md` | `strong_positive` | 내부 gold positive로 승인 가능한지 |  |  |  |
| 2 | `generated/excellent-post.md` | `strong_positive` | synthetic positive로 유지할지, gold에서는 제외할지 |  |  |  |
| 3 | `generated/good-post.md` | `acceptable_positive` | acceptable positive 기준으로 충분한지 |  |  |  |
| 4 | `real/2025-09-14-Implementing-MCP-Servers-in-Python.md` | `acceptable_positive` | 실제 HFKREW positive 후보로 승인 가능한지 |  |  |  |
| 5 | `real/2025-10-12-vlm-explained-ko.md` | `acceptable_positive` | 이미지 많은 실제 positive 후보로 승인 가능한지 |  |  |  |
| 6 | `real/2025-11-17-hf_translation_hub_mcp_design_and_tooling.md` | `acceptable_positive` | 실제 workflow/도구 글 positive 후보로 승인 가능한지 |  |  |  |
| 7 | `curated/semantic-negative-description.md` | `negative` | description-body mismatch negative로 승인 가능한지 |  |  |  |
| 8 | `curated/semantic-negative-title.md` | `negative` | title-body mismatch negative로 승인 가능한지 |  |  |  |
| 9 | `curated/metadata-policy-positive.md` | `acceptable_positive` | canonical 정책 case의 기대 동작 결정 |  |  |  |
| 10 | `curated/hreflang-policy-positive.md` | `acceptable_positive` | hreflang 정책 case의 기대 동작 결정 |  |  |  |

## Gold Positive 승인 기준 초안

- 제목, description, rendered H1, 첫 문단이 같은 주제를 설명한다.
- 첫 문단에서 독자, 주제, 글의 범위가 드러난다.
- 외부 근거 링크가 본문 주장과 직접 연결된다.
- 이미지가 있으면 alt가 파일명이나 `image-1`이 아니라 이미지의 역할을 설명한다.
- canonical/hreflang은 팀 정책이 정해진 경우에만 자동 판정한다.

## Exclude 기준

- 테스트를 위해 일부러 만든 극단적 synthetic negative는 gold 품질 라벨에서 제외할 수 있다.
- 현재 checker 동작만 고정하기 위한 golden snapshot은 gold label 근거로 쓰지 않는다.
- 팀 정책이 아직 없는 canonical/hreflang 샘플은 `policy_pending`으로 남긴다.

