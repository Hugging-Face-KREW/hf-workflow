# 전처리와 제한 수정 루프 실제 실행 결과

**최신 예산 지시: 공식 OpenAI 직접 청구는 한도 제외. 비OpenAI는 총 $10 한도와 미정산 arm 차단 유지.**

상태: `completed`. 새 upstream 호출 154회, 완료 154회, 진행 중 0회입니다.

## 입력 모델과 대조군

요청 모델: `{"gpt-5-mini-2025-08-07": 154}`. 원본 입력·조건은 `execution-plan.json`과 이 폴더의 snapshot/manifest 또는 원본 참조에 고정했습니다. 비OpenAI arm은 다른 모델로 대체하지 않습니다.

## 실제 결과

```json
{
  "result": {
    "status": "completed",
    "generation_cases": 12,
    "generation_arms": 4,
    "max_repairs": 2,
    "ecl_control": "51d5f22 original link-whole protector, deliberate legacy contrast; not current production default",
    "scope": "fresh model calls; v2 reuses valid first assessments from this new run, not old historical calls"
  },
  "metrics": {
    "translation_arms": {
      "url_generic": {
        "n": 12,
        "restore_failure": 0,
        "mechanical_clean": 10,
        "remaining_descriptive_labels": 3
      },
      "url_policy": {
        "n": 12,
        "restore_failure": 0,
        "mechanical_clean": 8,
        "remaining_descriptive_labels": 0
      },
      "whole_generic": {
        "n": 12,
        "restore_failure": 0,
        "mechanical_clean": 9,
        "remaining_descriptive_labels": 13
      },
      "whole_policy": {
        "n": 12,
        "restore_failure": 0,
        "mechanical_clean": 10,
        "remaining_descriptive_labels": 13
      }
    },
    "validation_loops": 23,
    "repairs": 21,
    "final_decisions": {
      "repair": 6,
      "pass_candidate": 17
    }
  },
  "failure": null
}
```

## 사용량과 비용

```json
{
  "actual_upstream_attempts": 154,
  "completed": 154,
  "inflight": 0,
  "errors": 0,
  "requested_models": {
    "gpt-5-mini-2025-08-07": 154
  },
  "resolved_models": {
    "gpt-5-mini-2025-08-07": 154
  },
  "usage_derived_estimate_usd_known_sum": 0.19506575,
  "unknown_estimate_attempts": 0,
  "provider_reported_cost_usd": null,
  "billing_confirmed_actual_usd": null,
  "billing_scope": "Official OpenAI direct; exempt from non-OpenAI $10 cap",
  "input_tokens": 91079,
  "output_tokens_including_reasoning": 86148,
  "cache_read_tokens": 0,
  "cache_write_tokens": 0,
  "cache_write_30m_tokens": 0,
  "cache_write_12h_tokens": 0,
  "reasoning_tokens": 51520,
  "service_tiers": {
    "default": 154
  },
  "automatic_upstream_retries": 0,
  "summed_request_seconds": 928.2007677548099
}
```

사용량은 원본 응답에서 수집했습니다. 위 금액은 cache read/write와 reasoning 포함 output을 반영한 단가 기반 추정이며 청구서 확인값이 아닙니다. 서비스 tier나 긴 문맥 등 계산하지 않은 조건은 추정 미확인으로 남깁니다. SDK upstream 자동 재시도는 0이며, 명시적 프로토콜 재검증·실패·fallback은 각각 기록합니다. Data Designer의 로컬 프록시 재요청은 발생 시 각 전달 시도로 계측하고 전체 upstream 8회로 제한합니다.

## 해석과 한계

이전 historical/dev 입력을 다시 사용한 진단·회귀 실험입니다. 사람 정답 승인 수는 0이며, 별도 호출의 model judge도 같은 모델 계열 편향을 가질 수 있습니다. 일부 실험은 합성 오류·가상 업데이트를 포함합니다. 무료 회귀, 과거 결과, 이번 새 호출을 섞지 않습니다. 병렬 실험의 벽시계 시간은 통제된 지연 성능 비교가 아닙니다.

## 비교 관찰과 채택 판단

whole은 과거 링크 전체 숨김, url은 URL만 숨김입니다. generic은 일반 프롬프트, policy는 검토된 용어 정책을 추가합니다.

| 조건 | 생성 수 | 복원 실패 | 기계 검사 무결점 | 잔여 설명 라벨 |
|---|---:|---:|---:|---:|
| url_generic | 12 | 0 | 10 | 3 |
| url_policy | 12 | 0 | 8 | 0 |
| whole_generic | 12 | 0 | 9 | 13 |
| whole_policy | 12 | 0 | 10 | 13 |

별도 오류 seed의 제한 수정 루프는 23개, 수정 시도 21회, 마지막 pass_candidate 17개/repair 잔류 6개였습니다. 이 seed 평가는 위 48개 생성물의 종단 평가가 아닙니다. URL 노출은 라벨 현지화에 도움이 됐지만 기계 검사 결과도 함께 보아야 합니다. 현재 운영에 이미 반영된 방향이며 NVIDIA 고유 효과로 채택하지 않습니다. 실패 시 승인 중단과 제한 루프만 후속 회귀 조건으로 유지합니다.
