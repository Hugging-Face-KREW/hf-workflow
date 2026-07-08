# SEO Skill Improvement Proposal

작성 시점: 2026-06-29

목적: 현재 `skills/seo`의 평가 로직을 실제 테스트셋과 외부 근거로 재검토하고, 하드코딩을 줄이면서 더 범용적인 SEO review skill로 개선하기 위한 수정 위치와 설계를 확정한다.

## 결론

현재 skill은 "테스트가 통과하는 상태"이지만, 평가기로서 충분히 안정적이라고 보기는 어렵다. 문제는 테스트 부재가 아니라 gate의 층위가 섞여 있다는 점이다.

- `noindex`, 깨진 내부 링크, 깨진 로컬 이미지처럼 게시 안정성을 해치는 항목은 deterministic hard blocker로 유지해야 한다.
- `H1 개수`, `도입부 길이`, `citation 존재 여부`처럼 page type과 렌더링 방식에 따라 의미가 달라지는 항목은 hard gate에서 빼고 policy/advisory layer로 내려야 한다.
- `title-description-body mismatch`, 의미 없는 alt, canonical/hreflang 정책 충돌처럼 의미 판단이 필요한 항목은 현재 deterministic checker만으로는 잡히지 않으므로 schema-bound LLM policy judge가 필요하다.
- metadata writer는 바로 자동 생성부터 붙이면 위험하다. 먼저 canonical/hreflang/content policy를 입력으로 받는 계약을 확정하고, 정책이 없으면 후보만 만들고 적용은 막아야 한다.

따라서 권장 구조는 다음 3층이다.

```text
Layer 1. Deterministic hard blockers
  - indexability/publish-safety/link-integrity/file-integrity
  - 실패 시 BLOCKED

Layer 2. Deterministic evidence signals
  - title, description, opening, rendered H1, heading structure, image/alt/link/citation signals
  - 자체로 pass/fail을 확정하지 않고 JSON evidence로 노출

Layer 3. Policy/rubric judge
  - page_type, translation policy, semantic_review packet, evidence signals를 입력
  - JSON schema로만 출력
  - FAIL/NEEDS_CHANGES/ADVISORY를 결정하되 human review 가능하게 rationale 포함
```

## 현재 코드 기준 확인

최신 worktree 기준 전체 테스트는 통과한다.

```bash
/tmp/hf-workflow-seo-test-venv/bin/python -m pytest skills/seo/tests
```

결과:

```text
76 passed
```

현재 보강된 데이터셋은 다음을 포함한다.

- generated quality gradient
- mutated negative/blocker fixtures
- curated semantic negative/positive fixtures
- 실제 HFKREW 글 fixtures
- 31개 실제 블로그 글 audit 결과
- golden snapshot regression

하지만 이 결과는 "현재 코드가 의도한 대로 돈다"는 증거이지 "현재 정책이 SEO 관점에서 충분하다"는 증거는 아니다.

## 외부 근거 조사 요약

### Google Search Central

Google의 SEO Starter Guide는 SEO를 검색엔진이 콘텐츠를 이해하도록 돕고 사용자가 검색결과에서 방문 여부를 판단하게 하는 작업으로 설명한다. 또한 Search Essentials를 따른다고 특정 페이지의 색인이나 순위가 보장되는 것은 아니며, 고정 점수보다 crawl/index/understand 가능성이 중요하다.

근거:

- https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- https://developers.google.com/search/docs/fundamentals/creating-helpful-content

title link 문서는 `<title>`뿐 아니라 시각적 제목, heading, `og:title`, 앵커 텍스트 등 여러 신호가 title link 생성에 쓰일 수 있음을 설명한다. 따라서 raw markdown H1 개수 하나만으로 게시 차단을 판단하는 것은 부정확하다.

근거:

- https://developers.google.com/search/docs/appearance/title-link

snippet/meta description 문서는 meta description이 snippet에 사용될 수 있지만 항상 그대로 쓰이지 않으며, 페이지 내용을 정확히 요약하는 고유 description이 중요하다고 설명한다. 따라서 description 길이만으로 품질을 hard gate하는 방식은 부적절하다.

근거:

- https://developers.google.com/search/docs/appearance/snippet

canonical 문서는 중복 URL 중 대표 URL을 명시하는 방식이며, 절대 URL과 일관성이 중요하다. 번역본 canonical을 self로 둘지 source로 둘지는 checker가 임의로 결정할 문제가 아니라 콘텐츠 색인 정책이다.

근거:

- https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls

hreflang 문서는 번역/지역 버전의 대체 페이지를 명시하는 신호이며, 각 언어 버전이 자기 자신과 다른 언어 버전을 함께 나열해야 한다고 설명한다. HFKREW 번역글에는 canonical/hreflang 정책 입력이 필요하다.

근거:

- https://developers.google.com/search/docs/specialty/international/localized-versions

### Lighthouse

Lighthouse SEO audit는 meta description 존재 같은 기계적 항목을 검사하는 데 유용하지만, description의 의미 품질이나 본문과의 정합성까지 평가하지 않는다. CI에서는 technical smoke gate로만 쓰고, 콘텐츠 품질 판정은 별도 layer가 필요하다.

근거:

- https://developer.chrome.com/docs/lighthouse/seo/

### Naver Search Advisor

Naver 공식 문서는 robots.txt, canonical, 검색로봇 접근 허용 같은 기술적 조건을 강조한다. 한국어 블로그 대상이면 Google 전용이 아니라 Naver용 robots/canonical/site status 검증도 optional scope로 분리하는 것이 맞다.

근거:

- https://searchadvisor.naver.com/guide/seo-basic-robots
- https://searchadvisor.naver.com/guide/markup-structure
- https://searchadvisor.naver.com/guide/seo-basic-intro

### 관련 오픈소스 프로젝트

HTMLProofer는 렌더링된 HTML에서 이미지 alt, 내부 이미지, 내부 링크, 외부 링크, OpenGraph metadata 등을 검사한다. README에서도 CI 신뢰성을 위해 주관적 검사보다 문서화된 표준과 추적 가능한 오류를 선호한다고 설명한다. 이 방향은 현재 skill의 deterministic layer에 적합하다.

근거:

- https://github.com/gjtorikian/html-proofer

lychee는 Markdown/HTML/reStructuredText/웹사이트의 깨진 URL을 찾는 Rust 기반 link checker다. 현재 내부 링크/외부 링크 검증을 자체 구현으로 키우기보다, 장기적으로 link integrity는 lychee/html-proofer 계열로 위임하는 편이 낫다.

근거:

- https://github.com/lycheeverse/lychee

markdownlint는 Markdown/CommonMark style checker다. heading hierarchy 같은 형식 규칙은 SEO checker 내부 hardcode보다 markdownlint-compatible rule 또는 configurable policy로 분리하는 편이 재사용성이 높다.

근거:

- https://github.com/DavidAnson/markdownlint

Vale는 prose lint/style guide 도구다. "문체", "금지 표현", "번역투" 같은 팀 스타일 규칙은 SEO hard gate가 아니라 Vale-style external policy로 분리하는 것이 맞다.

근거:

- https://vale.sh/docs/

### LLM-as-judge 논문과 프롬프트 설계

G-Eval은 LLM 평가를 chain-of-thought와 form-filling으로 구조화하면 사람 평가와의 상관이 개선될 수 있음을 보였다. SEO skill에는 "자유 서술형 리뷰"보다 schema-bound form filling이 맞다.

근거:

- https://arxiv.org/abs/2303.16634
- https://aclanthology.org/2023.emnlp-main.153/

Prometheus는 customized score rubric과 reference material을 함께 제공할 때 fine-grained evaluation 성능이 좋아진다는 점을 보여준다. SEO skill도 rubric만 던지는 방식이 아니라 evidence packet, page type, policy, source hints를 함께 줘야 한다.

근거:

- https://arxiv.org/abs/2310.08491
- https://github.com/prometheus-eval/prometheus

MT-Bench/Chatbot Arena의 LLM-as-a-judge 연구는 강한 LLM judge가 사람 선호와 높은 일치도를 보일 수 있지만 position, verbosity, self-enhancement bias 같은 한계가 있음을 지적한다. 따라서 LLM judge는 단독 hard blocker가 아니라 deterministic evidence와 human review가 가능한 structured rationale로 제한해야 한다.

근거:

- https://arxiv.org/abs/2306.05685
- https://openreview.net/forum?id=uccHPGDlao

OpenAI structured outputs는 모델 출력을 JSON schema에 맞추는 방법을 제공한다. CI에서 GPT 결과를 쓰려면 free-form markdown이 아니라 JSON schema 검증이 필수다.

근거:

- https://platform.openai.com/docs/guides/structured-outputs

## 실제 시뮬레이션 결과

기존 테스트셋과 실제 HFKREW 31개 글을 대상으로 policy variant를 비교했다. 결과 파일:

- `skills/seo/reports/skill-improvement-simulation.json`
- `skills/seo/reports/skill-improvement-simulation.md`

재현 명령:

```bash
/tmp/hf-workflow-seo-test-venv/bin/python skills/seo/tools/simulate_policy_variants.py \
  --manifest skills/seo/tests/fixtures/evaluation_manifest.yml \
  --posts-dir /home/hong/code/hugging-face-krew.github.io/_posts \
  --json skills/seo/reports/skill-improvement-simulation.json \
  --markdown skills/seo/reports/skill-improvement-simulation.md
```

주의: internal link/local image blocker는 `target_root`가 제공될 때만 실제 파일 resolve를 수행한다. 위 기본 시뮬레이션은 기존 비교 결과와 맞추기 위해 target root 없이 돌린 값이다. GitHub Action 또는 실제 repo audit에서는 반드시 `--target-root` 또는 이에 상응하는 repo root를 전달해야 한다.

### Fixtures 42개

| variant | result |
|---|---|
| current | `{'PASS': 22, 'NEEDS_CHANGES': 11, 'FAIL': 7, 'BLOCKED': 2}` |
| demote_h1 | `{'PASS': 28, 'NEEDS_CHANGES': 9, 'FAIL': 3, 'BLOCKED': 2}` |
| demote_contextual | `{'PASS': 35, 'FAIL': 2, 'BLOCKED': 2, 'NEEDS_CHANGES': 3}` |
| blockers_plus_structural | `{'PASS': 35, 'FAIL': 2, 'BLOCKED': 2, 'NEEDS_CHANGES': 3}` |
| blockers_only | `{'PASS': 40, 'BLOCKED': 2}` |

### 실제 HFKREW 글 31개

| variant | result |
|---|---|
| current | `{'NEEDS_CHANGES': 13, 'FAIL': 13, 'PASS': 5}` |
| demote_h1 | `{'PASS': 13, 'NEEDS_CHANGES': 13, 'FAIL': 5}` |
| demote_contextual | `{'PASS': 19, 'NEEDS_CHANGES': 8, 'FAIL': 4}` |
| blockers_plus_structural | `{'PASS': 19, 'NEEDS_CHANGES': 8, 'FAIL': 4}` |
| blockers_only | `{'PASS': 31}` |

### 해석

`demote_contextual`은 실제 글 과차단을 크게 줄인다. 특히 HFKREW layout에서 frontmatter title이 H1으로 렌더링되는 구조 때문에 raw markdown H1 gate로 막히던 글이 다수 풀린다.

하지만 `blockers_only`는 너무 느슨하다. negative fixture 대부분이 PASS가 된다. 즉 "hardcoded threshold를 없애자"는 방향은 맞지만, 모든 deterministic rule을 제거하면 semantic negative와 저품질 글을 통과시키는 문제가 생긴다.

따라서 최종 방향은 다음이다.

- 하드코딩된 길이/개수 기준을 줄인다.
- 대신 deterministic evidence를 더 풍부하게 만든다.
- semantic 판단은 structured LLM judge와 human label 기반 회귀 테스트로 옮긴다.

## 현재 로직의 구체 문제

### 1. `opening_summary`가 hardcoded required gate다

위치:

- `skills/seo/tools/checkers/content.py:37`
- `skills/seo/tools/checkers/content.py:41`
- `skills/seo/tools/checkers/content.py:45`
- `skills/seo/tools/checkers/content.py:50`

문제:

- 한국어 150자, 영어 50단어라는 기준이 모든 글 유형에 일괄 적용된다.
- 회고, 공지, 짧은 사용 안내, 번역 원문 구조 보존 글에서는 과차단이 발생한다.
- Google helpful content 원칙은 "고정 단어 수"가 아니라 사용자가 찾는 내용을 실제로 제공하는지에 가깝다.

수정:

- `opening_summary`를 required에서 `review` 또는 `recommended`로 내린다.
- `signals.opening.first_real_paragraph_chars`와 `semantic_review.opening_text`는 유지한다.
- policy judge가 page_type별로 "도입부가 주제를 충분히 요약하는지"를 판정한다.

### 2. `h1_count == 1`이 raw markdown 기준 required gate다

위치:

- `skills/seo/tools/checkers/content.py:76`
- `skills/seo/tools/checkers/content.py:80`
- `skills/seo/tools/checkers/content.py:81`

문제:

- HFKREW Jekyll layout은 frontmatter title을 H1으로 렌더링할 수 있다.
- raw markdown body에 H1이 없다는 이유로 실패시키면 false negative가 생긴다.
- raw markdown body에 H1이 1개 있다는 이유로 통과시키면 실제 렌더 HTML에서는 layout H1 + body H1이 되어 false positive가 생길 수 있다.

수정:

- raw markdown H1 gate를 제거하거나 advisory로 내린다.
- `render_signals.extract_render_signals()`의 `rendered_effective_h1_count`를 우선 사용한다.
- 최종적으로는 Jekyll full render 후 HTML parser로 `<h1>`을 검사한다.

### 3. `citations >= 1`이 모든 글에 required다

위치:

- `skills/seo/tools/checkers/content.py:86`
- `skills/seo/tools/checkers/content.py:90`
- `skills/seo/tools/checkers/content.py:91`

문제:

- 정보성 기술 글에는 citation이 중요하지만, 프로젝트 공지/행사 회고/사용 안내에는 항상 필수라고 보기 어렵다.
- Citation count 자체도 링크의 권위나 문맥 적합성을 보장하지 않는다.

수정:

- default는 `recommended`로 내린다.
- `page_type: research | technical_explainer | benchmark` 같은 policy에서만 required로 승격한다.
- LLM judge는 citation이 "있는지"보다 "주장의 근거로 작동하는지"를 평가한다.

### 4. alt 품질이 형식 rule에 머문다

위치:

- `skills/seo/tools/checkers/images.py:54`
- `skills/seo/tools/checkers/images.py:66`
- `skills/seo/tools/checkers/images.py:76`
- `skills/seo/tools/checkers/images.py:85`

문제:

- 빈 alt와 파일명 alt는 잡지만, `참고 이미지`, `image-1`, `screenshot` 같은 무의미한 alt를 안정적으로 잡기 어렵다.
- 반대로 장식 이미지에는 빈 alt가 적절할 수 있는데, 현재는 모든 이미지에 동일하게 요구한다.

수정:

- `alt_text_coverage`는 deterministic signal로 유지하되 required 여부는 policy로 결정한다.
- HTMLProofer/axe/pa11y 계열의 접근성 관점과 결합한다.
- semantic judge에는 `image src`, `alt`, 주변 문단 일부를 전달해 alt가 본문 맥락을 설명하는지 평가하게 한다.

### 5. semantic metadata negative를 현재 gate가 통과시킨다

위치:

- `skills/seo/tools/rubric.py:78`
- `skills/seo/tools/rubric.py:91`
- `skills/seo/tools/seo_eval.py:153`
- `skills/seo/tools/seo_eval.py:159`

문제:

- `rubric.py`가 skeleton이라 title/description/body mismatch가 PASS될 수 있다.
- 실제 manifest에는 `semantic_metadata_negative`, `title_body_mismatch`, `description_body_mismatch` 케이스가 존재하지만 현재 deterministic gate는 이 문제를 직접 차단하지 못한다.

수정:

- `rubric.evaluate()`를 실제 OpenAI structured output 기반 judge로 구현한다.
- 입력은 전체 본문 raw가 아니라 `signals.semantic_review`, heading summary, link/image summary, page policy로 제한한다.
- 출력은 JSON schema로 검증한다.

### 6. metadata generation policy contract가 없다

위치:

- `skills/seo/tools/metadata.py:51`
- `skills/seo/tools/metadata.py:60`

문제:

- `apply()`는 구현되어 있지만 `build_plan()`은 없다.
- canonical/hreflang은 정책 없이 자동 확정하면 위험하다.
- 번역본을 독립 색인 대상으로 볼지, 원문 보조 자료로 볼지에 따라 canonical이 달라진다.

수정:

- `manifest.handoff.seo.policy`를 명시적으로 받는다.
- policy가 없으면 `build_plan()`은 `needs_policy_decision`을 반환하고 canonical/hreflang을 적용하지 않는다.
- title/description 후보는 만들 수 있지만, write-back은 approval flag가 있을 때만 한다.

## 권장 수정안

### A. Severity를 코드 하드코딩이 아니라 policy config로 분리

새 파일:

- `skills/seo/config/default-policy.yml`
- `skills/seo/config/hfkrew-translation-policy.example.yml`

예시:

```yaml
version: 1
profiles:
  default_article:
    hard_blockers:
      - robots_noindex
      - broken_internal_link
      - broken_local_image
      - empty_body
    required:
      - heading_hierarchy
      - primary_topic_present
    review:
      - opening_summary
      - citations
      - semantic_metadata_alignment
      - alt_semantic_quality
    advisory:
      - internal_links
      - word_count
      - webp_format
      - lazy_loading

  hfkrew_translation:
    extends: default_article
    canonical_policy: needs_explicit_decision
    hreflang_policy: needs_explicit_decision
    raw_markdown_h1: advisory
    rendered_h1: review
```

수정 위치:

- `skills/seo/tools/seo_eval.py`
- `skills/seo/tools/checkers/content.py`
- `skills/seo/tools/checkers/images.py`

핵심 변경:

- checker는 `severity`를 최종 결정하지 않고 `name`, `passed`, `evidence`, `default_severity`를 반환한다.
- `seo_eval.py`가 policy config를 적용해 final severity를 계산한다.
- 기존 golden test는 default policy 기준으로 유지하되, policy override test를 추가한다.

### B. Deterministic checker를 "판정기"에서 "증거 수집기"로 낮추기

수정 위치:

- `skills/seo/tools/checkers/content.py`
- `skills/seo/tools/checkers/images.py`
- `skills/seo/tools/signals.py`
- `skills/seo/tools/report.py`

원칙:

- deterministic layer가 잘하는 것: 존재 여부, 파싱 가능 여부, 파일 존재 여부, 링크 resolve 여부, noindex 여부.
- deterministic layer가 못하는 것: 글이 사용자의 의도를 충족하는지, description이 본문을 정확히 요약하는지, alt가 의미 있는지, citation이 권위 있는지.

구체 변경:

- `opening_summary`: required -> review evidence
- `citations`: required -> page_type-dependent review
- `h1_count`: raw markdown required -> rendered evidence
- `descriptive_alt_text`: required -> review, 단 empty alt는 policy에 따라 required 가능
- `image_files_exist`: blocker로 이동

### C. LLM judge를 JSON schema로 구현

수정 위치:

- `skills/seo/tools/rubric.py`
- `skills/seo/tools/seo_eval.py`
- `skills/seo/tests/test_rubric_policy.py` 추가

입력:

```json
{
  "page_type": "translation_article",
  "primary_keyword": "...",
  "source_url": "...",
  "policy": {
    "canonical_policy": "self | source | needs_review",
    "hreflang_required": true
  },
  "signals": {
    "title_text": "...",
    "description_text": "...",
    "opening_text": "...",
    "rendered_h1_texts": ["..."],
    "headings": [],
    "links": {},
    "images": {}
  }
}
```

출력 schema:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["status", "scores", "findings", "metadata_decision", "confidence"],
  "properties": {
    "status": {
      "type": "string",
      "enum": ["PASS", "NEEDS_CHANGES", "FAIL", "NEEDS_POLICY_DECISION"]
    },
    "scores": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "intent_alignment",
        "metadata_alignment",
        "opening_usefulness",
        "heading_usefulness",
        "alt_usefulness",
        "citation_quality"
      ],
      "properties": {
        "intent_alignment": {"type": "integer", "minimum": 1, "maximum": 5},
        "metadata_alignment": {"type": "integer", "minimum": 1, "maximum": 5},
        "opening_usefulness": {"type": "integer", "minimum": 1, "maximum": 5},
        "heading_usefulness": {"type": "integer", "minimum": 1, "maximum": 5},
        "alt_usefulness": {"type": "integer", "minimum": 1, "maximum": 5},
        "citation_quality": {"type": "integer", "minimum": 1, "maximum": 5}
      }
    },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["severity", "code", "evidence", "recommendation"],
        "properties": {
          "severity": {"type": "string", "enum": ["required", "review", "advisory"]},
          "code": {"type": "string"},
          "evidence": {"type": "string"},
          "recommendation": {"type": "string"}
        }
      }
    },
    "metadata_decision": {
      "type": "object",
      "additionalProperties": false,
      "required": ["title_ok", "description_ok", "canonical_ok", "hreflang_ok"],
      "properties": {
        "title_ok": {"type": "boolean"},
        "description_ok": {"type": "boolean"},
        "canonical_ok": {"type": "boolean"},
        "hreflang_ok": {"type": "boolean"}
      }
    },
    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
  }
}
```

프롬프트 원칙:

```text
You are a Korean technical SEO policy judge.
Evaluate only the provided evidence packet. Do not invent page content.
Do not penalize a page for missing arbitrary word counts.
Distinguish hard publishing blockers from editorial improvements.
If canonical/hreflang policy is missing, return NEEDS_POLICY_DECISION instead of guessing.
Return JSON only, matching the provided schema.
```

### D. Metadata writer는 정책 없이는 canonical/hreflang을 확정하지 않기

수정 위치:

- `skills/seo/tools/metadata.py`
- `skills/seo/tests/test_metadata_e2e.py`

새 입력:

```yaml
handoff:
  seo:
    policy:
      page_type: translation_article
      target_locale: ko-KR
      source_locale: en
      translation_indexing: independent
      canonical_policy: self
      hreflang_policy: bidirectional
      metadata_apply_requires_approval: true
```

동작:

- title/description 후보는 본문 evidence와 source_url을 기준으로 생성한다.
- canonical/hreflang은 policy가 있으면 생성하고, 없으면 `needs_policy_decision`에 넣는다.
- `apply()`는 이미 승인된 `MetadataPlan`만 반영한다. 이 구조는 유지한다.

### E. Full render 기반 검증 추가

수정 위치:

- `skills/seo/tools/render_signals.py`
- `skills/seo/tools/sample_audit.py`
- GitHub Action workflow

단기:

- 현재 approximation 유지하되 report에 "approximate render signal"임을 명시한다.

중기:

- Jekyll build 후 `_site` HTML을 대상으로 검사한다.
- HTMLProofer 또는 custom BeautifulSoup parser로 `<title>`, meta description, canonical, og tags, rendered H1, internal links, images를 확인한다.

## 우선순위

### P0: 현재 과차단과 오탐을 줄이는 최소 수정

1. `opening_summary`, `citations`, raw `h1_count`를 hard required에서 내린다.
2. `empty_body`, `noindex`, broken internal link, broken local image를 hard blocker로 명확히 분리한다.
3. `semantic_review` packet을 PR comment에 노출한다.
4. `rubric.py`는 아직 GPT를 붙이지 않더라도 schema와 fixture stub test를 먼저 만든다.

### P1: LLM policy judge 연결

1. OpenAI structured output 기반 judge를 `rubric.py`에 구현한다.
2. API key가 없거나 fork PR이면 deterministic-only mode로 graceful fallback한다.
3. semantic negative fixture는 mock judge로 FAIL/NEEDS_CHANGES가 나는지 회귀 테스트한다.

### P2: metadata generation

1. `build_plan()`을 policy-aware로 구현한다.
2. canonical/hreflang policy 없이는 적용하지 않는다.
3. metadata 후보는 `metadata-suggestion.json`으로 남기고, write-back은 별도 승인 뒤 한다.

### P3: rendered HTML/Action E2E

1. Jekyll full render 후 HTMLProofer/lychee 계열 검사 추가.
2. sandbox repo에서 composite action E2E를 정기 실행.
3. fork PR 보안 때문에 GPT judge는 maintainer-trigger 또는 split workflow로 분리.

## 다음 테스트 설계

현재 테스트셋은 내부 회귀용으로는 양호하지만, 최종 benchmark로는 부족하다. 특히 gold label이 사람 합의로 확정되지 않았다.

추가해야 할 테스트:

- `test_policy_severity_override.py`: 같은 checker result라도 policy profile에 따라 severity가 바뀌는지 확인
- `test_rubric_schema.py`: LLM judge output JSON schema 검증
- `test_semantic_negative_with_stub_judge.py`: title/body mismatch, description/body mismatch, meaningless alt가 deterministic pass라도 policy judge에서 걸리는지 확인
- `test_metadata_policy_required.py`: canonical/hreflang policy가 없으면 metadata plan이 NEEDS_POLICY_DECISION으로 멈추는지 확인
- `test_rendered_html_signals.py`: Jekyll build output에서 rendered H1/head metadata를 검사

## 현재 전달해야 할 판단

팀에 전달할 메시지는 다음이 가장 정확하다.

```text
현재 SEO skill은 테스트셋을 보강했고 전체 76개 테스트는 통과합니다.
다만 이 green test는 현재 구현의 회귀 안정성을 의미할 뿐, 평가 정책이 완성됐다는 뜻은 아닙니다.

실제 31개 HFKREW 글과 42개 fixture로 시뮬레이션한 결과,
raw markdown H1, opening length, citation count 같은 contextual rule을 hard gate로 쓰면 실제 글을 과하게 막습니다.
반대로 blocker-only로 완화하면 semantic negative가 통과합니다.

따라서 v1 개선 방향은 hardcoded 점수표가 아니라
1) deterministic hard blocker,
2) deterministic evidence signal,
3) schema-bound LLM policy judge
의 3층 구조로 가는 것입니다.

우선 P0에서는 H1/opening/citation hard gate를 내리고,
noindex/broken link/broken image/empty body만 BLOCKED로 유지하며,
semantic metadata mismatch는 rubric layer로 옮기겠습니다.
canonical/hreflang은 SEO 도구가 임의 결정하지 않고 번역/콘텐츠 정책 입력을 받은 뒤 적용합니다.
```

## 완료 기준

이 개선이 완료됐다고 말하려면 다음 증거가 필요하다.

- policy config가 있고 checker severity가 코드 상수만으로 결정되지 않는다.
- semantic negative fixture가 deterministic pass여도 policy judge layer에서 잡힌다.
- real HFKREW 31개 글 audit에서 site layout 때문에 생기는 H1 false negative가 줄어든다.
- metadata generation은 canonical/hreflang policy 없이 write-back하지 않는다.
- pytest뿐 아니라 sandbox GitHub Action E2E가 통과한다.

현재 상태는 "보강된 테스트셋과 문제 분석 완료, 개선 방향 확정" 단계다. 아직 "개선 구현 완료" 상태는 아니다.
