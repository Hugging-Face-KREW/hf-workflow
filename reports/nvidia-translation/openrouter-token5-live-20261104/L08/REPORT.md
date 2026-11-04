# L08 Qwen 실제 후속 비교

**실제 새 생성 5개**, 보고 비용 $0.00013810. 과거 11월1일 기록과 구분한 11월4일 실행입니다.

기존 네이티브 라우터가 Qwen을 선택했던 5개 부분 수정 조건을 새 호출했습니다. 원래 지적·source·candidate와 출력 cap을 유지했습니다. 기존 Luna 수정 5개와 원본 5개 검토는 이전 결과로 구분합니다. 모델 usable과 major 오류가 함께 나올 수 있어 declared usable과 major=0·구조 보존을 별도로 셉니다.

| 실제 비교군 | 모델 평가 단위 | major=0·구조 보존 | major 수 | 코드/URL 손상 | 응답 비용 USD |
|---|---:|---:|---:|---:|---:|
| L08-C-switchyard-pr238_intro | 1 | 0 | 1 | 0/0 | 3.2e-05 |
| L08-C-switchyard-pr238_reasoning | 1 | 1 | 0 | 0/0 | 1.392e-05 |
| L08-C-switchyard-pr238_thanks | 1 | 1 | 0 | 0/0 | 2.11e-05 |
| L08-C-switchyard-pr239_linear | 1 | 1 | 0 | 0/0 | 4.507e-05 |
| L08-C-switchyard-pr239_requirements | 1 | 1 | 0 | 0/0 | 2.601e-05 |

## 대표 관찰

```json
[
  {
    "id": "L08-C-switchyard-pr238_intro:pr238_intro",
    "issues": [
      "“a drop-in replacement for Apple's Foundation Models framework”가 “애플의 Foundation Models 프레임워크를 위한 대체 API”로 번역되어, 프레임워크 자체를 대체하는 drop-in replacement라는 의미가 “프레임워크를 위한 API”로 바뀌었고 ‘drop-in’의 호환성 의미도 누락되었습니다.",
      "“multiple inference providers”의 “inference”가 번역되지 않아 “여러 inference 제공자”라는 부자연스럽고 기술적으로 불명확한 표현이 되었습니다."
    ],
    "major_errors": 1,
    "minor_errors": 1
  }
]
```

## 해석과 채택 판단

현재 결과는 노출된 개발 입력·모델 판정에 따른 진단입니다. 사람 정답은 0입니다. 자동 운영 채택은 보류하고, 실패를 회귀 입력으로 남깁니다. 신규 5개 중 4개가 major 없음·구조 보존이며 첫 소개 문단에 major 1건이 남았습니다. 모델 usable=true만으로 자동 승인하지 않습니다.

[세부 집계·이전 결과 분리](report.json) · [전체 예산·정책](../README.md)
