# transformers 한국어 문서 번역 품질 스킬 빌드 플랜 (Phase 3)

Phase 1(`blog-vs-transformers-docs-differences.md`)과 Phase 2
(`quality-harness-architecture.md`)를 결합해 파이프라인의 모든 평가 항목을
분류한다. **이 문서가 Phase 4 구현의 유일한 입력이다** — 여기 없는 변경은
Phase 4에서 즉흥적으로 하지 않는다.

분류 기준: Keep / 자산만 재설정 / 완화·강화 / 비활성화 / 새 파싱 필요 /
새 게이트·검증기 필요 / 구조적으로 불가능.

사용자 승인 완료(2026-08-29):
- **D1**: `front_matter` 오탐은 harness 1줄 additive 패치로 해결.
- **D2**: 앵커·지시문·autodoc 참조·MDX 컴포넌트 보존 게이트 4개를 **`reject`
  (하드/critical) 등급**으로 신규 추가.
- **D3**: 문장 종결 콜론(→마침표, 예외 없는 규칙)은 **전용 결정적 검증기**로
  추가, `review_required` 등급 + `style_penalty` 가중치 8.

---

## 1. 평가 항목별 keep/modify/new 결정

| 평가 항목 | 분류 | 무엇이 바뀌나 | 근거 (Phase 1/2) |
|---|---|---|---|
| `markdown_parse` 하드게이트 | **Keep** | 없음 | P2 §3. 펜스 미종료 검사, 장르 무관 |
| `front_matter` 하드게이트 | **비활성화 (+ harness 1줄 수정)** | `gates.yml`에 `required_target_keys: []`, `preserved_source_keys: []`. 파서가 `key: []`를 빈 리스트로 읽도록 `read_yaml_scalars` 한 줄 additive 패치 | P1-A 메타데이터; P2 §4-A. transformers는 `frontmatter=={}` → 현재 100% 오탐. 라이선스 헤더 주석 블록이 frontmatter 역할을 대신하지만 별도 검증은 D2의 새 게이트/`todo_markers`/MQM로 커버 |
| `code_blocks` 하드게이트 | **완화 (reject→review_required)** | `gates.yml` `code_blocks.status: review_required` | P1-C 코드 주석 번역. #41340에서 `# 2D location…`→`# 이미지 내 창문의 2차원 위치` 실제 병합. 실행 토큰은 아래 하드게이트가 계속 보호 |
| `inline_code` 하드게이트 | **Keep** | 없음 (reject, exact) | P1-C. `` `Trainer` `` 등 |
| `environment_variables` 하드게이트 | **Keep** | 없음 (reject, exact) | P1-C. `CUDA_VISIBLE_DEVICES`, `ZE_AFFINITY_MASK` |
| `cli_flags` 하드게이트 | **Keep** | 없음 (reject, exact) | P1-C. `--nproc_per_node` 등 |
| `links` 하드게이트 | **Keep** | 없음 (reject, exact target) | P1-C. transformers 본체는 `/ko/` 스왑 예외 없음 |
| `images` 하드게이트 | **Keep** | 없음 (reject, exact target) | P1-C |
| `latex` 하드게이트 | **Keep** | 없음 (reject, exact) | 장르 무관 |
| `tables` 하드게이트 | **Keep** | 없음 (reject, shape) | P1-C. 벤치마크 표 |
| `todo_markers` 하드게이트 | **Keep** | 없음 (reject). markers 기본값 유지(`TODO/FIXME/TBD/{{/}}`) | P1-B 재동기화. #47157에서 `<!-- TODO: … not up to date … -->` 제거가 핵심 작업. `configured_todo_markers`가 "원문에 없고 번역에만 있는" 마커만 잡으므로 재동기화 신호로 정확 |
| `bare_urls` 리뷰게이트 | **Keep** | 없음 (review) | 장르 무관 |
| `protected_tokens` (model_ids, python_identifiers) 리뷰게이트 | **Keep** | 없음 (review, exact) | P1-C. 모델 ID, `data.processors.utils.DataProcessor` 등 점 있는 경로. autodoc 경로형 앵커·API 참조를 **부분** 보호 (D2 새 게이트가 정식 보호) |
| `numbers` 리뷰게이트 | **Keep** | 없음 (review, exact) | P1-C. `model_doc` 정형 줄 날짜, 벤치마크 수치 |
| `korean_ratio` / `untranslated_english` 리뷰게이트 | **자산만 재설정 (Phase 5)** | 임계값은 Phase 5까지 블로그 기본값. 라이선스 헤더 영어 줄이 `english_ratio`를 약간 올림 → Phase 5에서 표본으로 확인 | P2 §8 |
| `length_ratio` 리뷰게이트 | **자산만 재설정 (Phase 5)** | 기본 0.35..2.60 유지, Phase 5에서 transformers 표본으로 검증 | P2 §5 |
| segment coverage / 중복 / additional-segments | **Keep (코드 고정)** | 없음 | P2 §5. `model_doc` 정형 줄 세그먼트 개수 이슈는 "새 파싱" 항목에서 다룸 |
| glossary 검증 | **자산만 재설정** | 기존 3개 TSV 재사용 + `glossary/transformers_terms.tsv` 신규 (소수 용어) | P1-C 용어 |
| `validate_modal_strength` | **자산만 재설정** | `style_policy.yml`의 `modal_strength.source_terms` 유지/보강 (experimental, deprecated 포함) | P1-B 경고 약화 금지 |
| `validate_overstatement` | **자산만 재설정** | `style_policy.yml` `overstatement.risky_pairs` — 블로그 마케팅 표현 빼고 문서용으로 | P1-B |
| `validate_translationese` | **자산만 재설정** | `translationese.discouraged` 유지 (`~을 가능하게 합니다` 등) | P1-C, best-practice corpus |
| `validate_information_addition` | **Keep** | 없음 | P1-B. 재현성 보호 목적 |
| `validate_list_consistency` | **Keep** | 없음 (`enabled: true`) | P1-C 목록 구조 |
| `validate_emoji_delta` | **Keep** | 없음 (`forbid_added_emoji: true`). `🤗`, `> [!TIP]`, `(🌎로 표시)`는 원문에 있으면 유지되므로 delta 0 | P1-B 이모지 |
| `validate_alt_text_and_link_text` | **Keep** | 없음 (`require_korean_when_source_english: true`) | P1-C 이미지/링크 텍스트 |
| `validate_first_mention_terms` | **자산만 재설정** | `first_mention_terms`에 transformers 빈출 용어(`fine-tuning`, `quantization`, `checkpoint`, `inference`, `attention` 등) 병기 규칙 | P1-C 용어 병기 (`연산 능력(compute capability)` 등 실제 사례) |
| `validate_title_style` | **Keep (no-op)** | 없음. transformers는 frontmatter title 없음 → 안전한 no-op (P2 §6) | P2 §6 |
| `validate_intro_closing_style` | **Keep (no-op)** | 없음. 하드코딩 블로그 인사말 → transformers엔 부재 | P2 §6 |
| `validate_locale_punctuation` | **Keep** | 없음. `gates.yml`에서 `。 、` 기본값 유지 (일본어 문장부호 금지) | P2 §3 |
| MQM judge 프롬프트 | **자산 전면 교체** | `judges/mqm_prompt.md` 신규: "transformers 기술 문서" 기준, 앵커·지시문·API참조·MDX·`> [!WARNING]` 약화 금지·`model_doc` 정형 줄·재동기화 규칙 포함, 블로그 제목/이모지 규칙 제거 | 전반 |
| metric triage (QE/embedding/chrF) | **Keep** | 없음 | P2 §7 |
| **앵커 보존** (`[[slug]]` + 헤딩 레벨) | **새 파싱 + 새 하드게이트** | 아래 §2, §3 | P1-A 헤딩 앵커; P2 §1·§9. #39519 앵커 관례 논쟁 |
| **지시문 보존** (`[[autodoc]]`, `[[open-in-colab]]`) | **새 파싱 + 새 하드게이트** | 아래 §2, §3 | P1-A 렌더링 지시문 |
| **autodoc 참조 보존** (`` [`~mod.Class`] ``) | **새 파싱 + 새 하드게이트** | 아래 §2, §3 | P1-A API 참조 문법 |
| **MDX/알림 컴포넌트 보존** (`<Tip>`, `> [!WARNING]`, `<hfoptions>` …) | **새 파싱 + 새 하드게이트** | 아래 §2, §3 | P1-A MDX 컴포넌트 |
| **문장 종결 콜론** (→ 마침표) | **새 검증기 (스타일)** | 아래 §3 | P1-C 콜론 (사용자: 예외 없는 절대 규칙) |
| 라이선스 헤더 블록 보존/최신성 | **MQM judge + 수동 체크** | 전용 게이트 안 만듦. MQM 프롬프트에 규칙 추가, 체크리스트에 명시 | P1-A. 원문/번역 동일해 세그먼트 정렬로 대부분 커버, `⚠️ Note` 최신성만 판단 필요 |
| `_toctree.yml` 정합성 (`local`/`title`, 구조 동기화, 중복 섹션) | **구조적으로 불가능** | 자동화 범위 밖. 스킬 문서에 "수동 확인" 명시 | P2 §9-6. 단일 소스↔타깃 비교 구조 |

---

## 2. 새 파싱 요구사항

모든 신규 필드는 `markdown_doc()` (harness L638)에서 `body`(= frontmatter 제거 +
scaffold 제거 후, **`[[...]]`는 남아 있음**) 기준으로 추출한다. `body_without_code`
(펜스 제거본)를 대상으로 해 코드 블록 안 예시는 제외한다.

| 추출 대상 | 위치/방법 | 비교 방법 | 게이트 등급 |
|---|---|---|---|
| **heading_anchors**: 각 헤딩의 `[[slug]]` 문자열 목록 | `body_without_code` 각 줄에 `^(#{1,6})\s+.*?\[\[([^\]\n]+)\]\]\s*$` 정규식. 그룹2가 anchor slug | 원문↔번역 **multiset(Counter) 차집합** (links와 동일 패턴). missing/extra → 이슈 | **reject / critical** |
| **heading_levels**: 헤딩 레벨(`#` 개수)의 **순서 있는** 목록 | 위 정규식 그룹1 길이, 앵커 없는 헤딩(`^(#{1,6})\s+\S`)도 포함 | 원문↔번역 리스트 **순서까지 정확히 동일**한지 (multiset 아님). 불일치 → 이슈 | **reject / critical** |
| **directives**: `[[open-in-colab]]`, `[[autodoc]] <path>` 정규화 문자열 | `\[\[(open-in-colab\|autodoc)\]\](?:[ \t]+(\S+))?` on `body_without_code`. `[[autodoc]] X` → `"[[autodoc]] X"`, `[[open-in-colab]]` → 그대로 | multiset 차집합 | **reject / critical** |
| **autodoc_refs**: 대괄호+백틱 API 참조 `` [`token`] `` 의 내부 토큰 | `\[`([^`\n]+)`\]` on `body_without_code` | multiset 차집합 | **reject / critical** |
| **mdx_components**: MDX/JSX 여는 태그 + GitHub 알림 마커 | ① `<([A-Za-z][A-Za-z0-9]*)((?:\s+[a-zA-Z_:][-a-zA-Z0-9_:.]*(?:=(?:"[^"]*"\|'[^']*'\|\{[^}]*\}))?)*)\s*/?>` 로 여는/자기닫음 태그, 닫는 태그 `</name>` 포함. 태그명 + **정렬된 속성 문자열**로 정규화(prop 값 포함, 내부 산문 무관). ② `^>\s*\[!(TIP\|WARNING\|NOTE\|IMPORTANT\|CAUTION)\]` 알림 마커 | multiset 차집합 | **reject / critical** |

**정규화 주의**:
- heading_anchors/levels는 `strip_heading_anchors`가 `[[...]]`를 **안 지우므로**
  `markdown_doc`의 `strip_heading_anchors(strip_workflow_scaffold(body))` 결과를
  그대로 써도 됨. 단 `parse_code_blocks`로 코드 펜스는 제거.
- mdx_components: `<pt>`, `<tf>`, `<hfoption>` 처럼 속성 없는 태그도 포함. HTML
  `<div class="...">`, `<img src="...">` 도 매칭되지만 원문↔번역 동일하면 무해
  (링크·이미지 게이트와 중복 보호).
- autodoc_refs: `` [`Trainer`] `` 의 `` `Trainer` `` 는 `inline_code`에도 잡히지만
  중복 이슈는 `deduplicate_detector_issues`가 정리하지 않음 → 라벨을 구분해
  (`autodoc reference`) 사용자가 원인을 알 수 있게. (중복 발동 수용 — 둘 다
  같은 근본 원인)

---

## 3. tool 코드(harness) 변경 목록

**모두 `skills/quality/tools/translation_quality_harness.py` 한 파일. additive
지향, 기존 블로그 동작 불변이 목표. 변경 후 `skills/quality/tests/` 전체 재실행
(현재 85 pass / 1 pre-existing unrelated fail: `zip() takes no keyword
arguments`).**

1. **`read_yaml_scalars` (L1077) 1줄**: `values[key_path] = parse_yaml_scalar(raw_value)`
   → `values[key_path] = [] if raw_value.strip() == "[]" else parse_yaml_scalar(raw_value)`.
   블로그 config는 `[]` 문법 미사용 → 영향 없음 (확인 필요).
2. **`MarkdownDoc` 데이터클래스 (L189)에 필드 5개 추가**: `heading_anchors:
   list[str]`, `heading_levels: list[int]`, `directives: list[str]`,
   `autodoc_refs: list[str]`, `mdx_components: list[str]`. 기본값 `field(default_factory=list)`
   또는 `markdown_doc`에서 항상 채움.
3. **추출 함수 5개 신규**: `extract_heading_anchors`, `extract_heading_levels`,
   `extract_directives`, `extract_autodoc_refs`, `extract_mdx_components`.
   `markdown_doc()` (L648~) 반환에 배선.
4. **`validate_documents`의 `source_is_structural` 블록 (L2882~) 확장**:
   `exact_match_checks` 리스트에 3줄 추가 —
   `("anchor_preservation", "enabled", "formatting", "heading anchor", source.heading_anchors, target.heading_anchors, "critical")`,
   `("directive_preservation", "enabled", "formatting", "doc-builder directive", source.directives, target.directives, "critical")`,
   `("autodoc_reference_preservation", "enabled", "technical", "autodoc reference", source.autodoc_refs, target.autodoc_refs, "critical")`,
   `("mdx_component_preservation", "enabled", "formatting", "MDX component", source.mdx_components, target.mdx_components, "critical")`.
   heading_levels는 순서 비교라 별도 `if` 블록 (tables 비교 L2968 패턴):
   `if gate_policy.enabled("anchor_preservation", "enabled") and source.heading_levels != target.heading_levels: issue(..., gate_policy.severity("anchor_preservation", "critical"), "Heading level structure changed.", ...)`.
5. **`validate_sentence_final_colon` 신규** + `validate_style_guide` (L1553,
   target-only 구간)에서 호출. 로직: `parse_code_blocks(target.body)` prose →
   `INLINE_CODE_RE.sub("", strip_markdown_targets(prose))` → 각 비어있지 않은
   줄에서 `line.rstrip()` 이 `:` 또는 `：` 로 끝나고 `has_korean(line)` 이면
   style_issue(category `style_locale`, severity `major`, guide_rule
   `sentence_final_colon`). 표 행(`|` 시작), 헤딩(`#` 시작) 제외.
6. **`style_penalty` weights (L1568)에 `"sentence_final_colon": 8.0` 추가.**
7. (선택, 안전) `EvaluationPolicy`에 새 게이트 기본 severity가 필요 없음 —
   `enabled(gate, "enabled", fallback=True)` 가 `gate_options`에 없으면 True 반환,
   `severity(gate, "critical")` 가 `gate_statuses`에 없으면 `"critical"` 반환.
   따라서 `gates.yml`에 명시만 하면 됨. **단 원문 없이(HTML fetch) 실행되는
   경우 이 게이트들은 `source_is_structural` 블록 안이라 자동 스킵** — 의도된 동작.

### Phase 4/5에서 계획에 추가된 harness 변경 (사후 기록)

- **P4-a** `strip_workflow_scaffold`: `<!--Copyright … -->` doc-builder 라이선스
  헤더 블록을 세그먼트/스타일 비교 전에 제거. 라이선스 줄의 "may"가
  `modal_strength`를, 영어 헤더가 `korean_ratio`를 오탐시켜 파싱 단계 제외가
  필요했음. 블로그는 이 헤더가 없어 무영향.
- **P5-a** `anchor_preservation`: EN 원문에 명시적 `[[...]]` 앵커가 있을 때만
  앵커 문자열 비교, 없으면 헤딩 레벨 순서만 검사 (Phase 5 오탐 8/8).
- **P5-b** `strip_bracket_heading_anchors`: 헤딩 줄 끝 `[[slug]]`를 식별자/
  세그먼트 추출 전에 제거 (API 경로형 앵커의 `python_identifiers` 누수 3/8).
- **P5-c** `preserved_name_present`: `preserve_product_name` 판정에서 영어명 뒤
  한국어 조사 허용 (`Transformers에서` 오탐 6/8).

상세 근거는 `docs/calibration-notes.md`.

### 새 게이트가 config로 꺼질 수 있는지 확인

`enabled("anchor_preservation", "enabled")` → `gates.yml`에
`hard_gates: anchor_preservation: enabled: false` 로 끌 수 있어야 함.
`load_evaluation_policy` L1108이 `key_path[0] in {"hard_gates","review_gates"}`,
len 3 → `gate_options["anchor_preservation"]["enabled"] = False`. `parse_yaml_scalar("false")`
→ `False`. OK. **패치 1 이후** `enabled: []` 같은 건 안 쓰므로 무관.

---

## 4. 자산 파일 목록

### 신규 파일 (블로그와 전혀 다름 → 새로 작성)

- `skills/quality-transformers/SKILL.md`
- `skills/quality-transformers/README.md`
- `skills/quality-transformers/AGENTS.md`
- `skills/quality-transformers/style/hf-transformers-ko-translation-guide.md`
- `skills/quality-transformers/judges/mqm_prompt.md`
- `skills/quality-transformers/glossary/transformers_terms.tsv` (소수 용어만)
- `skills/quality-transformers/examples/input-manifest.yaml`
- `skills/quality-transformers/tests/fixtures/sample_source.md` / `sample_target.md`
  (앵커·`> [!WARNING]`·`` [`AutoTokenizer`] ``·`[[autodoc]]`·번역된 주석 포함
  최소 쌍)
- `skills/quality-transformers/docs/*` (Phase 1·2·3·5 산출물 — 이미 일부 존재)

### 기존 파일 복사 후 소수 값만 변경 (`cp` + `diff` + `Edit`)

- `configs/gates.yml` ← `skills/quality/configs/gates.yml`: `front_matter` 두
  리스트 `[]`, `code_blocks.status: review_required`, `hard_gates`에
  `anchor_preservation`/`directive_preservation`/`autodoc_reference_preservation`/
  `mdx_component_preservation` (각 `status: reject`, `enabled: true`) 추가.
- `configs/eval_config.yml` ← 동일 파일: **값 변경 없음**, transformers용 주석만.
  (Phase 5 전까지 블로그 기본값)
- `configs/style_policy.yml` ← 동일 파일: 블로그 전용 `title_quality` 제거,
  `modal_strength`/`overstatement`/`translationese`/`first_mention_terms`를
  transformers용으로 조정. (파서가 읽는 경로만 — P2 §4-B)
- `configs/protected_patterns.yml` ← 동일 파일: 그대로 (diff로 확인).
- `schemas/mqm_judge.schema.json`, `schemas/quality_report.schema.json` ←
  그대로 복사 (구조 동일, diff로 확인).

### 그대로 두고 경로만 참조 (복사 안 함)

- `skills/quality/glossary/{ml_terms,product_terms,ko}.tsv` — README/CLI 예시에서
  원본 경로 그대로 `--glossary`로 전달. 두 곳에 두면 drift 위험.
- `skills/quality/tools/translation_quality_harness.py` — 공유. 이 스킬은 자체
  `tools/`·`pyproject.toml`를 두지 않음 (`skills/quality-docs`와 동일 판단).

### tool 코드 (harness) 변경

- 위 §3의 7개 항목. **모두 `skills/quality` 소유 파일** — Phase 4에서 첫 변경
  시 사용자에게 범위·영향(블로그 테스트 재실행 결과) 보고.

---

## 5. 사용자 승인이 필요한 항목 (전부 승인 완료 2026-08-29)

- [x] `read_yaml_scalars` 1줄 additive 패치 (D1)
- [x] 새 하드게이트 4개: `anchor_preservation`(+heading level),
  `directive_preservation`, `autodoc_reference_preservation`,
  `mdx_component_preservation` — 전부 `status: reject` (D2)
- [x] `code_blocks` reject→review_required 완화 (Phase 1 확인)
- [x] `validate_sentence_final_colon` 신규 검증기, `review_required` +
  `style_penalty` 8 (D3)
- [x] transformers만 범위 한정, `skills/quality`·`skills/quality-skill-builder`
  미변경, `skills/quality-docs`는 참조 전용

## 6. 구조적으로 불가능 → 스킬 문서에 "수동 확인"으로 명시

- `_toctree.yml`의 `local` 미번역 / `title` 번역 / 원문 구조·순서 동기화 /
  중복 섹션 없음.
- 라이선스 헤더 `⚠️ Note` 줄이 **최신 영어 원문 문구와 일치**하는지 (재동기화
  PR에서 `contain`→`contains` 같은 수정). MQM judge가 보조.
- `model_doc` 정형 줄의 날짜가 실제 발표일/추가일과 맞는지 (원문에 없을 수
  있어 세그먼트 비교로는 한계).
- KREW 초기 리뷰 → maintainer 최종 리뷰 → `build-doc` → doc-builder preview
  프로세스 완료 여부.
