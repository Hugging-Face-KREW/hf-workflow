# Policy Config Implementation Result

작성 시점: 2026-06-29

## 무엇을 바꿨나

하드코딩된 SEO 판정을 줄이기 위해 checker와 policy를 분리했다.

- `skills/seo/config/default-policy.yml` 추가
- `skills/seo/tools/policy.py` 추가
- `seo_eval.py`에서 checker 결과에 policy severity를 적용하도록 변경
- `opening_summary`, raw markdown `h1_count`, `citations`는 기본 policy에서 `review`로 이동
- `body_not_empty`는 blocker로 추가
- `rubric.py`에서 token-overlap 같은 임시 semantic heuristic 제거
- manifest의 `handoff.seo.policy.severities`로 프로젝트별 severity override 가능
- `test_policy_config.py` 추가로 policy override가 코드 변경 없이 동작함을 검증

## 왜 이렇게 바꿨나

기존 구조는 `content.py` 내부에서 어떤 항목이 required인지 직접 결정했다. 이 방식은 빠르지만 다음 문제가 있다.

- 블로그 layout에 따라 달라지는 H1 구조를 raw markdown만 보고 차단한다.
- 글 유형에 따라 달라지는 citation 필요성을 일괄 required로 강제한다.
- 도입부 길이 같은 편집 규칙을 고정 숫자로 차단한다.
- 프로젝트별 정책 변경을 위해 checker 코드를 수정해야 한다.

변경 후 구조는 다음과 같다.

```text
checker: deterministic evidence 생성
policy config: severity 결정
rubric: 의미 판단용 schema-bound judge seam
report: gated/review/advisory를 분리해 표시
```

## 검증 결과

전체 테스트:

```bash
/tmp/hf-workflow-seo-test-venv/bin/python -m pytest skills/seo/tests
```

결과:

```text
78 passed
```

golden snapshot도 의도된 output 변경에 맞춰 재생성했다.

```bash
UPDATE_GOLDEN=1 /tmp/hf-workflow-seo-test-venv/bin/python -m pytest skills/seo/tests/test_golden_regression.py
```

결과:

```text
9 passed
```

## 시뮬레이션 결과

재생성 파일:

- `skills/seo/reports/skill-improvement-simulation.md`
- `skills/seo/reports/skill-improvement-simulation.json`
- `skills/seo/reports/internal-hfkrew-31-sample-audit.md`
- `skills/seo/reports/internal-hfkrew-31-sample-audit.json`

### 42개 fixture

```text
current: {'PASS': 34, 'FAIL': 2, 'BLOCKED': 3, 'NEEDS_CHANGES': 3}
blockers_only: {'PASS': 39, 'BLOCKED': 3}
```

기존보다 contextual 과차단은 줄었다. `h1_count`, `opening_summary`, `citations`를 기본 hard gate에서 내렸기 때문이다.

### 실제 HFKREW 31개 글

```text
current: {'PASS': 19, 'NEEDS_CHANGES': 8, 'FAIL': 4}
```

이전 audit의 주요 실패는 다음이었다.

```text
{'h1_count': 19, 'citations': 1, 'opening_summary': 7, 'descriptive_alt_text': 7, 'alt_text_coverage': 6, 'heading_hierarchy': 4}
```

변경 후 required failure는 다음으로 줄었다.

```text
{'descriptive_alt_text': 7, 'alt_text_coverage': 6, 'heading_hierarchy': 4}
```

즉 HFKREW layout/글 유형에 의존하던 H1, 도입부 길이, citation 과차단은 제거됐고, 남은 실패는 이미지 alt와 heading hierarchy처럼 더 명확한 구조 문제다.

## 남은 리스크

semantic negative는 여전히 deterministic gate를 통과한다.

예:

- `description_body_mismatch`
- `semantic-negative-description`
- `semantic-negative-title`
- `meaningless_alt`

이것을 token overlap, 특정 단어 목록, 한국어 조사 제거 같은 heuristic으로 막을 수는 있다. 하지만 이는 사용자가 요구한 "하드코딩 지양"과 맞지 않고, 실제 글에서 false positive를 만들 가능성이 높다.

따라서 이 문제는 다음 단계에서 처리해야 한다.

```text
schema-bound LLM policy judge
  입력: deterministic evidence packet + page_type + translation policy
  출력: JSON schema validated review result
  테스트: fixture stub judge + real sample simulation
```

## 현재 판단

이번 변경은 평가셋을 더 늘린 것이 아니라 skill 구조를 개선한 것이다.

좋아진 점:

- severity 정책이 checker 코드에서 분리됐다.
- 프로젝트별 policy override가 가능하다.
- HFKREW 실제 글의 과차단이 줄었다.
- empty body는 명확한 blocker로 승격됐다.
- semantic 판단을 임시 휴리스틱으로 오염시키지 않았다.

아직 남은 점:

- LLM policy judge는 아직 실제 연결되지 않았다.
- semantic metadata mismatch는 evidence로만 남고 자동 차단하지 않는다.
- full Jekyll render 기반 `<head>`/H1 검증은 아직 별도 단계다.

다음 구현 우선순위:

1. `rubric.py`에 OpenAI structured output 기반 judge 연결
2. fork PR/secret 없음 환경에서는 rubric unavailable로 graceful fallback
3. semantic negative fixture는 mock judge로 FAIL/NEEDS_CHANGES 회귀 테스트
4. metadata `build_plan()`은 policy 없이는 canonical/hreflang을 확정하지 않도록 구현
