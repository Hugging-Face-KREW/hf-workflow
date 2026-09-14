# 번역 품질 harness 아키텍처 (코드 직접 추적)

`skills/quality/tools/translation_quality_harness.py`를 `main`(커밋 c63d680,
`tool_version` `0.6.0`, 3568줄)에서 직접 읽어 정리한 Phase 2 참조 문서다.
도구 자체를 설명하므로, `skills/quality-transformers`가 이 harness를 그대로
호출하고 자산만 바꾼다는 점을 근거로 keep/modify 판단(Phase 3)에 쓴다.
`main` 기준으로 작성했다(pr-24의 harness는 약 390줄 이전이라 MQM 캐싱·구조화
복구·PR 리뷰 게이트 배선이 없음).

---

## 0. 실행 진입점과 CLI

`main()` (L3423) → `build_report()` (L3364) → `validate_documents()` (L2778) →
`markdown_report()`/`pr_comment_report()`.

- **필수 인자**: `--manifest`, `--target-root`, `--output-md`, `--output-json`.
- 매니페스트는 `read_simple_manifest()` (L219)가 파싱 — `<section>:` 다음 2칸
  들여쓰기 `<key>: <value>` 를 `section.key`로 평탄화. 인식 키:
  `translation.file_path`, `source.file_path`, `source.url`, `source.hash`,
  `translation.commit_sha`.
- `--source`(로컬 파일 경로)를 주면 매니페스트 `source.file_path`를 덮어씀.
  **transformers는 `--source docs/source/en/<path>`를 항상 명시**해야 함
  (`source.url` 자동 fetch는 `huggingface.co/blog/...`만 인식 — L576
  `hf_blog_raw_markdown_candidates`).
- 자산 교체 플래그: `--style-guide`, `--style-policy`, `--evaluation-config`,
  `--gates-config`, `--glossary`(복수), `--llm-judge-prompt`.
- `--qe-metric {off,heuristic,cometkiwi}` (기본 heuristic),
  `--llm-judge-provider {off,openai,fixture}` (기본 off),
  `--fail-on-reject` → status가 `reject`/`source_changed`면 exit 1.

---

## 1. 파싱 단계 — `markdown_doc()` (L638)

순서: `strip_frontmatter` → `strip_workflow_scaffold` → `strip_heading_anchors`
→ `parse_code_blocks` → 각종 정규식 추출 → `extract_segments`.

| 추출 필드 | 방법 | transformers 관련 주의 |
|---|---|---|
| `frontmatter` | `strip_frontmatter` (L236): 문서가 `---\n`으로 시작할 때만 파싱 | transformers 문서는 `<!--Copyright...`로 시작 → **`frontmatter` = `{}` 항상**. `front_matter` 하드게이트에 직접 영향 (§4) |
| `body` | frontmatter 제거 후 scaffold/앵커 제거 | `strip_workflow_scaffold` (L262)는 `> Source:`, `* TOC`, 블로그 번역 고지문, `<!-- Review instructions: -->` 주석만 제거. **transformers 라이선스 헤더 `<!--Copyright ... -->` 블록은 "Review instructions:"가 없으므로 본문에 그대로 남음** → 세그먼트로 들어가지만 원문/번역이 동일해 정렬됨 (무해) |
| 헤딩 앵커 | `strip_heading_anchors` (L310): `^#... {#slug}$` (kramdown 스타일)만 제거 | **`[[slug]]` 스타일은 제거하지 않음** → `# 프로세서[[processors]]`의 `[[processors]]`가 body에 남아 세그먼트/식별자 추출 대상이 됨 |
| `code_blocks` | `parse_code_blocks` (L314): `FENCE_RE = ^(`{3,}\|~{3,})(.*)$`. info string 무시 | ` ```cli ` , ` ```py `, ` ```bash ` 모두 정상 인식 |
| `inline_code` | `` INLINE_CODE_RE = `([^`\n]+)` `` | `` [`Trainer`] `` 안의 `` `Trainer` ``도 인라인 코드로 잡힘 |
| `link_targets` / `image_targets` | `LINK_RE`/`IMAGE_RE` (target만) | 상대 경로(`../model_doc/clip`), 외부 URL 모두 포함 |
| `urls` | body에서 마크다운 링크 제거 후 남은 bare URL | |
| `model_ids` | `MODEL_ID_RE = \b[\w.-]+/[\w.-]+\b`, `extract_model_ids` (L482)로 필터 | `syscv-community/sam-hq-vit-base` 잡힘. 상대 경로 조각(`model_doc/clip`)도 매칭될 수 있으나 원문/번역 동일하면 무해 |
| `python_identifiers` | `PY_IDENTIFIER_RE = \b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+\b` (점 있는 것) | **`[[autodoc]] data.processors.utils.DataProcessor`, `` [`~data.processors.utils.InputExample`] ``, 앵커 `[[transformers.ProcessorMixin]]`의 점 있는 경로가 여기 잡힘** → `protected_tokens`(major)로 원문 대비 비교됨. autodoc 경로형 앵커·API 참조는 이 경로로 **부분 보호됨** |
| `env_vars` | `ENV_VAR_RE = \b[A-Z][A-Z0-9]*_[A-Z0-9_]*\b` | `CUDA_VISIBLE_DEVICES`, `ZE_AFFINITY_MASK`, `HF_TOKEN` 등 |
| `cli_flags` | `CLI_FLAG_RE = (?<!\w)--[a-zA-Z0-9][\w-]*` | `--nproc_per_node` 등. ` ```cli ` 코드는 code block이라 body_without_code에서 제외 → **코드블록 안 플래그는 안 잡힘** (§3 참고, code_blocks 해시로만 커버) |
| `numbers` | `NUMBER_RE` (단위 `%,ms,s,kb…` 포함) | 벤치마크 수치 |
| `table_shapes` | 파이프 테이블의 행별 셀 수 리스트 | |
| `todo_markers` | `TODO_RE = \b(TODO\|FIXME\|TBD)\b\|\{\{\|\}\}` | 재동기화 감지에 중요 (§4) |
| `segments` | `extract_segments` (L383): 문단/헤딩/목록/표행을 정규화해 세그먼트화. `normalize_segment_text`가 링크·이미지·인라인코드 마크업을 텍스트만 남김 | 정렬의 기본 단위 |

**파싱 한계**:
- 헤딩 레벨(`#` 개수)은 세그먼트 텍스트에서 정규화되며 **별도 필드로 저장되지
  않음** → "헤딩 레벨이 원문과 같은가"를 지금 구조로는 검사 불가.
- `[[slug]]` 앵커 문자열은 헤딩 세그먼트 텍스트의 일부로만 존재. 점 없는 kebab
  앵커(`[[overview]]`, `[[xnli]]`)는 어떤 정규식 필드에도 안 잡힘.
- `[[autodoc]]`/`[[open-in-colab]]` 지시문 토큰 자체는 전용 추출 필드 없음
  (지시문 뒤 점 있는 경로만 `python_identifiers`로).

---

## 2. 세그먼트 정렬 — `align_segments()` (L826)

`zip(source.segments, target.segments)` — **순서 기반 zip**. 의미 기반 매칭
아님. `alignment_id`, `source_id/target_id`, 해시, kind, 텍스트를 쌍으로 묶음.

**한계**: 원문/번역의 세그먼트 개수가 어긋나면(문단 병합·분할, 번역자가 추가한
줄 등) 그 지점 이후 정렬이 통째로 밀린다. → MQM judge, 메트릭이 잘못된 쌍을
비교하게 됨. transformers에서 특히 주의할 케이스:
- **`model_doc` 정형 줄** `*이 모델은 …추가되었습니다.*` 이 번역본에는 있는데
  raw 영어 원문에는 없으면 target 세그먼트가 +1 → §5의 "additional text
  segments"(major) 오탐 가능. Phase 4에서 실제 model_doc 원문 쌍으로 확인 필요.

---

## 3. 하드/리뷰 게이트 — **두 개의 다른 메커니즘이 아님**

`EvaluationPolicy.severity(gate, fallback)` (L168):

```
status == "reject"           -> "critical"
status == "review_required"  -> "major"
그 외(미설정)                 -> fallback 인자
```

즉 하드게이트/리뷰게이트는 **동일한 비교 로직 + `gates.yml`의 `status` 값
차이**일 뿐이다. `gates.yml`에서 `status`만 바꾸면 심각도가 바뀐다 (로직 변경
아님).

`validate_documents()` 내 결정적(deterministic) 비교:

| 검사 | 비교 방법 | 기본 심각도 | 게이트명/옵션 |
|---|---|---|---|
| `code_blocks` | 블록 전체 sha256 해시 리스트를 **multiset(Counter) 차집합** (`compare_counter`→`counter_diff` L671) | critical | `code_blocks.compare_hashes` |
| `inline_code` | 값 리스트 multiset 차집합 | critical | `inline_code.exact_match` |
| `links` | `normalize_link_targets_for_comparison` 후 multiset 차집합 | critical | `links.exact_target_match` |
| `images` | multiset 차집합 | critical | `images.exact_target_match` |
| `bare_urls` | multiset 차집합 | major | `bare_urls.exact_match` |
| `protected_tokens` (model_ids) | multiset 차집합 | major | `protected_tokens.exact_match` |
| `protected_tokens` (python_identifiers) | multiset 차집합 | major | 〃 |
| `environment_variables` | multiset 차집합 | critical | `environment_variables.exact_match` |
| `cli_flags` | multiset 차집합 | critical | `cli_flags.exact_match` |
| `numbers` | multiset 차집합 | major | `numbers.exact_match` |
| `latex` | multiset 차집합 | critical | `latex.exact_match` |
| `tables` | `source.table_shapes != target.table_shapes` (행별 셀 수 리스트 전체 동일성) | critical | `tables.compare_shape` |
| `markdown_parse` | 펜스 미종료 등 파서 에러 | critical | `markdown_parse` |
| `front_matter` | §4 | critical | `front_matter.*` |
| `todo_markers` | §4 | critical | `todo_markers.markers` |
| `locale_punctuation` | §4 | **critical** | `locale_punctuation.forbidden` |
| `korean_ratio` | `korean_ratio(body) < min_korean_letter_ratio` | major | `korean_ratio` |
| `untranslated_english` | `english_ratio(body) > max_untranslated_english_ratio` | major | `untranslated_english` |
| `length_ratio` | §5 세그먼트 문자 수 비율 | major | `length_ratio` |
| segment coverage / 중복 | §5 | major (고정, `status`로 못 바꿈) | — |

`compare_counter` (L714)는 `counter_diff`로 missing/extra 원소를 구해 각각
issue를 만든다. **"다수결"이 아니라 다중집합(bag) 차집합**이다.

**구조적으로 없는 게이트** (transformers에 필요하지만 현재 부재):
- `[[slug]]` 앵커 문자열 보존 (점 없는 kebab 앵커)
- 헤딩 레벨(`#` 개수) 보존
- `[[autodoc]]`/`[[open-in-colab]]` 지시문 토큰 보존 (점 있는 경로만 부분 커버)
- `<Tip ...>`/`> [!WARNING]`/`<hfoptions id=...>` 컴포넌트 태그·속성 보존
- 라이선스 헤더 블록 보존/최신성

---

## 4. 설정 파서 — **하드코딩된 경로만 인식, 나머지는 조용히 무시**

### 4-A. `read_yaml_scalars()` (L1052) — `eval_config.yml` + `gates.yml`

들여쓰기 2칸 = 1레벨인 손수 만든 미니 YAML 파서. **인라인 리스트 `key: []`를
지원하지 않는다**: L1077 `if raw_value.strip():` 는 `"[]"`를 참으로 보고
`parse_yaml_scalar("[]")` → 문자열 `"[]"` 반환 (빈 리스트 아님). 여러 줄
`- item` 형식은 지원하지만, 항목이 하나도 없으면 그 키가 dict에 아예 안 생김.

`load_evaluation_policy()` (L1083)가 인식하는 **고정 경로**:
- `score.{auto_pass_score, review_required_min_score, style_review_required_min_score}`
- `language.{min_korean_letter_ratio, max_untranslated_english_ratio}`
- `length_ratio.{min_target_to_source, max_target_to_source}`
- `gates.yml`: `{hard_gates|review_gates}.<gate>.status` → `gate_statuses[gate]`,
  `{hard_gates|review_gates}.<gate>.<option>` (len 3) 또는
  `...<gate>.<option>.<subkey>` (len 4) → `gate_options`.

`EvaluationPolicy.list_option(gate, name, fallback)` (L182): 저장값이 리스트가
아니면 **fallback 반환**.

> **⚠️ transformers 필수 확인 사항**: `front_matter.required_target_keys`
> 기본값은 `["title"]` (L2828). transformers 문서는 `frontmatter == {}` 이므로
> `"title" not in target.frontmatter` → **모든 transformers 문서에서
> `front_matter` critical 이슈가 상시 발동** (100% 오탐). `gates.yml`에
> `required_target_keys: []` 를 써도 파서가 `"[]"` 문자열로 읽어 `list_option`이
> fallback `["title"]`로 돌아감 → **설정만으로는 끌 수 없음.** 여러 줄 빈
> 리스트도 키가 안 생겨 같은 결과.
> → Phase 3에서 harness 한 줄 수정(`"[]"` → 빈 리스트)을 사용자 승인 하에
> 결정. (Phase 4에서 이 패치를 적용, 블로그 테스트 회귀 없음 확인.)

### 4-B. `load_style_policy()` (L1123) — `style_policy.yml`

`StylePolicy` 데이터클래스(L139)에 필드가 있는 항목만 읽는다. **인식하는 경로**:
- `review_rules.emoji.forbid_added_emoji`
- `review_rules.list_consistency.enabled`
- `review_rules.alt_text.require_korean_when_source_english`
- `first_mention_terms.<term>.{ko, required_first}`
- 리스트 항목: `modal_strength.source_terms.<term>.- …`,
  `overstatement.risky_pairs.<pair>.- …`, `translationese.discouraged.- …`,
  `title_quality.discouraged.- …`

**그 외 키는 전부 조용히 무시된다.** `anchor_preservation`,
`directive_preservation`, `autodoc_reference_preservation`,
`mdx_component_preservation`, `style_score.max_penalty.*` 같은 키를
`style_policy.yml`에 써도 **파서가 무시한다** — 선언만으로는 실행되지 않는다.
새 스타일 규칙을 실제로 돌리려면 `validate_style_guide`에 검증 함수를 추가하고
`style_penalty` weights와 `StylePolicy`/`load_style_policy` 파서에 배선해야 함.
(이 스킬은 앵커·지시문·MDX·콜론 검증을 그렇게 harness에 직접 배선했다 — Phase
4 참고.)

---

## 5. 세그먼트 커버리지·길이 — `validate_segment_coverage()` (L845)

- `target_count < source_count` → major "coverage low" (누락)
- `target_count > source_count` → major "additional text segments" (원문에 없는
  문단 추가/원문 잔존/중복). **`gates.yml`로 심각도 조정 불가 — 코드 고정.**
- 정규화 후 20자 이상 target 세그먼트가 중복되면 → major "Duplicate target
  segments"
- 세그먼트 문자 수 비율 `target_length / source_length` 가
  `[min_target_to_source_ratio, max_target_to_source_ratio]` (기본 0.35..2.60)
  밖이면 → `severity("length_ratio", "major")`

---

## 6. 스타일 가이드 검증기 — `validate_style_guide()` (L1545)

`--disable-style-guide`가 없고 `MetricConfig.enable_style_guide`가 참일 때 실행.
`policy is None`이면 즉시 반환.

**원문 불필요** (target만): `validate_translationese`, `validate_title_style`,
`validate_intro_closing_style`, `validate_list_consistency`.
**원문 필요**: `validate_modal_strength`, `validate_overstatement`,
`validate_information_addition`, `validate_emoji_delta`,
`validate_alt_text_and_link_text`, `validate_first_mention_terms`.

`validate_locale_punctuation` (L1520)는 `validate_style_guide` **밖에서**,
`validate_documents` 본문 L2826에서 **항상** 호출된다(원문·스타일가이드 무관).
`gates.yml`의 `locale_punctuation.forbidden` 리스트(기본 `["。","、"]`)에 있는
문자열이 코드/인라인코드/링크타깃 제거한 prose에 나타나면 이슈. 심각도는
`severity("locale_punctuation", "critical")` → **기본 critical**.

| guide_rule | style_penalty 가중치 (L1567) | 비고 |
|---|---|---|
| `modal_strength` | 8 | 의미 강도 |
| `overstatement` | 8 | 과장 |
| `information_addition` | 8 | 정보 추가 |
| `locale_punctuation` | 8 | 로케일 문장부호 |
| `title_quality` | 3 | 블로그용 (transformers는 frontmatter title 없음 → no-op) |
| `intro_closing_style` | 2 | 블로그용 (하드코딩 인사말 → transformers엔 no-op) |
| `list_consistency` | 2 | |
| `emoji_delta` | 2 | |
| `alt_text_caption` | 2 | |
| `link_text_translation` | 2 | |
| `first_mention_bilingual` | 2 | 병기 |
| `translationese` | 1 | |
| (미등록 rule) | 2 (기본) | |

`style_penalty`는 각 이슈에 위 가중치 + (major면 +2), 합계 **최대 40**.

`validate_title_style`/`validate_intro_closing_style`는 transformers에서
**안전한 no-op** (frontmatter title 없음 / 블로그 인사말 문구 부재). 공유 코드를
건드릴 이유 없음.

---

## 7. 메트릭·MQM judge

- `evaluate_metrics()` (L1752): `--qe-metric heuristic` 기본. 세그먼트별
  reference-free QE 점수(길이 유사도 + 보호 토큰 겹침), 임베딩 유사도(char
  n-gram 코사인) 이상치, 선택적 chrF. `metric_cache`로 캐시.
- `validate_metric_thresholds()` (L1854): QE < `qe_review_threshold`(0.55),
  임베딩 이상치 → review 이슈.
- MQM judge (`--llm-judge-provider openai|fixture`): 정렬된 세그먼트를 프롬프트
  (`--llm-judge-prompt`)로 LLM에 보내 MQM 오류를 받아 정규화·보정
  (`normalize_mqm_result` L2227, `calibrate_mqm_error` L2066). `off`면 스킵.
- **MQM judge가 완전히 돌지 않으면**(`semantic_evaluation_complete` False)
  L3046에서 major "Semantic adequacy evaluation is incomplete" 이슈 →
  **`auto_pass` 불가**. 즉 LLM judge 없이 결정적 게이트만으로는 최대
  `review_required`.

---

## 8. 점수·상태 집계 — `validate_documents()` L3056~L3082 (정확한 공식)

```python
effective_issues = deduplicate_detector_issues(issues)          # L3056
critical         = [i for i in effective_issues if i.severity == "critical"]
major            = [i for i in effective_issues if i.severity == "major"]
minor            = [i for i in effective_issues if i.severity == "minor"]
style_issues     = [i for i in effective_issues if is_style_guide_issue(i)]   # guide_rule 있고 MQM judge 아님
non_style_major  = [i for i in major if not is_style_guide_issue(i)]
style_major      = [i for i in major if is_style_guide_issue(i)]

quality_score = max(0.0,
    100.0
    - 15.0 * len(critical)
    - 5.0  * len(non_style_major)
    - 2.0  * len(style_major)
    - 1.0  * len(minor))

if critical:
    status = "reject"
elif source_changed:                                            # 매니페스트 source.hash 불일치
    status = "source_changed"
elif quality_score >= auto_pass_score(기본 90)
     and not major and not style_issues
     and semantic_evaluation_complete:
    status = "auto_pass"
elif quality_score >= review_required_min_score(기본 75)
     or (style_issues and quality_score >= style_review_required_min_score(기본 60)):
    status = "review_required"
else:
    status = "reject"
```

`dimension_scores` (L3092): adequacy / technical_accuracy / completeness /
terminology / fluency / publishing_integrity / style_locale 를 별도 산출
(각 이슈 카테고리 개수 × 15~20 감점, style_locale은 `style_penalty`). MQM judge
평균이 있으면 adequacy/technical/fluency를 그 값으로 **하향** 클램프만 함.
`quality_score`(위 공식)와 `status` 결정에는 `dimension_scores`가 **관여하지
않는다** — 오직 이슈 심각도 카운트.

**임계값 상수 출처**: `auto_pass_score`/`review_required_min_score`/
`style_review_required_min_score` = `EvaluationPolicy` 필드 기본값 90/75/60
(L158~160), `eval_config.yml`의 `score.*`로 오버라이드. 감점 계수 15/5/2/1과
길이 비율 0.35/2.60은 **코드 상수** (`eval_config.yml`로 못 바꿈).

---

## 9. Phase 3 판단에 직접 쓰이는 한계 목록

1. `front_matter.required_target_keys` 기본 `["title"]`를 **설정으로 못 끔**
   (`[]` 파싱 버그) → transformers 100% 오탐. harness 한 줄 수정 필요.
2. `[[slug]]` kebab 앵커·헤딩 레벨·지시문 토큰·MDX 컴포넌트 보존 게이트 **부재**.
   `style_policy.yml`에 선언해도 파서가 무시 → 실제로 돌리려면 `validate_style_guide`에
   함수 추가 + `style_penalty`/`StylePolicy` 배선.
3. 문장 끝 콜론(`:`) → 마침표: `locale_punctuation.forbidden`에 `":"`를 넣으면
   URL·시각·비율 등 정당한 콜론까지 오탐. **문장 종결 콜론 전용 검증기**를 새로
   추가하는 편이 정확 (Phase 3 승인 항목).
4. 세그먼트 정렬은 순서 기반 zip → `model_doc` 정형 줄 등으로 개수가 어긋나면
   이후 정렬·MQM이 밀림.
5. LLM judge 없이는 `auto_pass` 불가 (구조상 최대 `review_required`).
6. `_toctree.yml` 정합성은 단일 소스↔타깃 비교 구조상 **자동화 불가** → 수동.
7. segment coverage/중복/length_ratio의 major 심각도는 **코드 고정** (일부는
   `gates.yml`로 조정 가능, coverage·중복은 불가).
