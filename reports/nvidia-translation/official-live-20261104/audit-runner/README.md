# 감사용 실행 소스 스냅샷

2026-11-04 실행에 사용한 로컬 경로 의존 도우미입니다. 기존 미게시 실험 runner·고정 원문·별도 patched checkout·PR #35 prompt snapshot·NeMo 패키지가 필요합니다. 이 폴더만 내려받아 실행하는 범용 runner가 아닙니다. 자동 재실행하지 마세요. 코드에는 자격 증명 값이 없고 meter는 기존 환경 파일을 정상적으로 읽어 고정 공식 API 목적지만 호출합니다. `summarize.py` 다음 `insights.py`가 리포트를 생성합니다.

최종 검증: patched checkout 네트워크 차단 테스트 411개(기존 404+schema 7), 계측기 테스트 4개 통과. 과거 477개 무료 회귀와 중복되므로 합산하지 않습니다.
