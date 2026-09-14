# transformers 한국어 문서 품질 스킬 — 임계값 보정 노트 (Phase 5)

Phase 4가 기능적으로 검증된 뒤, 실제 병합된 `[i18n-KO]` PR 8건을 표본으로
harness를 돌려 오탐/미탐을 확인하고 근거가 있는 조정만 적용했다.

## 사용한 표본

전부 `huggingface/transformers`에서 병합되고 maintainer(`@stevhliu` 등) 승인을
거친 한국어 번역. 각 PR의 merge commit에서 영어 원문(`docs/source/en/...`)과
한국어 번역(`docs/source/ko/...`)을 같은 ref로 가져와 비교.

| PR | 파일 | 문서 유형 | 리뷰 | merge |
|---|---|---|---|---|
| [#39519](https://github.com/huggingface/transformers/pull/39519) | `main_classes/processors.md` | API 레퍼런스 | KREW + stevhliu | 2025-08-13 |
| [#41340](https://github.com/huggingface/transformers/pull/41340) | `model_doc/sam_hq.md` | 모델 문서 | KREW + stevhliu | 2025-10-16 |
| [#47157](https://github.com/huggingface/transformers/pull/47157) | `accelerator_selection.md` | 가이드 (재동기화) | stevhliu | 2026-07-08 |
| [#39913](https://github.com/huggingface/transformers/pull/39913) | `tiny_agents.md` | 개념/가이드 (페이지 일부) | KREW + stevhliu | 2025-08-13 |
| [#40445](https://github.com/huggingface/transformers/pull/40445) | `model_doc/big_bird.md` | 모델 문서 (대형) | KREW + stevhliu | 2025-10-16 |
| [#39577](https://github.com/huggingface/transformers/pull/39577) | `main_classes/pipelines.md` | API 레퍼런스 (대형) | KREW + stevhliu | 2025-08-13 |
| [#39535](https://github.com/huggingface/transformers/pull/39535) | `cache_explanation.md` | 개념 | KREW + stevhliu | 2025-08-05 |
| [#40011](https://github.com/huggingface/transformers/pull/40011) | `optimizers.md` | 가이드 | KREW + stevhliu | 2025-08-13 |

## 1차 실행 (블로그 기본 설정 그대로)

`--qe-metric heuristic`, 블로그 glossary 3개 + `transformers_terms.tsv`, 앵커
게이트가 KO↔EN 앵커 문자열 직접 비교.

**결과: 8/8 `reject`.** 주요 오탐:

| 신호 | 발동 | 원인 |
|---|---|---|
| `heading anchor mismatch` (critical) | 8/8 | **설계 오류.** 최신 transformers 영어 `.md`에는 `[[...]]` 앵커가 없다. 한국어 번역이 doc-builder 자동 슬러그(영어 헤딩 텍스트의 kebab, 또는 `[[autodoc]]` 헤딩은 API 경로)를 수동으로 붙인다. KO 앵커를 "빈 EN 앵커 집합"과 비교하니 항상 불일치 |
| `Python/API identifier mismatch` (major) | 3/8 | 위와 같은 뿌리. `[[transformers.ProcessorMixin]]` 같은 API 경로형 앵커가 `strip_heading_anchors`에서 안 지워져 `python_identifiers`로 새어 `protected_tokens` 게이트를 침 |
| `QE metric score is low` (major, 문서당 5~96회) | 5/8 | 휴리스틱 QE는 길이·토큰 겹침 기반. 한국어 기술 문서는 정당하게 원문 대비 0.56~0.87 길이. 점수를 0까지 끌어내림 |
| `Product or library name was not preserved` (major) | 6/8 | `term_present`의 단어 경계 정규식이 `Transformers에서`·`Spaces에`(영어명+한국어 조사)를 "미보존"으로 판정. 공유 블로그 `product_terms.tsv`에서 발생 |
| `Required glossary term is not used` (major) | 3/8 | 공유 블로그 `ml_terms.tsv`/`ko.tsv`의 `required` 항목이 문서에는 과도 |
| `Modal or certainty strength` (style-major) | 6/8, 문서당 3~10회 | 기존 `validate_modal_strength`. 정렬된 세그먼트에 "may"가 있고 "수 있습니다"가 없으면 발동 — 한국어가 가능성을 다르게 표현하면 오탐 |

## 적용한 조정

### 코드 (`skills/quality/tools/translation_quality_harness.py`, additive, 블로그 무영향)

| # | 변경 | 근거 |
|---|---|---|
| C1 | `anchor_preservation`: **EN 원문에 명시적 `[[...]]` 앵커가 있을 때만** KO↔EN 앵커 문자열 multiset 비교. 없으면 앵커 문자열 검사를 건너뛰고 **헤딩 레벨 순서 비교만** critical로 유지. 앵커 문자열 정합성은 MQM judge + 사람의 "Check Inline TOC" 단계로 이동 | 8/8 오탐. doc-builder의 정확한 슬러그 규칙(특히 autodoc 경로형)은 헤딩 텍스트만으로 재현 불가 |
| C2 | `strip_bracket_heading_anchors`: 헤딩 줄 끝의 `[[slug]]`를 파이프라인 나머지 단계 전에 제거 (앵커/레벨/지시문 추출은 그 전에 완료). `[[autodoc]]`/`[[open-in-colab]]` 지시문 줄은 건드리지 않음 | API 경로형 앵커가 `python_identifiers`로 새는 3/8 오탐 |
| C3 | `preserved_name_present` 헬퍼: `preserve_product_name`/`preserve_or_first_mention` 판정 시 영어명 뒤 한국어 조사를 허용 (`Transformers에서` = 보존됨) | 6/8 오탐. 블로그 MQM 프롬프트도 이미 "조사는 정상"이라 명시하나 결정적 검증기는 못 걸러냈음 |

블로그 테스트 스위트: **85 passed / 1 pre-existing 무관 실패** — C1~C3 이후에도 동일, 회귀 0.

### 설정 (`skills/quality-transformers/`)

| 파일 | 키 | 기존 | 변경 | 근거 |
|---|---|---|---|---|
| `configs/eval_config.yml` | `language.min_korean_letter_ratio` | 0.20 | **0.15** | #40445 `big_bird.md`(정상 병합된 대형 모델 문서)가 "Korean letter ratio is low"로 발동. 모델 문서는 클래스명·`[[autodoc]]` 블록·코드 비중이 커서 0.20이 과함. 0.15에서 해소되고 실제 미번역 페이지는 여전히 잡힘 (조정 후 #40445 77→82, 발동 사라짐) |
| `configs/style_policy.yml` | `modal_strength.source_terms.{experimental,deprecated}` | 추가했던 항목 | **되돌림(제거)** | Phase 4에서 추가했으나 밀도 높은 기술 산문에서 오탐 증가. experimental/deprecated 경고 강도는 MQM 프롬프트가 담당 |

### CLI 사용법 (`README.md` 반영)

| 항목 | 변경 | 근거 |
|---|---|---|
| `--qe-metric` | `heuristic` → **`off`** (+ `--disable-embedding-similarity`) | 휴리스틱 QE는 블로그 길이 산문 기준. reference-free 기술 문서에서는 순수 노이즈(문서당 최대 96개 major). 의미 적합성은 MQM judge가 정식으로 담당 |
| `--glossary` | 공유 블로그 3개 제거, **`transformers_terms.tsv`만** | `product_terms.tsv`의 `preserve_product_name` 조사 오탐, `ml_terms.tsv`/`ko.tsv`의 `required` 과도. 제품·클래스·API명 보존은 `protected_tokens`/`inline_code`/`autodoc_reference` 하드게이트 + MQM가 커버 |

## 조정 후 재검증 (동일 표본 8건)

| PR | 1차 | 최종 | 최종 status 근거 |
|---|---|---|---|
| #39519 processors | reject / 0 | **reject / 54** | 크리티컬 없음. 세그먼트 커버리지 −1(실제 문단 1개 누락 가능), 중복 세그먼트 `이러한 프로세서들은 다음과 같습니다:`(실제, 콜론도 포함), modal 오탐 6개가 60점 스타일 하한 밑으로 끌어내림. **경계 사례** |
| #41340 sam_hq | reject / 17 | **review_required / 72** | 정상. 콜론 1개(진짜), code 해시(주석 번역), API id 등 리뷰 항목 |
| #47157 accelerator | reject / 70 | **reject / 75** | 크리티컬 1개: 번역자가 "exporting"을 `` `export` `` 인라인 코드로 표기 → `inline_code` 하드게이트. 경계 사례 |
| #39913 tiny_agents | reject / 69 | **review_required / 89** | 정상 |
| #40445 big_bird | reject / 2 | **review_required / 82** | 정상 (min_korean_letter_ratio 조정 효과) |
| #39577 pipelines | reject / 0 | **reject / 6** | 크리티컬 3개 — `` [`파이프라인`] ``으로 API 참조를 번역해 doc-builder 링크가 깨짐. **진짜 결함(병합된 것을 harness가 잡음). 미탐이 아니라 정탐** |
| #39535 cache_explanation | reject / 27 | **reject / 47** | 크리티컬 2개 — 표 2개를 1개(4행)로 합침 + `{{`/`}}` 마커. **진짜 구조 변경. 정탐** |
| #40011 optimizers | reject / 31 | **review_required / 81** | 정상 |

**정리**: 8/8 reject → **4 review_required + 4 reject**. reject 4건 중 **2건(#39577, #39535)은 harness가 병합된 실제 결함을 잡아낸 정탐**, 1건(#47157)은 사소한 인라인 코드 표기 차이, 1건(#39519)은 modal 오탐 노이즈에 눌린 경계 사례.

## 남은 한계 (조정하지 않음 — 근거 부족 / 마스킹 위험)

- **`validate_modal_strength` 오탐**: 밀도 높은 기술 산문에서 문서당 3~10개
  style-major(점수 −2씩). 심각도가 코드 하드코딩이라 config로 못 낮춤. 이걸
  가리려고 `review_required_min_score`(75)나 `style_review_required_min_score`
  (60)를 낮추면 실제 문제도 통과시키게 되므로 **손대지 않음.** `review_required`
  → 사람 리뷰가 흡수하는 것이 맞다.
- **`Link text appears untranslated`(minor)**: 병합 문서도 논문 제목·API명 등
  일부 링크 텍스트를 영어로 둠. minor라 상태에 큰 영향 없음. 유지.
- **`validate_information_addition` (`때문에`/`덕분에`)**: 하드코딩 style-major.
  한국어가 영어 인과 구조를 자연스럽게 옮길 때 오탐. 노이즈로 문서화만.
- **`Semantic adequacy evaluation is incomplete` (major)**: LLM judge 없이는
  항상 발동 → 구조상 `auto_pass` 불가, 최대 `review_required`. 의도된 설계.
  실운영에서는 `--llm-judge-provider openai` 사용.
- **앵커 문자열 정합성**: EN 원문에 앵커가 없는 최신 문서는 자동 검증 안 함
  (C1). MQM 프롬프트 + `[i18n-KO]` "Check Inline TOC" 체크리스트가 담당.

## 사용자 승인

- 승인: (Phase 5 체크포인트에서 확인 예정)
- `min_korean_letter_ratio` 0.20→0.15 및 CLI 기본값(`--qe-metric off`,
  transformers glossary만)에 대한 승인 필요.
