# 야간 번역 파이프라인 실험 현황

> **후속 지시 안내:** 이 문서는 OpenAI 직접 호출도 비용 미확인으로 차단했던 당시의 기록입니다. 이후 사용자가 공식 OpenAI 직접 청구를 한도에서 제외했으며, 최신 실행 상태는 [OpenAI 직접 후속 실행](../official-live-20261104/README.md)에 있습니다. 비OpenAI 서비스의 총 $10 한도와 미정산 arm 차단은 유지합니다.

2026년 11월 4일 한국 시간 기준으로 준비된 runner와 아이디어를 구분해 점검했습니다. **#256은 paused, 관련 기존 실행은 모두 종료**입니다. 최초 연결 테스트는 부분 실패였으며, 원격 비용 미확인으로 유료 본 실험은 진행하지 않았습니다. 모든 수정은 Draft 검토 대상으로만 남기고 merge하지 않습니다.

## 원인 수정과 무료 재검증

- 독립 검증기가 `review_required`를 조기 반환하여 불완전 의미 평가를 승인하던 경로를 제거했습니다. 실패 보고서 자체는 검증 가능하며, 완전한 review_required는 기존처럼 허용합니다.
- #256 실제 artifact 5개를 수정 전후 재생: 기존에는 5개 모두 수락, 수정 후 완전한 1개만 수락하고 불완전 4개를 거절했습니다. [원본 재생 결과](verifier-replay.json)
- hf-workflow 전체 404개, 기존 NVIDIA fixture 45개, native Guardrails 11개, native Switchyard 11개, 블로그 이벤트 조건 회귀 6개가 네트워크 차단 상태에서 통과했습니다. [검증 기록](free-validation.json)
- 블로그 [Draft PR #257](https://github.com/Hugging-Face-KREW/hugging-face-krew.github.io/pull/257)은 이벤트 당시 managed/paused 라벨로 트리거를 거르고, review/feedback 수정 경로를 PR 단위 비취소 group으로 직렬화합니다. 직접 중앙 dispatch까지 분산 잠금을 제공하지는 않습니다.
- 기존 [hf-workflow PR #35](https://github.com/Hugging-Face-KREW/hf-workflow/pull/35)는 MQM 응답 격리와 incomplete repair 차단을 다룹니다. 이 작업은 그 PR을 merge하거나 중복 구현하지 않았고 독립 검증기 우회 경로를 보완합니다.
- [비용 설명](COSTS.md): 전체 한도 $10, 알려진 로컬 초벌 추정 $0.0033022, 원격 비용과 잔여액 미확인. 새 로컬 선예약 원장은 Actions 비용 차단이 배포됐다는 뜻이 아닙니다.

## 실행 도구가 있는 기존 실험

아래 준비는 구현 또는 이전 실행 자료가 있다는 뜻입니다. 같은 runner를 오늘 유료로 다시 실행했다는 뜻은 아닙니다.

| 실험 | 상태와 결과 |
|---|---|
| [L01 원문 기반 최소 수정 E1](experiments/L01.md) | archived_runner_paid_blocked |
| [L02 피드백 표현 비교 E2](experiments/L02.md) | archived_runner_paid_blocked |
| [L03 용어 정책 후속 비교](experiments/L03.md) | archived_runner_paid_blocked |
| [L04 전처리와 용어 정책 및 제한 수정 루프](experiments/L04.md) | archived_runner_paid_blocked |
| [L05 네이티브 Guardrails와 직접 검사 비교](experiments/L05.md) | archived_runner_paid_blocked |
| [L06 문서 번역 모델 라우팅 A](experiments/L06.md) | archived_runner_paid_blocked |
| [L07 Data Designer와 가이드 계획 B](experiments/L07.md) | archived_runner_paid_blocked |
| [L08 부분 수정과 라우팅 C](experiments/L08.md) | archived_runner_paid_blocked |
| [L09 증분 갱신과 전체 재번역 D](experiments/L09.md) | archived_runner_paid_blocked |
| [L10 링크 보호 전처리 회귀](experiments/L10.md) | archived_runner_paid_blocked |
| [L11 PR 기반 전체 번역 연결 테스트](experiments/L11.md) | integration_failed_paid_blocked |

## 기존 15개 제안의 구현 준비 상태

| 제안 | 현재 준비 |
|---|---|
| [N01 분류 결과 문서 역할별 재사용](experiments/N01.md) | 설치 API와 기존 매 요청 classifier만 준비. 새 session 수명·격리 비교 runner 필요. |
| [N02 도구 결과 기반 수정 모델 선택](experiments/N02.md) | stage_router Python API는 있지만 번역 도구 trace adapter와 고정 대조군은 추가 구현 필요. |
| [N03 독립 검사 병렬 실행](experiments/N03.md) | 설정과 fake native 테스트는 있으나 동일 후보의 직렬/병렬·직접/native matrix는 별도 준비. |
| [N04 조건부 검사와 조기 중단](experiments/N04.md) | 기존 facts/output short circuit 계약은 무료 검증. 비용 기반 조건부 검사 정책의 본 실험은 준비 전. |
| [N05 실패 이력에 따른 모델 승격](experiments/N05.md) | 기존 설치 API 수준 확인. native 상태 전이와 역할별 실패 기록 adapter 필요. |
| [N06 완료 시점 조언과 재작업](experiments/N06.md) | 현재 Python factory에 해당 기능이 없어 고정 Rust/서버 경로부터 확인 필요. |
| [N07 승인 버전 문맥을 가진 검색](experiments/N07.md) | 승인·문서 버전·정책 일치 데이터와 실제 retrieval adapter가 필요. |
| [N08 의미 대조쌍과 장애 조합 생성](experiments/N08.md) | 기존 유사 예시 생성 파일럿은 있으나 factorial 생성·선별·미사용 평가셋은 새로 구성해야 함. |
| [N09 실측 모델 능력 기반 정책](experiments/N09.md) | 기존 저장 verdict replay는 가능하나 새 held-out 문서와 오류 유형별 능력표 필요. |
| [N10 가이드 압축과 번역 역할별 모델 풀](experiments/N10.md) | 기존 compression model 분리 기능은 있음. role별 route/session/동일 정책 비교는 추가 구현. |
| [N11 문서 관계와 변경 영향 검사](experiments/N11.md) | 현재 구간별 MQM과 다른 관계 자료/평가 계약이 필요. 불완전 MQM 먼저 차단해야 함. |
| [N12 표 그림 PDF 구조 추출](experiments/N12.md) | 자료 선정·추출 모듈·자원/모델 의존성 확인 필요. 설치/실행 준비 완료가 아님. |
| [N13 번역 메모리 중복과 상충 정제](experiments/N13.md) | 충분한 자료 규모와 최소 대조쌍 보호 기준 필요. 라이브러리 도입 준비 전. |
| [N14 후보 생성 후 검증 라우팅](experiments/N14.md) | 현재 Python export에 없음. logprobs endpoint와 고정 빌드 경로 미확보. |
| [N15 반복 실행과 복구 표준화](experiments/N15.md) | 기존 runner 대조군은 있으나 Evaluator 연동과 동일 scorer 계약은 미구현. |

## 재개 조건

먼저 기존 원격 비용·수수료를 정산하고, 모든 호출이 공유 원장에 선예약되는 실행 경로를 마련해야 합니다. 그다음 검증기와 중복 트리거 수정의 검토·배포를 거쳐 원문 1편으로 재검증합니다. 본문 오류 자동수정·사람 피드백 경로는 이전 #256 실행으로 성공을 확인하지 못했습니다. 새로운 본 실험은 초기 연결이 정상임을 확인한 뒤 진행합니다.

추가 후보는 [아침 검토용 기획](ADDITIONAL-PLANS.md)에 따로 정리하며 실행하거나 예산을 사용하지 않습니다. 기존 15개 제안과 실행 준비된 11개 runner 단위를 혼합하지 않습니다. [기계 판독 목록](inventory.json)에는 각 항목의 준비 수준·출처·차단 이유를 남겼습니다.
