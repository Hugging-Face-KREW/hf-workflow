# 아직 실행하지 않은 실험 제안19개

**아래 항목은 실행 결과가 아닙니다.** 기존 제안15개와 실행 중 발견한 문제에서 추가한 제안4개입니다. 비용 때문에만 미룬 목록이 아니라, 새 비교 조건·실행 도구·자료 준비가 필요한 제안입니다.

## 기존 제안15개

| 제안 | 확인하려는 질문 | 사용 후보 |
|---|---|---|
| [N01. 분류 결과 문서 역할별 재사용](experiments/N01.md) | 같은 문서의 여러 작업에서 모델 선택을 재사용하면 분류 호출을 줄일 수 있는가? | Switchyard session affinity |
| [N02. 도구 결과 기반 수정 모델 선택](experiments/N02.md) | 리뷰 도구가 보고한 오류 종류에 따라 적절한 수정 모델을 선택할 수 있는가? | Switchyard stage_router |
| [N03. 독립 검사 병렬 실행](experiments/N03.md) | 같은 번역의 독립 검사를 병렬화하면 판정을 유지하면서 시간을 줄일 수 있는가? | Guardrails parallel output rails |
| [N04. 조건부 검사와 조기 중단](experiments/N04.md) | 앞선 검사 결과에 따라 필요한 검사만 실행해도 오류를 놓치지 않는가? | Guardrails conditional flow |
| [N05. 실패 이력에 따른 모델 승격](experiments/N05.md) | 수정 실패 뒤에만 상위 모델을 쓰면 고정 상위 모델의 품질에 가까워지는가? | Switchyard escalation |
| [N06. 완료 시점 조언과 재작업](experiments/N06.md) | 결과를 완료해도 되는지 판단하고 필요한 경우에만 재작업할 수 있는가? | Switchyard Advisor Gate |
| [N07. 승인 버전 문맥을 가진 검색](experiments/N07.md) | 승인된 버전의 번역 문맥만 검색해 수정에 활용할 수 있는가? | Guardrails retrieval rails |
| [N08. 의미 대조쌍과 장애 조합 생성](experiments/N08.md) | 의미가 비슷하지만 정답이 다른 예시와 복합 오류를 만들어 평가를 강화할 수 있는가? | Data Designer |
| [N09. 실측 모델 능력 기반 정책](experiments/N09.md) | 오류 유형별 실제 모델 성적에 따라 모델 선택 정책을 만들면 나아지는가? | Switchyard custom classifier |
| [N10. 가이드 압축과 번역 역할별 모델 풀](experiments/N10.md) | 가이드 압축과 역할별 모델 선택을 함께 적용하면 비용·품질이 어떻게 달라지는가? | Switchyard role pools |
| [N11. 문서 관계와 변경 영향 검사](experiments/N11.md) | 문서 간 관계와 링크를 이용해 원문 변경의 번역 영향 범위를 찾을 수 있는가? | Guardrails context output rails |
| [N12. 표 그림 PDF 구조 추출](experiments/N12.md) | 표·그림·PDF 구조를 추출하는 도구를 쓰면 번역 입력이 더 정확해지는가? | NeMo Retriever |
| [N13. 번역 메모리 중복과 상충 정제](experiments/N13.md) | 중복·상충하는 과거 번역을 정제하면 검색 예시 품질이 좋아지는가? | NeMo Curator |
| [N14. 후보 생성 후 검증 라우팅](experiments/N14.md) | 생성한 후보를 검증한 뒤 다음 모델을 고르는 방식이 유리한가? | Switchyard VGR |
| [N15. 반복 실행과 복구 표준화](experiments/N15.md) | 반복 실행·장애 복구·평가 기록을 공통 도구로 묶으면 실험 운영이 쉬워지는가? | NeMo Evaluator |

## 추가 제안4개

| 제안 | 무엇을 비교할까 |
|---|---|
| [A01. 평가 결과를 받아들일 조건을 한곳에서 관리](plans/A01.md) | 직접 Python 검증과 Guardrails 흐름에 같은 SHA·hash·평가 구간 완전성 규칙을 적용해, 규칙을 추가할 때의 누락과 수정량을 비교합니다. |
| [A02. 번역 오류와 평가기 장애의 복구를 구분](plans/A02.md) | 고정 모델·직접 분기·Switchyard Stage Router를 비교합니다. 평가 JSON 장애를 번역 오류로 오인해 번역문을 고치는 일이 줄어드는지 봅니다. |
| [A03. 애매한 self-check 응답의 처리 비교](plans/A03.md) | Guardrails 기본 해석과 엄격한 해석을 비교합니다. yes/no가 아닌 빈 응답·uncertain·timeout 등을 주입해 근거 없는 통과를 찾습니다. |
| [A04. 모델 선택 횟수와 실제 API 시도 수 대조](plans/A04.md) | 호스트 원장과 Switchyard 계측을 로컬 가짜 응답에서 비교해 재시도·fallback·취소의 누락 집계를 찾습니다. |

[실행한11개 실험으로 돌아가기](../official-live-20261104/README.md)
