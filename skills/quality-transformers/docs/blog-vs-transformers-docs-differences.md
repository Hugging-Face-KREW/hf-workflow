# 블로그 vs transformers 한국어 문서: 번역 품질 스킬 차이점 정리

`skills/quality`(Hugging Face 기술 블로그 번역 품질 스킬)를 기반으로
`skills/quality-transformers`(github.com/huggingface/transformers 저장소의
`docs/source/ko/` MDX 문서 번역 품질 스킬)를 만들기 위해 확인한 차이점을 정리한
Phase 1 참조 문서다. 새 스킬 자산이 "블로그 가정"을 빠짐없이 걷어냈는지 이
문서를 기준으로 점검한다.

**범위 한정**: 이 문서와 스킬은 `huggingface/transformers` 저장소의 한국어
문서에만 초점을 맞춘다. diffusers/smolagents/lerobot/huggingface_hub 등 다른
저장소는 관례가 대체로 비슷하지만 이 스킬의 범위 밖이고, 아래 표의 근거는
transformers PR·리뷰·이슈로 좁혔다.

## 근거 자료

1. `translation-flow/docs/hf_ko_translation_best_practice.md` — transformers를
   포함한 HF 저장소의 실제 한국어 번역 PR/이슈/리뷰 코멘트 corpus (출처 링크
   포함). Phase 1-A의 1차 자료.
2. `translation-flow/docs/hf_translation_conventions.md` — 일반 번역 컨벤션
   (블로그 기준으로 작성됨, 보조 자료).
3. 공식 [`docs/TRANSLATING.md`](https://github.com/huggingface/transformers/blob/main/docs/TRANSLATING.md) — verbatim 확인.
4. 실제 병합된 원문↔번역 파일 쌍:
   - `docs/source/en/accelerator_selection.md` ↔ `docs/source/ko/accelerator_selection.md`
     (PR [#47157](https://github.com/huggingface/transformers/pull/47157), 최신화 재동기화 PR)
5. 사용자가 지정한 병합 PR 4건의 diff + 리뷰 스레드:
   - [#39519](https://github.com/huggingface/transformers/pull/39519) `main_classes/processors.md` (API 레퍼런스, 앵커 관례 논쟁)
   - [#41340](https://github.com/huggingface/transformers/pull/41340) `model_doc/sam_hq.md` (모델 문서, 논문 초록·사용 팁)
   - [#47157](https://github.com/huggingface/transformers/pull/47157) `accelerator_selection.md` (가이드, 오래된 번역 재동기화)
   - [#39913](https://github.com/huggingface/transformers/pull/39913) `tiny_agents.md` (개념/가이드, 페이지 일부 번역)
6. 추적 이슈 [transformers#20179](https://github.com/huggingface/transformers/issues/20179) (`Translating the docs to Korean`).

---

## A. 파일 형식 (구조/문법)

| 항목 | 블로그 (`skills/quality`) | transformers 한국어 문서 (`skills/quality-transformers`) |
|---|---|---|
| 메타데이터 위치 | YAML frontmatter (`title`, `authors`, `thumbnail`, `tags`, `blog`) | **frontmatter 없음.** 파일 최상단에 Apache-2.0 **라이선스 주석 블록**(`<!--Copyright <year> The HuggingFace Team ... -->`)이 있고, 그 안에 `⚠️ Note that this file is in Markdown but contains specific syntax for our doc-builder ...` 안내 줄이 들어감. 이 줄은 **영어 그대로 두되 최신 원문 문구와 동기화**함(#47157에서 `contain`→`contains` 오타를 원문에 맞춰 고침). 사이드바 메타데이터는 언어별 `docs/source/ko/_toctree.yml`의 `local`(경로, 미번역)/`title`(번역) |
| 목차 (사이드바) | translation-flow가 페이지 안에 생성하는 인라인 TOC 블록 (harness가 하드 비교 전에 정규화) | `docs/source/ko/_toctree.yml` 한 파일이 전체 사이드바 트리를 관리. 원문 `docs/source/en/_toctree.yml` 구조를 복제하며, 아직 번역 안 된 항목은 `local: in_translation` + `title: (번역중) <영문 제목>` placeholder로 남김. 공식 `TRANSLATING.md`가 "Keep this name for your .md file / Translate this"로 명시 |
| 목차 (페이지 내부) | 없음 | 페이지 내 "on this page" 내비게이션은 **문서 자체의 헤딩·앵커 구조에서 doc-builder가 자동 생성**. 별도 블록이 없음. → 헤딩 앵커와 헤딩 레벨이 이 자동 목차의 정확성을 결정 |
| 헤딩 앵커 | 앵커 규칙 약함, 필수 아님 | `# 제목[[anchor]]` 관례. **앵커 문자열은 영어 원문의 앵커와 바이트 단위로 동일**해야 함. 형태가 두 가지: ① 일반 kebab 슬러그(`[[overview]]`, `[[xnli]]`, `[[squad]]`), ② `[[autodoc]]` 연동 헤딩은 **정규화된 Python API 경로**(`[[transformers.ProcessorMixin]]`, `[[transformers.data.processors.squad.SquadProcessor]]`) — 라이브 문서에서 헤딩 클릭 시 이동하는 실제 URL 앵커를 그대로 쓰기 때문(#39519 리뷰에서 maintainer `stevhliu`가 처음엔 kebab로 바꾸라 제안했다가 "actual URL anchors" 관례 유지로 철회). 번역자가 **번역된 제목이나 영어 제목에서 슬러그를 새로 만들면 안 됨.** 헤딩 레벨(`#` 개수)도 원문과 동일. 최신 가이드 페이지는 앵커가 아예 없기도 함(`accelerator_selection.md`) — 그 경우 번역문도 앵커를 만들지 않음 |
| 렌더링 지시문 | 없음 | `[[open-in-colab]]`, `[[autodoc]] module.Class` (doc-builder 전용). 절대 번역·변형 금지 |
| API 참조 문법 | 없음 | `` [`Trainer`] ``, `` [`~data.processors.utils.InputExample`] `` — doc-builder가 API 링크로 변환. 대괄호·백틱·틸드·경로 모두 원문 유지, 설명 문장만 번역 |
| MDX / doc-builder 컴포넌트 | 거의 없음 | 두 세대가 공존: **구형** `<Tip>`, `<Tip warning={true}>`, `<frameworkcontent>`, `<pt>`/`<tf>` — **신형** GitHub 스타일 알림 `> [!TIP]`, `> [!WARNING]`, `> [!NOTE]`. 공통: `<hfoptions id="...">`/`<hfoption id="...">`, `<Youtube id="..."/>`. 태그·속성(`id`, `warning={true}`)은 유지, 내부 산문만 번역. `id` 값이 원문에서 바뀌면 번역문도 따라 바뀜(#47157: `select-gpu`→`accelerator-type`) |
| 코드 펜스 언어 태그 | ` ```py `, ` ```bash ` 등 표준 | 위 + transformers 고유 ` ```cli ` (명령줄 예시). 펜스 언어 태그는 원문 그대로 |
| 모델 문서 정형 줄 | 없음 | `model_doc/*.md`는 doc-builder가 넣는 `*이 모델은 <날짜>에 발표되었으며 <날짜>에 Hugging Face Transformers에 추가되었습니다.*` 줄이 있음(#41340). 문장은 번역, 날짜는 보존. 기여자 줄 `이 모델은 [name](url)님께서 기여해주셨습니다. 원본 코드는 [여기](url)에서 확인하실 수 있습니다.`도 정형 |
| 저장 위치 | `huggingface/blog` 저장소의 `blog/<slug>.md` | `huggingface/transformers` 저장소 `docs/source/ko/` — 영어 `docs/source/en/` 폴더 구조를 그대로 복제(`cp -r source/en source/ko`) |
| 파일 수명 | 발행 시점 스냅샷 | 라이브러리 버전과 함께 갱신되는 living document. 오래된 번역을 최신 원문에 맞추는 재동기화 PR이 정식 작업 유형(#47157) |

---

## B. 내용: 글의 흐름·스타일·구조

| 항목 | 블로그 | transformers 한국어 문서 |
|---|---|---|
| 문체 기준 | 장르별 톤 조정(연구소개=차분한 합니다체, 제품발표=활기, 튜토리얼=해요체 …) | 단일 기준: "친구에게 설명하듯 친근하되 예의 있는" **해요체/합니다체 혼용** + 성 중립. 절차·튜토리얼(`~하세요`, `~해 보겠습니다`)은 해요체 비중이 높고, API 레퍼런스·개념 설명·논문 초록은 합니다체 비중이 높음. 추적 이슈 #20179가 "informal tone (imagine you are talking with a friend 🤗)"과 "gender-neutral" 명시 |
| 제목 (H1) | 검색성·전달력·기대값 우선, 과장/클릭베이트 방지가 핵심 | 원문 제목을 충실히 옮김. 제품명·모델명·클래스명이 들어가면 원문 표기 유지(`# SAM-HQ[[sam_hq]]`). 마케팅 임팩트 개념 없음 |
| 사이드바 제목 (`_toctree.yml` title) | 해당 없음 | 페이지가 사이드바에서 하는 역할 기준으로 정하고 리뷰어와 합의. 원문 제목과 달라질 수 있음. 미번역은 `(번역중) <영문 제목>`, 완료 시 한국어로 교체(#47157) |
| 도입부 | "무엇을 다루는 글인지" 후킹 문장이 필수 규칙 | 페이지가 다룰 개념/절차를 간결히 서술. 후킹 아님 |
| 마무리 | 과하지 않은 CTA, 다음 업데이트 예고 등 별도 규칙 | 별도 마무리 규칙 없음. 관련 문서 링크나 다음 섹션으로 자연스럽게 끝남 |
| 이모지 | 명시적 정책(원문에 없으면 추가 금지) | 거의 안 씀. `🤗 Transformers` 브랜드 표기, `> [!TIP]`류 알림 문법, 리소스 목록의 `(🌎로 표시)` 커뮤니티 마커처럼 **원문에 의미가 있는 경우만 유지**. 추가 금지 |
| 글의 구조 | 서사적 흐름(도입-설명-예시-정리), 문단 중심 | 절차적/참조적. 헤딩·번호 목록·코드 예제·표 중심. **재현 가능성**이 핵심 |
| 정보 추가 금지 | 원문에 없는 설명·평가·예시·결론 추가 금지 — 목적은 **마케팅 과장 방지** | 같은 규칙, 목적은 **재현성·정확성 보호**. 다만 번역 중 원문 자체의 오류/모호함을 발견하면 PR에서 원문도 함께 고치는 관행이 있음(quicktour.md #24664, accelerator_selection의 `contain`→`contains`). 이때 PR 본문에 원문도 고쳤다고 명시 |
| 경고/제한 표현 강도 | 과장 방지 중심 | **위험 약화 금지**가 핵심. 실험적 API 경고("언제든지 변경될 수 있습니다"), deprecated 안내, `> [!WARNING]` 블록의 안전 관련 경고는 강도를 절대 낮추지 않음 |
| 작업 유형 | 신규 발행 1종 | **신규 번역**과 **오래된 번역 재동기화(freshness sync)** 둘 다 정식 작업 유형(사용자 확인). 재동기화 PR은 stale 콘텐츠(옛 섹션명, `TODO` 주석, 사라진 환경 변수 안내)를 제거하고 최신 원문 구조로 교체해야 함(#47157: `<!-- TODO: ... not up to date ... -->` 주석과 `# GPU 선택하기` 섹션 삭제). deprecated 기능·환경 변수·안전/윤리 안내는 **최신 영어 원문과 지속 동기화** |
| 협업/리뷰 프로세스 | translation-flow 자동화 기반, 가벼움 | 무거운 공식 프로세스: 추적 이슈 연결(`Part of #20179`), PR 제목 `🌐 [i18n-KO] Translated <file> to Korean`, "Before reviewing" 체크리스트(번역 누락/중복·맞춤법·용어집·Inline TOC·live-preview), KREW 초기 리뷰 → `@stevhliu` 최종 리뷰 → `build-doc` 액션 → doc-builder preview 확인. 한국어 리뷰 대화는 반말/존댓말 섞인 캐주얼 톤이지만 **문서 본문 문체와는 무관** |

---

## C. 디테일: 주석·링크 등 세부 규칙

| 항목 | 블로그 | transformers 한국어 문서 |
|---|---|---|
| 코드 주석 번역 | 가이드는 "자유롭게 번역 가능"이라 하지만 harness `code_blocks` 하드게이트(해시 비교)가 항상 reject — 가이드와 도구가 모순 | 조건부 허용: **식별자·환경 변수·문자열 리터럴·경로·옵션·모델 ID는 절대 불가**, 설명 주석/docstring/`Args` 설명만 안전할 때 번역 가능(#41340: `# 2D location of a window in the image` → `# 이미지 내 창문의 2차원 위치`). `code_blocks`를 `review_required`로 낮춰 모순 해소 |
| 코드 블록 속 출력/전사(transcript) | 해당 사례 적음 | 에이전트 세션 로그, 오류 메시지, 모델 입출력 예시는 **원문 유지**가 기본. 독자용 설명 줄만 번역(#39913: `tiny-agents` 세션 로그는 그대로 두고 마지막 한국어 설명 문장만 번역) |
| 하이퍼링크 타깃 | 절대 변경 금지, 예외 없음 | 원칙은 동일. 상대 경로(`../model_doc/clip`, `./main_classes/deepspeed`)와 외부 URL 모두 유지, 링크 텍스트만 번역. transformers 본체에는 `/ko/` 스왑 예외 사례가 확인되지 않음(그 예외는 course 저장소 한정) |
| 목록 구조 | 문장형/명사구형 혼용 금지 정도 | 위 규칙 + 원문과 같은 불릿·들여쓰기·중첩 유지. 들여쓰기가 깨지면 원문에서 같은 항목이던 문장이 별도 문단으로 렌더링됨(LeRobot #3383 리뷰가 근거). 번호 목록의 항목 수·순서도 원문과 일치 |
| 문장 끝 콜론 | 일반 스타일 항목 | **절대 규칙: 한국어 문장 끝의 콜론(`:`)은 항상 마침표로 옮긴다.** 한국어는 원래 콜론을 문장 종결에 쓰지 않는다. 4개 PR 중 3개(#41340, #39913, llm_tutorial_optimization #32372 요약)에서 반복 지적됐고, 병합된 문서에 `다음과 같습니다:`가 남아 있는 것은 **검수 누락**이지 허용 사례가 아니다(사용자 확인). 결정적(deterministic)으로 탐지 가능하므로 상시 발동하는 **리뷰 게이트 + 높은 스타일 감점**으로 구현하되, 스타일 가이드에는 예외 없는 규칙으로 명시한다. (콜론 자체가 빌드를 깨지는 않으므로 harness `status`는 `reject`가 아니라 `review_required`) |
| 번역투 | `~에 의해`, `~하는 것에 있어`, `~를 가지다`, `~을 가능하게 합니다` 등 | 동일. 특히 절차 문장은 독자가 수행할 행동을 명확히("Run the following" → "다음을 실행하세요"). 영어 명사구를 한국어 서술 구조로 재배열 |
| 용어 우선순위 | 검색성을 정확성과 동급 | **문서 내 일관성·API 정확성** 우선. 첫 등장 시 `한국어(English)` 병기(`양자화(quantization)`, `연산 능력(compute capability)`), 이후 한국어로 통일. `_toctree.yml` 제목에도 병기 스타일 적용(`서빙(Serving)`) |
| 제품명·라이브러리명·모델명·클래스명·API명 | 원문 유지 | 동일하게 엄격. `Trainer`, `SamHQModel`, `ProcessorMixin`, `PEFT`, `Accelerate`, 모델 ID(`syscv-community/sam-hq-vit-base`), 데이터셋명(`GLUE`, `SQuAD`, `XNLI`), 환경 변수(`CUDA_VISIBLE_DEVICES`, `ZE_AFFINITY_MASK`) 모두 문자 단위 보존 |
| 이미지/캡션 | 캡션·alt text 번역, 파일 경로 유지 | 파일 경로 유지. alt text 번역은 선택(#41340은 `![example image]`를 영어로 둠). `<div class="flex ...">`, `<img>` 태그 구조 유지 |
| 표/벤치마크 | 열·행 수, 정렬, 숫자·단위 보존 | 동일. 비교 방향(higher/lower is better), `up to N%`(최대값), 지연·처리량 수치 보존 |
| 소스 자동 수집 | harness가 `huggingface.co/blog/...` URL을 인식해 `huggingface/blog`에서 원문 자동 fetch | **지원 안 됨.** 항상 `--source`로 `docs/source/en/<path>` 파일(또는 raw URL)을 직접 지정. transformers는 URL 자동 인식 대상이 아님 |
| `_toctree.yml` 정합성 | 해당 없음 | `local`(경로) 미번역, `title` 번역, 원문 `_toctree.yml` 구조/순서와 동기화, 중복 섹션 없음. **단일 소스 파일↔단일 타깃 파일 비교 구조인 harness로는 검증 불가** — 사람/에이전트 수동 확인 항목 |

---

## D. 도구(harness) 레벨 차이 — Phase 2와 함께 채움

| 게이트/검증기 | 블로그 (`skills/quality/configs/*`) | transformers 문서에 필요한 값 | 근거 |
|---|---|---|---|
| `front_matter` 하드게이트 | `required_target_keys: [title]`, `preserved_source_keys: [authors, thumbnail, tags, blog]` — reject | `required_target_keys: []`, `preserved_source_keys: []` — frontmatter 없음. harness YAML 파서가 `key: []`를 인식하는지 Phase 2에서 확인 필요(파서가 `[]`를 무시하고 기본값 `[title]`로 돌아가면 모든 문서가 항상 reject됨 — Phase 2에서 실제로 그 gap을 확인) | A: 메타데이터 위치 |
| `code_blocks` 하드게이트 | `status: reject`, 해시 완전 일치 | `status: review_required`로 완화 — 주석/docstring 번역 허용, 사람이 검토 | C: 코드 주석 번역 |
| `inline_code`/`environment_variables`/`cli_flags`/`links`/`images`/`latex`/`tables`/`todo_markers` | hard reject, exact match | 동일 유지 (실행 토큰·링크 보호는 장르 무관) | C: 제품명/링크/표 |
| 라이선스 헤더 주석 블록 | 없음 | 원문 그대로 유지되는지, `⚠️ Note ...` 줄이 최신 원문과 일치하는지 확인. 기존 하드게이트로는 안 잡힘 | A: 메타데이터 위치 |
| 헤딩 앵커 `[[...]]` 보존 | 해당 문법 없음 | 앵커 문자열이 **영어 원문과 바이트 단위 동일**한지 + 헤딩 레벨 동일한지. `[[autodoc]]` 연동 헤딩은 API 경로 형태 허용. 현재 어떤 게이트도 검증 안 함 | A: 헤딩 앵커 |
| 지시문 `[[autodoc]]`/`[[open-in-colab]]` 보존 | 없음 | 지시문 토큰과 대상 경로 보존. 현재 게이트 없음 | A: 렌더링 지시문 |
| API 참조 `` [`~mod.Class`] `` 보존 | 없음 | 대괄호·백틱·틸드·경로 보존. 현재 게이트 없음 | A: API 참조 문법 |
| MDX/알림 컴포넌트 보존 | 없음 | `<Tip ...>`, `> [!WARNING]`, `<hfoptions id=...>` 태그·속성 보존, 내부 산문만 번역. 현재 게이트 없음 | A: MDX 컴포넌트 |
| 문장 끝 콜론 스타일 | 일반 스타일 감점 | 상시 발동 리뷰 게이트 + 높은 스타일 감점 (결정적 탐지, 예외 없는 규칙) | C: 문장 끝 콜론 |
| MQM judge 프롬프트 | "technical blog posts", 제목 과장·이모지 규칙 | "transformers 기술 문서", 앵커·지시문·API참조·MDX·라이선스헤더·모델문서 정형줄·재동기화 규칙 포함, 제목/이모지 규칙 제거 | 전반 |
| glossary | `skills/quality/glossary/*.tsv` | 동일 3파일 재사용 + transformers 고유 용어 소수(`autodoc`, `doc-builder`, `toctree`, `hfoptions`, `infer_device` 등) | C: 용어 |
| eval_config 임계값 | score 90/75/60, length_ratio 0.35–2.60 등 | Phase 5 전까지 **블로그 기본값 그대로**. transformers 실제 PR 표본으로 오탐 확인 후에만 조정 | Phase 5 |

---

## E. 아직 해결하지 않은 항목 (Phase 3에서 결정)

- **앵커/지시문/API참조/MDX 자동 검증 게이트를 harness에 추가할지**: 링크·이미지처럼
  이미 하드게이트가 있는 항목과 위험도가 비슷한데(빌드/렌더 깨짐) 게이트가 없다.
  추가한다면 `anchor_preservation`(슬러그 문자열 + 헤딩 레벨), `directive_preservation`,
  `autodoc_reference_preservation`, `mdx_component_preservation` 4개 후보. harness
  코드 추가가 필요하므로 Phase 3에서 사용자 승인 후 결정. `[[autodoc]]` 연동 헤딩의
  앵커가 API 경로 형태(`transformers.ProcessorMixin`)라는 점 때문에 "슬러그를
  헤딩 텍스트에서 재생성했는가"를 단순 검사하면 안 되고, **원문 앵커와의 직접 비교**여야 함.
- **`_toctree.yml` 정합성**: 별도 YAML 파일 전체를 대상으로 하므로 단일 소스↔타깃
  비교 구조인 harness로는 다룰 수 없음. 수동 확인 항목으로 문서화.
- **라이선스 헤더 주석 블록 검증**: 원문 대비 보존 + `⚠️ Note` 줄의 최신성. 새
  가벼운 검사가 필요한지, 아니면 MQM judge/수동 체크로 충분한지 Phase 3에서 판단.
- **재동기화(freshness sync) PR 지원**: harness는 "현재 원문 ↔ 현재 번역"을
  비교하므로, "옛 번역에 stale 콘텐츠가 남아있는지"는 원문에 없는 문단(추가/중복)
  탐지로 부분적으로만 잡힌다. `TODO`/`FIXME` 마커는 `todo_markers` 하드게이트가
  잡음. 그 이상(옛 섹션명 잔존 등)은 MQM/수동.
- **`code_blocks` 완화의 트레이드오프**: 하드→리뷰로 낮추면 `inline_code`/
  `environment_variables`/`cli_flags` 정규식이 못 잡는 실행 토큰 변경(예: 문자열
  리터럴 일부만 변경)이 자동으로 안 막힘. 운영 데이터가 쌓이면 재조정 필요할 수 있음.

---

## F. (참고) 범위를 diffusers/smolagents/lerobot 등으로 넓힐 경우 달라질 부분

향후 별도 스킬로 다른 저장소를 다루게 될 경우를 대비한 분석. harness 게이트와
스타일 가이드 **핵심(문체·앵커·지시문·API참조·MDX·코드보존·콜론·번역투·리뷰
워크플로)은 그대로 재사용 가능**하고, 저장소별로 조정이 필요한 지점만: 

| 지점 | transformers 전용인가 | 넓힐 때 필요한 변경 |
|---|---|---|
| `model_doc/*.md` 정형 줄 (`*이 모델은 …에 추가되었습니다.*`) | **transformers 전용** doc-builder 삽입 줄 | diffusers 모델 문서는 형식이 다르거나 없음 → judge/스타일 규칙에서 저장소 조건 분기 |
| `[[autodoc]]` 앵커가 FQ Python 경로 | transformers·smolagents 공통이나 transformers에서 가장 빈번 | 규칙 자체는 동일("원문 앵커와 바이트 동일"). 표본만 늘리면 됨 |
| 파일 확장자 | transformers는 `.md` | **lerobot은 `.mdx`** → 입력 glob·파서 확장자 목록에 `.mdx` 추가 |
| `/ko/` 링크 스왑 | transformers 본체에선 **금지** | **course/agents-course는 현지화 노트북 링크에 한해 허용** → `links` 하드게이트에 저장소별 예외 |
| 안전/윤리 문서 최신성 | transformers도 있으나 비중 낮음 | **diffusers `ethical_guidelines.md`** 등에서 비중 큼 → judge의 "위험 강도 보존" 규칙 가중치 상향 |
| deprecated 환경 변수 정리 | transformers도 있음 | **huggingface_hub**(`hf_transfer`→`HF_XET`)에서 특히 잦음 → 재동기화 체크리스트 공통화 |
| glossary | `Trainer`, `TrainingArguments`, `pipeline`, `AutoModelFor*`, `GLUE`/`SQuAD`/`XNLI` 등 | 저장소별 제품·클래스·API 용어 파일 추가 (`diffusers_terms.tsv` 등) |
| 추적 이슈·PR 템플릿 | #20179 + 스프레드시트 + `(번역중)` placeholder | smolagents #1607, lerobot 등 저장소마다 별도. 프로세스 문서만 일반화 |
| ` ```cli ` 펜스 | transformers 도입 | 다른 저장소는 ` ```bash `/` ```py ` 위주 → 펜스 언어 화이트리스트에 추가만 하면 무해 |

결론: 넓히는 작업은 **새 harness 로직이 거의 필요 없고**, (1) glossary 파일 추가,
(2) `.mdx` 확장자, (3) `links` 게이트의 저장소별 `/ko/` 예외, (4) judge 규칙의
저장소 조건 분기(모델문서 정형 줄, 안전문서 가중치) 정도다. 저장소마다 관례
차이가 뚜렷하므로 하나로 합치기보다 저장소별 프로파일로 나누는 편이
유지보수에 유리하다.

---

## 작업 점검용 자기 질문

새 스킬 자산(스타일 가이드, config, judge 프롬프트)을 쓰거나 검토할 때 아래로
"블로그 가정이 남아있지 않은가"를 빠르게 점검한다.

1. frontmatter(title, authors 등)를 전제로 한 문구·설정이 남아있는가? 라이선스
   헤더 주석 블록과 `_toctree.yml` 처리로 대체했는가?
2. 앵커 규칙이 "원문 앵커와 바이트 단위 동일"로 쓰였는가? `[[autodoc]]` 연동
   헤딩의 API 경로 형태 앵커, 앵커 없는 최신 페이지를 모두 다루는가?
3. 문체가 "장르별 톤 조정"이 아니라 "일관된 친근한 존댓말(해요체/합니다체 혼용)
   + 성 중립"으로 쓰였는가?
4. 코드/링크 규칙이 "절대 불변(식별자·환경변수·모델ID·링크타깃)"과 "조건부
   허용(설명 주석·docstring·`Args`)"을 명확히 구분하는가?
5. 최신성 동기화, 실험적/`> [!WARNING]` 경고 약화 금지, 재동기화 PR 처리처럼
   living document 특유의 규칙이 들어있는가?
6. transformers 고유 요소(` ```cli ` 펜스, `> [!TIP]`/`> [!WARNING]` 알림,
   `model_doc` 정형 줄, `🌎` 커뮤니티 마커, `[i18n-KO]` PR 프로세스)를 블로그
   버전에서 누락 없이 반영했는가?
