# 용어 정책 및 편집 범위 실제 실행 결과

**최신 예산 지시: 공식 OpenAI 직접 청구는 한도 제외. 비OpenAI는 총 $10 한도와 미정산 arm 차단 유지.**

상태: `completed`. 새 upstream 호출 112회, 완료 112회, 진행 중 0회입니다.

## 입력 모델과 대조군

요청 모델: `{"gpt-5-mini-2025-08-07": 112}`. 원본 입력·조건은 `execution-plan.json`과 이 폴더의 snapshot/manifest 또는 원본 참조에 고정했습니다. 비OpenAI arm은 다른 모델로 대체하지 않습니다.

## 실제 결과

```json
{
  "result": {
    "status": "completed",
    "cases": 16,
    "arms": [
      "A",
      "B",
      "C"
    ],
    "scope": "fresh generation/detection/judge; same previously exposed input; model-only review"
  },
  "metrics": {
    "rows": 48,
    "A": {
      "n": 16,
      "decisions": {
        "model_pass_candidate": 14,
        "reject": 1,
        "needs_review": 1
      },
      "native_direct_agreement": 16,
      "remaining_english_labels": 2,
      "missing_curated_terms": 2,
      "model_meaning_preserved": 16,
      "model_localization_complete": 15,
      "model_unnecessary_change": 2
    },
    "B": {
      "n": 16,
      "decisions": {
        "needs_review": 2,
        "reject": 1,
        "model_pass_candidate": 13
      },
      "native_direct_agreement": 16,
      "remaining_english_labels": 2,
      "missing_curated_terms": 2,
      "model_meaning_preserved": 15,
      "model_localization_complete": 14,
      "model_unnecessary_change": 3
    },
    "C": {
      "n": 16,
      "decisions": {
        "model_pass_candidate": 15,
        "needs_review": 1
      },
      "native_direct_agreement": 16,
      "remaining_english_labels": 1,
      "missing_curated_terms": 1,
      "model_meaning_preserved": 16,
      "model_localization_complete": 15,
      "model_unnecessary_change": 1
    }
  },
  "failure": null
}
```

## 사용량과 비용

```json
{
  "actual_upstream_attempts": 112,
  "completed": 112,
  "inflight": 0,
  "errors": 0,
  "requested_models": {
    "gpt-5-mini-2025-08-07": 112
  },
  "resolved_models": {
    "gpt-5-mini-2025-08-07": 112
  },
  "usage_derived_estimate_usd_known_sum": 0.11392125,
  "unknown_estimate_attempts": 0,
  "provider_reported_cost_usd": null,
  "billing_confirmed_actual_usd": null,
  "billing_scope": "Official OpenAI direct; exempt from non-OpenAI $10 cap",
  "input_tokens": 65077,
  "output_tokens_including_reasoning": 48826,
  "cache_read_tokens": 0,
  "cache_write_tokens": 0,
  "cache_write_30m_tokens": 0,
  "cache_write_12h_tokens": 0,
  "reasoning_tokens": 29376,
  "service_tiers": {
    "default": 112
  },
  "automatic_upstream_retries": 0,
  "summed_request_seconds": 523.047329166031
}
```

사용량은 원본 응답에서 수집했습니다. 위 금액은 cache read/write와 reasoning 포함 output을 반영한 단가 기반 추정이며 청구서 확인값이 아닙니다. 서비스 tier나 긴 문맥 등 계산하지 않은 조건은 추정 미확인으로 남깁니다. SDK upstream 자동 재시도는 0이며, 명시적 프로토콜 재검증·실패·fallback은 각각 기록합니다. Data Designer의 로컬 프록시 재요청은 발생 시 각 전달 시도로 계측하고 전체 upstream 8회로 제한합니다.

## 해석과 한계

이전 historical/dev 입력을 다시 사용한 진단·회귀 실험입니다. 사람 정답 승인 수는 0이며, 별도 호출의 model judge도 같은 모델 계열 편향을 가질 수 있습니다. 일부 실험은 합성 오류·가상 업데이트를 포함합니다. 무료 회귀, 과거 결과, 이번 새 호출을 섞지 않습니다. 병렬 실험의 벽시계 시간은 통제된 지연 성능 비교가 아닙니다.

## 비교 관찰과 채택 판단

A는 용어 정책만, B는 탐지 피드백+문맥, C는 JSON target_id와 읽기 전용 문맥으로 편집 범위를 제한합니다.

| 조건 | 후보/변경 | 게이트 통과/거부/검토 | 잔여 영어 라벨/누락 지정 용어 | 모델 의미보존/완전현지화/불필요변경 |
|---|---:|---:|---:|---:|
| A | 16/13 | 14/1/1 | 2/2 | 16/15/2 |
| B | 16/10 | 13/1/2 | 2/2 | 15/14/3 |
| C | 16/13 | 15/0/1 | 1/1 | 16/15/1 |

native/직접 계약 판정은 48/48 일치했습니다. 예를 들어 B는 previous post를 그대로 남긴 무변경 후보를 검토로 보냈습니다. C의 통과 수가 가장 많지만 같은 개발 입력과 모델 판정으로 얻은 진단값입니다. 편집 경계 계약은 후속 실험 후보로 유지하되 운영 자동 승인과 통계적 우월 판단은 보류합니다.
