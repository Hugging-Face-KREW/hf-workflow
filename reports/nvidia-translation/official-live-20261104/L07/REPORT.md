# Data Designer와 계획 B 실제 실행 결과

**최신 예산 지시: 공식 OpenAI 직접 청구는 한도 제외. 비OpenAI는 총 $10 한도와 미정산 arm 차단 유지.**

상태: `data_generation_completed_translation_contrast_blocked`. 새 upstream 호출 9회, 완료 9회, 진행 중 0회입니다.

## 입력 모델과 대조군

요청 모델: `{"gpt-5.6-luna": 9}`. 원본 입력·조건은 `execution-plan.json`과 이 폴더의 snapshot/manifest 또는 원본 참조에 고정했습니다. 비OpenAI arm은 다른 모델로 대체하지 않습니다.

## 실제 결과

```json
{
  "result": {
    "status": "data_generation_completed_translation_contrast_blocked",
    "dd_rows": 8,
    "dd_usable": 6,
    "translation_model_unchanged": "qwen/qwen3.7-flash"
  },
  "metrics": {},
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
  "usage_derived_estimate_usd_known_sum": 0.00487495,
  "unknown_estimate_attempts": 0,
  "provider_reported_cost_usd": null,
  "billing_confirmed_actual_usd": null,
  "billing_scope": "Official OpenAI direct; exempt from non-OpenAI $10 cap",
  "input_tokens": 2814,
  "output_tokens_including_reasoning": 3525,
  "cache_read_tokens": 0,
  "cache_write_tokens": 1643,
  "cache_write_30m_tokens": 1643,
  "cache_write_12h_tokens": 0,
  "reasoning_tokens": 1660,
  "service_tiers": {
    "default": 9
  },
  "automatic_upstream_retries": 0,
  "summed_request_seconds": 41.5778383340803
}
```

사용량은 원본 응답에서 수집했습니다. 위 금액은 cache read/write와 reasoning 포함 output을 반영한 단가 기반 추정이며 청구서 확인값이 아닙니다. 서비스 tier나 긴 문맥 등 계산하지 않은 조건은 추정 미확인으로 남깁니다. SDK upstream 자동 재시도는 0이며, 명시적 프로토콜 재검증·실패·fallback은 각각 기록합니다. Data Designer의 로컬 프록시 재요청은 발생 시 각 전달 시도로 계측하고 전체 upstream 8회로 제한합니다.

## 해석과 한계

이전 historical/dev 입력을 다시 사용한 진단·회귀 실험입니다. 사람 정답 승인 수는 0이며, 별도 호출의 model judge도 같은 모델 계열 편향을 가질 수 있습니다. 일부 실험은 합성 오류·가상 업데이트를 포함합니다. 무료 회귀, 과거 결과, 이번 새 호출을 섞지 않습니다. 병렬 실험의 벽시계 시간은 통제된 지연 성능 비교가 아닙니다.

## 비교 관찰과 채택 판단

NeMo Data Designer로 실제 8행을 생성하고 별도 Luna 검토에서 6행 사용 가능 판정을 받았습니다. 나머지 2행은 검토 불통과로 보존했습니다. 계획 B는 이 예시 유무/선정 방식에 따른 번역 대조 실험이지만 기존 Qwen 모델을 바꾸지 않아 3개 arm 전부 미실행입니다. 데이터 생성 기능의 실행은 확인했고, 예시가 번역 품질을 높이는지는 보류합니다. 모델 검토 6/8을 사람 검수나 최종 번역 성공으로 세지 않습니다.
