# PR Ready Summary: SEO Skill Evaluation Dataset and Semantic/Metadata Seams

## PR 제목 제안

```text
Add SEO evaluation fixtures and semantic metadata seams
```

## 무엇을 PR하는가

이번 PR은 `skills/seo`를 실제 PR 리뷰에 올릴 수 있는 기준선으로 정리한다.

- 실제 HFKREW 블로그 글, 변형 negative 샘플, curated 샘플을 포함한 SEO 평가셋을 추가한다.
- deterministic SEO harness가 `PASS`, `NEEDS_CHANGES`, `FAIL`, `BLOCKED`를 안정적으로 구분하도록 policy/config/golden test를 보강한다.
- LLM을 직접 호출하지 않는 provider-free semantic judge seam을 추가한다.
- `semantic_metadata`와 `alt_semantics`를 분리한다.
- metadata 생성은 canonical/hreflang을 임의 추론하지 않고, 정책 입력이 없으면 `PARTIAL`로 반환한다.
- 기존 CLI와 deterministic path는 유지하고, 하위호환 테스트를 추가한다.

## 왜 PR하는가

SEO 작업의 대부분은 Lighthouse류 도구 실행보다 **결정적 검사 + 정책 판단 + 사람에게 설명 가능한 feedback**이 중요하다. 이번 PR은 그 기반을 만든다.

- 본문/메타 의미 불일치는 단순 token overlap이나 keyword density로 안정적으로 잡기 어렵다.
- 이미지 alt는 빈 alt와 “비어 있지는 않지만 무의미한 alt”를 분리해야 한다.
- 번역글 canonical/hreflang은 SEO 도구가 추론할 문제가 아니라 콘텐츠/번역 정책 결정이다.
- 실제 OpenAI API 호출이나 GitHub Action 자동 코멘트는 다음 단계로 분리하는 편이 리뷰 가능성과 안정성 면에서 낫다.

## 어떻게 구현했는가

### Evaluation harness

- deterministic checker 결과를 policy config로 required/review/recommended/optional/info로 매핑한다.
- publish safety 문제는 `BLOCKED`로 분리한다.
- body quality 문제는 실패 개수에 따라 `NEEDS_CHANGES` 또는 `FAIL`로 분리한다.
- Lighthouse/benchmark성 결과는 gate가 아니라 informational로 둔다.

### Semantic judge seam

- `signals.py`가 title, description, rendered H1, opening, heading, image detail evidence를 수집한다.
- `rubric.py`는 실제 model/provider를 직접 호출하지 않고 `judge(name, payload)`를 주입받는다.
- `semantic_metadata`는 title/description/H1/opening의 의미 불일치만 본다.
- `alt_semantics`는 non-empty alt가 `image-1`, `mcp-list`, `image/png`, 파일명형 alt처럼 무의미한지만 본다.
- 빈 alt는 LLM judge가 아니라 deterministic alt coverage checker가 계속 담당한다.

### Metadata policy seam

- `metadata.build_plan()`은 `MetadataBuildResult`를 반환한다.
- title/description 후보는 만들 수 있지만, canonical/hreflang은 `metadata_policy`가 없으면 `PARTIAL`로 남긴다.
- `target_url`, `source_url`, `canonical_policy`, `translation_indexing`, `target_locale`, `source_locale`가 모두 있어야 `READY`가 된다.
- `MetadataPlan` 필드 접근은 `MetadataBuildResult`에서 위임해 단순 plan-like 사용을 유지한다.

### Compatibility

- 기존 CLI 호출 방식은 유지한다.
- `evaluate()` / `evaluate_path()` 기존 인자는 유지하고, 새 `rubric_judge`는 optional keyword-only 인자로 추가했다.
- 기존 R1~R6 rubric score contract를 유지한다.
- JSON output은 additive 확장이다. exact schema consumer가 있다면 `signals`, `policy`, `blockers`, `rubric.checks`, `gate.status` 추가를 반영해야 한다.

## 검증 결과

전체 테스트:

```bash
/tmp/hf-workflow-seo-test-venv/bin/python -m pytest skills/seo/tests
```

결과:

```text
92 passed
```

재시뮬레이션:

```text
42 fixture deterministic statuses:
PASS 34 / FAIL 2 / BLOCKED 3 / NEEDS_CHANGES 3

31 real HFKREW posts deterministic statuses:
PASS 19 / NEEDS_CHANGES 8 / FAIL 4

31 real HFKREW posts metadata build without URL policy:
PARTIAL 31
```

LLM methodology simulation:

```text
semantic metadata fixture expected negatives:
3/3 detected

false positives:
0

real 31 post semantic metadata judge:
PASS 31 / FAIL 0 / NEEDS_CHANGES 0

real image post alt semantic judge:
PASS 11 / NEEDS_CHANGES 2 / FAIL 7
```

## 이번 PR에서 하지 않는 것

- GitHub Action에서 OpenAI API를 실제 호출하는 wiring
- PR line comment 자동 작성
- metadata 자동 commit
- canonical/hreflang 최종 콘텐츠 정책 결정
- alt semantic judge를 hard gate로 승격

## 리뷰어가 중점적으로 봐야 할 부분

- `semantic_metadata`와 `alt_semantics`를 분리한 것이 합리적인가
- alt semantic judge를 `review` severity로 둔 것이 운영상 안전한가
- `metadata_policy` 없이는 canonical/hreflang을 `PARTIAL`로 남기는 정책이 맞는가
- JSON output additive 변경을 PR 본문에 명시하면 충분한가
- fixture/golden 구조가 향후 회귀 테스트 기반으로 적절한가

## PR 본문 초안

~~~markdown
## Summary

This PR prepares the SEO skill for reviewable use by adding a broader fixture set, policy-configurable deterministic gates, semantic judge seams, and policy-aware metadata generation.

## Changes

- Add real/mutated/curated SEO fixtures and golden regression coverage.
- Add deterministic policy config and status separation: `PASS`, `NEEDS_CHANGES`, `FAIL`, `BLOCKED`.
- Add signal evidence for semantic review, including image `src`/`alt` details.
- Add provider-free `semantic_metadata` and `alt_semantics` judge seams.
- Add policy-aware `metadata.build_plan()` that returns `PARTIAL` without canonical/hreflang policy.
- Preserve CLI/deterministic-path compatibility and add backward-compatibility tests.

## Verification

```text
/tmp/hf-workflow-seo-test-venv/bin/python -m pytest skills/seo/tests
92 passed
```

Additional simulation:

- 42 fixtures: `PASS 34 / FAIL 2 / BLOCKED 3 / NEEDS_CHANGES 3`
- 31 real HFKREW posts: `PASS 19 / NEEDS_CHANGES 8 / FAIL 4`
- Metadata without URL policy: `PARTIAL 31`
- Semantic metadata judge simulation: expected negatives `3/3`, false positives `0`

## Not included

- No OpenAI API wiring in GitHub Actions yet.
- No automatic metadata commit yet.
- No final canonical/hreflang content policy decision.
- `alt_semantics` remains review-only, not a hard gate.
~~~
