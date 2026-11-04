# 로컬 전체 파이프라인 실제 실행 결과

**최신 예산 지시: 공식 OpenAI 직접 청구는 한도 제외. 비OpenAI는 총 $10 한도와 미정산 arm 차단 유지.**

상태: `local_pipeline_completed`. 새 upstream 호출 54회, 완료 54회, 진행 중 0회입니다.

## 입력 모델과 대조군

요청 모델: `{"gpt-5.6-luna": 49, "gpt-5-nano": 5}`. 원본 입력·조건은 `execution-plan.json`과 이 폴더의 snapshot/manifest 또는 원본 참조에 고정했습니다. 비OpenAI arm은 다른 모델로 대체하지 않습니다.

## 실제 결과

```json
{
  "result": {
    "status": "local_pipeline_completed",
    "initial": {
      "sha": "2d94e12189ace978bf253e3c9fe2b544dcdb938a",
      "semantic_complete": true,
      "quality_status": "review_required",
      "quality_score": 81.0,
      "segments_requested": 22,
      "segments_evaluated": 22,
      "verifier_passed": true,
      "reason": "Verified exact local SHA/source/target",
      "seo_exit": 0,
      "mqm_attempts": 1,
      "prompt_source": "existing unmerged PR35, commit 973b75b6952a456a0f7944239b8bc657f1892f52; prompt only reused",
      "review_source": "frozen snapshot, no source fetch"
    },
    "feedback_disposition": "actionable",
    "after_feedback": {
      "sha": "a3d20c5db40d934dfe7946eda6a4966221a65be5",
      "semantic_complete": true,
      "quality_status": "review_required",
      "quality_score": 81.0,
      "segments_requested": 22,
      "segments_evaluated": 22,
      "verifier_passed": true,
      "reason": "Verified exact local SHA/source/target",
      "seo_exit": 0,
      "mqm_attempts": 1,
      "prompt_source": "existing unmerged PR35, commit 973b75b6952a456a0f7944239b8bc657f1892f52; prompt only reused",
      "review_source": "frozen snapshot, no source fetch"
    },
    "remote_pr_mutated": false,
    "remote_loop_restarted": false,
    "body_quality_repair_claim": false
  },
  "metrics": {},
  "failure": null
}
```

## 사용량과 비용

```json
{
  "actual_upstream_attempts": 54,
  "completed": 54,
  "inflight": 0,
  "errors": 0,
  "requested_models": {
    "gpt-5.6-luna": 49,
    "gpt-5-nano": 5
  },
  "resolved_models": {
    "gpt-5.6-luna": 49,
    "gpt-5-nano-2025-08-07": 5
  },
  "usage_derived_estimate_usd_known_sum": 0.04525666,
  "unknown_estimate_attempts": 0,
  "provider_reported_cost_usd": null,
  "billing_confirmed_actual_usd": null,
  "billing_scope": "Official OpenAI direct; exempt from non-OpenAI $10 cap",
  "input_tokens": 540841,
  "output_tokens_including_reasoning": 15062,
  "cache_read_tokens": 454548,
  "cache_write_tokens": 83105,
  "cache_write_30m_tokens": 83105,
  "cache_write_12h_tokens": 0,
  "reasoning_tokens": 1199,
  "service_tiers": {
    "default": 54
  },
  "automatic_upstream_retries": 0,
  "summed_request_seconds": 195.15593049791642
}
```

사용량은 원본 응답에서 수집했습니다. 위 금액은 cache read/write와 reasoning 포함 output을 반영한 단가 기반 추정이며 청구서 확인값이 아닙니다. 서비스 tier나 긴 문맥 등 계산하지 않은 조건은 추정 미확인으로 남깁니다. SDK upstream 자동 재시도는 0이며, 명시적 프로토콜 재검증·실패·fallback은 각각 기록합니다. Data Designer의 로컬 프록시 재요청은 발생 시 각 전달 시도로 계측하고 전체 upstream 8회로 제한합니다.

## 해석과 한계

이전 historical/dev 입력을 다시 사용한 진단·회귀 실험입니다. 사람 정답 승인 수는 0이며, 별도 호출의 model judge도 같은 모델 계열 편향을 가질 수 있습니다. 일부 실험은 합성 오류·가상 업데이트를 포함합니다. 무료 회귀, 과거 결과, 이번 새 호출을 섞지 않습니다. 병렬 실험의 벽시계 시간은 통제된 지연 성능 비교가 아닙니다.

초기 구버전은 21/22에서 안전하게 멈췄고, 조건부 schema와 캐시 namespace 분리 후 최초/피드백 후 모두 22/22·verifier 통과했습니다. 두 상태는 review_required 81점입니다. 제어된 H1 편집 처리 성공이며, 본문 품질 오류 자동 해결 또는 원격 PR의 인증/이벤트/수정 루프 성공은 아닙니다. #256은 계속 paused입니다.

## 비교 관찰과 채택 판단

기존 PR 이벤트 대신 로컬 git 대상에 초벌 번역·품질 평가·명시적 H1 편집·재평가를 연결했습니다. 구버전 protocol은 21/22에서 중단됐으며, PR #35 강화 prompt와 조건부 schema를 적용하고 별도 캐시 namespace에서 같은 번역을 재검증했습니다. 수정 후 최초/피드백 후 모두 22/22, verifier/SEO 통과, review_required 81점입니다. 자동 승인도 본문 오류 해결도 아닙니다. 로컬 실행 경로는 후속 smoke 기반으로 유지하고 원격 루프 검증은 #60/#257 반영 전 보류합니다.
