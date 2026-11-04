> 후속 실행 완료: 이 문서는 이전 OpenAI 단계의 기록입니다. [L06 Qwen 실제 실행·평가 결과](../../openrouter-token5-live-20261104/L06/REPORT.md).

# 문서 번역 모델 라우팅 실제 실행 결과

**최신 예산 지시: 공식 OpenAI 직접 청구는 한도 제외. 비OpenAI는 총 $10 한도와 미정산 arm 차단 유지.**

상태: `partial_non_openai_arms_blocked`. 새 upstream 호출 18회, 완료 18회, 진행 중 0회입니다.

## 입력 모델과 대조군

요청 모델: `{"gpt-5.6-luna": 18}`. 원본 입력·조건은 `execution-plan.json`과 이 폴더의 snapshot/manifest 또는 원본 참조에 고정했습니다. 비OpenAI arm은 다른 모델로 대체하지 않습니다.

## 실제 결과

```json
{
  "result": {
    "status": "partial_non_openai_arms_blocked",
    "documents": 4,
    "completed": 10,
    "blocked": 6,
    "candidate_model": "qwen/qwen3.7-flash",
    "no_substitution": true
  },
  "metrics": {
    "by_arm": {
      "luna": {
        "status": {
          "completed": 4
        },
        "selected": {
          "luna": 4
        }
      },
      "cheap": {
        "status": {
          "blocked_non_openai_budget_unreconciled": 4
        },
        "selected": {
          "cheap": 4
        }
      },
      "rule": {
        "status": {
          "completed": 4
        },
        "selected": {
          "luna": 4
        }
      },
      "switchyard": {
        "status": {
          "completed": 2,
          "blocked_non_openai_budget_unreconciled": 2
        },
        "selected": {
          "luna": 2,
          "cheap": 2
        }
      }
    },
    "model_reviews_by_document": {
      "pr252-quality": {
        "review": {
          "reviews": [
            {
              "id": "0",
              "usable": true,
              "major_errors": 0,
              "minor_errors": 2,
              "issues": [
                "DSA 인덱서의 괄호 설명이 원문의 의미를 어색하게 옮겼습니다(“a direction in other models”를 “한 방향”으로 번역).",
                "“Llama.cpp과” 등 일부 조사·띄어쓰기와 표현이 다소 어색합니다."
              ]
            },
            {
              "id": "1",
              "usable": true,
              "major_errors": 0,
              "minor_errors": 1,
              "issues": [
                "DSA 인덱서의 괄호 설명이 원문의 의미를 어색하게 옮겼습니다(“a direction in other models”를 “다른 모델에도 적용되는 방향”으로 번역)."
              ]
            },
            {
              "id": "2",
              "usable": true,
              "major_errors": 0,
              "minor_errors": 2,
              "issues": [
                "FP8 저장소를 설명하는 문장에서 동일한 링크가 중복되고 문장 구조가 어색합니다.",
                "일부 기술 용어가 영어와 한국어로 혼용되어 문체 일관성이 다소 떨어집니다(예: “index”, “examples”, “draft head”)."
              ]
            }
          ]
        },
        "lookup": {
          "0": "luna",
          "1": "rule",
          "2": "switchyard"
        }
      },
      "pr251-quality": {
        "review": {
          "reviews": [
            {
              "id": "0",
              "usable": true,
              "major_errors": 0,
              "minor_errors": 1,
              "issues": [
                "“약 [$190 billion을 연구 개발에 투자”는 금액을 한국어로 자연스럽게 옮기지 못한 표현이며, “약 1,900억 달러를 연구 개발에 투자”가 적절합니다."
              ]
            },
            {
              "id": "1",
              "usable": false,
              "major_errors": 1,
              "minor_errors": 1,
              "issues": [
                "“Erkenntnissen”이 독일어로 번역되지 않은 채 남아 있어 명백한 번역 오류입니다.",
                "“약 [$190 billion을 연구 및 개발에 투자”는 금액을 한국어로 자연스럽게 옮기지 못한 표현이며, “약 1,900억 달러를 연구 개발에 투자”가 적절합니다."
              ]
            },
            {
              "id": "2",
              "usable": true,
              "major_errors": 0,
              "minor_errors": 1,
              "issues": [
                "“[NASA IMPACT의](...) 27개 저장소”는 링크와 조사가 어색하게 결합되어 있으며, “NASA IMPACT의 [27개 저장소](...)”처럼 다듬는 것이 자연스럽습니다."
              ]
            }
          ]
        },
        "lookup": {
          "0": "luna",
          "1": "rule",
          "2": "switchyard"
        }
      },
      "pr239-quality": {
        "review": {
          "reviews": [
            {
              "id": "0",
              "usable": true,
              "major_errors": 0,
              "minor_errors": 0,
              "issues": []
            },
            {
              "id": "1",
              "usable": true,
              "major_errors": 0,
              "minor_errors": 1,
              "issues": [
                "일부 이미지 대체 텍스트에서 처리량 단위(tokens/s)가 반복적으로 생략되어 수치 표현이 약간 덜 명확합니다."
              ]
            }
          ]
        },
        "lookup": {
          "0": "luna",
          "1": "rule"
        }
      },
      "pr238-quality": {
        "review": {
          "reviews": [
            {
              "id": "0",
              "usable": true,
              "major_errors": 0,
              "minor_errors": 1,
              "issues": [
                "Anthropic API의 \"effort options\"를 \"추론 노력 옵션\"으로 옮겨 표현이 다소 어색하고 기술적 의미가 불명확합니다."
              ]
            },
            {
              "id": "1",
              "usable": true,
              "major_errors": 0,
              "minor_errors": 1,
              "issues": [
                "Anthropic API의 \"effort options\"가 영어 \"effort\"로 남아 있어 한국어 번역의 일관성이 약합니다."
              ]
            }
          ]
        },
        "lookup": {
          "0": "luna",
          "1": "rule"
        }
      }
    }
  },
  "failure": null
}
```

## 사용량과 비용

```json
{
  "actual_upstream_attempts": 18,
  "completed": 18,
  "inflight": 0,
  "errors": 0,
  "requested_models": {
    "gpt-5.6-luna": 18
  },
  "resolved_models": {
    "gpt-5.6-luna": 18
  },
  "usage_derived_estimate_usd_known_sum": 0.08079425,
  "unknown_estimate_attempts": 0,
  "provider_reported_cost_usd": null,
  "billing_confirmed_actual_usd": null,
  "billing_scope": "Official OpenAI direct; exempt from non-OpenAI $10 cap",
  "input_tokens": 115971,
  "output_tokens_including_reasoning": 47383,
  "cache_read_tokens": 21980,
  "cache_write_tokens": 93937,
  "cache_write_30m_tokens": 93937,
  "cache_write_12h_tokens": 0,
  "reasoning_tokens": 2759,
  "service_tiers": {
    "default": 18
  },
  "automatic_upstream_retries": 0,
  "summed_request_seconds": 338.3496635448537
}
```

사용량은 원본 응답에서 수집했습니다. 위 금액은 cache read/write와 reasoning 포함 output을 반영한 단가 기반 추정이며 청구서 확인값이 아닙니다. 서비스 tier나 긴 문맥 등 계산하지 않은 조건은 추정 미확인으로 남깁니다. SDK upstream 자동 재시도는 0이며, 명시적 프로토콜 재검증·실패·fallback은 각각 기록합니다. Data Designer의 로컬 프록시 재요청은 발생 시 각 전달 시도로 계측하고 전체 upstream 8회로 제한합니다.

## 해석과 한계

이전 historical/dev 입력을 다시 사용한 진단·회귀 실험입니다. 사람 정답 승인 수는 0이며, 별도 호출의 model judge도 같은 모델 계열 편향을 가질 수 있습니다. 일부 실험은 합성 오류·가상 업데이트를 포함합니다. 무료 회귀, 과거 결과, 이번 새 호출을 섞지 않습니다. 병렬 실험의 벽시계 시간은 통제된 지연 성능 비교가 아닙니다.

## 비교 관찰과 채택 판단

luna는 고정 Luna, cheap는 고정 Qwen, rule은 문서 특징 규칙, switchyard는 NeMo Switchyard 네이티브 분류기로 모델을 선택합니다.

| 조건 | 완료 | 비OpenAI 차단 | 선택 |
|---|---:|---:|---|
| luna | 4 | 0 | Luna 4 |
| cheap | 0 | 4 | Qwen 4 |
| rule | 4 | 0 | Luna 4 |
| switchyard | 2 | 2 | Luna 2/Qwen 2 |

완료한 10개 문서의 모델 검토는 Luna 4/4, rule 3/4, switchyard 2/2 사용 가능 판정입니다. rule의 NASA 번역에는 독일어 Erkenntnissen이 남아 major 1건으로 지적됐습니다. 같은 모델 선택도 재생성마다 달라집니다. 실제 네이티브 선택 실행은 확인했지만 Qwen 대조군 없이 비용 절감/품질 유지 주장은 보류합니다.
