# 피드백 표현 비교 실제 실행 결과

**최신 예산 지시: 공식 OpenAI 직접 청구는 한도 제외. 비OpenAI는 총 $10 한도와 미정산 arm 차단 유지.**

상태: `completed`. 새 upstream 호출 8회, 완료 8회, 진행 중 0회입니다.

## 입력 모델과 대조군

요청 모델: `{"gpt-5-mini-2025-08-07": 8}`. 원본 입력·조건은 `execution-plan.json`과 이 폴더의 snapshot/manifest 또는 원본 참조에 고정했습니다. 비OpenAI arm은 다른 모델로 대체하지 않습니다.

## 실제 결과

```json
{
  "result": {
    "status": "completed",
    "cases": 1,
    "arms": [
      "F0",
      "F1",
      "F2",
      "F3"
    ],
    "accepted": 3,
    "native_direct_agree": true,
    "human_approved": 0,
    "scope": "fresh candidates on previously exposed natural input; no superiority claim from this sample"
  },
  "metrics": {
    "arms": {
      "F0": {
        "gate_decision": "reject",
        "reasons": [
          "no_change",
          "semantic_review_failed"
        ],
        "native_direct_equal": true,
        "replacement": "[dataset card](https://huggingface.co/datasets/aws-neuron/torch-neuronx-model-support)에서 각 결과의 정확한 의미를 확인할 수 있습니다."
      },
      "F1": {
        "gate_decision": "accept_candidate",
        "reasons": [],
        "native_direct_equal": true,
        "replacement": "[데이터셋 카드](https://huggingface.co/datasets/aws-neuron/torch-neuronx-model-support)에서 각 결과의 정확한 의미를 확인할 수 있습니다."
      },
      "F2": {
        "gate_decision": "accept_candidate",
        "reasons": [],
        "native_direct_equal": true,
        "replacement": "[데이터셋 카드](https://huggingface.co/datasets/aws-neuron/torch-neuronx-model-support)"
      },
      "F3": {
        "gate_decision": "accept_candidate",
        "reasons": [],
        "native_direct_equal": true,
        "replacement": "[데이터셋 카드](https://huggingface.co/datasets/aws-neuron/torch-neuronx-model-support)에서 각 결과의 정확한 의미를 확인할 수 있습니다."
      }
    },
    "adjudication_note": "F2 returned only the dataset-card link, omitting the sentence proposition about exact meanings of results. The primary same-model review and shared native/Python contract accepted it. This is a gate false-accept observation by Codex, not human gold and not a repaired result."
  },
  "failure": null
}
```

## 사용량과 비용

```json
{
  "actual_upstream_attempts": 8,
  "completed": 8,
  "inflight": 0,
  "errors": 0,
  "requested_models": {
    "gpt-5-mini-2025-08-07": 8
  },
  "resolved_models": {
    "gpt-5-mini-2025-08-07": 8
  },
  "usage_derived_estimate_usd_known_sum": 0.0060868499999999996,
  "unknown_estimate_attempts": 0,
  "provider_reported_cost_usd": null,
  "billing_confirmed_actual_usd": null,
  "billing_scope": "Official OpenAI direct; exempt from non-OpenAI $10 cap",
  "input_tokens": 21549,
  "output_tokens_including_reasoning": 1905,
  "cache_read_tokens": 13824,
  "cache_write_tokens": 0,
  "cache_write_30m_tokens": 0,
  "cache_write_12h_tokens": 0,
  "reasoning_tokens": 1216,
  "service_tiers": {
    "default": 8
  },
  "automatic_upstream_retries": 0,
  "summed_request_seconds": 22.618057914893143
}
```

사용량은 원본 응답에서 수집했습니다. 위 금액은 cache read/write와 reasoning 포함 output을 반영한 단가 기반 추정이며 청구서 확인값이 아닙니다. 서비스 tier나 긴 문맥 등 계산하지 않은 조건은 추정 미확인으로 남깁니다. SDK upstream 자동 재시도는 0이며, 명시적 프로토콜 재검증·실패·fallback은 각각 기록합니다. Data Designer의 로컬 프록시 재요청은 발생 시 각 전달 시도로 계측하고 전체 upstream 8회로 제한합니다.

## 해석과 한계

이전 historical/dev 입력을 다시 사용한 진단·회귀 실험입니다. 사람 정답 승인 수는 0이며, 별도 호출의 model judge도 같은 모델 계열 편향을 가질 수 있습니다. 일부 실험은 합성 오류·가상 업데이트를 포함합니다. 무료 회귀, 과거 결과, 이번 새 호출을 섞지 않습니다. 병렬 실험의 벽시계 시간은 통제된 지연 성능 비교가 아닙니다.

F2의 축약 링크만 남은 출력은 원문 명제 누락 사례입니다. 게이트 accept를 실제 의미 보존 성공으로 보지 않습니다. native와 Python이 같은 잘못된 판정을 공유하므로 Guardrails 프레임워크 자체의 품질 우위 근거가 아닙니다.

## 비교 관찰과 채택 판단

F0은 무피드백 재작성, F1은 구조화된 지적 제공, F2는 F1과 같은 지적에 설명 문단만 확장, F3은 F1에 추가 문맥을 포함하는 기존 피드백 표현 조건입니다(정확한 실제 prompt는 원시 요청에 보존). 4개 중 F0 무변경은 거부, F1/F2/F3은 승인됐고 native/직접 판정은 4/4 일치했습니다. 그러나 F2는 “각 결과의 정확한 의미를 설명한다”는 명제를 버리고 링크만 반환했습니다. 승인 3/4를 의미 보존 성공 3/4로 해석할 수 없습니다. 피드백 표현만으로 안전한 수정을 보장한다는 가정은 보류하고, 이 누락을 별도 회귀 입력으로 남깁니다.
