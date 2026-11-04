# L06 Qwen 실제 후속 비교

**실제 새 생성 6개**, 보고 비용 $0.003838182. 과거 11월1일 기록과 구분한 11월4일 실행입니다.

고정 Qwen 4문서와 기존 네이티브 Switchyard가 Qwen을 선택한 2문서를 새 호출했습니다. 기존 고정 Luna 4·규칙 4·Switchyard Luna 2 결과와 합쳐 네 조건의 생성 경로가 채워집니다. 새로 라우팅하지 않았습니다. 기존 OpenAI와 새 Qwen의 모델 평가 문맥/시점이 달라 통계적·인과적 품질 우위로 해석하지 않습니다.

| 실제 비교군 | 모델 평가 단위 | major=0·구조 보존 | major 수 | 코드/URL 손상 | 응답 비용 USD |
|---|---:|---:|---:|---:|---:|
| L06-pr238-cheap | 1 | 1 | 0 | 0/0 | 0.00032044 |
| L06-pr238-switchyard | 1 | 0 | 1 | 0/0 | 0.000280716 |
| L06-pr239-cheap | 1 | 0 | 2 | 0/0 | 0.00098847 |
| L06-pr239-switchyard | 1 | 1 | 0 | 0/0 | 0.000845276 |
| L06-pr251-cheap | 1 | 0 | 2 | 0/0 | 0.0004749 |
| L06-pr252-cheap | 1 | 0 | 0 | 1/1 | 0.00092838 |

## 기존 OpenAI 결과를 합친 네 조건

| 조건 | 문서 수 | major 없음·구조 보존 | 코드/URL 위반 문서 | 생성+라우터 비용 USD |
|---|---:|---:|---:|---:|
| luna | 4 | 4 | 0/0 | 0.02447775 |
| cheap | 4 | 1 | 1/1 | 0.00271219 |
| rule | 4 | 3 | 0/0 | 0.02131350 |
| switchyard | 4 | 2 | 0/1 | 0.01822124 |

OpenAI는 raw usage 단가 추정, OpenRouter는 provider reported 비용이며 청구서 금액은 아닙니다. Switchyard에는 분류기 비용을 포함합니다. 평가 호출 비용은 이 비교 표에서 별도로 뺐습니다.

## 대표 관찰

```json
[
  {
    "id": "L06-pr252-cheap:pr252",
    "issues": [
      "부자연스럽고 혼합 문자가 들어간 표현이 있습니다: “사용자의 통제下に 둡니다”는 한국어 문장 안에 일본어/한자 표현이 섞여 있으며, “사용자의 통제하에 둡니다”가 자연스럽습니다.",
      "기술 용어가 번역되지 않은 채 어색하게 남아 있습니다: “메모리_footprint_가 작고”는 “메모리 풋프린트가 작고” 또는 “메모리 사용량이 적고”가 적절합니다.",
      "문장에 중국어 문자가 삽입되어 자연스럽지 않습니다: “프리필吞吐量(prefill throughput)는”은 “프리필 처리량(prefill throughput)은”으로 고쳐야 합니다.",
      "일부 기술 표현이 부분적으로만 번역되어 일관성이 떨어집니다. 예를 들어 “hands-on 보안 문제”는 “실무형 보안 문제” 또는 “직접 수행하는 보안 문제”가 자연스럽고, “day-0 지원”도 문맥에 따라 “출시 당일부터 지원”으로 옮길 수 있습니다. 의미 자체의 누락이나 수치 오류는 보이지 않습니다."
    ],
    "major_errors": 0,
    "minor_errors": 4
  },
  {
    "id": "L06-pr238-switchyard:pr238",
    "issues": [
      "중대한 미번역/오역이 있습니다. “또한它们是 개발자들이 활용할 수 있는 다양한 모델 유형 중 하나입니다.”에 중국어 문자와 한국어가 혼입되어 문장이 손상되었습니다. 원문의 “They're also one of many kinds of models developers can put to work.”는 “또한 개발자가 활용할 수 있는 여러 종류의 모델 중 하나이기도 합니다.”처럼 번역해야 합니다.",
      "“Foundation Models API를 사용하여 앱에 맞는 모델로 사용합니다.”는 문법적으로 부자연스럽고 의미 관계가 불명확합니다. 원문의 의미인 “Foundation Models API를 사용하면서 앱에 맞는 모델을 선택합니다”가 더 정확합니다.",
      "Open Responses 항목의 “호환 가능한 엔드포인트가 있는 모든 제공자에게”는 문장이 완결되지 않고 의미가 어색합니다. “호환 가능한 엔드포인트를 제공하는 모든 제공자에서 사용할 수 있습니다”처럼 번역해야 합니다.",
      "“가이드 생성, 스트리밍과 함께 하는 도구 호출”은 의미는 전달되지만 한국어 기술 문체로 부자연스럽습니다. “가이드 생성, 스트리밍을 지원하는 도구 호출”이 자연스럽습니다."
    ],
    "major_errors": 1,
    "minor_errors": 3
  },
  {
    "id": "L06-pr239-cheap:pr239",
    "issues": [
      "중대한 기술 용어 오역: 원문의 표는 “Convolutions, padding, and training” 및 “Constant padding”과 “Out-of-place dropout”을 구분하지만, 번역은 TL;DR에서 “합성곱(convolutions), 패딩(dropout)”이라고 하여 padding을 dropout으로 잘못 표기했습니다.",
      "중대한 기술 용어 오역: “Out-of-place dropout”을 “[위치 비동기 dropout]”으로 번역했습니다. ‘out-of-place’는 입력을 변경하지 않고 별도 출력을 생성한다는 의미이지 ‘위치 비동기’가 아닙니다. “인플레이스가 아닌 드롭아웃” 또는 “비제자리 드롭아웃” 등이 적절합니다.",
      "자연스럽지 않고 의미가 불명확합니다. “eligible bias additions fused in”을 “자격 있는(bias) 편향 추가가 융합(fused)됩니다”로 옮겼는데, ‘eligible’은 ‘조건을 충족하는/지원되는’이라는 뜻입니다. 예: “조건을 충족하는 바이어스 덧셈은 융합됩니다.”",
      "원문의 “fewer GPU-CPU syncs”가 “fewer GPU-CPU 동기화”로 번역되지 않고 영어로 남아 있어 문체가 일관되지 않습니다. “GPU-CPU 동기화 횟수 감소”가 자연스럽습니다.",
      "“triangular solves”를 반복해서 “삼각방정식 풀이”로 옮겼습니다(예: “복잡한 LU 및 삼각방정식 풀이”). 이는 일반적으로 “삼각 시스템 풀이” 또는 “삼각행렬 풀이”가 더 정확합니다.",
      "“PyTorch 2.16 commits the command buffer every 16 kernels”를 “커널마다 16개씩 명령 버퍼를 커밋”으로 번역해 방향이 모호하거나 잘못 읽힙니다. 의미는 “커널 16개마다 명령 버퍼를 커밋”입니다.",
      "“FP8 gives you another way” 등에서 “FP8가”를 반복 사용해 조사 결합이 부자연스럽습니다. 기술적으로 큰 오류는 아니지만 제목과 본문에서는 “FP8은/FP8이”가 자연스럽습니다."
    ],
    "major_errors": 2,
    "minor_errors": 5
  },
  {
    "id": "L06-pr251-cheap:pr251",
    "issues": [
      "Major: The amount “$190 billion annually” is mistranslated as “$190억” (“19억 달러”/about $1.9 billion), a 100-fold numerical error. Evidence: source “$190 billion annually” vs. candidate “매년 약 [$190억을 연구 개발에 투자]”. It should be “연간 1,900억 달러” or “연간 1,900억 달러(약 190 billion dollars)”.",
      "Major: “memorandum of understanding” is mistranslated as “이해관계 일치서,” which means something like “statement of aligned interests,” not the established legal/organizational term “양해각서(MOU)”. Evidence: “이해관계 일치서(Memorandum of Understanding)”.",
      "Minor: The internal link target is likely broken after translation. The label is translated to “[참여 방법]” but the fragment remains “#the-first-challenge-climate-risk-intelligence,” while the corresponding Korean heading would normally generate a different slug. Evidence: “[참여 방법](#the-first-challenge-climate-risk-intelligence)”.",
      "Minor: “Cooling degree days” is rendered as “냉난방도,” which suggests both heating and cooling rather than the specific cooling metric. A more precise term is “냉방도일(Cooling Degree Days)”.",
      "Minor: “inaugural” is awkwardly translated as “초대 ProtoStar 챌린지”; “첫 번째 ProtoStar 챌린지” or “제1회 ProtoStar 챌린지” is natural and preserves the meaning.",
      "Minor: The phrase “including applications that combine resources across institutions or disciplines” contains an unintended mixed-script artifact: “기관이나 학제를横跨하여”. “기관이나 학제를 넘어/가로질러 자원을 결합하는” would be natural Korean.",
      "Minor: Several technical phrases are overly literal and unnatural, such as “AI 준비 완료 형식” and “공공 자금 지원 과학.” More natural terms would be “AI 활용에 적합한 형식”/“AI 준비형식” and “공공 자금이 지원된 과학 연구,” though the meaning remains generally recoverable."
    ],
    "major_errors": 2,
    "minor_errors": 5
  }
]
```

## 해석과 채택 판단

현재 결과는 노출된 개발 입력·모델 판정에 따른 진단입니다. 사람 정답은 0입니다. 자동 운영 채택은 보류하고, 실패를 회귀 입력으로 남깁니다. 평가자 계산 오류: 원문 $190 billion은 1,900억 달러입니다. 후보 190억 달러는 $19 billion으로 10배 작습니다. raw judge의 100배/19억/$1.9 billion 설명은 잘못된 산술이므로 사실로 채택하지 않습니다. raw 발언은 보존했습니다. 전체 네 조건의 기존/신규 합성 집계는 report.json의 combined_four_arms에 있습니다. 이전 OpenAI 모델평가와 새 Qwen 모델평가는 문맥/시점이 달라 동일 판정자로 통제된 비교가 아닙니다.

[세부 집계·이전 결과 분리](report.json) · [전체 예산·정책](../README.md)
