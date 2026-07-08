# Latest SEO Test Audit

작성 시점: 2026-06-29

목적: 현재 repo의 최신 SEO 테스트를 실제로 실행하고, 현재 테스트가 보증하는 범위와 아직 수정해야 할 위치를 문서화한다.

## 조사 대상

- Branch: `pr-8-seo-skill`
- SEO skill root: `skills/seo`
- Entry point: `skills/seo/tools/seo_eval.py`
- Test root: `skills/seo/tests`
- Fixture manifest: `skills/seo/tests/fixtures/evaluation_manifest.yml`
- Dataset review: `skills/seo/reports/dataset-quality-review.md`
- Internal audit: `skills/seo/reports/internal-hfkrew-31-sample-audit.md`

현재 worktree에는 SEO skill 관련 변경과 신규 fixture/report/test 파일이 다수 있다. 이 문서는 현재 worktree 상태를 기준으로 한다.

## 실제 실행 결과

### 전체 pytest

실행:

```bash
/tmp/hf-workflow-seo-test-venv/bin/python -m pytest skills/seo/tests
```

결과:

```text
76 passed
```

테스트 범위:

- checker 단위 테스트
- CLI smoke test
- dataset manifest coverage test
- generated quality-level test
- real/mutated/curated internal sample test
- blocker test
- render signal test
- semantic review signal test
- metadata write-back E2E test
- golden snapshot regression

### 31개 실제 HFKREW 글 audit

실행:

```bash
/tmp/hf-workflow-seo-test-venv/bin/python skills/seo/tools/sample_audit.py \
  --posts-dir /home/hong/code/hugging-face-krew.github.io/_posts \
  --target-root /home/hong/code/hugging-face-krew.github.io \
  --json skills/seo/reports/internal-hfkrew-31-sample-audit.json \
  --markdown skills/seo/reports/internal-hfkrew-31-sample-audit.md
```

결과 요약:

```text
Total posts: 31
Status counts: {'NEEDS_CHANGES': 13, 'FAIL': 13, 'PASS': 5}
Missing metadata: {'description': 31, 'author': 1}
Required failures: {
  'h1_count': 19,
  'citations': 1,
  'opening_summary': 7,
  'descriptive_alt_text': 7,
  'alt_text_coverage': 6,
  'heading_hierarchy': 4
}
Blocker failures: {}
```

해석:

- 실제 블로그 글 31개 중 hard blocker는 없다.
- 대부분의 실패는 게시 차단성 오류가 아니라 현재 body gate의 구조/가독성 규칙에서 나온다.
- `h1_count`가 19건으로 가장 많다. HFKREW layout이 frontmatter title을 H1으로 렌더링하는 구조와 raw markdown H1 gate가 충돌할 가능성이 높다.
- 모든 실제 글에서 `description`이 누락되어 metadata 보완 수요가 크다. 다만 frontmatter는 body gate가 아니므로 현재 PR gate 차단 사유는 아니다.

### 대표 CLI 확인

실행:

```bash
/tmp/hf-workflow-seo-test-venv/bin/python skills/seo/tools/seo_eval.py \
  --file skills/seo/tests/fixtures/generated/good-post.md \
  --output /tmp/seo-good.md
```

확인한 점:

- `description` 74자도 frontmatter advisory에서 통과한다.
- description 길이는 pass/fail이 아니라 semantic review evidence로 제공된다.
- report에 title, description, opening, rendered H1 candidates가 함께 출력된다.

## 현재 테스트가 보증하는 것

현재 테스트셋은 내부 개발/회귀 테스트 용도로는 충분한 수준이다.

- 42개 fixture case가 manifest에 등록되어 있다.
- source type은 `synthetic`, `mutation`, `curated_internal`, `real_hfkrew`로 나뉜다.
- noindex, broken internal link, broken local image path는 blocker로 검증된다.
- title/description/opening/H1 semantic mismatch는 pass/fail로 하드코딩하지 않고 evidence packet으로 노출된다.
- approved `MetadataPlan` write-back은 post frontmatter와 manifest 기록 후 재평가까지 E2E로 검증된다.
- 고정 description 길이 기준은 제거되어, 불필요한 휴리스틱 gate가 줄었다.

## 현재 테스트가 보증하지 못하는 것

다음은 아직 테스트가 통과해도 보증되지 않는다.

- 팀이 승인한 gold positive label
- 실제 Jekyll full render 결과의 최종 `<head>`, `<title>`, canonical, og tag, rendered H1
- `metadata.build_plan()`이 생성하는 title/description/canonical/hreflang 품질
- LLM rubric의 실제 판단 품질
- GitHub Action artifact 생성, sticky PR comment, fork PR 보안 모델
- URL 기반 Lighthouse/Rich Results/Search Console 계열 검증

## 수정해야 할 위치와 방법

### 1. H1 gate를 rendered signal 기반으로 바꾸기

위치:

- `skills/seo/tools/checkers/content.py`
- 현재 로직: markdown body의 H1 개수만 세고 `h1_count == 1`을 required로 둔다.

문제:

- HFKREW `_layouts/post.html`은 frontmatter title을 H1으로 렌더링한다.
- 따라서 body H1이 0개여도 최종 HTML에는 H1이 1개일 수 있다.
- 반대로 body H1이 1개면 최종 HTML에서는 layout title H1 + body H1로 2개가 될 수 있다.

수정 방향:

- `h1_count`를 raw markdown required gate에서 제거하거나 advisory로 낮춘다.
- `render_signals.extract_render_signals()`의 `effective_h1_count`를 사용해 evidence를 제공한다.
- Jekyll full render가 붙기 전까지는 H1을 hard fail로 쓰지 않는 것이 안전하다.

우선순위: 높음

### 2. `opening_summary`와 `citations`를 required에서 policy/review로 이동

위치:

- `skills/seo/tools/checkers/content.py`

문제:

- 현재 `opening_summary`는 한국어 150자, 영어 50단어 기준으로 required다.
- `citations >= 1`도 required다.
- 정보성 기술 글에는 유용하지만 회고, 공지, 사용 안내, 프로젝트 소개 글에는 과차단이 될 수 있다.

수정 방향:

- blocker가 아닌 품질 항목으로 보고 `recommended` 또는 `needs_review` 계층으로 이동한다.
- page type 또는 manifest policy가 있는 경우에만 required로 승격한다.
- PR comment에서는 “수정 필요”가 아니라 “리뷰 필요 evidence”로 보여준다.

우선순위: 높음

### 3. `metadata.build_plan()` 구현 전 policy contract 확정

위치:

- `skills/seo/tools/metadata.py`

현재 상태:

- `apply()`는 구현되어 있다.
- `build_plan()`은 아직 `NotImplementedError`다.

문제:

- metadata write-back은 검증되지만 title/description/canonical/hreflang 후보 생성 품질은 보증되지 않는다.
- 특히 canonical/hreflang은 SEO 팀 단독 결정이 아니라 번역본을 독립 색인 대상으로 볼지에 대한 콘텐츠 정책이 필요하다.

수정 방향:

- `translation-seo-policy.yml` 또는 manifest 입력으로 다음 값을 받는다.
- `translation_indexing`: `independent` 또는 `source_support`
- `canonical_policy`: `self` 또는 `source`
- `hreflang`: `enabled/disabled`, source locale, target locale
- `build_plan()`은 이 policy 없이는 canonical/hreflang을 확정하지 않고 `NEEDS_REVIEW`를 반환해야 한다.

우선순위: 높음

### 4. LLM rubric을 실제로 연결하되 deterministic output schema로 제한

위치:

- `skills/seo/tools/rubric.py`
- `skills/seo/tools/seo_eval.py`

현재 상태:

- rubric은 skeleton이며 항상 unavailable이다.
- gate는 deterministic result만 사용한다.

문제:

- curated semantic negative는 현재 gate를 통과한다.
- title/description/opening mismatch는 evidence로는 보이지만 자동 판단은 없다.

수정 방향:

- LLM은 tool 실행자가 아니라 `semantic_review` packet을 평가하는 policy judge로만 사용한다.
- output은 JSON schema로 고정한다.
- 최소 필드:
  - `meaning_consistency`: `pass | needs_review | fail`
  - `title_description_alignment`
  - `description_opening_alignment`
  - `canonical_policy_risk`
  - `rationale`
- deterministic gate와 LLM policy gate를 분리해 report에 둘 다 표시한다.

우선순위: 중간~높음

### 5. GitHub Action E2E를 sandbox에서 검증

위치:

- 이 repo 또는 sandbox repo의 `.github/workflows/*`

현재 상태:

- 로컬 CLI와 pytest는 검증되어 있다.
- GitHub Action artifact/comment 흐름은 현재 보고서 기준 미검증이다.

수정 방향:

- workflow_dispatch 기반 sandbox action부터 만든다.
- 입력은 fixture path 또는 URL list로 시작한다.
- output artifact:
  - `seo-report.json`
  - `seo-report.md`
  - optional `metadata-candidate.json`
- PR comment는 다음 단계에서 sticky comment action으로 연결한다.
- fork PR 처리는 split workflow 또는 manual trigger로 별도 설계한다.

우선순위: 중간

### 6. Jekyll full render 검증 추가

위치:

- 새 테스트 또는 도구: `skills/seo/tools/jekyll_render.py` 같은 별도 모듈
- 기존 근사 모듈: `skills/seo/tools/render_signals.py`

현재 상태:

- `render_signals.py`는 HFKREW layout의 title H1 주입을 근사한다.
- 실제 Jekyll build는 하지 않는다.

문제:

- jekyll-seo-tag, Liquid include, 최종 HTML head를 보증하지 못한다.

수정 방향:

- Ruby/Bundler 환경이 있는 CI job에서만 full render test를 optional로 실행한다.
- 로컬 offline test는 지금처럼 근사 render signal을 유지한다.
- full render 결과에서 title, meta description, canonical, og tag, H1 count를 별도 artifact로 저장한다.

우선순위: 중간

## 결론

현재 SEO 테스트는 “로컬 deterministic harness + 내부 평가셋 + semantic evidence + metadata write-back”까지는 잘 검증한다. 최신 실행 기준 `76 passed`이며, 31개 실제 글 audit도 생성된다.

하지만 지금 당장 수정해야 할 핵심은 두 가지다.

1. `h1_count`, `opening_summary`, `citations` 같은 문맥 의존 항목을 hard required gate에서 낮추는 것
2. `metadata.build_plan()`과 LLM rubric을 구현하기 전에 policy contract와 JSON output schema를 확정하는 것

이 두 가지를 고치지 않으면 GitHub Action에 올렸을 때 “테스트는 통과하지만 실제 PR에서는 과차단하거나 semantic mismatch를 놓치는” 상태가 된다.
