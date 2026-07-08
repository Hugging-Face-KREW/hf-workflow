# SEO Evaluation Dataset Quality Review

작성 목적: 현재 `skills/seo/tests/fixtures` 평가 데이터셋이 SEO skill 검증 근거로 충분한지, 기존 평가를 답습하지 않고 다시 수동/정성 평가한다.

## 이번 재평가의 전제

이전 리포트의 `8/10` 평가는 과했다. 당시 평가는 자동 audit 결과, manifest 분포, 일부 대표 샘플 확인을 섞은 판단이었고, 모든 fixture 원문을 사람이 다시 읽고 라벨을 확정한 전수 정성평가라고 보기 어려웠다.

이번 개선에서는 다음을 먼저 보강했다.

- `generated/excellent-post.md`, `generated/good-post.md`에서 `example.com`, 근거 없는 성능 수치, generic anchor를 제거했다.
- `curated/` 샘플 5개를 추가했다.
- `curated/realistic-positive-no-image.md`는 이미지 없이도 본문 구조와 공식 근거 링크가 안정적인 positive control이다.
- `curated/metadata-policy-positive.md`는 canonical/hreflang처럼 도구가 자동 확정하면 안 되는 정책형 positive case다.
- `curated/semantic-negative-description.md`는 body gate와 frontmatter 형식은 통과하지만 description이 본문과 의미적으로 불일치하는 negative case다.
- `curated/semantic-negative-title.md`는 body gate는 통과하지만 frontmatter title이 본문과 다른 약속을 하는 negative case다.
- `curated/hreflang-policy-positive.md`는 번역 페이지의 hreflang/canonical 후보 검토처럼 정책 입력이 필요한 positive case다.
- `evaluation_manifest.yml`에 `curated_internal`, `curated_gold_positive`, `semantic_metadata_negative`를 추가했다.
- semantic negative가 current gate를 통과한다는 사실을 테스트로 고정했다. 이는 버그를 숨기는 것이 아니라, 현재 deterministic body gate의 한계를 명시적으로 드러내기 위한 장치다.
- `signals.frontmatter.title_text`, `signals.frontmatter.description_text`, `signals.opening.first_real_paragraph`를 리포트에 노출했다. 이는 semantic mismatch를 휴리스틱으로 판정하지 않고, LLM/사람 리뷰가 판단할 원문 증거를 제공하기 위한 보강이다.
- `signals.semantic_review` packet을 추가했다. title, description, rendered H1 후보, opening, canonical/permalink를 한 묶음으로 제공하므로 PR 코멘트와 LLM policy가 같은 evidence를 볼 수 있다.
- `reports/gold-label-review-worksheet.md`를 추가했다. 팀이 gold positive와 policy case를 직접 승인할 수 있게 만든 운영용 검토표다.
- `metadata.apply()`의 deterministic write-back을 구현했다. 생성 로직은 여전히 stage 2로 남겨두되, 승인된 `MetadataPlan`을 post frontmatter와 manifest에 기록한 뒤 다시 `seo_eval`로 검증하는 E2E 테스트를 추가했다.
- frontmatter description 검사를 `150~160자` 고정 길이 기준에서 `존재 여부 + semantic review evidence` 기준으로 완화했다. 고정 길이 휴리스틱을 줄이고, 품질 판단은 title/description/opening 비교로 넘긴다.
- 검증: `/tmp/hf-workflow-seo-test-venv/bin/python -m pytest skills/seo/tests` 기준 76개 테스트가 모두 통과했다.

## 현재 데이터셋 상태

`evaluation_manifest.yml` 기준 현재 케이스는 42개다.

| source type | 수량 | 정성 평가 |
|---|---:|---|
| `synthetic` | 5 | 상태 분기 smoke test로 유용하다. positive 샘플은 이전보다 현실적이지만 여전히 실제 번역글 대표성은 낮다. |
| `mutation` | 19 | failure mode 단위 검증에는 좋다. 단일 base 글 변형이 많아 일반화 근거로는 약하다. |
| `curated_internal` | 5 | 이번에 추가한 핵심 보강점이다. positive control, semantic negative, translation policy case를 분리해 보여준다. 수량은 아직 많지 않지만 최소 커버리지는 생겼다. |
| `real_hfkrew` | 13 | 실제 블로그 구조 회귀 테스트로 가치가 있다. 다만 gold label이 아니라 current behavior 관찰용이다. |

라벨 분포:

| label | 수량 | 정성 평가 |
|---|---:|---|
| `strong_positive` | 2 | 이전보다 좋아졌지만 여전히 팀 승인 gold positive는 아니다. |
| `acceptable_positive` | 7 | 내부 회귀 테스트용으로는 충분한 최소선에 가까워졌다. |
| `borderline` | 9 | 충분하다. |
| `negative` | 10 | 단순 결측뿐 아니라 semantic metadata negative가 추가되어 좋아졌다. |
| `blocker` | 4 | noindex, broken internal link, broken image path는 커버한다. HTTP/X-Robots-Tag/robots.txt는 아직 없다. |
| `real_regression` | 10 | 실제 형태 보존에는 유용하지만 품질 정답 라벨은 아니다. |

커버된 주요 현상은 40개다. 특히 `curated_gold_positive`, `semantic_metadata_negative`, `title_body_mismatch`, `hreflang_policy_review`, `hfkrew_layout_h1_ambiguity`, `source_canonical_policy_conflict`가 들어간 점은 현재 로직의 과차단/미탐 위험을 설명하는 데 중요하다.

## 직접 원문을 읽고 본 정성 판단

### 좋아진 점

`generated/excellent-post.md`와 `generated/good-post.md`는 이제 최소한 positive control로 쓸 수 있다. 이전처럼 `example.com/research`나 근거 없는 “30% 향상” 문장이 없고, 제목, 첫 문단, 소제목, 공식 근거 링크, 이미지 alt가 같은 주제를 설명한다.

`curated/realistic-positive-no-image.md`는 현재 데이터셋에서 가장 쓸 만한 positive control이다. 이미지가 없어도 통과해야 하는 케이스를 보여주며, 실제 HFKREW SEO 리뷰 업무와 직접 연결된다.

`curated/semantic-negative-description.md`와 `curated/semantic-negative-title.md`는 중요한 negative case다. 현재 deterministic body gate는 둘 다 통과할 수 있지만, 사람이 읽으면 description 또는 title이 본문과 다른 주제를 말한다는 것을 바로 알 수 있다. 이 샘플들은 “현재 로직을 통과했으니 좋은 글”이라는 주장이 틀렸음을 테스트셋 안에서 증명한다. 또한 report의 Signals 섹션과 semantic review packet에 title, description, rendered H1 후보, opening text가 함께 출력되므로, 이후 LLM policy 또는 사람 리뷰가 이 불일치를 실제 증거 기반으로 판단할 수 있다.

`curated/hreflang-policy-positive.md`는 번역 SEO 정책 케이스를 positive 방향에서 보강한다. 현재는 태그 생성까지 검증하지 않지만, canonical/hreflang 판단이 도구 단독 결정이 아니라 정책 입력을 필요로 한다는 점을 데이터셋에 남긴다.

실제 HFKREW 31개 글 audit도 계속 유지되고 있다. 결과는 `PASS 5`, `NEEDS_CHANGES 13`, `FAIL 13`, blocker `0`이다. 이 분포는 현재 checker가 실제 블로그에서 H1, description, alt, opening summary 문제를 많이 잡는다는 것을 보여주지만, 동시에 HFKREW layout과 raw markdown H1 기준이 충돌할 수 있음을 보여준다.

### 여전히 약한 점

팀이 승인한 gold positive가 없다. 현재 positive는 “내가 수동으로 보기에 reasonable”한 내부 control이지, HFKREW 콘텐츠/SEO 팀이 합의한 정답 라벨은 아니다. 다만 `reports/gold-label-review-worksheet.md`를 추가했으므로, 이 공백은 이제 “무엇을 승인해야 하는지 모르는 상태”가 아니라 “팀 리뷰만 남은 상태”로 줄었다.

`curated_internal`은 5개로 늘었지만 여전히 적다. description mismatch, title mismatch, canonical/hreflang policy case는 생겼지만, 한국어/영어 혼합 제목, 번역본-원문 관계, 생성된 JSON-LD 품질, 실제 SERP snippet 후보 같은 케이스는 아직 없다.

real fixture는 실제성을 주지만, 대부분 `description`이 누락되어 있다. 따라서 “실전 SEO gold benchmark”보다는 “현재 블로그 상태에서 로직이 어떻게 반응하는지 보는 regression set”으로 봐야 한다.

Jekyll full render 검증은 아직 없다. 현재 `render_signals.py`는 HFKREW `_layouts/post.html`의 `page.title` H1 주입을 반영하지만, Ruby/Bundler가 없어 실제 Liquid include, jekyll-seo-tag, 최종 HTML head까지 렌더링하지 못했다. H1 관련 판단은 아직 advisory 또는 evidence로 두는 것이 맞다.

metadata writer E2E는 일부 개선됐다. 승인된 `MetadataPlan`을 post frontmatter와 manifest에 write-back하고 다시 `seo_eval`로 검증하는 경로는 테스트한다. 다만 description을 생성하는 `build_plan()`은 아직 skeleton이며, 생성된 description의 의미 정합성이나 canonical/hreflang 정책 선택은 아직 policy/rubric layer가 필요하다.

## 현재 로직에 대한 판단

현재 로직은 “게시 전 명확한 구조 문제를 빠르게 발견하는 deterministic harness”로는 쓸 수 있다. 하지만 “SEO 품질을 최종 판정하는 gate”로는 아직 부족하다.

특히 다음 항목은 hard gate로 유지하면 위험하다.

- raw markdown `h1_count == 1`: HFKREW layout이 title을 H1으로 렌더링하므로 body H1 기준만으로 판단하면 오탐/역오탐이 모두 가능하다.
- `opening_summary` 길이 기준: TOC, 인용문, 공지/회고형 글에서 과차단 가능성이 있다.
- `citations >= 1`: 정보성 글에는 유용하지만 회고, 사용 안내, 프로젝트 공지에는 부적절할 수 있다.

이번 개선에서 meta description의 `150~160자` 고정 pass/fail 기준은 제거했다. description은 존재 여부만 required로 보고, 길이와 품질은 semantic review evidence에서 사람이 또는 policy layer가 판단하도록 바꿨다.

반대로 hard blocker로 유지해도 되는 항목은 비교적 명확하다.

- `robots: noindex`
- target repository 기준 깨진 내부 링크
- target repository 기준 깨진 로컬 이미지 경로
- 빈 본문 또는 사실상 게시 불가능한 본문

## 점수 재산정

| 항목 | 점수 | 이유 |
|---|---:|---|
| 문제 발견용 evidence | 8.7/10 | real audit, mutation, curated semantic negative, translation policy case, semantic review packet이 있어 현재 로직의 과차단/미탐을 잘 보여준다. |
| 회귀 테스트용 | 8.4/10 | 42개 manifest case, 76개 pytest, golden snapshot, blocker/semantic evidence/metadata write-back E2E 테스트가 있어 구현 변경 감지에는 충분하다. |
| 실전 SEO benchmark용 | 6.5/10 | positive control, metadata write-back, description 길이 휴리스틱 완화는 개선됐지만 팀 승인 gold label, full render, metadata generation policy가 없다. |
| PR gate 신뢰성 검증용 | 6.4/10 | blocker, body structure, metadata write-back, description evidence 방식은 검증되지만 GitHub Action artifact/comment 적용과 fork PR 운영은 별도 검증이 필요하다. |
| 데이터셋 설명 가능성 | 8.5/10 | rationale/limitation, semantic review packet, gold-label worksheet가 있어 팀 논의 자료로 설명하기 쉬워졌다. |

종합: **8.0/10**

이전의 8/10보다 낮지만, 이번 점수가 더 정직하다. 데이터셋은 실제로 개선됐고 내부 개발/리뷰 근거로는 쓸 수 있다. 그러나 실전 SEO benchmark라고 부르려면 아직 부족하다.

## 다음 개선이 필요하다면 우선순위

1. HFKREW 팀이 승인한 gold positive 5개를 정한다.
2. Jekyll full render 기반으로 최종 HTML의 title, H1, meta description, canonical, og tag를 검사한다.
3. description-body mismatch, title-opening mismatch, source canonical policy conflict를 policy/rubric layer에서 평가한다.
4. `metadata.build_plan()`이 생성한 description/canonical/hreflang 후보를 팀 정책에 맞게 검증한다.
5. GitHub Action sandbox에서 artifact 생성과 PR sticky comment까지 검증한다.

## 결론

현재 데이터셋은 “내부 로직 개선과 PR 리뷰 논의용”으로는 충분히 쓸 수 있는 수준까지 왔다. 하지만 “이 데이터셋을 통과하면 SEO가 좋다”는 주장은 아직 하면 안 된다.

정확한 표현은 다음이다.

```text
현재 데이터셋은 SEO checker의 blocker 처리, body 구조 검사, HFKREW layout 충돌, semantic metadata gap, metadata write-back을 검증하는 내부 평가셋으로는 적절하다.
다만 실전 SEO benchmark 또는 최종 PR gate 품질 보증으로 쓰려면 team-approved gold labels, Jekyll full render, metadata generation/policy E2E, GitHub Action E2E가 추가로 필요하다.
```
