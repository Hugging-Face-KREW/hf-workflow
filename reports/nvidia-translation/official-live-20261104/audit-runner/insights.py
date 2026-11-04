"""Add readable comparisons to generated reports without new API calls."""
import json
from pathlib import Path
from meter import OUT
notes={
'L01':'''F1은 원문·기존 번역·해당 지적만 주고 최소 수정하는 조건입니다. 1개 후보가 변경되었고 직접/NeMo 게이트 모두 승인했습니다. 링크 라벨은 한국어로 바뀌었습니다. 노출된 입력 1건의 연결 확인이므로 품질 우위 근거로 쓰지 않고, 회귀 입력으로 유지합니다.''',
'L02':'''F0은 무피드백 재작성, F1은 구조화된 지적 제공, F2는 F1과 같은 지적에 설명 문단만 확장, F3은 F1에 추가 문맥을 포함하는 기존 피드백 표현 조건입니다(정확한 실제 prompt는 원시 요청에 보존). 4개 중 F0 무변경은 거부, F1/F2/F3은 승인됐고 native/직접 판정은 4/4 일치했습니다. 그러나 F2는 “각 결과의 정확한 의미를 설명한다”는 명제를 버리고 링크만 반환했습니다. 승인 3/4를 의미 보존 성공 3/4로 해석할 수 없습니다. 피드백 표현만으로 안전한 수정을 보장한다는 가정은 보류하고, 이 누락을 별도 회귀 입력으로 남깁니다.''',
'L03':'''A는 용어 정책만, B는 탐지 피드백+문맥, C는 JSON target_id와 읽기 전용 문맥으로 편집 범위를 제한합니다.

| 조건 | 후보/변경 | 게이트 통과/거부/검토 | 잔여 영어 라벨/누락 지정 용어 | 모델 의미보존/완전현지화/불필요변경 |
|---|---:|---:|---:|---:|
{L03_ROWS}

native/직접 계약 판정은 48/48 일치했습니다. 예를 들어 B는 previous post를 그대로 남긴 무변경 후보를 검토로 보냈습니다. C의 통과 수가 가장 많지만 같은 개발 입력과 모델 판정으로 얻은 진단값입니다. 편집 경계 계약은 후속 실험 후보로 유지하되 운영 자동 승인과 통계적 우월 판단은 보류합니다.''',
'L04':'''whole은 과거 링크 전체 숨김, url은 URL만 숨김입니다. generic은 일반 프롬프트, policy는 검토된 용어 정책을 추가합니다.

| 조건 | 생성 수 | 복원 실패 | 기계 검사 무결점 | 잔여 설명 라벨 |
|---|---:|---:|---:|---:|
{L04_ROWS}

별도 오류 seed의 제한 수정 루프는 23개, 수정 시도 21회, 마지막 pass_candidate 17개/repair 잔류 6개였습니다. 이 seed 평가는 위 48개 생성물의 종단 평가가 아닙니다. URL 노출은 라벨 현지화에 도움이 됐지만 기계 검사 결과도 함께 보아야 합니다. 현재 운영에 이미 반영된 방향이며 NVIDIA 고유 효과로 채택하지 않습니다. 실패 시 승인 중단과 제한 루프만 후속 회귀 조건으로 유지합니다.''',
'L05':'''generic은 일반 직접 검사, facts는 NeMo 내장 self_check_facts, quality는 번역용 프롬프트를 쓴 내장 self_check_output, combined는 facts→quality, matched는 combined와 같은 프롬프트를 직접 실행합니다. 모델 호출이 독립적이므로 native/direct 간 차이를 프레임워크 효과로 단정할 수 없습니다.

| 조건 | 39개 노출 정답상 false pass | false block |
|---|---:|---:|
{L05_ROWS}

최종 판정 195개(39×5), 비표준 verdict 0개입니다. 재사용 합성 16개/회귀 23개의 분리 집계는 아래 JSON에 있습니다. 제한 수정 pipeline 48개 중 **승인되었지만 불변조건을 위반한 결과가 5개**입니다. 일반 사실성 검사만으로 번역 누락·라벨 현지화를 다루기 어렵습니다. quality 프롬프트는 후속 후보지만, gate 승인과 독립 구조검사를 결합하기 전 자동 반영은 보류합니다. 사람 정답이 아닌 개발용 라벨 기준입니다.''',
'L06':'''luna는 고정 Luna, cheap는 고정 Qwen, rule은 문서 특징 규칙, switchyard는 NeMo Switchyard 네이티브 분류기로 모델을 선택합니다.

| 조건 | 완료 | 비OpenAI 차단 | 선택 |
|---|---:|---:|---|
| luna | 4 | 0 | Luna 4 |
| cheap | 0 | 4 | Qwen 4 |
| rule | 4 | 0 | Luna 4 |
| switchyard | 2 | 2 | Luna 2/Qwen 2 |

완료한 10개 문서의 모델 검토는 Luna 4/4, rule 3/4, switchyard 2/2 사용 가능 판정입니다. rule의 NASA 번역에는 독일어 Erkenntnissen이 남아 major 1건으로 지적됐습니다. 같은 모델 선택도 재생성마다 달라집니다. 실제 네이티브 선택 실행은 확인했지만 Qwen 대조군 없이 비용 절감/품질 유지 주장은 보류합니다.''',
'L07':'''NeMo Data Designer로 실제 8행을 생성하고 별도 Luna 검토에서 6행 사용 가능 판정을 받았습니다. 나머지 2행은 검토 불통과로 보존했습니다. 계획 B는 이 예시 유무/선정 방식에 따른 번역 대조 실험이지만 기존 Qwen 모델을 바꾸지 않아 3개 arm 전부 미실행입니다. 데이터 생성 기능의 실행은 확인했고, 예시가 번역 품질을 높이는지는 보류합니다. 모델 검토 6/8을 사람 검수나 최종 번역 성공으로 세지 않습니다.''',
'L08':'''C는 5개 지적 대상 문단의 부분 수정입니다. 고정 Luna 5개는 완료했고 네이티브 라우터가 고른 Qwen 5개는 비용 미정산으로 차단했습니다. failed=5는 이 차단과 동일하며 별도 파싱 오류가 아닙니다. coverage 누락/중복은 0개입니다. 모델 검토상 수정 5/5와 원본 대조 5/5가 모두 사용 가능하므로 이 작은 표본에서 품질 상승은 입증되지 않았습니다. 실제 부분 수정 연결만 확인했고 라우팅 채택은 보류합니다.''',
'L09':'''D는 조건 변경/플랫폼 변경의 두 가상 원문 갱신을 전체 재번역(full_luna)과 변경 부분 번역 후 재조립(partial_luna)으로 비교합니다. 2×2=4개 조건은 완료, Switchyard가 고른 Qwen 2개는 차단했습니다. 각 완성 문서의 3문단, 총 12개가 모델 검토에서 사용 가능했으며 별도 C 원본 5개 대조도 동일 판정입니다. coverage 누락/중복 0개입니다. 재조립 경로는 실행됐지만 가상 변경 2건으로 의미 보존이나 비용 우위를 일반화하지 않습니다. 실제 업데이트 회귀 자료를 늘리기 전 운영 채택은 보류합니다.''',
'L10':'''과거 whole 보호와 url 보호로 같은 24문단을 각각 번역했습니다. 양쪽 모두 URL/코드 등 불변조건 24/24 유지, 잔여 영어 설명 라벨은 28→1입니다. 남은 1개도 성공으로 감추지 않았습니다. 별도 의미 판정은 하지 않았습니다. 현 운영에는 이미 라벨 노출 방식이 있으므로 새 NVIDIA 개선으로 채택하지 않고 전처리 회귀 근거로만 유지합니다.''',
'L11':'''기존 PR 이벤트 대신 로컬 git 대상에 초벌 번역·품질 평가·명시적 H1 편집·재평가를 연결했습니다. 구버전 protocol은 21/22에서 중단됐으며, PR #35 강화 prompt와 조건부 schema를 적용하고 별도 캐시 namespace에서 같은 번역을 재검증했습니다. 수정 후 최초/피드백 후 모두 22/22, verifier/SEO 통과, review_required 81점입니다. 자동 승인도 본문 오류 해결도 아닙니다. 로컬 실행 경로는 후속 smoke 기반으로 유지하고 원격 루프 검증은 #60/#257 반영 전 보류합니다.'''
}
# Check original F-arm definitions before publishing; this file holds interpretation only.
def main():
 for key,note in notes.items():
  d=OUT/key;r=json.loads((d/'report.json').read_text());m=r['metrics']
  if key=='L03':
   rows=json.loads((d/'results.json').read_text());out=[]
   for arm in 'ABC':
    a=m[arm];c=a['decisions'];changed=sum(x['changed'] for x in rows if x['arm']==arm)
    out.append(f"| {arm} | 16/{changed} | {c.get('model_pass_candidate',0)}/{c.get('reject',0)}/{c.get('needs_review',0)} | {a['remaining_english_labels']}/{a['missing_curated_terms']} | {a['model_meaning_preserved']}/{a['model_localization_complete']}/{a['model_unnecessary_change']} |")
   note=note.replace('{L03_ROWS}','\n'.join(out))
  if key=='L04':note=note.replace('{L04_ROWS}','\n'.join(f"| {a} | {v['n']} | {v['restore_failure']} | {v['mechanical_clean']} | {v['remaining_descriptive_labels']} |" for a,v in m['translation_arms'].items()))
  if key=='L05':note=note.replace('{L05_ROWS}','\n'.join(f"| {a} | {v['false_pass_on_exposed_labels']} | {v['false_block_on_exposed_labels']} |" for a,v in m['arms'].items()))
  p=d/'REPORT.md';s=p.read_text();p.write_text(s+'\n## 비교 관찰과 채택 판단\n\n'+note+'\n')
if __name__=='__main__':main()
