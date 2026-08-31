# Hugging Face transformers 한국어 문서 번역 스타일 가이드

`github.com/huggingface/transformers` 저장소의 `docs/source/ko/**/*.md` 문서를
한국어로 번역·검수할 때의 기준이다. Hugging Face 블로그 번역은 `skills/quality`를
쓴다. diffusers/smolagents/lerobot 등 다른 저장소는 이 스킬의 범위 밖이다.

근거: 공식 [`docs/TRANSLATING.md`](https://github.com/huggingface/transformers/blob/main/docs/TRANSLATING.md),
추적 이슈 [transformers#20179](https://github.com/huggingface/transformers/issues/20179),
`translation-flow/docs/hf_ko_translation_best_practice.md`의 실제 병합 PR·리뷰
사례, 그리고 병합 PR
[#39519](https://github.com/huggingface/transformers/pull/39519)(`main_classes/processors.md`),
[#41340](https://github.com/huggingface/transformers/pull/41340)(`model_doc/sam_hq.md`),
[#47157](https://github.com/huggingface/transformers/pull/47157)(`accelerator_selection.md` 재동기화),
[#39913](https://github.com/huggingface/transformers/pull/39913)(`tiny_agents.md`).

---

# 1. 번역 철학: 정확성·재현성·렌더링 구조가 문장의 매끄러움보다 우선입니다

기술 문서는 독자가 그대로 따라 실행할 수 있어야 합니다. 문장은 자연스러운
한국어로 다시 쓰되, **코드·앵커·지시문·API 참조·MDX 컴포넌트처럼 doc-builder
빌드와 직접 연결된 요소는 원문 그대로 둡니다.** 번역 중 원문 자체의 오류를
발견하면 조용히 고치지 말고 PR 본문에 영어 원문도 함께 수정했다고 밝힙니다
(#24664 `quicktour.md`, #47157에서 라이선스 안내 줄 `contain`→`contains` 수정).

---

# 2. 문체: 친근하되 예의 있는 존댓말, 성 중립

추적 이슈 #20179가 "informal tone (imagine you are talking with a friend about
transformers 🤗)"과 "translate in a gender-neutral way"를 명시합니다. 실제 병합
문서는 반말이 아니라 **해요체/합니다체를 섞은 친절한 존댓말**입니다.

- 절차·튜토리얼·가이드: 해요체 비중이 높습니다 (`~하세요`, `~해 보겠습니다`,
  `~살펴봅니다`).
- API 레퍼런스·개념 설명·논문 초록: 합니다체 비중이 높습니다.
- "당신", "우리는"을 기계적으로 넣지 않습니다. 논문 초록의 `we`는 문맥상 "저희는"
  또는 주어 생략으로 옮깁니다 (#41340).

| 원문 | 비권장 | 권장 |
|---|---|---|
| Make sure you have the libraries installed. | 라이브러리가 설치되어 있는지 확인하십시오. | 라이브러리가 설치되어 있는지 확인하세요. |
| This guide shows you how to fine-tune a model. | 이 가이드는 당신에게 모델을 파인튜닝하는 방법을 보여줄 것입니다. | 이 가이드에서는 모델을 미세 조정하는 방법을 살펴봅니다. |

---

# 3. 페이지 메타데이터: frontmatter가 없습니다

transformers 문서 `.md` 파일에는 YAML frontmatter가 없습니다. 대신:

- **라이선스 헤더 주석 블록** `<!--Copyright <연도> The HuggingFace Team ... -->`:
  번역자가 **그대로 유지**합니다. 안의 `⚠️ Note that this file is in Markdown but
  contains specific syntax for our doc-builder ...` 줄도 **영어 그대로** 두되,
  최신 영어 원문 문구와 일치시킵니다 (오래된 복사본은 `contain` 오타가 있음).
- **사이드바 목차** `docs/source/ko/_toctree.yml`: `local`(파일 경로 참조)은
  **번역하지 않고**, `title`(표시 제목)만 번역합니다. 아직 번역 안 한 항목은
  `local: in_translation` + `title: (번역중) <영문 제목>` 관례입니다.
  번역 완료 시 `title`을 한국어로 교체합니다 (#47157: `(번역중) Accelerator
  selection` → `가속기 선택`).
- 페이지 **내부** 목차("On this page")는 별도 블록이 아니라 그 문서의 헤딩·앵커
  구조에서 doc-builder가 자동 생성합니다. → 4장의 앵커·레벨 규칙이 내부 목차의
  정확성을 결정합니다.

```yaml
- local: accelerator_selection   # 번역하지 않음
  title: 가속기 선택              # 번역함
- local: in_translation
  title: (번역중) Video processors
```

---

# 4. 헤딩 앵커 `[[...]]`와 헤딩 레벨: 원문과 정확히 같아야 합니다 (하드 게이트)

`# 제목[[anchor]]` 형식에서 **제목만 번역하고 `[[anchor]]` 문자열은 영어 원문의
앵커와 바이트 단위로 동일**하게 둡니다. `#` 개수(헤딩 레벨)도 원문과 같아야
합니다.

앵커 문자열은 **라이브 문서에서 헤딩을 클릭했을 때 이동하는 실제 URL 앵커**를
씁니다. 두 형태가 있습니다.

1. **일반 kebab 슬러그**: `[[overview]]`, `[[load-a-tokenizer]]`, `[[xnli]]`,
   `[[squad]]`.
2. **`[[autodoc]]` 연동 헤딩의 정규화된 API 경로**: `[[transformers.ProcessorMixin]]`,
   `[[transformers.DataProcessor]]`,
   `[[transformers.data.processors.squad.SquadProcessor]]` (#39519).

번역자가 **번역된 제목이나 영어 제목에서 슬러그를 새로 만들면 안 됩니다.**
#39519에서 maintainer가 처음엔 API 경로형 앵커를 kebab로 바꾸라고 제안했다가,
"실제 URL 앵커를 쓴다"는 관례를 확인하고 철회했습니다.

최신 가이드 페이지(`accelerator_selection.md` 등)는 앵커가 아예 없기도 합니다.
그 경우 번역문도 앵커를 만들지 않습니다.

**권장**

```md
# 토크나이저[[tokenizer]]
## 토크나이저 가져오기[[load-a-tokenizer]]
## API[[transformers.AutoTokenizer]]
```

**비권장**

```md
# 토크나이저[[토크나이저]]              (슬러그 번역)
## 토크나이저 가져오기[[load-tokenizer]] (원문 slug와 다름)
### API[[transformers.AutoTokenizer]]   (원문은 ## 인데 ### 로 레벨 변경)
```

---

# 5. 렌더링 지시문 `[[open-in-colab]]`, `[[autodoc]]`은 번역하지 않습니다 (하드 게이트)

doc-builder 전용 문법입니다. 지시문 토큰과 뒤따르는 모듈/클래스 경로를 원문
그대로 둡니다.

```md
[[open-in-colab]]

[[autodoc]] AutoTokenizer
[[autodoc]] data.processors.utils.DataProcessor
```

---

# 6. API 참조 `` [`Class`] ``, `` [`~mod.Class.method`] ``은 번역하지 않습니다 (하드 게이트)

대괄호·백틱·틸드·경로를 모두 원문 그대로 두고, 설명 문장만 번역합니다.

```md
[`AutoTokenizer`]로 토크나이저를 가져옵니다.
[`~data.processors.utils.InputExample`] 목록을 반환합니다.
[`Trainer`]와 [`Seq2SeqTrainer`]를 사용합니다.
```

---

# 7. MDX 컴포넌트와 알림 블록은 태그·속성을 유지하고 내부 산문만 번역합니다 (하드 게이트)

transformers 문서는 두 세대의 문법이 공존합니다.

- **구형 MDX**: `<Tip>`, `<Tip warning={true}>`, `<frameworkcontent>`,
  `<pt>`/`<tf>`, `<hfoptions id="...">`/`<hfoption id="...">`, `<Youtube id="..."/>`
- **신형 GitHub 스타일 알림**: `> [!TIP]`, `> [!WARNING]`, `> [!NOTE]`

태그명과 속성(`id`, `warning={true}`)은 **번역·변형하지 않습니다.** 컴포넌트
내부의 산문만 옮깁니다. 속성 `id` 값이 영어 원문에서 바뀌면 번역문도 따라
바꿉니다 (#47157: `id="select-gpu"` → `id="accelerator-type"`는 원문이 바뀐 것).

**권장**

```md
> [!WARNING]
> 이 API는 실험적이며 언제든지 변경될 수 있습니다.

<hfoptions id="accelerator-type">
<hfoption id="CUDA">
...
</hfoption>
</hfoptions>
```

**비권장**: `<hfoption id="쿠다">`, `> [!경고]`, `<정보>` …

---

# 8. 코드 블록: 실행 토큰은 절대 보존, 설명 주석·docstring은 조건부 번역 가능

## 반드시 원문 그대로 (하드 게이트)

- 식별자: 변수명, 함수명, 클래스명, 인자명, `import` 경로
- 문자열 리터럴 중 실행 의미가 있는 값: 모델 ID(`google-bert/bert-base-uncased`,
  `syscv-community/sam-hq-vit-base`), URL, 파일 경로
- 환경 변수(`HF_TOKEN`, `CUDA_VISIBLE_DEVICES`, `ZE_AFFINITY_MASK`), CLI 명령과
  플래그(`torchrun --nproc_per_node`), config 키
- 코드 펜스 언어 태그: ` ```py `, ` ```bash `, ` ```cli `, ` ```json `
- 예제의 실행 결과, 오류 메시지, 에이전트 세션 로그, 모델 입출력 예시
  (#39913의 `tiny-agents` 세션 로그는 그대로 두고 마지막 한국어 설명만 번역)

## 조건부로 번역 가능 (문맥상 안전할 때)

- 설명용 주석: `# Load the tokenizer for BERT` → `# BERT용 토크나이저를 가져옵니다`
  (#41340: `# 2D location of a window in the image` → `# 이미지 내 창문의 2차원 위치`)
- 사용자 정의 도구 예제의 docstring, `Args:` 설명 (함수명·인자명 자체는 유지)

주석/docstring을 번역하면 코드 블록 해시가 바뀌므로 harness가 `code_blocks`를
`review_required`로 표시합니다 — 자동 실패가 아니라 리뷰어가 "실행 토큰은
안 바뀌었는지" 확인하는 신호입니다.

---

# 9. 문장 종결 콜론(`:`)은 항상 마침표로 바꿉니다 (예외 없음)

한국어는 문장 끝에 콜론을 쓰지 않습니다. 영어 원문이 목록·코드 블록 앞에서
콜론을 쓰더라도, 한국어 문장은 마침표로 끝냅니다. #41340, #39913, #32372 등
여러 병합 PR에서 반복적으로 지적된 항목입니다. 병합된 문서에 종결 콜론이 남아
있다면 그것은 검수 누락이지 허용 사례가 아닙니다.

| 원문 | 비권장 | 권장 |
|---|---|---|
| For example, to select accelerators 0 and 2 out of four: | 예를 들어, 네 개 중 0번과 2번을 선택하려면: | 예를 들어, 네 개의 가속기 중 0번과 2번을 선택하려면 다음과 같이 실행하세요. |
| SAM-HQ introduces 5 key improvements: | SAM-HQ는 5가지 핵심 개선 사항을 도입했습니다: | SAM-HQ는 다음과 같은 5가지 핵심 개선 사항을 도입했습니다. |

목록 항목 레이블(`- PCIe 버스 ID 순서로 정렬:` 처럼 항목 안에서 다시 중첩
블록을 여는 짧은 구)의 콜론은 harness가 문장으로 보지 않으므로 예외적으로
남을 수 있으나, 가능하면 이것도 마침표나 줄바꿈으로 정리합니다.

---

# 10. 목록: 원문과 같은 불릿·번호·들여쓰기 구조를 유지합니다

- 항목 수와 순서를 원문과 동일하게 둡니다.
- 목록 항목에 이어지는 문장의 들여쓰기를 잃지 않습니다. 들여쓰기가 깨지면
  원문에서 같은 항목이던 문장이 별도 문단으로 렌더링됩니다 (LeRobot #3383 리뷰).
- 한 목록 안에서 문장형과 명사구형을 섞지 않습니다.

---

# 11. 링크와 이미지: 타깃은 유지하고 텍스트만 번역합니다 (하드 게이트)

- 링크 타깃(상대 경로 `../model_doc/clip`, `./installation`, 외부 URL)은 절대
  바꾸지 않습니다. 링크 **텍스트**는 번역합니다.
- transformers 본체 문서에서는 영어 링크를 `/ko/` 경로로 바꾸지 않습니다
  (현지화 노트북 링크 스왑 예외는 course 저장소 한정).
- 이미지 파일 경로는 유지합니다. `alt` 텍스트와 캡션은 번역할 수 있습니다.
  `<div class="flex ...">`, `<img>` 태그 구조는 유지합니다.

---

# 12. 용어: Glossary → 승인된 기존 번역 → 병기 순으로 참고합니다

1. `skills/quality/glossary/*.tsv` + `skills/quality-transformers/glossary/transformers_terms.tsv`에
   등록된 용어를 우선합니다.
2. 같은 추적 이슈(#20179)에서 이미 병합된 인접 문서의 번역을 따릅니다.
3. 첫 등장 시 `한국어(English)` 병기 후 이후 한국어로 통일합니다
   (`미세 조정(fine-tuning)`, `양자화(quantization)`, `연산 능력(compute
   capability)`). `_toctree.yml` 제목에도 적용합니다 (`서빙(Serving)`).

문서 내 일관성과 API 정확성을 검색성보다 우선합니다. 독자는 검색보다 목차·상호
참조로 이동하는 경우가 많습니다.

---

# 13. 제품명·라이브러리명·모델명·데이터셋명·클래스명·API명은 번역하지 않습니다

`🤗 Transformers`, `PEFT`, `Accelerate`, `Datasets`, `Hub`, `Trainer`,
`TrainingArguments`, `AutoTokenizer`, `SamHQModel`, `ProcessorMixin`,
`from_pretrained()`, `device_map`, `torch_dtype` 등. 데이터셋·벤치마크명
`GLUE`, `SQuAD`, `XNLI`, `MNLI`도 유지합니다. 한국어 조사가 자연스럽게 붙는
것은 정상입니다 (`Trainer에`, `Transformers에서`, `Hub의`).

---

# 14. 번역투를 줄이고 절차 문장은 독자의 행동을 명확히 씁니다

- `~에 의해`, `~하는 것에 있어`, `~를 가지다`, `~을/를 가능하게 합니다`,
  `~로 하여금`, `사용되어질 수 있습니다` 같은 표현을 피합니다.
- `under the hood` → "내부적으로", `out of the box` → "별도 설정 없이".
- "Run the following" → "다음을 실행하세요" / "다음 명령어를 실행합니다".
- 영어 명사구 구조를 한국어 서술 구조로 재배열합니다
  (예: "검색된 사실에 응답의 근거를 둠으로써" → "답변의 근거를 검색 결과에 두어").

---

# 15. 의미·조건·확신의 강도, 경고는 약화하지 않습니다

- `may`/`can`/`should`/`must`/`only`/`up to`/`in some cases`/`not always`의 강도를
  그대로 유지합니다. `up to 30%`는 "최대 30%"이지 평균·보장값이 아닙니다.
- **실험적 API 경고**("언제든지 변경될 수 있습니다", "결과도 달라질 수 있습니다"),
  **deprecated 안내**, `> [!WARNING]` 안의 안전 관련 문구는 표현을 다듬되 위험
  범위를 축소하지 않습니다.

---

# 16. 최신성 동기화와 재동기화 PR

transformers 문서는 라이브러리 버전과 함께 갱신되는 living document입니다.
신규 번역과 **오래된 번역 재동기화** 둘 다 정식 작업 유형입니다.

재동기화 PR(#47157)에서는:

- 최신 영어 원문 구조로 본문을 교체합니다.
- stale 콘텐츠를 제거합니다: `<!-- TODO: ... not up to date ... -->` 주석,
  사라진 섹션(`# GPU 선택하기`), 없어진 환경 변수 안내(`CUDA_DEVICE_ORDER`의
  옛 설명), 깨진 문자.
- 라이선스 안내 줄, `_toctree.yml` 제목을 함께 갱신합니다.
- PR 본문에 "최신 영어 원문과 동기화했다"고 밝힙니다.
- deprecated 환경 변수/CLI 출력은 항목을 남기지 말고 삭제하거나 warning으로
  바꿉니다 (huggingface_hub #3804 관례).

---

# 17. 정보 추가는 원칙적으로 금지하되, 연결 문장은 허용합니다

원문에 없는 설명·평가·예시·결론을 추가하지 않습니다. 목적은 재현성·정확성
보호입니다. `즉`, `다만`, `이 경우`, `예를 들어` 같은 연결 표현은 원문 흐름을
자연스럽게 잇는 용도로만 씁니다. 초벌 번역 후 원문 문단이 번역문 아래 그대로
남아 있지 않은지 확인합니다 (#33959 리뷰의 원문 중복 삭제 요청).

---

# 18. 표: 벤치마크·비교표는 구조를 유지합니다 (하드 게이트)

열 수, 행 수, 열 순서, 정렬 마커를 유지합니다. 셀의 설명 텍스트는 번역하되
모델명·metric명·score·단위·버전 번호는 보존합니다. 비교 방향(higher/lower is
better)이 바뀌면 안 됩니다.

---

# 19. 이모지: 원문에 있는 경우에만 유지합니다

새로 추가하지 않습니다. `🤗 Transformers` 브랜드 표기, `> [!TIP]`류 알림 문법,
리소스 목록의 `(🌎로 표시)` 커뮤니티 마커(#41340)처럼 원문에 의미가 있는
경우만 유지합니다.

---

# 20. `model_doc/*.md` 정형 줄

모델 문서에는 doc-builder가 넣는 정형 줄이 있습니다.

- `*This model was released on <date> and added to Hugging Face Transformers on <date>.*`
  → `*이 모델은 <날짜>에 발표되었으며 <날짜>에 Hugging Face Transformers에
  추가되었습니다.*` — 문장은 번역, **날짜는 원문 그대로**.
- `This model was contributed by [name](url). The original code can be found [here](url).`
  → `이 모델은 [name](url)님께서 기여해주셨습니다. 원본 코드는 [여기](url)에서
  확인하실 수 있습니다.`
- 논문 초록은 `*` 블록으로, 학술 문체(합니다체, "저희는")로 옮깁니다.

---

# 21. PR·리뷰 프로세스 (harness가 자동 검증하지 않는 부분 — 수동 확인)

- PR 제목: `🌐 [i18n-KO] Translated <file> to Korean`, 본문에 `Part of
  https://github.com/huggingface/transformers/issues/20179`.
- "Before reviewing" 체크리스트: 번역 누락/중복, 맞춤법, 용어집, Inline TOC
  (`[[lowercased-header]]`), live-preview.
- KREW/PseudoLab 초기 리뷰 → 반영 → `@stevhliu`(또는 담당 maintainer) 최종
  리뷰 요청 → `build-doc` 코멘트 → doc-builder preview 확인 → `make style`,
  충돌 해결.
- `_toctree.yml`의 `local` 미번역 / `title` 번역 / 원문 구조·순서 동기화 /
  중복 섹션 없음 — harness가 검증하지 못하므로 사람이 확인합니다.
- `(번역중)` 표시가 항상 "누가 작업 중"을 뜻하지는 않습니다. 추적 이슈·상태표·
  최근 PR을 함께 확인합니다.

---

# 22. 품질 게이트 요약

## Hard Gate (실패 시 반드시 수정 — `reject`)

- Markdown 파싱, 인라인 코드, 환경 변수, CLI 플래그, 링크·이미지 타깃, LaTeX,
  표 구조, `TODO`/`FIXME`/`{{ }}` 마커
- **헤딩 앵커 문자열 + 헤딩 레벨** 원문 일치
- **`[[open-in-colab]]`/`[[autodoc]]` 지시문** 원문 일치
- **`` [`~mod.Class`] `` API 참조** 원문 일치
- **MDX 컴포넌트 태그·속성 + `> [!WARNING]`류 알림 마커** 원문 일치

## Review Gate (사람이 판단 — `review_required`)

- 코드 블록 해시 (주석/docstring 번역 시)
- 숫자·단위 토큰, 모델/데이터셋 ID, Python/API 식별자, bare URL
- 한국어 비율 / 미번역 영어 비율 / 길이 비율
- **문장 종결 콜론** (→ 마침표, 예외 없는 규칙, 높은 스타일 감점)
- 의미 강도, 과장, 번역투, 목록 일관성, 병기, alt 텍스트

## 수동 확인 (자동화 불가)

- `_toctree.yml` 정합성, 라이선스 `⚠️ Note` 줄 최신성, `model_doc` 날짜 정확성,
  리뷰 프로세스 완료 여부

---

# 23. 번역 전 체크리스트

- [ ] 라이선스 헤더 블록을 그대로 두었는가?
- [ ] 모든 헤딩의 `[[앵커]]`가 영어 원문과 바이트 단위로 같은가? 헤딩 레벨은?
- [ ] `[[autodoc]]`/`[[open-in-colab]]`, `` [`Class`] `` 참조를 건드리지 않았는가?
- [ ] `<Tip>`/`> [!WARNING]`/`<hfoptions id=...>` 태그·속성을 유지했는가?
- [ ] 코드 블록의 식별자·환경 변수·모델 ID·CLI를 바꾸지 않았는가?
      (주석/docstring만 번역)
- [ ] 문장 끝에 콜론이 하나도 남지 않았는가?
- [ ] 목록 항목 수·들여쓰기가 원문과 같은가?
- [ ] 링크 타깃을 유지하고 텍스트만 번역했는가?
- [ ] 실험적·deprecated·안전 경고의 강도를 약화하지 않았는가?
- [ ] 원문에 없는 설명을 추가하거나 원문 문단을 중복으로 남기지 않았는가?
- [ ] `_toctree.yml`의 `local`은 그대로, `title`만 번역했는가?
- [ ] (재동기화라면) stale 콘텐츠·TODO 주석·사라진 섹션을 제거했는가?
