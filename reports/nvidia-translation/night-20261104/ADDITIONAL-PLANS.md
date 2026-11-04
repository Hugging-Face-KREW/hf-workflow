# 추가 제안4개

아직 실행하지 않은 계획입니다. 기존15개 제안과 섞이지 않도록 A01~A04로 구분했습니다.

- [A01. 평가 결과를 받아들일 조건을 한곳에서 관리](plans/A01.md) — 직접 Python 검증과 Guardrails 흐름에 같은 SHA·hash·평가 구간 완전성 규칙을 적용해, 규칙을 추가할 때의 누락과 수정량을 비교합니다.
- [A02. 번역 오류와 평가기 장애의 복구를 구분](plans/A02.md) — 고정 모델·직접 분기·Switchyard Stage Router를 비교합니다. 평가 JSON 장애를 번역 오류로 오인해 번역문을 고치는 일이 줄어드는지 봅니다.
- [A03. 애매한 self-check 응답의 처리 비교](plans/A03.md) — Guardrails 기본 해석과 엄격한 해석을 비교합니다. yes/no가 아닌 빈 응답·uncertain·timeout 등을 주입해 근거 없는 통과를 찾습니다.
- [A04. 모델 선택 횟수와 실제 API 시도 수 대조](plans/A04.md) — 호스트 원장과 Switchyard 계측을 로컬 가짜 응답에서 비교해 재시도·fallback·취소의 누락 집계를 찾습니다.

[미실행 제안19개 전체](PLANNED-EXPERIMENTS.md)
