# 링크 보호 전처리 실제 실행 결과

**최신 예산 지시: 공식 OpenAI 직접 청구는 한도 제외. 비OpenAI는 총 $10 한도와 미정산 arm 차단 유지.**

상태: `completed`. 새 upstream 호출 48회, 완료 48회, 진행 중 0회입니다.

## 입력 모델과 대조군

요청 모델: `{"gpt-5-mini-2025-08-07": 48}`. 원본 입력·조건은 `execution-plan.json`과 이 폴더의 snapshot/manifest 또는 원본 참조에 고정했습니다. 비OpenAI arm은 다른 모델로 대체하지 않습니다.

## 실제 결과

```json
{
  "result": {
    "status": "completed",
    "paired_paragraphs": 24,
    "arms": {
      "whole": {
        "completed": 24,
        "invariant_ok": 24,
        "untranslated_labels": 28
      },
      "url": {
        "completed": 24,
        "invariant_ok": 24,
        "untranslated_labels": 1
      }
    },
    "control": "legacy 51d5f22 link-whole protector vs existing experimental URL-only protector; current production already uses label-visible protection",
    "scope": "fresh paragraph generation; deterministic label/structure metrics, not independent human review"
  },
  "metrics": {
    "whole": {
      "completed": 24,
      "invariant_ok": 24,
      "untranslated_labels": 28
    },
    "url": {
      "completed": 24,
      "invariant_ok": 24,
      "untranslated_labels": 1
    }
  },
  "failure": null
}
```

## 사용량과 비용

```json
{
  "actual_upstream_attempts": 48,
  "completed": 48,
  "inflight": 0,
  "errors": 0,
  "requested_models": {
    "gpt-5-mini-2025-08-07": 48
  },
  "resolved_models": {
    "gpt-5-mini-2025-08-07": 48
  },
  "usage_derived_estimate_usd_known_sum": 0.05675275,
  "unknown_estimate_attempts": 0,
  "provider_reported_cost_usd": null,
  "billing_confirmed_actual_usd": null,
  "billing_scope": "Official OpenAI direct; exempt from non-OpenAI $10 cap",
  "input_tokens": 8987,
  "output_tokens_including_reasoning": 27253,
  "cache_read_tokens": 0,
  "cache_write_tokens": 0,
  "cache_write_30m_tokens": 0,
  "cache_write_12h_tokens": 0,
  "reasoning_tokens": 20672,
  "service_tiers": {
    "default": 48
  },
  "automatic_upstream_retries": 0,
  "summed_request_seconds": 297.3701236268389
}
```

사용량은 원본 응답에서 수집했습니다. 위 금액은 cache read/write와 reasoning 포함 output을 반영한 단가 기반 추정이며 청구서 확인값이 아닙니다. 서비스 tier나 긴 문맥 등 계산하지 않은 조건은 추정 미확인으로 남깁니다. SDK upstream 자동 재시도는 0이며, 명시적 프로토콜 재검증·실패·fallback은 각각 기록합니다. Data Designer의 로컬 프록시 재요청은 발생 시 각 전달 시도로 계측하고 전체 upstream 8회로 제한합니다.

## 해석과 한계

이전 historical/dev 입력을 다시 사용한 진단·회귀 실험입니다. 사람 정답 승인 수는 0이며, 별도 호출의 model judge도 같은 모델 계열 편향을 가질 수 있습니다. 일부 실험은 합성 오류·가상 업데이트를 포함합니다. 무료 회귀, 과거 결과, 이번 새 호출을 섞지 않습니다. 병렬 실험의 벽시계 시간은 통제된 지연 성능 비교가 아닙니다.

## 비교 관찰과 채택 판단

과거 whole 보호와 url 보호로 같은 24문단을 각각 번역했습니다. 양쪽 모두 URL/코드 등 불변조건 24/24 유지, 잔여 영어 설명 라벨은 28→1입니다. 남은 1개도 성공으로 감추지 않았습니다. 별도 의미 판정은 하지 않았습니다. 현 운영에는 이미 라벨 노출 방식이 있으므로 새 NVIDIA 개선으로 채택하지 않고 전처리 회귀 근거로만 유지합니다.
