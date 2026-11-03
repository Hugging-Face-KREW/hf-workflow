# 아침 검토용 NVIDIA OSS 추가 실험 기획

현재는 **기획만 완료했고 아래 추가 실험은 실행하지 않았습니다.** 기존 원격 비용이 미확인이므로 $10 한도의 정확한 잔여액도 미확인입니다. 유료 실행 가능하다고 판단하지 않습니다. 아래 네 후보의 첫 단계는 저장된 자료·가짜 응답·로컬 실행만 사용하도록 설계해 모델 비용 최대치를 각각 $0으로 제한했습니다. 외부 모델 호출과 클라우드 자원 대여를 허용하지 않으며, 이후 유료 확대는 범위와 예산을 다시 검토해야 합니다.

현재 설치는 Guardrails 0.24.1, Switchyard 0.3.0, Data Designer 0.9.7입니다. 최신 웹 문서와 설치 버전은 구분합니다. 특히 설치된 `stage_router`에는 `tool_semantics`와 `classifier`가 있지만 최신 문서의 모든 hold 설정이 Python 인자로 노출되지는 않습니다.

## 1 평가 결과 채택 계약을 실행 흐름으로 묶기

**가설:** 번역문 자체가 아닌 평가 artifact의 완전성·SHA·hash 계약을 output rail로 표현하면, 평가기 추가·정책 변경 때 누락된 게이트를 찾고 변경하기 쉬워질 수 있습니다. #256의 20/22 MQM 결과 Pass가 직접적인 회귀 사례입니다.

- NVIDIA 기여: 실제 LLMRails custom action과 flow의 차단·활성화 로그·정책 조합을 사용합니다. 누락 판별 로직은 현재 Python 검증기와 동일하게 유지합니다. 같은 판정이면 품질 향상이 아니라 운영 편의만 측정합니다.
- 대조군/변수: 직접 Python 게이트와 Guardrails 게이트, 정책 1개/3개/5개. 동일 artifact·계약 함수·판정 기준을 사용하고 검증기에 새로운 의미 점수를 만들지 않습니다.
- 입력/절차: #256 artifact 5개와 source hash 불일치·중복 ID·stale SHA·미완료 coverage를 포함한 24개 고정 fixture를 만듭니다. 두 경로에서 채택 여부를 비교한 뒤, 동일한 새 계약 하나를 추가하는 데 필요한 수정 파일·수정량·시간을 기록합니다. 기존 CLI 검증기를 우회해 운영에 적용하지 않습니다.
- 지표/성공: false accept 0, 두 경로 판정 일치 100%, 오류 사유·대상 SHA 추적 100%. 정책 추가 작업에서 반복 수정이 줄어드는지 봅니다.
- 중단: 정상 자료를 막거나 불완전 자료를 한 번이라도 통과시키면 중단합니다. 동일 Python 함수에 의미 없는 wrapper만 늘어나면 도입 우선순위를 낮춥니다.
- 최대 비용/위험: 모델 $0, 외부 네트워크 차단. Guardrails 설치·런타임 복잡성이 편의보다 클 수 있습니다. Guardrails 프레임워크가 기존 검증 함수보다 판정력이 높다고 가정하지 않습니다.

근거: Guardrails는 모델과 독립적인 실행 규칙을 구성하는 도구라는 [원 논문](https://arxiv.org/abs/2310.10501), runtime의 차단·변경·관찰 구분을 설명하는 [공식 FAQ](https://docs.nvidia.com/nemo/guardrails/resources/runtime-security-faq). 두 링크의 본문 접근을 2026-11-04 확인했습니다.

## 2 번역 오류와 평가기 장애의 회복 경로 구분

**가설:** JSON/coverage 장애를 번역 내용 오류와 구분해 tool 결과로 전달하면, 잘못된 번역 수정 대신 평가기 회복에 모델 선택을 집중할 수 있습니다. 기존 도구 신호 라우팅 제안에서 한 단계 좁혀, 이번에 관측한 오류 종류를 비교 변수로 삼습니다.

- NVIDIA 기여: native Switchyard Stage Router가 실제 tool-result 이력에서 모델 tier를 고릅니다. 어떤 작업을 재실행할지는 공통 host가 결정하며, router가 자동으로 평가기나 수정 도구를 구현한다고 보지 않습니다.
- 대조군/변수: 고정 모델 tier, 오류 종류별 직접 if 분기, native stage routing. 입력 trace와 host 동작은 같고 라우팅만 다릅니다. classifier를 끄고 추가 judge 호출이 없는 경로부터 설계합니다.
- 입력/절차: 정상 검토·coverage 누락·비정형 판정·실제 의미 오류·수정 성공 등 12개 trace를 고정합니다. `review_translation`, `verify_artifact`, `repair_translation`의 정확한 이름을 role에 매핑합니다. 실패 종류와 exit status를 공개된 tool 신호 형식으로 표현할 수 있는지 먼저 확인합니다. 정책이 결과 JSON 내부를 자동 해석한다고 가정하지 않습니다.
- 지표/성공: 평가기 장애만 있는 trace에서 번역문 수정 0회, 실제 오류 trace에서 필요한 회복 tier 선택, 불필요한 상위 tier 선택 횟수와 route 변경 횟수. 선택 이유를 전부 기록합니다.
- 중단: 설치 버전의 신호 형식으로 필요한 오류를 구분할 수 없거나, 직접 분기와 결과가 같으면서 더 복잡하면 중단합니다. 최신 문서 기능을 확인 없이 끌어오지 않습니다.
- 최대 비용/위험: 가짜 model target을 사용해 $0. native 코드의 기본 신호가 코딩 작업에 맞춰져 있어 번역 장애를 잘못 해석할 수 있습니다. session 유지가 API 중복 실행 방지 기능은 아니므로 workflow 중복 제어와 분리합니다.

근거: [공식 Stage Router 문서](https://nvidia-nemo.github.io/Switchyard/routing_algorithms/stage_router_routing/), classifier와 stage의 역할을 나누는 [Composite Routing](https://nvidia-nemo.github.io/Switchyard/routing_algorithms/composite_routing/). 두 본문 접근을 확인했습니다. 설치 Python signature는 조회만 했으며 이 추가 trace 실험은 실행하지 않았습니다.

## 3 비정형 self-check 판정과 오류 극성의 결합 회귀

**가설:** facts와 output의 yes/no 의미가 다른 상태에서 비정형·빈 응답을 정책별로 고정해 검사하면, parser 버전 변경으로 생기는 잘못된 통과를 빨리 찾을 수 있습니다. 기존 무료 테스트에서 facts에 `uncertain`을 주면 통과하는 동작을 기록하고 있습니다.

- NVIDIA 기여: 실제 Guardrails 내장 facts/output action과 parser를 실행합니다. 같은 프롬프트·응답을 받는 엄격한 Python parser, native 기본 parser, 명시적 custom parser를 비교해 native runtime과 설정의 영향을 분리합니다.
- 변수/절차: `yes`, `no`, `uncertain`, `no (allow)`, 빈 문자열, 길이 제한 종료, timeout의 가짜 응답을 같은 원문·후보에 주입합니다. facts/output 순서와 결과 극성을 고정합니다. 버전을 바꿀 때는 별도 환경에서 동일 fixture를 사용하며 최신 develop 코드를 운영 버전으로 취급하지 않습니다.
- 지표/성공: 비정형 판정의 무근거 통과 0, canonical 응답의 판정 일치, 실패 이유·재시도 수·후속 검사 호출 수 추적. 정책 설정 변경만으로 안전한 거절을 구성할 수 있는지 비교합니다.
- 중단: ambiguous 응답을 정상 의미 판정으로 집계하면 중단합니다. native parser 행동과 host의 보완 정책을 섞어 NVIDIA 기본 동작이 안전했다고 보고하지 않습니다.
- 최대 비용/위험: fake judge만 사용해 $0. parser 보완이 유효 번역을 과하게 막거나, 설치 버전에서 custom parser 적용 범위가 다를 수 있습니다. 이 실험은 의미 정확도 자체를 평가하지 않습니다.

근거: [공식 self-check 구현 문서](https://github.com/NVIDIA-NeMo/Guardrails/blob/develop/docs/configure-rails/guardrail-catalog/self-check.mdx)는 output의 차단 응답 극성과 reasoning 모델의 빈 응답 문제를 설명합니다. 접근은 확인했지만 develop과 0.24.1의 동작 일치를 보장하지 않습니다. 회귀 fixture는 설치 버전에서 먼저 고정해야 합니다.

## 4 라우팅 결정 수와 실제 유료 시도 수를 분리한 계측

**가설:** Switchyard의 native client span/attempt 계측을 host 원장과 대조하면, route 결정만 세어서 retry·fallback 비용을 빠뜨리는 문제를 줄일 수 있습니다. #256의 원격 비용 미계측과 직접 연결되는 운영 실험입니다.

- NVIDIA 기여: native libsy/client의 routing·candidate·HTTP attempt 식별과 이용 가능한 usage를 사용합니다. 수기 host 로그만 남기는 대조군과 같은 fake 응답을 처리하고 기록 누락을 비교합니다. 기록은 청구서나 예산 차단을 대신하지 않습니다.
- 변수/절차: 성공, 실패 후 fallback, 429 후 retry, 응답 도중 취소, usage 미제공의 로컬 stub을 설계합니다. 실제 자격 증명은 제거하고 loopback 외 네트워크는 막습니다. 각 trace의 예상 route/candidate/attempt 수를 먼저 고정하고 원장 예약과 span을 연결합니다.
- 지표/성공: 시도 누락·이중 집계 0, 요청한 모델과 실제 모델 구분, usage 미제공을 0으로 만들지 않음, 모든 비용 항목의 provenance 연결. 취소·실패한 시도도 예약이 남아야 합니다.
- 접근성 gate: 현재 Python `run_stream` host는 자기 I/O를 직접 계측해야 합니다. 문서의 native LLM client driver와 exporter 연결을 현재 버전에서 사용할 수 있는지 확인하지 못하면 Rust 경로의 준비 비용을 따로 평가하고 유료 확대를 보류합니다. 단순 환경변수 설정만으로 수집이 켜진다고 가정하지 않습니다.
- 중단: native 로그가 실제 시도를 식별하지 못하거나 변동 schema 때문에 대조군보다 누락이 많으면 중단합니다. 모델 요청 텍스트·비밀키를 외부 collector에 내보내지 않습니다.
- 최대 비용/위험: 로컬 stub과 로컬 collector만 사용해 $0. 실제 backend 요금·취소 시 청구는 검증하지 못하며, 이를 확인하려면 별도 승인과 유료 호출 경계가 필요합니다. 현재 미확인 원격 과거 비용을 소급 복구하는 실험도 아닙니다.

근거: [공식 OpenTelemetry 문서](https://nvidia-nemo.github.io/Switchyard/reference/opentelemetry/)는 host가 exporter를 설치해야 하고, 직접 run_stream을 구동하면 I/O도 host가 계측해야 한다고 설명합니다. 현재 schema는 별도 안정 버전 계약이 아니며 usage가 없으면 필드를 생략합니다. 본문 접근을 확인했습니다. 잘못 추정한 `/reference/otel/` 주소는 접근 실패해 사용하지 않습니다.

## 검토 순서와 예산 관계

현재 파이프라인 보완과 기존 실험의 비용 차단 리포트가 우선입니다. 위 후보는 아침 검토 후 1번 또는 3번처럼 가벼운 fixture 회귀부터 선택할 수 있습니다. 네 후보의 문서상 첫 단계 합계 모델 비용 상한은 $0이며, 이것이 오늘 $10 예산에 잔액이 있다는 뜻은 아닙니다. native OSS의 운영 편의가 단순 Python 대조군보다 나은 근거가 없으면 도입하지 않습니다.

접근성 기록: 최신 공식 Guardrails FAQ/config, Switchyard Stage/Composite/OTel, GitHub self-check 문서, arXiv 논문은 본문을 읽을 수 있었습니다. 예전 Guardrails `/latest/user-guides/guardrails-library.html` URL은 404였으므로 근거로 사용하지 않습니다. 설치 import 확인과 웹 문서 접근 확인은 별개이며, 위 추가 후보는 실행 결과가 아닙니다.
