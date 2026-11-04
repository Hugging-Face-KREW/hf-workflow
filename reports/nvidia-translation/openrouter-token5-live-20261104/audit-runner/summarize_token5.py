"""Final actual Qwen comparisons, explicit historical/new/provider scopes."""
from pathlib import Path
from collections import Counter,defaultdict
from decimal import Decimal
import json,hashlib
from evaluate_token5 import features
ROOT=Path('/Users/simso/Project/hf-workflow');OUT=ROOT/'reports/nvidia-translation/openrouter-token5-live-20261104';PRIOR=ROOT/'reports/nvidia-translation/official-live-20261104'
def read(p,default=None):return json.loads(p.read_text()) if p.exists() else default
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def quality(rows):return {'n':len(rows),'model_declared_usable':sum(x.get('usable',False) for x in rows),'major_error_free_and_invariant_clean':sum(x.get('major_errors',0)==0 and not x.get('code_changed') and not x.get('url_targets_changed') for x in rows),'major_errors':sum(x.get('major_errors',0) for x in rows),'minor_errors':sum(x.get('minor_errors',0) for x in rows),'code_changed':sum(bool(x.get('code_changed')) for x in rows),'url_targets_changed':sum(bool(x.get('url_targets_changed')) for x in rows)}
def main():
 ledger=read(OUT/'token-budget.json');calls=ledger['requests'];outputs=[read(p) for p in sorted((OUT/'outputs').glob('*.json'))];evals=read(OUT/'evaluations.json',[]);official=read(OUT/'official-judge/usage.json',{'calls':[]})['calls'];groups={}
 token_cost=sum(Decimal(str(r.get('raw_usage',{}).get('cost',0))) for r in calls);reserved=sum(Decimal(r['reserved_upper_usd']) for r in calls)
 usage={'upstream_attempts':len(calls),'completed':sum(r['status']=='completed' for r in calls),'inflight_or_uncertain':sum(r['status']=='reserved_uncertain' for r in calls),'response_reported_cost_usd':str(token_cost),'reserved_token_upper_usd':str(reserved),'local_conservative_limit_usd':'5','historical_separately_included_margin_usd':'.01228904','latest_user_authorized_scope':'This OpenRouter comparison execution only <=$10; past experiments excluded. Existing stricter $5 ledger retained without reset.','new_non_byok_responses':sum(r.get('raw_usage',{}).get('is_byok') is False for r in calls),'input_tokens':sum(r.get('raw_usage',{}).get('prompt_tokens',0) for r in calls),'output_tokens':sum(r.get('raw_usage',{}).get('completion_tokens',0) for r in calls),'cache_read_tokens':sum(r.get('raw_usage',{}).get('prompt_tokens_details',{}).get('cached_tokens',0) for r in calls),'cache_write_tokens':sum(r.get('raw_usage',{}).get('prompt_tokens_details',{}).get('cache_write_tokens',0) for r in calls),'reasoning_tokens':sum(r.get('raw_usage',{}).get('completion_tokens_details',{}).get('reasoning_tokens',0) for r in calls),'resolved_models':dict(Counter(r['resolved_model'] for r in outputs)),'providers':dict(Counter(r['provider'] for r in outputs)),'response_service_tiers':dict(Counter((read(p)['response'].get('service_tier') or 'not_reported') for p in (OUT/'raw').glob('*.json'))),'official_openai_evaluator_calls':len(official),'official_evaluator_estimate_usd':sum(r.get('estimated_usd') or 0 for r in official),'invoice_verified':False,'automatic_retries':0}
 for family in ['L06','L07','L08','L09']:
  rows=[r for r in outputs if r['family']==family];reviews=[r for r in evals if r['family']==family];cost=sum(Decimal(str(r.get('usage',{}).get('cost',0))) for r in rows)
  item={'family':family,'actual_new_outputs':len(rows),'status_counts':dict(Counter(r['status'] for r in rows)),'coverage_failures':{r['id']:r['coverage_failures'] for r in rows if r['coverage_failures']},'response_reported_cost_usd':str(cost),'new_quality':quality(reviews),'by_arm':{},'new_proposals_executed':False,'human_gold':0}
  for r in rows:
   rev=[v for v in reviews if v['id'].startswith(r['id']+':')];item['by_arm'][r['id']]={'cost_usd':r['usage'].get('cost'),'prompt_tokens':r['usage'].get('prompt_tokens'),'completion_tokens':r['usage'].get('completion_tokens'),'quality':quality(rev),'resolved_model':r['resolved_model'],'provider':r['provider'],'status':r['status']}
  previous={}
  if family=='L06':
   q=[]
   for p in (PRIOR/'L06').glob('*-quality.json'):
    d=read(p)
    for v in d['review']['reviews']:q.append({**v,'arm':d['lookup'][v['id']]})
   previous={a:quality([v for v in q if v['arm']==a]) for a in ['luna','rule','switchyard']}
  if family in ['L08','L09']:
   old=read(PRIOR/family/'evaluations.json',[])
   for group in sorted({r['id'].split(':')[0] for r in old}):previous[group]=quality([r for r in old if r['id'].split(':')[0]==group])
  if family=='L06':
   docs={d['id']:d for d in read(PRIOR/'L06/documents.json')};oldrows=read(PRIOR/'L06/results.json');oldusage=read(PRIOR/'usage.json')['calls'];combined=[]
   newindex={r['id']:r for r in rows};newreviews={r['id']:r for r in reviews}
   for old in oldrows:
    identifier='L06-'+old['document']+'-'+old['arm'];new=newindex.get(identifier)
    if new:
     text=new['text'];v=newreviews.get(identifier+':'+old['document'],{});amount=Decimal(str(new['usage']['cost']));basis='OpenRouter reported'
    else:
     text=old['translation'];qdoc=read(PRIOR/'L06'/(old['document']+'-quality.json'));idx=next(k for k,v in qdoc['lookup'].items() if v==old['arm']);v=next(v for v in qdoc['review']['reviews'] if v['id']==idx);amount=sum((Decimal(str(c.get('estimated_usd') or 0)) for c in oldusage if c['id']=='L06-'+old['document']+'-'+old['arm']+'-translation'),Decimal(0));basis='OpenAI usage estimate'
    a,b=features(docs[old['document']]['source']),features(text);combined.append({'document':old['document'],'arm':old['arm'],'major_errors':v.get('major_errors'),'model_usable':v.get('usable'),'code_changed':a[0]!=b[0],'url_targets_changed':a[1]!=b[1],'generation_cost_usd':str(amount),'cost_basis':basis})
   classifier=sum((Decimal(str(c.get('estimated_usd') or 0)) for c in oldusage if c['experiment']=='L06' and c['id'].endswith('-classifier')),Decimal(0))
   item['combined_four_arms']={}
   for arm in ['luna','cheap','rule','switchyard']:
    a=[r for r in combined if r['arm']==arm];combined_cost=sum((Decimal(r['generation_cost_usd']) for r in a),Decimal(0));combined_cost+=classifier if arm=='switchyard' else Decimal(0)
    item['combined_four_arms'][arm]={'n':len(a),'major_free_and_invariant_clean':sum(r['major_errors']==0 and not r['code_changed'] and not r['url_targets_changed'] for r in a),'code_changed':sum(r['code_changed'] for r in a),'url_targets_changed':sum(r['url_targets_changed'] for r in a),'generation_and_router_cost_usd':str(combined_cost),'includes_classifier_estimate':arm=='switchyard'}
   item['combined_rows']=combined
  item['earlier_openai_results_separate_evaluation']=previous
  item['representative_observations']=[{'id':v['id'],'issues':v['issues'],'major_errors':v['major_errors'],'minor_errors':v['minor_errors']} for v in reviews if v['major_errors'] or v['code_changed'] or v['url_targets_changed']][:5]
  groups[family]=item;d=OUT/family;d.mkdir(exist_ok=True);save(d/'report.json',item)
  table='| 실제 비교군 | 모델 평가 단위 | major=0·구조 보존 | major 수 | 코드/URL 손상 | 응답 비용 USD |\n|---|---:|---:|---:|---:|---:|\n'
  for arm,r in item['by_arm'].items():
   q=r['quality'];table+=f"| {arm} | {q['n']} | {q['major_error_free_and_invariant_clean']} | {q['major_errors']} | {q['code_changed']}/{q['url_targets_changed']} | {r['cost_usd']} |\n"
  if family=='L06':
   table+='\n## 기존 OpenAI 결과를 합친 네 조건\n\n| 조건 | 문서 수 | major 없음·구조 보존 | 코드/URL 위반 문서 | 생성+라우터 비용 USD |\n|---|---:|---:|---:|---:|\n'
   for arm,v in item['combined_four_arms'].items():table+=f"| {arm} | {v['n']} | {v['major_free_and_invariant_clean']} | {v['code_changed']}/{v['url_targets_changed']} | {float(v['generation_and_router_cost_usd']):.8f} |\n"
   table+='\nOpenAI는 raw usage 단가 추정, OpenRouter는 provider reported 비용이며 청구서 금액은 아닙니다. Switchyard에는 분류기 비용을 포함합니다. 평가 호출 비용은 이 비교 표에서 별도로 뺐습니다.\n'
  explanation={
   'L06':'고정 Qwen 4문서와 기존 네이티브 Switchyard가 Qwen을 선택한 2문서를 새 호출했습니다. 기존 고정 Luna 4·규칙 4·Switchyard Luna 2 결과와 합쳐 네 조건의 생성 경로가 채워집니다. 새로 라우팅하지 않았습니다. 기존 OpenAI와 새 Qwen의 모델 평가 문맥/시점이 달라 통계적·인과적 품질 우위로 해석하지 않습니다.',
   'L07':'같은 8개 입력에 baseline / plan_real / plan_dd 세 조건을 실행했습니다. plan_real은 기존 development 예시 4개와 계획, plan_dd는 여기에 이번 Data Designer 검토 통과 예시 6개를 추가합니다. Data Designer 생성 도구의 실행과 예시 연결은 확인됐지만, 예시 수·프롬프트 길이도 달라 프레임워크만의 효과를 분리한 비교는 아닙니다.',
   'L08':'기존 네이티브 라우터가 Qwen을 선택했던 5개 부분 수정 조건을 새 호출했습니다. 원래 지적·source·candidate와 출력 cap을 유지했습니다. 기존 Luna 수정 5개와 원본 5개 검토는 이전 결과로 구분합니다. 모델 usable과 major 오류가 함께 나올 수 있어 declared usable과 major=0·구조 보존을 별도로 셉니다.',
   'L09':'조건/플랫폼의 두 가상 원문 갱신에서 기존 라우터가 선택한 Qwen으로 변경 문단만 번역한 뒤 원래 재조립 규칙으로 이웃 문단을 붙였습니다. 모델 원출력과 조립 출력을 따로 보존했습니다. 2문서×3문단을 평가하며, 변경하지 않은 이웃도 포함하므로 6개를 모두 새 번역으로 세지 않습니다.'}[family]
  decision='현재 결과는 노출된 개발 입력·모델 판정에 따른 진단입니다. 사람 정답은 0입니다. 자동 운영 채택은 보류하고, 실패를 회귀 입력으로 남깁니다.'
  if family=='L06':decision+=' 평가자 계산 오류: 원문 $190 billion은 1,900억 달러입니다. 후보 190억 달러는 $19 billion으로 10배 작습니다. raw judge의 100배/19억/$1.9 billion 설명은 잘못된 산술이므로 사실로 채택하지 않습니다. raw 발언은 보존했습니다. 전체 네 조건의 기존/신규 합성 집계는 report.json의 combined_four_arms에 있습니다. 이전 OpenAI 모델평가와 새 Qwen 모델평가는 문맥/시점이 달라 동일 판정자로 통제된 비교가 아닙니다.'
  if family=='L07':decision+=' baseline/plan_real/plan_dd 모두 8/8 major 없음·구조 보존으로 천장 효과가 있습니다. minor 지적은 3/5/6건, 응답 비용은 $0.00014122/$0.00024559/$0.00031109로 이번 자료에서는 DD 추가의 품질 개선을 관찰하지 못했습니다.'
  if family=='L08':decision+=' 신규 5개 중 4개가 major 없음·구조 보존이며 첫 소개 문단에 major 1건이 남았습니다. 모델 usable=true만으로 자동 승인하지 않습니다.'
  if family=='L09':decision+=' 두 변경 문단과 네 재사용 이웃을 포함한 6개 평가 단위가 major 없음·구조 보존이었습니다. 실제 새 번역은 변경 문단 2개뿐이며 가상 변경 두 건의 진단으로 제한합니다.'
  (d/'REPORT.md').write_text(f'# {family} Qwen 실제 후속 비교\n\n**실제 새 생성 {len(rows)}개**, 보고 비용 ${cost}. 과거 11월1일 기록과 구분한 11월4일 실행입니다.\n\n'+explanation+'\n\n'+table+'\n## 대표 관찰\n\n```json\n'+json.dumps(item['representative_observations'],ensure_ascii=False,indent=2)+'\n```\n\n## 해석과 채택 판단\n\n'+decision+'\n\n[세부 집계·이전 결과 분리](report.json) · [전체 예산·정책](../README.md)\n')
 summary={'status':'actual_comparisons_completed' if len(outputs)==16 and len(evals)==41 else 'execution_or_evaluation_in_progress','usage':usage,'families':groups,'evaluation_expected_new_units':41,'evaluation_actual_new_units':len(evals),'code_url_invariant_scope':'new output units, including assembled unchanged neighbors in L09','source_scope':'Previously exposed development/diagnostic inputs; hypothetical D updates; human gold0','remote_pr256_paused':True,'merged':False,'proposal15_additional4_executed':False}
 save(OUT/'summary.json',summary);print(json.dumps({'status':summary['status'],'calls':len(calls),'cost':str(token_cost),'evaluations':len(evals)}))
if __name__=='__main__':main()
