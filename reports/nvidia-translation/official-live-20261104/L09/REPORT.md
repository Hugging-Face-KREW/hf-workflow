# 증분 갱신 D 실제 실행 결과

**최신 예산 지시: 공식 OpenAI 직접 청구는 한도 제외. 비OpenAI는 총 $10 한도와 미정산 arm 차단 유지.**

상태: `completed_with_non_openai_blocked_arms`. 새 upstream 호출 9회, 완료 9회, 진행 중 0회입니다.

## 입력 모델과 대조군

요청 모델: `{"gpt-5.6-luna": 9}`. 원본 입력·조건은 `execution-plan.json`과 이 폴더의 snapshot/manifest 또는 원본 참조에 고정했습니다. 비OpenAI arm은 다른 모델로 대체하지 않습니다.

## 실제 결과

```json
{
  "result": {
    "status": "completed_with_non_openai_blocked_arms",
    "output_files": 6,
    "blocked_non_openai": 2,
    "failed": 2,
    "coverage_failures": [],
    "model_substitution": false,
    "scope": "fresh correction/update requests; existing diagnostic inputs, same-family model review"
  },
  "metrics": {
    "model_reviews": 17,
    "usable": 17,
    "reviews_by_group": {
      "C-original": {
        "n": 5,
        "model_usable": 5,
        "major_errors": 0
      },
      "D-condition-full_luna": {
        "n": 3,
        "model_usable": 3,
        "major_errors": 0
      },
      "D-condition-partial_luna": {
        "n": 3,
        "model_usable": 3,
        "major_errors": 0
      },
      "D-platform-full_luna": {
        "n": 3,
        "model_usable": 3,
        "major_errors": 0
      },
      "D-platform-partial_luna": {
        "n": 3,
        "model_usable": 3,
        "major_errors": 0
      }
    }
  },
  "failure": null
}
```

## 사용량과 비용

```json
{
  "actual_upstream_attempts": 9,
  "completed": 9,
  "inflight": 0,
  "errors": 0,
  "requested_models": {
    "gpt-5.6-luna": 9
  },
  "resolved_models": {
    "gpt-5.6-luna": 9
  },
  "usage_derived_estimate_usd_known_sum": 0.0061208,
  "unknown_estimate_attempts": 0,
  "provider_reported_cost_usd": null,
  "billing_confirmed_actual_usd": null,
  "billing_scope": "Official OpenAI direct; exempt from non-OpenAI $10 cap",
  "input_tokens": 8674,
  "output_tokens_including_reasoning": 3360,
  "cache_read_tokens": 0,
  "cache_write_tokens": 7080,
  "cache_write_30m_tokens": 7080,
  "cache_write_12h_tokens": 0,
  "reasoning_tokens": 1278,
  "service_tiers": {
    "default": 9
  },
  "automatic_upstream_retries": 0,
  "summed_request_seconds": 43.22295354108792
}
```

사용량은 원본 응답에서 수집했습니다. 위 금액은 cache read/write와 reasoning 포함 output을 반영한 단가 기반 추정이며 청구서 확인값이 아닙니다. 서비스 tier나 긴 문맥 등 계산하지 않은 조건은 추정 미확인으로 남깁니다. SDK upstream 자동 재시도는 0이며, 명시적 프로토콜 재검증·실패·fallback은 각각 기록합니다. Data Designer의 로컬 프록시 재요청은 발생 시 각 전달 시도로 계측하고 전체 upstream 8회로 제한합니다.

## 해석과 한계

이전 historical/dev 입력을 다시 사용한 진단·회귀 실험입니다. 사람 정답 승인 수는 0이며, 별도 호출의 model judge도 같은 모델 계열 편향을 가질 수 있습니다. 일부 실험은 합성 오류·가상 업데이트를 포함합니다. 무료 회귀, 과거 결과, 이번 새 호출을 섞지 않습니다. 병렬 실험의 벽시계 시간은 통제된 지연 성능 비교가 아닙니다.

## 비교 관찰과 채택 판단

D는 조건 변경/플랫폼 변경의 두 가상 원문 갱신을 전체 재번역(full_luna)과 변경 부분 번역 후 재조립(partial_luna)으로 비교합니다. 2×2=4개 조건은 완료, Switchyard가 고른 Qwen 2개는 차단했습니다. 각 완성 문서의 3문단, 총 12개가 모델 검토에서 사용 가능했으며 별도 C 원본 5개 대조도 동일 판정입니다. coverage 누락/중복 0개입니다. 재조립 경로는 실행됐지만 가상 변경 2건으로 의미 보존이나 비용 우위를 일반화하지 않습니다. 실제 업데이트 회귀 자료를 늘리기 전 운영 채택은 보류합니다.
