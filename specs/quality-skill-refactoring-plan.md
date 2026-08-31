# 번역 품질 스킬(`skills/quality`) 리팩토링 계획

> 출처: `quality-refactoring` 세션(워크트리 `quality-profiles-refactor`) 대화 정리.
> 목표 — 문서 유형·작업 repo별로 갈아끼우는 부분과 글로벌하게 재사용할 부분을
> 구조적으로 분리하고, 기존 워크플로우를 깨지 않으면서 마이그레이션한다.
>
> 이 리팩토링이 `quality-skill-builder` 스킬에 주는 영향은
> [`skills/quality-skill-builder/REFACTORING.md`](../skills/quality-skill-builder/REFACTORING.md) 참조.

## 최종 합의 사항 (Phase 0 결정)

대화 중 사용자가 확정한 내용:

1. **폴더 스킴**: `skills/quality/profiles/<name>/`. 최상단 경로를 `skills/quality`로
   유지해 워크플로우·CI·spec 경로가 안 깨지게 한다. (sibling 스킬 `skills/quality-<name>` 안 씀)
2. **계층**: 지금은 **2계층**(`core → 프로파일`)만. 3계층 체인과 빈 중간 계층(`hf-docs-generic`)은
   실제 중복이 쌓이기 전까지 만들지 않는다(YAGNI). `profile.yml`에 `extends` 필드는 스키마로
   넣어두되 값은 당장 `core`뿐 — 나중에 N단으로 확장해도 로더 재작업 없음.
3. **기본 프로파일** = `hf-blog`. `--profile` 미지정 시 현재 동작과 바이트 단위로 동일해야 한다.
4. **오버레이 병합** = "effective 파일로 pre-merge" 방식. 즉 병합 결과를 단일 파일로 렌더해
   기존 로더에 넘긴다(같은 파일을 하나만 본다).
5. `configs/protected_patterns.yml`은 **삭제하지 않고 그대로 둔다**. 참조 코드가 없어 병합에
   끼어들 여지가 없고, 원 작성자 의도가 확인되면 그때 core 자산 편입 여부를 결정.
6. 현재 문서 프로파일은 `transformers-ko` 하나뿐이므로 `hf-docs-generic` 같은 중간
   계층은 지금 만들지 않는다.
7. 작업은 **새 브랜치 + 워크트리**에서 진행.

---

## 1. 검토 결론

**방향은 맞다.** 스캐폴딩 복사 문제는 실재한다:

- `quality-skill-builder`의 Phase 4가 `cp` + `diff`로 `schemas/*.json`, `pyproject.toml`,
  `eval_config.yml`, glossary, `gates.yml` / `style_policy.yml`의 구조 부분을 **물리적으로 복제**하도록 지시.
- `quality-harness-architecture.md`도 "도구 자체 설명이라 문서 유형마다 다시 만들지 말 것"이라며 복사 문제를 이미 인정.
- 엔진(`translation_quality_harness.py`)은 이미
  `--style-guide / --style-policy / --gates-config / --evaluation-config / --glossary / --llm-judge-prompt`
  플래그로 자산을 갈아끼울 수 있게 설계됨 → "엔진 공유, 자산만 교체"의 큰 틀은 절반 완성.

**조정한 경계선:** 현재 `skills/quality` 자체가 사실상 '블로그 프로파일'이다
(이름·`SKILL.md`·`style/hf-blog-*.md`·`gates.yml`의 `front_matter` 키·`mqm_prompt.md`의
"technical blog posts" 문구가 전부 블로그 가정). 따라서 엔진/스키마/공유 glossary는
`skills/quality/`에 그대로 두고, **블로그 고유 자산만 `skills/quality/profiles/hf-blog/`로 내려
"블로그도 하나의 프로파일"로** 만든다.

**갈아끼우는 축은 원래 2개**지만(문서 유형 / 작업 repo), 현재는 문서 프로파일이
`transformers-ko` 하나뿐이므로 `core → transformers-ko` 평면으로 시작하고,
`diffusers-ko` 등이 생겨 실제 중복이 보이면 그때 공통부를 부모로 추출한다.

---

## 2. 자산 분류: 글로벌(core) vs 갈아끼우기(프로파일)

| 자산 | 분류 | 근거 |
|---|---|---|
| `tools/translation_quality_harness.py`, `simple_quality_report.py`, `tools/__init__.py` | **core** | 파이프라인 엔진. 이미 CLI 플래그로 자산 주입 가능 |
| `schemas/mqm_judge.schema.json`, `quality_report.schema.json` | **core** | 출력 형태. 문서 유형과 무관 |
| `pyproject.toml` | **core** | 패키징·의존성 |
| `tests/test_translation_quality_harness.py`, `test_simple_quality_report.py` | **core** | 엔진 단위 테스트(파싱/정렬/게이트 메커니즘/점수 공식) |
| `glossary/ml_terms.tsv`, `product_terms.tsv`, `ko.tsv` | **core(공유) + 프로파일 델타** | 셋 다 HF 전반 ML/제품 용어. 프로파일은 소수 용어만 추가 |
| `configs/eval_config.yml` (임계값) | **core 기본값 + 프로파일 오버레이(보정 후에만)** | 블로그 보정값을 baseline으로. 문서 유형별 보정은 빌더 Phase 5에서만 |
| `configs/gates.yml` **구조** | **core** | 게이트 목록·심각도 라우팅 메커니즘 |
| `configs/gates.yml` **값** (`front_matter.required/preserved_keys`, `code_blocks.status`, `locale_punctuation.forbidden`, `todo_markers`) | **doc-type 프로파일** | frontmatter 유무, 코드 주석 번역 허용 여부 등이 문서 유형마다 다름 |
| `configs/style_policy.yml` **구조**(validator 배선) | **core** | |
| `configs/style_policy.yml` **값**(`modal_strength` / `overstatement` / `translationese` / `title_quality` / `first_mention_terms`) | **doc-type 프로파일** | 전부 로컬라이제이션 가이드에서 파생 |
| `judges/mqm_prompt.md` **골격**(JSON 스키마·MQM 카테고리 설명) | **core** | |
| `judges/mqm_prompt.md` **루브릭 문구**("technical blog posts", 제목/이모지 규칙) | **doc-type 프로파일** | |
| `style/hf-blog-ko-translation-guide.md` (761줄) | **doc-type 프로파일** | 통째로 블로그 가이드 |
| `SKILL.md`, `examples/input-manifest.yaml` | **doc-type 프로파일** | |
| `tests/golden_set.yml`, `challenge_set.yml`, `fixtures/`, `test_acceptance_sets.py` | **doc-type 프로파일** | 블로그 승인/도전 세트 |
| `AGENTS.md`, `README.md` | **분리**: CLI 사용법 = core, 나머지 = 프로파일 | |
| `configs/protected_patterns.yml` | **그대로 둠**(사장된 파일, 참조 없음) | 삭제 시 원 작성자 의도 유실 우려 |
| repo별: `.mdx` 확장자, `links` 게이트의 `/ko/` 예외, `transformers_terms.tsv`, `model_doc` 정형줄 가중치 | **repo 프로파일** | 차이점 문서 F절 |

---

## 3. 제안 아키텍처 (2계층 시작 구조)

```
skills/quality/                          # 최상단 경로 유지 → 워크플로우/CI/spec 경로 안 깨짐
  tools/
    translation_quality_harness.py       # 엔진 (그대로, 이동 금지)
    simple_quality_report.py
    profile_loader.py                     # ← 신규: profile.yml 해석 + 오버레이 deep-merge + effective 렌더
  schemas/                                # core
  configs/
    gates.base.yml                        # 구조 + 문서유형 중립 기본값
    style_policy.base.yml
    eval_config.base.yml                  # 블로그 보정값 = baseline (문서화)
    protected_patterns.yml               # 손대지 않고 유지
  glossary/                               # HF 공유 TSV (ml_terms, product_terms, ko) — 위치 불변
  judges/
    mqm_prompt.base.md                    # 골격 (include 지점 표시)
  pyproject.toml                          # 제자리 유지 (이동 금지)
  tests/                                  # 엔진 테스트만
  docs/quality-harness-architecture.md    # "도구 자체 설명" 문서 1부만

  profiles/
    README.md                             # core / 프로파일 경계 규칙, 탈출구 명시
    hf-blog/                              # ← 기존 skills/quality의 블로그 자산 이동
      profile.yml                         # extends: core
      SKILL.md
      style/hf-blog-ko-translation-guide.md
      configs/gates.overlay.yml           # base 대비 델타만
      configs/style_policy.overlay.yml
      configs/eval_config.overlay.yml     # 비어 있음 (보정 전)
      judges/mqm_prompt.overlay.md        # 블로그 루브릭 조각
      glossary/hf-blog_terms.tsv          # 프로파일 추가 용어만
      tests/{golden_set.yml,challenge_set.yml,fixtures/,test_acceptance_sets.py}
    transformers-ko/                       # 기존 skills/quality-transformers
      profile.yml                         # extends: core  (나중에 extends: hf-library-docs 로 교체 가능)
      style/transformers-ko-translation-guide.md
      configs/*.overlay.yml
      judges/mqm_prompt.overlay.md
      glossary/transformers_terms.tsv
      docs/blog-vs-transformers-docs-differences.md   # 이미 작성됨 → 여기로 이동
      tests/...
```

### `profile.yml` 예시

```yaml
name: transformers-ko
extends: core                    # 현재는 core 만. 미래에 hf-library-docs 등으로 교체
overlays:
  gates: configs/gates.overlay.yml
  style_policy: configs/style_policy.overlay.yml
  eval_config: configs/eval_config.overlay.yml
  mqm_prompt: judges/mqm_prompt.overlay.md
glossary:
  mode: append                   # core 3파일에 추가
  files: [glossary/transformers_terms.tsv]
style_guide: style/transformers-ko-translation-guide.md
merge_rules:
  gates.locale_punctuation.forbidden: replace     # 리스트 병합: 교체
  gates.todo_markers.markers: replace
  style_policy.first_mention_terms: merge_by_key
repo_bindings:                    # 워크플로우가 target_repo 로 프로파일 자동 선택
  - huggingface/transformers
file_globs: ["docs/source/ko/**/*.md"]
```

### 오버레이 병합 전략

하네스의 손수 만든 미니 YAML 파서를 **건드리지 않는다.** `profile_loader.py`가:

1. `extends` 체인을 따라 `base + 각 계층 overlay`를 **파이썬 dict에서 deep-merge**
   (dict는 재귀 병합, 리스트는 `merge_rules`에 따라 `replace` / `append` / `merge_by_key`).
   2단이든 3단이든 동일한 **N-way left fold** 한 함수:
   `effective = deep_merge(base, parent.overlay, child.overlay)`.
2. 병합 결과를 캐시 디렉터리에 **단일 effective 파일**로 씀
   (`.quality-cache/<profile>/gates.yml` 등).
3. 그 경로들을 기존 `--gates-config` 등 플래그에 그대로 넘김 → 기존 로더 코드 무수정.

**공유 내용은 물리적으로 부모 파일 한 곳에만 존재하고 절대 복제되지 않는다.**
자식 오버레이에 부모 블록을 복붙하고 있으면 → 그 블록은 부모로 올라가야 한다는 신호(또는 `merge_rule`이 틀림).

**pre-merge를 택한 이유:**
1. **파서 무수정.** `load_evaluation_policy` / `load_style_policy` / 게이트 로더는 각각
   파일 경로 딱 하나만 읽는다. pre-merge하면 취약한 미니 YAML 파서를 안 건드림.
2. **병합 로직 한 곳.** `profile_loader.py`의 평범한 dict 병합 하나로 격리·단위테스트 가능.
3. **등가성 증명이 쉬움.** effective 파일이 실제 산출물이라 `diff`·골든 스냅샷 커밋 가능 →
   Phase 2의 "리팩토링 전 `gates.yml`과 완전 동일" 검증이 스냅샷 비교 한 줄로 끝남.

---

## 4. 하네스에 필요한 변경 (전부 additive, 블로그 동작 불변)

| 변경 | 규모 | 리스크 |
|---|---|---|
| `--profile PATH` 플래그 추가. 없으면 오늘과 100% 동일(`DEFAULT_*` 상수 유지). 있으면 `profile_loader`가 effective 경로 6종 해석 | ~40줄 | 낮음 (미사용 시 no-op) |
| `profile_loader.py` 신규 (`extends` 해석 + deep-merge + effective 파일 렌더) | ~150줄 | 낮음 (독립 모듈) |
| `read_yaml_scalars()`의 `key: []` 파싱 버그 수정 (인라인 빈 리스트를 문자열 `"[]"`가 아니라 빈 리스트로) | 1줄 | 낮음. 블로그 config는 이 문법 안 씀 → 검증 후 no-op 확정. frontmatter 없는 프로파일의 전제 조건 |
| `DEFAULT_*` 상수를 `--profile` 미지정 시 암묵적으로 `profiles/hf-blog` effective set으로 resolve (또는 그대로 두고 워크플로우에서 항상 `--profile` 명시) | 소 | 낮음 |
| **범위 밖**: 앵커/지시문/MDX 컴포넌트/문장끝 콜론 validator 신설 | — | transformers 프로파일 구축(빌더 스킬 Phase 3–4)에서 별건. 리팩토링은 프로파일이 `extra_validators: [...]`를 선언하는 레지스트리만 준비 |

---

## 5. 기존 워크플로우 영향

| 소비자 | 현재 | 영향 / 대응 |
|---|---|---|
| `scripts/hf_agent/run_skill_review.py:151` | 하네스 경로 하드코딩, 자산 플래그 미전달 → 전적으로 `skills/quality/` 기본값 의존 | `--profile` 인자 추가, `target_repo` → 프로파일 매핑(`repo_bindings`) 주입. 그 전까지 기본 프로파일 = `hf-blog`면 바이트 동일 |
| `scripts/run_local_review.py:159` | 동일 | 동일. `--profile` 옵션 노출 |
| `.github/workflows/reusable-pr-review.yml:142,178` | MQM 캐시 키가 `hashFiles('workflow/skills/quality/judges/mqm_prompt.md', ...glossary/*.tsv)` | 자산이 `profiles/hf-blog/`로 이동하면 **glob 경로 수정 필수**. 캐시 키를 "프로파일명 + effective prompt/glossary 해시"로 전환 |
| `tests/test_pr_review_workflow.py:136-139` | 위 경로 리터럴을 assert | 경로 이동과 **동시에** 수정 |
| `tests/test_run_skill_review.py:262` | `command[1] == "skills/quality/tools/translation_quality_harness.py"` assert | `tools/`는 안 움직이므로 유지. `--profile` 추가 시 assert 보강 |
| `.github/workflows/quality-harness-tests.yml` | path filter `skills/quality/**`, `pip install -e skills/quality[dev]`, pytest | `profiles/`도 `skills/quality/**` 하위라 필터 OK. pyproject 제자리면 설치 OK. 프로파일 테스트 수집용 conftest만 추가 |
| `pyproject.toml:16` (루트 testpaths `skills/quality/tests`) | | `skills/quality/profiles/*/tests` 추가 또는 discovery conftest |
| `scripts/enforce_quality_gate.py` | `reports/pr-XXX/quality-report.json`의 `status` 소비 | **출력 스키마 불변 → 영향 없음** |
| `scripts/hf_agent/verify_review_artifacts.py` | `quality-eval.json` 메타(prompt hash, judge model, target hash) 검증 | 형태 불변. 단 blog prompt가 base+overlay 조립으로 바뀌면 내용이 같아도 **prompt_hash가 한 번 바뀜** → 커밋된 golden 해시 재생성 필요 |
| `translation-flow` ECL glossary 병합 (`skills/quality/glossary/*.tsv` 읽음) | | 공유 TSV 3파일은 `skills/quality/glossary/`에 **그대로 유지**, 프로파일 glossary는 additive → translation-flow 무영향. README에 명시 |
| `specs/*.md`, 루트 `README.md`, `translation-flow/README.md` | 경로 언급 | 기능 영향 없음. Phase 5에서 일괄 갱신 |
| **미머지 브랜치** `quality-transformers`, `quality-skill-builder` | 둘 다 sibling 폴더 모델(`skills/quality-transformers` 등) 전제 | 레이아웃 먼저 확정 후 두 브랜치 재조정해 머지. 안 그러면 마이그레이션 2회 |

---

## 6. 마이그레이션 순서 (각 단계 독립 배포 가능)

### Phase 0 — 결정 (코드 없음) — **완료**
위 "최종 합의 사항" 참조.

### Phase 1 — 프로파일 배관 도입, 동작 변화 0
- `profile_loader.py` 추가, `--profile` 플래그 추가(미지정 시 no-op)
- `key: []` 파서 수정 (블로그 config에 해당 문법 없음 → `skills/quality/tests` 그대로 green 확인)
- 배포. 아직 아무도 `--profile` 안 씀

### Phase 2 — `hf-blog` 프로파일을 제자리에서 분리 (**등가성 증명이 핵심**)
- `git mv`로 블로그 자산 → `skills/quality/profiles/hf-blog/`
- `gates.yml` → `gates.base.yml` + `hf-blog/configs/gates.overlay.yml`로 분해.
  **effective 렌더 결과가 리팩토링 전 `gates.yml`과 완전히 동일**함을 golden 스냅샷 테스트로 고정.
  `style_policy.yml`, `mqm_prompt.md`도 동일하게.
- `run_skill_review.py` / `run_local_review.py`가 `--profile skills/quality/profiles/hf-blog`
  명시하도록 수정 (동작 동일, 바인딩 가시화)
- CI `hashFiles` glob + `tests/test_pr_review_workflow.py` 리터럴 동시 수정
- golden 파일의 prompt/schema 해시 1회 재생성
- 전체 스윕: `skills/quality/tests` + 루트 `tests/` + 워크플로우 테스트 → "등가 증명" 게이트
- 배포

### Phase 3 — `transformers-ko` 프로파일 추가 (2번째 실사용 소비자)
- 여기서 `quality-skill-builder`의 Phase 1–5를 실제로 돌리되 산출물이 **프로파일 디렉터리**(sibling 스킬 아님)
- 이미 작성된 `skills/quality-transformers/docs/*` 2건을 `profiles/transformers-ko/docs/`로 이동
- `profile.yml`(현재 `extends: core`), 오버레이, transformers glossary, MQM overlay, transformers 스타일 가이드 작성
- transformers 전용 엔진 작업(앵커/지시문/MDX validator, 문장끝 콜론 validator, frontmatter 없음 처리)
  — 각각 빌더 스킬 체크포인트대로 사용자 승인 후
- 임계값 보정은 `profiles/transformers-ko/configs/eval_config.overlay.yml`에서만

### Phase 4 — 빌더 스킬을 프로파일 모델로 재작성
- `quality-skill-builder` Phase 0: "sibling 폴더 생성" → "`profiles/<name>/` 생성 + `profile.yml` 작성,
  schemas/pyproject/엔진은 절대 `cp` 안 함"
- Phase 4: `cp` + `diff` 파일트리 가이드 → "overlay 파일 작성 후 `profile_loader --render`로
  effective config를 base와 diff해 의도한 델타만 있는지 확인"
- `quality-skill-builder`의 문서(`AGENTS.md`, `RATIONALE.md`, `README.md`, `SKILL.md`,
  `phases/00-scope.md`)에 남아 있는, 존재하지 않는 스킬 폴더에 대한 worked-example 참조를
  실재하는 프로파일 경로로 교체
- 정합성 맞춘 뒤 `quality-skill-builder` 브랜치 머지

### Phase 5 — repo 서브프로파일 + 문서
- 실제 중복이 관측되면 `diffusers-ko`, `lerobot-ko`(`.mdx`) 등 얇은 repo 프로파일을 도입하고,
  이때 공통부를 문서유형 부모(`hf-library-docs`)로 추출하고 `extends`만 교체
- `specs/`, 루트 `README.md`, `translation-flow/README.md` 갱신
- `profiles/README.md` 작성: "core / 프로파일에 각각 무엇이 들어가는가" 규칙 + 탈출구
  ("translation-flow가 profile 자산을 직접 읽어야 하면 `skills/quality/profiles/`를 최상위
  `quality-profiles/`로 승격. 바인딩은 `run_skill_review.py`, `run_local_review.py`, CI `hashFiles` 3곳뿐.")

---

## 7. 리스크 및 체크포인트

- **effective-config 등가성**이 Phase 2의 전부. 완화책: 각 프로파일의 effective
  gates/style_policy/eval_config를 렌더해 체크인된 스냅샷과 비교하는 golden 테스트.
  `hf-blog`의 첫 스냅샷은 반드시 오늘의 `gates.yml` 등과 일치해야 함.
- **미니 YAML 파서 취약성**: Python에서 pre-merge 후 단일 파일 주입으로 파서 확장 회피.
  단 리스트 병합 의미(`replace` / `append` / `merge_by_key`)를 `profile.yml`에 **명시**해야 함.
- **prompt 해시 1회 변동**: 캐시된 MQM 결과 및 커밋된 해시가 한 번 무효화됨.
  워크플로우 캐시 키에 prompt 해시가 이미 포함돼 있어 자가 치유되지만, 커밋된 golden은 수동 재생성.
- **브랜치 분기**: `quality-transformers`, `quality-skill-builder` 둘 다 sibling 모델 전제 + 둘 다 미머지.
  **레이아웃 확정 전에는 두 브랜치 머지 보류.**
- **움직이지 말 것**: `skills/quality/tools/`, `skills/quality/pyproject.toml`.
  이게 `run_skill_review.py`·CI·루트 testpaths를 안정적으로 유지하는 앵커.

---

## 8. 미결 항목

- `profiles/`를 `skills/quality/` **밖**으로 뺄지 여부: 일단 `skills/quality/profiles/`로 진행,
  translation-flow 공유 범위가 구체화되면 최상위 `quality-profiles/`로 승격 검토(저비용 find-replace).
- 문서유형 → repo 계층 순서: 지금은 계층을 정하지 않음. `diffusers-ko`가 생겨 실제 중복이
  관측되면 "가장 적게 변하고 가장 넓게 공유되는 축을 위로" 원칙으로 부모 추출.
- `extends`는 **단일 부모 선형 체인**만 지원(다중 부모/믹스인 미지원).
