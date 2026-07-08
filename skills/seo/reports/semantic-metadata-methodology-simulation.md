# Semantic Metadata / Metadata Generation Simulation Report

작성일: 2026-06-30

## 결론

현재 시뮬레이션과 구현 결과는 **PR로 제출하기에 충분**하다. 다만 이 PR의 범위는 production GitHub Action 완성이 아니라, SEO skill의 평가셋/결정적 harness/semantic judge seam/metadata policy seam을 정리하는 것이다.

충분하다고 판단하는 범위는 다음이다.

- `semantic metadata mismatch`는 deterministic checker가 아니라 **증거 패킷 기반 LLM judge**로 분리해야 한다.
- `alt semantic usefulness`는 metadata semantic judge에 넣지 말고 **별도 judge**로 분리해야 한다.
- metadata 자동 생성은 title/description 생성과 canonical/hreflang 정책 결정을 분리해야 한다.
- LLM 출력은 자유 텍스트가 아니라 **JSON schema structured output**으로 받아야 한다.

이번 PR 이후에도 남는 범위는 다음이다.

- LLM의 숫자 점수는 안정적이지 않았다. `0~100` 스키마를 줬지만 실제 응답은 `9`, `90`, `4`, `12`처럼 보정되지 않은 값이 섞였다. 현재 구현은 숫자 점수를 gate에 쓰지 않고 `status`, `issues`, `problem_images` 중심의 seam만 제공한다.
- 실제 이미지 글에서 alt semantic judge가 `FAIL 7`, `NEEDS_CHANGES 2`를 냈다. 이 결과는 품질 문제를 잘 드러내지만, 기존 글을 대량 차단할 수 있으므로 처음에는 `review` 또는 `recommended` severity로 두는 것이 맞다.
- canonical/hreflang은 생성기가 추론하면 안 된다. HFKREW 콘텐츠 정책에서 번역본을 독립 색인 대상으로 볼지 먼저 결정해야 한다.

## 근거 자료

방법론은 아래 자료를 기준으로 잡았다.

- Google title link 문서: `<title>`만이 아니라 페이지의 시각적 제목, heading, 앵커 등 여러 신호가 title link에 영향을 준다. 따라서 title과 H1/opening 의미 정합성 검사가 필요하다.
  https://developers.google.com/search/docs/appearance/title-link
- Google snippet/meta description 문서: description은 snippet 후보일 뿐이며, 페이지 내용과 맞는 요약이어야 한다.
  https://developers.google.com/search/docs/appearance/snippet
- Google canonical 문서: canonical은 중복 URL의 대표 URL 정책이다. 번역본 canonical은 SEO 도구가 임의로 추론할 문제가 아니라 콘텐츠 정책 결정이다.
  https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- Google hreflang 문서: localized versions는 언어/지역별 URL 관계를 명확히 선언해야 한다.
  https://developers.google.com/search/docs/specialty/international/localized-versions
- OpenAI Structured Outputs 문서: LLM judge/generator 결과는 JSON schema로 제한해야 CI에서 검증 가능하다.
  https://platform.openai.com/docs/guides/structured-outputs
- G-Eval: LLM-as-judge를 쓸 때 평가 기준과 structured reasoning을 명시해야 한다는 근거로 참고했다.
  https://arxiv.org/abs/2303.16634
- Prometheus / LLM-as-judge 계열: rubric 기반 평가 모델은 범용 점수보다 명시적 criteria와 feedback 구조가 중요하다는 근거로 참고했다.
  https://arxiv.org/abs/2310.08491
  https://arxiv.org/abs/2306.05685

## 실행한 시뮬레이션

### 1. 구현 전 baseline 상태

명령:

```bash
/tmp/hf-workflow-seo-test-venv/bin/python -m pytest skills/seo/tests
```

결과:

```text
78 passed
```

의미:

- semantic judge seam과 policy-aware metadata build를 넣기 전 baseline이다.
- 이후 구현 후 검증 결과는 하단의 “구현 후 검증” 섹션에 별도 기록한다.

### 2. Semantic metadata judge - 42개 fixture

목표:

- title/description/H1/opening이 서로 다른 주제를 약속하는지 검출한다.
- noindex, 빈 description, 빈 alt, title 길이, citation 부족 같은 deterministic 항목은 평가하지 않는다.
- 테스트 정답 힌트가 모델에 들어가지 않도록 `label`, `phenomena`를 입력에서 제거한다.

결과 파일:

```text
/tmp/seo_semantic_metadata_judge_all_fixtures_v5_no_labels.json
```

결과 요약:

```text
PASS 39
FAIL 3
NEEDS_CHANGES 0
```

기대 semantic negative:

```text
mutated_description_body_mismatch
curated_semantic_negative_description
curated_semantic_negative_title
```

검출 결과:

```text
true positive 3/3
false positive 0
false negative 0
```

판단:

- 이 범위에서는 semantic metadata mismatch judge가 충분히 안정적이다.
- production 입력처럼 정답 힌트를 제거했을 때 오탐이 사라졌다.
- 따라서 `rubric.py`에 schema-bound semantic metadata judge를 넣는 방향은 타당하다.

### 3. Semantic metadata judge - 실제 HFKREW 31개 글

목표:

- 실제 블로그 글에서 의미 정합성 judge가 과잉 차단하지 않는지 확인한다.

결과 파일:

```text
/tmp/seo_semantic_judge_real31_v3.json
```

결과 요약:

```text
PASS 31
FAIL 0
NEEDS_CHANGES 0
```

판단:

- 실제 31개 글에서는 semantic mismatch 오탐이 없었다.
- 다만 description이 비어 있거나 비교 증거가 부족한 글에서 score가 `9`처럼 낮게 나왔다. status는 `PASS`였으므로 gate에는 score를 쓰면 안 된다.

### 4. Alt semantic judge - 실제 이미지 글 20개

목표:

- 빈 alt는 deterministic checker가 처리한다.
- LLM은 non-empty alt 중 `image-1`, `mcp-list`, `image/png`, 파일명형 alt처럼 의미 없는 문구만 판단한다.

결과 파일:

```text
/tmp/seo_alt_judge_real_image_posts_v1.json
```

결과 요약:

```text
PASS 11
NEEDS_CHANGES 2
FAIL 7
```

대표 검출 사례:

```text
2024-10-05-how-to-use-translator.md
- image-1, image-2, ... image-10

2025-09-29-building-hf-mcp-study.md
- hf-mcp-dashborad
- hf-mcp-transport-statistics
- hf-mcp-claude-test1

2025-10-20-2025-VLM.md
- d3ACkiw.png

2025-11-10-pi0-fast.md
- image/png

2025-12-28-translation-mcp-project-overview.md
- mcp-list 반복
```

판단:

- alt judge는 실제 품질 문제를 잘 드러낸다.
- 하지만 기존 글 다수를 `FAIL`로 만들 수 있으므로 v1에서는 hard gate가 아니라 advisory/review로 두는 것이 안전하다.
- `signals.py`가 현재 실제 alt 목록을 LLM evidence로 넘기지 않으므로, 코드 수정 없이는 이 judge를 정확히 붙일 수 없다.

### 5. Metadata generation - 실제 HFKREW 31개 글

목표:

- title/description 후보를 생성한다.
- canonical/hreflang은 정책 입력 없이는 생성하지 않고 `PARTIAL`로 반환한다.
- Structured Outputs에서 arbitrary dict를 피하고 `hreflang_entries: [{locale, url}]` 형태를 사용한다.

결과 파일:

```text
/tmp/seo_metadata_generation_31_simulation_v3.json
```

결과 요약:

```text
PARTIAL 31
```

모든 글에서 필요한 정책 결정:

```text
target_url
source_url
canonical_policy
translation_indexing
target_locale
source_locale
```

판단:

- title/description 생성 자체는 31개 모두 가능했다.
- canonical/hreflang은 정책 입력이 없으면 생성하지 않는 것이 맞다.
- `MetadataPlan.hreflang: dict[str, str]`는 내부 표현으로는 가능하지만, LLM structured output에서는 `hreflang_entries: list[{locale,url}]`가 안전하다.

## 현재 로직에 대한 판단

현재 deterministic checker는 “구조적 결함을 안정적으로 잡는 v1 harness”로 충분히 의미가 있다. 이번 구현으로 semantic mismatch와 metadata 자동 생성도 실제 model/provider를 직접 호출하지 않는 seam 수준까지 올라왔다.

따라서 현재 로직을 이렇게 판단해야 한다.

- `seo_eval.py`: orchestration과 gate shape는 유지하되 optional `rubric_judge`를 주입받는다.
- `signals.py`: LLM judge용 evidence로 `image_details`를 제공한다.
- `rubric.py`: 기존 R1~R6 score contract는 유지하고, narrow semantic judge 2개를 별도 seam으로 제공한다.
- `metadata.py`: `build_plan()`은 정책 인자를 받는 policy-aware generator seam으로 동작한다.
- `report.py`: signals, blockers, status를 사람이 볼 수 있게 표시한다. 실제 LLM judge 결과 표시 고도화는 다음 PR에서 다룰 수 있다.

## 구체 수정안

### 1. `skills/seo/tools/signals.py`

추가할 것:

```python
"images": {
    ...
    "image_details": [
        {"src": "...", "alt": "..."}
    ],
}
```

이유:

- 현재는 `empty_alt_count`, `filename_like_alt_count`만 있어 LLM이 alt 의미성을 판단할 수 없다.
- 하드코딩을 줄이려면 `image-1`, `mcp-list` 같은 패턴을 전부 규칙으로 늘리는 대신, 실제 alt 문구를 evidence로 넘기고 judge가 판단하게 해야 한다.

주의:

- 너무 많은 이미지는 token 비용을 늘리므로 상위 30개 정도로 제한한다.
- 빈 alt는 LLM이 아니라 deterministic coverage checker가 계속 담당한다.

### 2. `skills/seo/tools/rubric.py`

현재 R1~R6 평균 점수 contract는 하위호환을 위해 유지하고, v1에서는 아래 두 judge를 별도 seam으로 구현한다.

```python
evaluate_semantic_metadata(signals) -> RubricResult
evaluate_alt_semantics(signals) -> RubricResult
```

권장 gate:

- semantic metadata mismatch: `required` 가능
- alt semantic usefulness: 처음에는 `review` 또는 `recommended`

이유:

- semantic metadata judge는 fixture 42개에서 TP 3/3, FP 0, FN 0이었다.
- alt judge는 실제 문제를 잘 잡지만 기존 글 20개 중 9개를 non-pass로 만들었다. hard gate로 켜면 운영 충격이 크다.

구현 원칙:

- token overlap, keyword density, 한국어 조사/형태소 휴리스틱으로 의미 정합성을 흉내 내지 않는다.
- OpenAI API 사용 시 JSON schema strict output을 사용한다.
- API key가 없으면 지금처럼 `available=False`로 graceful fallback한다.
- 숫자 score는 표시용으로만 두거나 제거한다. gate는 `status`와 issue 목록으로 판단한다.

### 3. `skills/seo/tools/metadata.py`

`build_plan()`은 다음 구조의 `MetadataBuildResult`를 반환한다. 단순 plan-like 접근은 하위호환을 위해 `candidate`로 위임한다.

입력:

```python
body
frontmatter
signals
metadata_policy
source_url
target_url
target_locale
source_locale
canonical_policy
translation_indexing
```

출력:

```python
{
  "status": "READY" | "PARTIAL" | "BLOCKED",
  "candidate": {
    "title": "...",
    "description": "...",
    "canonical": "...",
    "hreflang": {
      "ko": "...",
      "en": "..."
    }
  },
  "needs_policy_decision": [...]
}
```

중요:

- LLM structured output에는 arbitrary object보다 `hreflang_entries` list를 쓰고, 내부 `MetadataPlan`에는 기존 `hreflang: dict[str, str]`를 유지한다.
- `target_url`, `source_url`, `canonical_policy`, `translation_indexing`, `target_locale`, `source_locale`가 없으면 `PARTIAL`을 반환한다.
- canonical/hreflang을 LLM이 임의 추론하지 않게 한다.

### 4. `skills/seo/tools/seo_eval.py`

통합 방식:

- deterministic checks 실행
- signals 수집
- semantic metadata judge 실행 가능하면 실행
- alt semantic judge 실행 가능하면 실행
- policy config로 각 judge severity 결정

권장 상태 매핑:

```text
semantic metadata FAIL + required => FAIL
semantic metadata NEEDS_CHANGES + required => NEEDS_CHANGES
alt semantic FAIL + review/recommended => PASS with advisory
alt semantic FAIL + required => NEEDS_CHANGES or FAIL
```

초기값:

```yaml
llm_judges:
  semantic_metadata:
    enabled: true
    severity: required
  alt_semantics:
    enabled: true
    severity: review
```

### 5. `skills/seo/tools/report.py`

추가 표시:

- semantic metadata judge status
- semantic mismatch evidence
- alt semantic problem images
- metadata generation status: `READY` / `PARTIAL`
- `needs_policy_decision`

이유:

- PR 리뷰에서 “왜 막혔는지”와 “정책 결정이 필요한지”를 분리해야 한다.
- 특히 canonical/hreflang은 SEO 코드 문제가 아니라 콘텐츠 정책 문제로 표시해야 한다.

### 6. tests

추가할 테스트:

```text
skills/seo/tests/test_rubric_semantic_metadata.py
skills/seo/tests/test_rubric_alt_semantics.py
skills/seo/tests/test_metadata_generation_policy.py
```

테스트 방식:

- 실제 API 호출은 하지 않는다.
- fixture LLM 응답을 stub으로 넣고 JSON schema parsing/gate mapping만 검증한다.
- API 통합은 별도 smoke/manual test로 둔다.

필수 regression:

- semantic mismatch 3개는 non-pass여야 한다.
- empty body, too long title, missing description, noindex는 semantic metadata judge에서 PASS여야 한다.
- meaningless alt는 alt semantic judge에서 non-pass여야 한다.
- missing alt는 alt semantic judge가 아니라 deterministic checker에서 잡혀야 한다.
- metadata policy fields가 없으면 generator는 `PARTIAL`이어야 한다.

## 충분성 평가

현재 시뮬레이션은 다음 판단에는 충분하다.

- semantic metadata mismatch는 LLM judge로 구현한다.
- alt 의미성은 별도 LLM judge로 구현한다.
- metadata 생성은 title/description 생성과 canonical/hreflang 정책 결정을 분리한다.
- LLM judge/generator 출력은 JSON schema로 제한한다.
- 숫자 점수는 gate에 쓰지 않는다.

다음 판단에는 아직 충분하지 않다.

- 실제 PR에서 몇 개를 blocker로 막을지 결정
- alt semantic judge를 required로 올릴지 결정
- canonical/hreflang 최종 정책 결정
- Search Console 성과 개선 여부 판단

이번 PR에는 다음 구현을 반영했다.

1. `signals.py`에 `image_details` 추가
2. `rubric.py`에 semantic metadata judge와 alt semantic judge를 schema-bound 방식으로 구현
3. `metadata.py`에 policy-aware `build_plan()` 구현
4. API 호출 없는 stub 기반 regression test 추가
5. 실제 API smoke test는 별도 명령으로 수동 실행하도록 남김
6. alt semantic judge는 처음에는 advisory로만 표시

## 구현 후 검증

위 수정안 중 1~4는 현재 코드에 반영했다.

반영한 파일:

```text
skills/seo/tools/signals.py
skills/seo/tools/rubric.py
skills/seo/tools/metadata.py
skills/seo/tools/seo_eval.py
skills/seo/tools/policy.py
skills/seo/config/default-policy.yml
skills/seo/tests/test_signals.py
skills/seo/tests/test_rubric_semantic_judges.py
skills/seo/tests/test_metadata_e2e.py
skills/seo/tests/test_backward_compatibility.py
skills/seo/tests/golden/*.json
```

구현 내용:

- `signals.py`: `images.image_details`를 추가해 LLM alt judge가 실제 `src`/`alt` evidence를 받도록 했다.
- `rubric.py`: 기존 offline fallback을 유지하되 `evaluate_from_signals()`를 추가했다. `semantic_metadata`와 `alt_semantics`를 별도 judge로 분리했고, 실제 model/provider는 `judge(name, payload)`로 주입하게 했다.
- `seo_eval.py`: optional `rubric_judge`를 받아 schema-bound judge 결과를 gate에 통합한다. judge가 없으면 기존 deterministic/offline 동작을 유지한다.
- `metadata.py`: `build_plan()`을 구현했다. title/description 후보는 만들 수 있지만, canonical/hreflang은 `metadata_policy`가 없으면 `PARTIAL`로 남긴다.
- `policy.py` / `default-policy.yml`: `llm_judges` 설정을 추가했다. 기본은 semantic metadata `required`, alt semantics `review`이며, 실제 judge 함수가 연결된 경우에만 실행된다.
- `test_backward_compatibility.py`: 기존 R1~R6 score contract와 plan-like metadata 사용을 검증한다.

검증 명령:

```bash
/tmp/hf-workflow-seo-test-venv/bin/python -m pytest skills/seo/tests
```

결과:

```text
92 passed
```

구현 후 재시뮬레이션:

```text
fixture deterministic statuses:
PASS 34 / FAIL 2 / BLOCKED 3 / NEEDS_CHANGES 3

real 31 deterministic statuses:
PASS 19 / NEEDS_CHANGES 8 / FAIL 4

real 31 metadata build statuses without URL policy:
PARTIAL 31
```

현재 상태 판단:

- 내부 테스트와 방법론 시뮬레이션 기준으로는 semantic metadata / alt semantics / metadata policy separation 구조가 충분한 수준까지 올라왔다.
- 아직 남은 것은 실제 OpenAI API 호출을 production path에 직접 연결하는 일이 아니라, Action/CLI에서 어떤 조건에서 `rubric_judge`를 주입할지 결정하는 orchestration 작업이다.
- alt semantics는 검출력이 있지만 실제 이미지 글 다수를 non-pass로 만들 수 있으므로, 현재처럼 `review` severity가 맞다.
