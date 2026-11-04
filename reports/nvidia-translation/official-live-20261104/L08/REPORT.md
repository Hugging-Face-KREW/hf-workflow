> 후속 실행 완료: 이 문서는 이전 OpenAI 단계의 기록입니다. [L08 Qwen 실제 실행·평가 결과](../../openrouter-token5-live-20261104/L08/REPORT.md).

# 부분 수정 라우팅 C 실제 실행 결과

**최신 예산 지시: 공식 OpenAI 직접 청구는 한도 제외. 비OpenAI는 총 $10 한도와 미정산 arm 차단 유지.**

상태: `completed_with_non_openai_blocked_arms`. 새 upstream 호출 12회, 완료 12회, 진행 중 0회입니다.

## 입력 모델과 대조군

요청 모델: `{"gpt-5.6-luna": 12}`. 원본 입력·조건은 `execution-plan.json`과 이 폴더의 snapshot/manifest 또는 원본 참조에 고정했습니다. 비OpenAI arm은 다른 모델로 대체하지 않습니다.

## 실제 결과

```json
{
  "result": {
    "status": "completed_with_non_openai_blocked_arms",
    "output_files": 10,
    "blocked_non_openai": 5,
    "failed": 5,
    "coverage_failures": [],
    "model_substitution": false,
    "scope": "fresh correction/update requests; existing diagnostic inputs, same-family model review"
  },
  "metrics": {
    "model_reviews": 10,
    "usable": 10,
    "reviews_by_group": {
      "C-luna-pr238_intro": {
        "n": 1,
        "model_usable": 1,
        "major_errors": 0
      },
      "C-luna-pr238_reasoning": {
        "n": 1,
        "model_usable": 1,
        "major_errors": 0
      },
      "C-luna-pr238_thanks": {
        "n": 1,
        "model_usable": 1,
        "major_errors": 0
      },
      "C-luna-pr239_linear": {
        "n": 1,
        "model_usable": 1,
        "major_errors": 0
      },
      "C-luna-pr239_requirements": {
        "n": 1,
        "model_usable": 1,
        "major_errors": 0
      },
      "C-original": {
        "n": 5,
        "model_usable": 5,
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
  "actual_upstream_attempts": 12,
  "completed": 12,
  "inflight": 0,
  "errors": 0,
  "requested_models": {
    "gpt-5.6-luna": 12
  },
  "resolved_models": {
    "gpt-5.6-luna": 12
  },
  "usage_derived_estimate_usd_known_sum": 0.0065880999999999995,
  "unknown_estimate_attempts": 0,
  "provider_reported_cost_usd": null,
  "billing_confirmed_actual_usd": null,
  "billing_scope": "Official OpenAI direct; exempt from non-OpenAI $10 cap",
  "input_tokens": 12061,
  "output_tokens_including_reasoning": 3047,
  "cache_read_tokens": 0,
  "cache_write_tokens": 10390,
  "cache_write_30m_tokens": 10390,
  "cache_write_12h_tokens": 0,
  "reasoning_tokens": 1190,
  "service_tiers": {
    "default": 12
  },
  "automatic_upstream_retries": 0,
  "summed_request_seconds": 39.49219391704537
}
```

사용량은 원본 응답에서 수집했습니다. 위 금액은 cache read/write와 reasoning 포함 output을 반영한 단가 기반 추정이며 청구서 확인값이 아닙니다. 서비스 tier나 긴 문맥 등 계산하지 않은 조건은 추정 미확인으로 남깁니다. SDK upstream 자동 재시도는 0이며, 명시적 프로토콜 재검증·실패·fallback은 각각 기록합니다. Data Designer의 로컬 프록시 재요청은 발생 시 각 전달 시도로 계측하고 전체 upstream 8회로 제한합니다.

## 해석과 한계

이전 historical/dev 입력을 다시 사용한 진단·회귀 실험입니다. 사람 정답 승인 수는 0이며, 별도 호출의 model judge도 같은 모델 계열 편향을 가질 수 있습니다. 일부 실험은 합성 오류·가상 업데이트를 포함합니다. 무료 회귀, 과거 결과, 이번 새 호출을 섞지 않습니다. 병렬 실험의 벽시계 시간은 통제된 지연 성능 비교가 아닙니다.

## 비교 관찰과 채택 판단

C는 5개 지적 대상 문단의 부분 수정입니다. 고정 Luna 5개는 완료했고 네이티브 라우터가 고른 Qwen 5개는 비용 미정산으로 차단했습니다. failed=5는 이 차단과 동일하며 별도 파싱 오류가 아닙니다. coverage 누락/중복은 0개입니다. 모델 검토상 수정 5/5와 원본 대조 5/5가 모두 사용 가능하므로 이 작은 표본에서 품질 상승은 입증되지 않았습니다. 실제 부분 수정 연결만 확인했고 라우팅 채택은 보류합니다.
