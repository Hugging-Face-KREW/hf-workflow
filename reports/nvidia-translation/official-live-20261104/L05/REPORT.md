# 내장 Guardrails 및 직접 검사 실제 실행 결과

**최신 예산 지시: 공식 OpenAI 직접 청구는 한도 제외. 비OpenAI는 총 $10 한도와 미정산 arm 차단 유지.**

상태: `completed`. 새 upstream 호출 313회, 완료 313회, 진행 중 0회입니다.

## 입력 모델과 대조군

요청 모델: `{"gpt-5-mini-2025-08-07": 313}`. 원본 입력·조건은 `execution-plan.json`과 이 폴더의 snapshot/manifest 또는 원본 참조에 고정했습니다. 비OpenAI arm은 다른 모델로 대체하지 않습니다.

## 실제 결과

```json
{
  "result": {
    "status": "completed",
    "cases": 39,
    "arms": [
      "generic",
      "facts",
      "quality",
      "combined",
      "matched"
    ],
    "max_repairs": 1,
    "scope": "fresh native/direct judges; all input previously exposed diagnostic/regression, not human gold"
  },
  "metrics": {
    "decisions": 195,
    "arms": {
      "generic": {
        "n": 39,
        "false_pass_on_exposed_labels": 16,
        "false_block_on_exposed_labels": 0,
        "noncanonical_verdicts": 0
      },
      "facts": {
        "n": 39,
        "false_pass_on_exposed_labels": 19,
        "false_block_on_exposed_labels": 0,
        "noncanonical_verdicts": 0
      },
      "quality": {
        "n": 39,
        "false_pass_on_exposed_labels": 4,
        "false_block_on_exposed_labels": 0,
        "noncanonical_verdicts": 0
      },
      "combined": {
        "n": 39,
        "false_pass_on_exposed_labels": 8,
        "false_block_on_exposed_labels": 0,
        "noncanonical_verdicts": 0
      },
      "matched": {
        "n": 39,
        "false_pass_on_exposed_labels": 6,
        "false_block_on_exposed_labels": 0,
        "noncanonical_verdicts": 0
      }
    },
    "by_exposed_split": {
      "new_synthetic_diagnostic": {
        "generic": {
          "n": 16,
          "false_pass": 3,
          "false_block": 0
        },
        "facts": {
          "n": 16,
          "false_pass": 4,
          "false_block": 0
        },
        "quality": {
          "n": 16,
          "false_pass": 0,
          "false_block": 0
        },
        "combined": {
          "n": 16,
          "false_pass": 1,
          "false_block": 0
        },
        "matched": {
          "n": 16,
          "false_pass": 1,
          "false_block": 0
        }
      },
      "seen_regression": {
        "generic": {
          "n": 23,
          "false_pass": 13,
          "false_block": 0
        },
        "facts": {
          "n": 23,
          "false_pass": 15,
          "false_block": 0
        },
        "quality": {
          "n": 23,
          "false_pass": 4,
          "false_block": 0
        },
        "combined": {
          "n": 23,
          "false_pass": 7,
          "false_block": 0
        },
        "matched": {
          "n": 23,
          "false_pass": 5,
          "false_block": 0
        }
      }
    },
    "split_note": "new_synthetic_diagnostic is a historical split name: reused diagnostic, not fresh held-out data",
    "repair_pipeline_rows": 48,
    "approved_invariant_failure": 5
  },
  "failure": null
}
```

## 사용량과 비용

```json
{
  "actual_upstream_attempts": 313,
  "completed": 313,
  "inflight": 0,
  "errors": 0,
  "requested_models": {
    "gpt-5-mini-2025-08-07": 313
  },
  "resolved_models": {
    "gpt-5-mini-2025-08-07": 313
  },
  "usage_derived_estimate_usd_known_sum": 0.14515075,
  "unknown_estimate_attempts": 0,
  "provider_reported_cost_usd": null,
  "billing_confirmed_actual_usd": null,
  "billing_scope": "Official OpenAI direct; exempt from non-OpenAI $10 cap",
  "input_tokens": 115187,
  "output_tokens_including_reasoning": 58177,
  "cache_read_tokens": 0,
  "cache_write_tokens": 0,
  "cache_write_30m_tokens": 0,
  "cache_write_12h_tokens": 0,
  "reasoning_tokens": 45760,
  "service_tiers": {
    "default": 313
  },
  "automatic_upstream_retries": 0,
  "summed_request_seconds": 804.4172290895949
}
```

사용량은 원본 응답에서 수집했습니다. 위 금액은 cache read/write와 reasoning 포함 output을 반영한 단가 기반 추정이며 청구서 확인값이 아닙니다. 서비스 tier나 긴 문맥 등 계산하지 않은 조건은 추정 미확인으로 남깁니다. SDK upstream 자동 재시도는 0이며, 명시적 프로토콜 재검증·실패·fallback은 각각 기록합니다. Data Designer의 로컬 프록시 재요청은 발생 시 각 전달 시도로 계측하고 전체 upstream 8회로 제한합니다.

## 해석과 한계

이전 historical/dev 입력을 다시 사용한 진단·회귀 실험입니다. 사람 정답 승인 수는 0이며, 별도 호출의 model judge도 같은 모델 계열 편향을 가질 수 있습니다. 일부 실험은 합성 오류·가상 업데이트를 포함합니다. 무료 회귀, 과거 결과, 이번 새 호출을 섞지 않습니다. 병렬 실험의 벽시계 시간은 통제된 지연 성능 비교가 아닙니다.

## 비교 관찰과 채택 판단

generic은 일반 직접 검사, facts는 NeMo 내장 self_check_facts, quality는 번역용 프롬프트를 쓴 내장 self_check_output, combined는 facts→quality, matched는 combined와 같은 프롬프트를 직접 실행합니다. 모델 호출이 독립적이므로 native/direct 간 차이를 프레임워크 효과로 단정할 수 없습니다.

| 조건 | 39개 노출 정답상 false pass | false block |
|---|---:|---:|
| generic | 16 | 0 |
| facts | 19 | 0 |
| quality | 4 | 0 |
| combined | 8 | 0 |
| matched | 6 | 0 |

최종 판정 195개(39×5), 비표준 verdict 0개입니다. 재사용 합성 16개/회귀 23개의 분리 집계는 아래 JSON에 있습니다. 제한 수정 pipeline 48개 중 **승인되었지만 불변조건을 위반한 결과가 5개**입니다. 일반 사실성 검사만으로 번역 누락·라벨 현지화를 다루기 어렵습니다. quality 프롬프트는 후속 후보지만, gate 승인과 독립 구조검사를 결합하기 전 자동 반영은 보류합니다. 사람 정답이 아닌 개발용 라벨 기준입니다.
