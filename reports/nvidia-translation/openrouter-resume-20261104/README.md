> 이후 상태 변경: 아래는 유료 실행 전 준비·차단 기록입니다. 이후 사용자 예산 정정에 따라 Qwen 16개를 실제 실행·평가했습니다. [최종 결과](../openrouter-token5-live-20261104/README.md).

# OpenRouter 비교군 재개 준비와 비용 확인

**예산 정책: 공식 OpenAI 직접 비용은 한도 제외, 이번 승인된 실험에 귀속되는 비OpenAI 과거 비용·수수료·재시도·병렬 호출은 모두 합쳐 총 $10 이내입니다. 무관한 계정 지출은 이 실험 범위에 넣지 않습니다.**

현재 상태는 **재개 준비 및 무료 검증 완료, 유료 재개 보류**입니다. 새 OpenRouter 유료 호출·선예약은 모두 0회입니다. 추가 제안 15개와 추가 기획 4개는 실행하지 않았고 #256은 paused를 유지합니다.

## 읽기 전용으로 확인한 비용과 귀속

기존 승인 키를 정상 인증 헤더에만 사용해 공식 GET `/api/v1/key` 1회와 `/api/v1/generation?id=...` 26회를 조회했습니다. 모두 HTTP 200입니다. 새 로그인, 관리키 사용, 키 발급, 충전·결제 설정 변경은 하지 않았습니다.

- 보존된 과거 OpenRouter generation 26/26의 ID·모델·비용이 일치했습니다. timestamp 차이는 최대 0.976초로 원래 응답의 정수초 표기와 부합합니다. 모두 non-BYOK입니다.
- 26건은 **2026-11-01 20:59:10~21:09:01 KST**(UTC 11:59:10.719~12:09:01.217)의 과거 실행이며, 조회된 inference 비용 합계는 **$0.01228904**입니다. **11월 4일 이번 재개 시도의 신규 OpenRouter 유료 호출·비용은 0**입니다. 현 키 usage도 이 합계와 일치합니다. 이번 실험의 확인된 과거 inference 비용이며, 다른 계정 잔액이나 key label은 공개하지 않습니다.
- key의 `limit_remaining`과 `effective_budget`도 확인했지만, 키의 사용 가능액은 실험의 과거 수수료를 정산한 값이 아닙니다. 식별정보와 인증정보를 저장하지 않은 필요한 숫자만 저장소 밖 0600 파일에 보관했습니다. 공개 리포트에는 잔액·한도 숫자를 담지 않습니다.
- 과거 #256의 고정 workflow·caller·리뷰 도구를 읽었습니다. hosted Ubuntu의 명시적 환경/인수에는 base URL override가 없고, 품질/SEO는 OpenAI SDK 기본 경로를 사용하도록 구성돼 있습니다. 따라서 **공식 OpenAI 기본 경로로 구성된 호출**로 분류합니다. 이는 설정에 근거한 추론이며 실제 네트워크 캡처나 청구서 증명은 아닙니다. 검사한 실험 원장·설정에서 추가 실험귀속 비OpenAI 호출의 근거는 찾지 못했습니다. 무관한 다른 키 지출 가능성만으로 범위를 넓히지 않습니다.

[26건 조회와 비용 대조](readonly-audit.json) · [원격 설정 연결 근거](remote-route-evidence.json)

## 왜 유료 재개를 보류하는가

실험에 배분할 **과거 충전·처리·세금 등 수수료의 금액 또는 보수적 상한**은 inference 조회에서 나오지 않습니다. 이를 0이나 단순 inference 비용 비율로 가정하지 않았습니다. 필요한 최소 정보는 **확인된 $0.01228904 이외의 추가 실험귀속 비OpenAI 비용·수수료를 합친 확정액 또는 보수적 상한(USD) 한 수치**입니다. 그 상한과 이번 실행의 요청별 최대비용을 합쳐 $10 이하인지 확인해야 합니다.

공식 공개 catalog/provider endpoint에서 확인 가능한 값은 아래에 채웠습니다. 요청당/부수비용과 account 호환 등 미확인 항목 때문에 별도 계약 파일은 미승인 상태입니다. 과거 성공 기록이나 공개 모델 등록만으로 현재 호환성을 가정하지 않습니다. 유료 1건 검증, 나머지 번역, JSON·coverage·코드/URL·모델 품질 평가는 이번 단계에서 실행하지 않았습니다. 검증된 provider 계약과 수수료 상한이 확보되면 1건 제한 실행→실제 사용량 확인→나머지 비교군 순으로 진행할 계획이며, 준비를 실제 실행 완료로 세지 않습니다. 기존 차단 기록도 그대로 보존했습니다.

OpenRouter 공식 자료상 [key 조회](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key)는 키 사용량/한도 정보를, [generation 조회](https://openrouter.ai/docs/api/api-reference/generations/get-request-&-usage-metadata-for-a-generation)는 개별 생성 비용 정보를 제공합니다. [요금 안내](https://openrouter.ai/pricing)는 구매 시 수수료와 inference 비용을 구분합니다. [provider max_price](https://openrouter.ai/docs/guides/routing/provider-selection#max-price)는 요청/토큰별 가격 제한을 지원하지만 과거 수수료 정산을 대신하지 않습니다.

## 공식 공개 catalog에서 추가 확인한 값

인증 없이 공식 GET models와 모델 endpoints를 읽었고 모두 HTTP 200입니다. [원본 공개 응답](public-catalog.json) · [명시적 계약](provider-contract.json)

| 항목 | 확인한 값 |
|---|---|
| 요청 alias → canonical | qwen/qwen3.7-flash → qwen/qwen3.7-flash-20260727 |
| provider 이름 / 기본 tag | Alibaba / alibaba |
| 별도 지역 variant | alibaba/us-east-1; 기본 tag와 가격이 달라 별도 제외 계약 필요 |
| context / prompt 최대 / completion 최대 | 1,000,000 / 983,616 / 65,536 tokens |
| 기본 endpoint 최악 tier 단가: 입력 / 출력 | $0.20 / $0.80 per million |
| 기본 endpoint 최악 tier: cache read / write | $0.04 / $0.25 per million |
| 파라미터 | max_tokens, reasoning, response_format 지원; reasoning 필수 아님 |
| 아직 미확인 | 요청당 fee(필드 없음≠0), 부수비용, BYOK/현재 계정 호환, provider 제외·가격 계약의 전체 적용 확인 |

응답 모델은 alias와 공식 canonical 두 값만 명시적으로 허용하도록 수정했습니다. 다른 모델은 계속 거부합니다. 과거 응답이 canonical을 반환한 정상 상황을 잘못 모델 변경으로 처리하지 않습니다. region variant는 같은 base slug prefix에 걸릴 수 있으므로 ignore 계약에 명시했고, 검증 완료 전 호출하지 않습니다. 공개 가격 등록은 현재 키/옵션 호환의 유료 검증을 대신하지 않습니다.

## 새로 준비한 고정 비교군

| 계열 | 재개할 비교군 | 준비 수 | 이번 유료 실행 |
|---|---|---:|---:|
| L06 | 고정 Qwen 4문서와 기존 Switchyard가 Qwen을 고른 2문서 | 6 | 0 |
| L07 | baseline / plan_real / plan_dd | 3 | 0 |
| L08 | 기존 Switchyard가 Qwen을 고른 부분 수정 | 5 | 0 |
| L09 | 기존 Switchyard가 Qwen을 고른 증분 갱신 | 2 | 0 |

모델은 `qwen/qwen3.7-flash`로 유지했습니다. L06/L08/L09의 라우터를 다시 호출하지 않고 실제 보존된 결정을 사용했습니다. 원래 입력·프롬프트·출력 cap을 유지하고 새 실행 ID/폴더에 16개 payload를 고정했습니다. provider pin과 가격 계약이 검증되기 전 전송하지 않습니다. [고정 요청](prepared-arms.json)

L07은 기존 `OUT.parent/dd-reviewed.json` 기본 경로를 쓰지 않고, **이번 L07/dd-reviewed.json의 새 검토 결과 8개 중 사용 가능 6개**를 명시적으로 연결했습니다. 기존 b()의 세 조건을 유지하며 plan_dd에만 이 6개를 추가합니다. baseline/plan_real과 기존 고정 development/heldout 입력은 그대로입니다. 과거 split 이름 heldout은 새로 확보한 검증 자료라는 뜻이 아닙니다. [연결·입력 해시](L07-input-provenance.json)

## 별도 예산 원장과 무료 검증

OpenAI가 섞인 옛 원장은 재사용하지 않았습니다. 새 [non-openai-budget.json](non-openai-budget.json)은 실험 과거비용·수수료 상한이 미확인이라 차단 상태입니다. [provider-contract.json](provider-contract.json)도 미승인입니다.

- Decimal 계산, 파일 잠금·원자적 저장으로 매 시도 전에 최악비용을 선예약합니다. 중복 ID, 자동 재시도, 원장 재초기화를 거부합니다.
- 성공·실패·timeout·JSON 오류에서도 예약을 해제하지 않습니다. 불확실 호출의 재전송을 막고, 관측 비용이 상한을 넘으면 이후 호출을 차단합니다.
- 공식 OpenRouter host와 고정 Qwen만 허용합니다. 검증된 provider pin, fallback 금지, 가격 상한, 명시적 출력 cap을 요구합니다. 텍스트 외 입력·도구·플러그인은 거부합니다.
- 입력 할인은 가정하지 않고 검증된 전체 context ceiling을 최악 입력 수로 잡아 uncached/read/write 중 가장 높은 단가를 사용합니다. 출력 cap에는 reasoning이 포함돼야 하며 요청당·부수비용의 검증된 상한도 더합니다. 미확인 필드는 차단합니다.
- 이는 **이 로컬 실행기의 원장**입니다. 계정 전체나 외부 실행기의 분산 잠금을 배포한 것은 아닙니다.

실제 socket을 막고 API 환경키를 제거한 무료 검사 **29개 통과**입니다. 30개 프로세스가 동시에 예약하는 시험에서 과거비용 fixture $8 + 요청별 fixture $0.1 × 20개만 허용해 정확히 $10을 지켰습니다. fixture 금액은 실제 계정 비용이 아닙니다. [검증 기록](validation.json)

감사용 소스는 이 날짜의 로컬 경로·기존 runner·고정 자료에 의존합니다. 다른 환경에 바로 배포할 범용 실행기를 제공하거나 비용 확인을 자동 승인하는 코드는 아닙니다. 기존 [실제 OpenAI 실험 결과](../official-live-20261104/README.md)와 이번 미실행 준비를 구분합니다.
