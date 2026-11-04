from pathlib import Path
from collections import Counter,defaultdict
import json,sys
from meter import ROOT,OUT,save
TITLES={'L01':'원문 기반 최소 수정','L02':'피드백 표현 비교','L03':'용어 정책 및 편집 범위','L04':'전처리와 제한 수정 루프','L05':'내장 Guardrails 및 직접 검사','L06':'문서 번역 모델 라우팅','L07':'Data Designer와 계획 B','L08':'부분 수정 라우팅 C','L09':'증분 갱신 D','L10':'링크 보호 전처리','L11':'로컬 전체 파이프라인'}

def read(path,default=None):return json.loads(path.read_text()) if path.exists() else default

def main():
 ledger=read(OUT/'usage.json',{'calls':[]});calls=ledger['calls'];groups=defaultdict(list)
 for c in calls:
  assert c['api_host']=='api.openai.com'
  groups[c['experiment'].split('-')[0]].append(c)
 reports=[]
 for identifier,title in TITLES.items():
  directory=OUT/identifier;directory.mkdir(exist_ok=True)
  result=read(directory/'result.json');failure=read(directory/'failure.json')
  records=groups[identifier]
  cost={
   'actual_upstream_attempts':len(records),'completed':sum(c['status']=='completed' for c in records),
   'inflight':sum(c['status']=='started' for c in records),'errors':sum(c['status'] not in ('started','completed') for c in records),
   'requested_models':dict(Counter(c['requested_model'] for c in records)),
   'resolved_models':dict(Counter(c.get('resolved_model','unreported') for c in records)),
   'usage_derived_estimate_usd_known_sum':sum(c.get('estimated_usd') or 0 for c in records),
   'unknown_estimate_attempts':sum(c.get('estimated_usd') is None for c in records),
   'provider_reported_cost_usd':sum(c['provider_reported_cost_usd'] for c in records if c.get('provider_reported_cost_usd') is not None) if any(c.get('provider_reported_cost_usd') is not None for c in records) else None,
   'billing_confirmed_actual_usd':None,'billing_scope':'Official OpenAI direct; exempt from non-OpenAI $10 cap',
   'input_tokens':sum(c.get('input_tokens') or 0 for c in records),'output_tokens_including_reasoning':sum(c.get('output_tokens') or 0 for c in records),
   'cache_read_tokens':sum(c.get('cache_read_tokens') or 0 for c in records),'cache_write_tokens':sum(c.get('cache_write_tokens') or 0 for c in records),
   'cache_write_30m_tokens':sum(c.get('cache_write_30m_tokens') or 0 for c in records),'cache_write_12h_tokens':sum(c.get('cache_write_12h_tokens') or 0 for c in records),
   'reasoning_tokens':sum(c.get('reasoning_tokens') or 0 for c in records),
   'service_tiers':dict(Counter(c.get('service_tier') or 'not_reported' for c in records)),
   'automatic_upstream_retries':0,'summed_request_seconds':sum(c.get('elapsed_seconds') or 0 for c in records),
  }
  metrics={}
  if identifier in ('L01','L02') and (directory/'results.json').exists():
   rows=read(directory/'results.json');metrics['arms']={r['arm']:{'gate_decision':r['direct']['decision'],'reasons':r['direct']['reasons'],'native_direct_equal':r['native']['decision']==r['direct']['decision'],'replacement':r['generation']} for r in rows}
   if identifier=='L02':
    metrics['adjudication_note']='F2 returned only the dataset-card link, omitting the sentence proposition about exact meanings of results. The primary same-model review and shared native/Python contract accepted it. This is a gate false-accept observation by Codex, not human gold and not a repaired result.'
  if identifier=='L03' and (directory/'results.json').exists():
   rows=read(directory/'results.json');metrics['rows']=len(rows)
   for arm in ('A','B','C'):
    selected=[x for x in rows if x.get('arm')==arm]
    metrics[arm]={'n':len(selected),'decisions':dict(Counter(x['decision'] for x in selected)),'native_direct_agreement':sum(x['python_matches_guardrails'] for x in selected),'remaining_english_labels':sum(len(x['remaining_english_labels']) for x in selected),'missing_curated_terms':sum(len(x['missing_curated_terms']) for x in selected),'model_meaning_preserved':sum(x['judge']['meaning_preserved'] for x in selected),'model_localization_complete':sum(x['judge']['localization_complete'] for x in selected),'model_unnecessary_change':sum(x['judge']['unnecessary_change'] for x in selected)}
  if identifier=='L04' and (directory/'translations.json').exists():
   rows=read(directory/'translations.json');metrics['translation_arms']={arm:{'n':len([x for x in rows if x['arm']==arm]),'restore_failure':sum(x['arm']==arm and x.get('candidate') is None for x in rows),'mechanical_clean':sum(x['arm']==arm and not x.get('mechanical') for x in rows),'remaining_descriptive_labels':sum(len(x.get('remaining_labels',[])) for x in rows if x['arm']==arm)} for arm in sorted({x['arm'] for x in rows})}
   ev=read(directory/'evaluations-v2.json',[]);metrics['validation_loops']=len(ev);metrics['repairs']=sum(x['loop'].get('repairs',0) for x in ev)
   metrics['final_decisions']=dict(Counter(x['loop']['trace'][-1]['decision'] for x in ev if x['loop']['trace']))
  if identifier=='L05' and (directory/'decisions').exists():
   data=read(directory/'dataset.json',[]);truth={x['id']:x for x in data};rows=[read(p) for p in (directory/'decisions').glob('*.json')]
   metrics['decisions']=len(rows);metrics['arms']={}
   for arm in ('generic','facts','quality','combined','matched'):
    a=[x for x in rows if x['arm']==arm]
    metrics['arms'][arm]={'n':len(a),'false_pass_on_exposed_labels':sum(bool(x['pass']) and truth[x['id']]['expected_bad'] for x in a),'false_block_on_exposed_labels':sum(not x['pass'] and not truth[x['id']]['expected_bad'] for x in a),'noncanonical_verdicts':sum(len(x.get('noncanonical',[])) for x in a)}
   metrics['by_exposed_split']={}
   for split in sorted({x['split'] for x in data}):
    metrics['by_exposed_split'][split]={}
    for arm in metrics['arms']:
     a=[x for x in rows if x['arm']==arm and truth[x['id']]['split']==split]
     metrics['by_exposed_split'][split][arm]={'n':len(a),'false_pass':sum(bool(x['pass']) and truth[x['id']]['expected_bad'] for x in a),'false_block':sum(not x['pass'] and not truth[x['id']]['expected_bad'] for x in a)}
   metrics['split_note']='new_synthetic_diagnostic is a historical split name: reused diagnostic, not fresh held-out data'
   pipes=[read(p) for p in (directory/'pipelines').glob('*.json')]
   metrics['repair_pipeline_rows']=len(pipes);metrics['approved_invariant_failure']=sum(x['approved'] and not x['invariant_ok'] for x in pipes)
  if identifier=='L06' and result:
   metrics['by_arm']={}
   for x in read(directory/'results.json',[]):
    a=metrics['by_arm'].setdefault(x['arm'],{'status':Counter(),'selected':Counter()});a['status'][x['status']]+=1;a['selected'][x.get('selected')]+=1
   metrics['model_reviews_by_document']={p.stem:read(p) for p in directory.glob('*-quality.json')}
  if identifier in ('L08','L09') and (directory/'evaluations.json').exists():
   rows=read(directory/'evaluations.json');metrics['model_reviews']=len(rows);metrics['usable']=sum(bool(x.get('usable')) and not x.get('code_changed') and not x.get('url_targets_changed') for x in rows)
   metrics['reviews_by_group']={}
   for group in sorted({x['id'].split(':')[0] for x in rows}):
    selected=[x for x in rows if x['id'].split(':')[0]==group]
    metrics['reviews_by_group'][group]={'n':len(selected),'model_usable':sum(bool(x.get('usable')) and not x.get('code_changed') and not x.get('url_targets_changed') for x in selected),'major_errors':sum(x.get('major_errors',0) for x in selected)}
  if identifier=='L10' and result:metrics=result.get('arms',{})
  status=result.get('status') if result else ('failed_requires_diagnosis' if failure else 'running_or_not_started')
  item={'id':identifier,'title':title,'status':status,'result':result,'failure':failure,'metrics':metrics,'usage':cost,'human_approved':0,'new_proposals_executed':False}
  save(directory/'report.json',item)
  text=f'# {title} 실제 실행 결과\n\n**최신 예산 지시: 공식 OpenAI 직접 청구는 한도 제외. 비OpenAI는 총 $10 한도와 미정산 arm 차단 유지.**\n\n상태: `{status}`. 새 upstream 호출 {cost["actual_upstream_attempts"]}회, 완료 {cost["completed"]}회, 진행 중 {cost["inflight"]}회입니다.\n\n## 입력 모델과 대조군\n\n요청 모델: `{json.dumps(cost["requested_models"],ensure_ascii=False)}`. 원본 입력·조건은 `execution-plan.json`과 이 폴더의 snapshot/manifest 또는 원본 참조에 고정했습니다. 비OpenAI arm은 다른 모델로 대체하지 않습니다.\n\n## 실제 결과\n\n```json\n'+json.dumps({'result':result,'metrics':metrics,'failure':failure},ensure_ascii=False,indent=2)+'\n```\n\n## 사용량과 비용\n\n```json\n'+json.dumps(cost,ensure_ascii=False,indent=2)+'\n```\n\n사용량은 원본 응답에서 수집했습니다. 위 금액은 cache read/write와 reasoning 포함 output을 반영한 단가 기반 추정이며 청구서 확인값이 아닙니다. 서비스 tier나 긴 문맥 등 계산하지 않은 조건은 추정 미확인으로 남깁니다. SDK upstream 자동 재시도는 0이며, 명시적 프로토콜 재검증·실패·fallback은 각각 기록합니다. Data Designer의 로컬 프록시 재요청은 발생 시 각 전달 시도로 계측하고 전체 upstream 8회로 제한합니다.\n\n## 해석과 한계\n\n이전 historical/dev 입력을 다시 사용한 진단·회귀 실험입니다. 사람 정답 승인 수는 0이며, 별도 호출의 model judge도 같은 모델 계열 편향을 가질 수 있습니다. 일부 실험은 합성 오류·가상 업데이트를 포함합니다. 무료 회귀, 과거 결과, 이번 새 호출을 섞지 않습니다. 병렬 실험의 벽시계 시간은 통제된 지연 성능 비교가 아닙니다.\n'
  if identifier=='L02':text+='\nF2의 축약 링크만 남은 출력은 원문 명제 누락 사례입니다. 게이트 accept를 실제 의미 보존 성공으로 보지 않습니다. native와 Python이 같은 잘못된 판정을 공유하므로 Guardrails 프레임워크 자체의 품질 우위 근거가 아닙니다.\n'
  if identifier=='L11':text+='\n초기 구버전은 21/22에서 안전하게 멈췄고, 조건부 schema와 캐시 namespace 분리 후 최초/피드백 후 모두 22/22·verifier 통과했습니다. 두 상태는 review_required 81점입니다. 제어된 H1 편집 처리 성공이며, 본문 품질 오류 자동 해결 또는 원격 PR의 인증/이벤트/수정 루프 성공은 아닙니다. #256은 계속 paused입니다.\n'
  (directory/'REPORT.md').write_text(text);reports.append(item)
 aggregate={'policy':'OpenAI direct exempt, non-OpenAI $10 unresolved/blocked','experiments':[{k:x[k] for k in ('id','title','status','usage')} for x in reports],
 'official_openai_calls':len(calls),'official_usage_estimate_known_sum':sum(x.get('estimated_usd') or 0 for x in calls),'unknown_estimate_attempts':sum(x.get('estimated_usd') is None for x in calls),'non_openai_new_paid_calls':0,'non_openai_remaining_usd':None,'historical_smoke_corrected_estimate_usd':.00355445,'human_approved':0,'proposal_15_and_additional_4_executed':False}
 save(OUT/'summary.json',aggregate)
 print(json.dumps({'statuses':{x['id']:x['status'] for x in reports},'calls':len(calls),'estimate':aggregate['official_usage_estimate_known_sum']},ensure_ascii=False))
if __name__=='__main__':main()
