# SEO Skill Logic Improvement Proposal

현재 평가 데이터셋과 수동 정성평가를 바탕으로, checker 로직을 어떻게 고쳐야 하는지 정리한다.

## 핵심 판단

현재 로직은 deterministic gate를 너무 빨리 `PASS/NEEDS_CHANGES/FAIL/BLOCKED`로 확정한다. HFKREW 블로그처럼 Jekyll layout, 번역 원문 구조, TOC marker, metadata writer가 섞이는 환경에서는 raw markdown만 보고 hard gate를 거는 방식이 과차단을 만든다.

따라서 v1에서 가장 합리적인 방향은 다음이다.

```text
deterministic checker = evidence/signal collector
hard gate = 명확한 blocker만
policy/rubric = signals를 보고 문맥별 판단
```

## 바로 고칠 항목

### 1. H1 gate

현재 문제:

- `_layouts/post.html`이 `page.title`을 `<h1 class="posttitle">`로 렌더링한다.
- body markdown에 H1이 0개인 글은 실제 HTML에서 H1 1개일 수 있다.
- body markdown에 H1이 1개인 글은 실제 HTML에서 layout H1 + body H1 = H1 2개일 수 있다.
- 따라서 raw markdown `h1_count == 1`은 HFKREW 구조에 맞지 않는다.

근거:

- `skills/seo/reports/render-signal-audit.md`
- `skills/seo/tests/test_render_signals.py`

제안:

- raw markdown H1 required gate 제거.
- rendered signal 기준으로 `layout_h1_count`, `body_h1_count`, `effective_h1_count`를 수집.
- full Jekyll render 전까지 H1은 `ADVISORY`로 둔다.
- HFKREW 정책으로는 body markdown H1을 쓰지 않고 `##`부터 시작하는 편이 자연스럽다.

### 2. Opening summary

현재 문제:

- 고정 길이 threshold는 글 유형에 따라 부정확하다.
- TOC marker나 HTML comment가 첫 문단으로 잡히면 오탐이 난다.

이미 개선한 것:

- `get_opening_paragraphs`에서 `<!--toc-->`, `* TOC`, `{:toc}`, HTML comment, Liquid marker를 제외.

추가 제안:

- `opening_summary`를 hard required gate에서 signal/advisory로 낮춘다.
- signal로는 `first_real_paragraph`, `first_real_paragraph_chars`, `first_three_paragraph_chars`, `toc_skipped`를 제공한다.
- policy/rubric이 글 유형별로 "도입부 보강 필요" 여부를 판단한다.

### 3. Description

현재 문제:

- description 존재/길이만으로는 부족하다.
- `description-body-mismatch.md`처럼 description이 있어도 본문과 다른 약속을 할 수 있다.

제안:

- deterministic: 존재 여부, 길이, 중복 여부만 signal로 수집.
- policy/rubric: title, H1, opening paragraph, description 의미 정합성 판단.
- metadata writer는 본문에 없는 claim을 만들지 않는 제약을 가져야 한다.

### 4. Image alt

현재 문제:

- 빈 alt는 잘 잡지만, `image-1` 같은 meaningless alt는 의미 품질을 안정적으로 잡기 어렵다.

제안:

- deterministic: empty alt, filename-like alt, repeated alt, too-short alt signal.
- policy/rubric: 주변 문맥과 alt 의미 정합성 검토.
- PR comment는 "빈 alt"와 "의미 약한 alt"를 분리한다.

### 5. Canonical / hreflang

현재 문제:

- 번역본 canonical을 self로 둘지 원문으로 둘지는 checker가 단독으로 결정할 수 없다.

제안:

- `translation-seo-policy.yml` 같은 정책 파일을 둔다.
- checker는 policy와 실제 frontmatter가 충돌하는지만 판단한다.
- 정책 미정이면 `NEEDS_POLICY_DECISION` 또는 advisory로 둔다.

## Gate 정책 제안

### `BLOCKED`

명확하고 문맥 의존성이 낮은 항목만 포함한다.

- `robots: noindex`
- 깨진 내부 링크
- 깨진 로컬 이미지 경로
- frontmatter 파싱 실패
- 파일 읽기 실패

### `NEEDS_CHANGES`

수정이 명확하지만 차단 여부는 팀 정책에 맡긴다.

- 빈 이미지 alt
- 필수 metadata 누락
- 빈 본문
- title 없음

### `ADVISORY` / `NEEDS_REVIEW`

문맥 판단이 필요한 항목이다.

- H1/heading 구조
- opening summary 길이/품질
- citation 필요 여부
- description-body semantic mismatch
- generic link text
- canonical/hreflang 정책 충돌

## 다음 구현 순서

1. `seo_eval.py` 결과에 `signals` 섹션을 추가한다. **완료:** frontmatter/opening/headings/links/images raw evidence를 수집한다.
2. `h1_count`, `opening_summary`, `citations`를 hard required에서 advisory로 낮춘다.
3. `blockers`는 현재보다 강화한다: broken local image도 blocker에 포함한다. **완료:** `local_images_resolve` blocker가 추가됐다.
4. `render_signals.py`를 evaluator에 연결해 rendered-ish H1 신호를 리포트한다. **부분 완료:** signals에 rendered effective H1이 포함된다.
5. policy/rubric layer가 signals를 받아 `PASS/NEEDS_CHANGES/FAIL`을 판단하도록 분리한다.
