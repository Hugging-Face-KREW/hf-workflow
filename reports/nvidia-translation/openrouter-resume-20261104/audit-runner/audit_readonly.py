"""Read-only billing evidence, never log credentials or full account metadata."""
from pathlib import Path
import json,os,sys,time
import requests
ROOT=Path('/Users/simso/Project/hf-workflow')
OUT=ROOT/'reports/nvidia-translation/openrouter-resume-20261104'
OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'experiments/nvidia_translation/switchyard_prep'))
from transport import credentials

def get(path,params=None):
 try:
  r=requests.get('https://openrouter.ai/api/v1/'+path,params=params,headers={'Authorization':'Bearer '+credentials('openrouter')},timeout=30,allow_redirects=False)
 except requests.RequestException: return {'http_status':None,'error':'network_failure'}
 if r.status_code!=200:return {'http_status':r.status_code}
 try:return {'http_status':200,'data':r.json().get('data',{})}
 except ValueError:return {'http_status':200,'error':'invalid_json'}

def main():
 key=get('key');d=key.get('data',{})
 # Only nonidentifying necessary numeric fields stored privately; no label/key/hash/organization/user IDs.
 allowed=['usage','usage_daily','usage_weekly','usage_monthly','byok_usage','limit','limit_remaining','limit_reset','include_byok_in_limit']
 private={'queried_at_unix':time.time(),'http_status':key['http_status'],'fields':{k:d[k] for k in allowed if k in d}}
 if isinstance(d.get('effective_budget'),dict):private['effective_budget']={k:d['effective_budget'].get(k) for k in ['limit_usd','remaining_usd','spend_usd','reset_interval','include_byok','scope']}
 else:private['effective_budget']=d.get('effective_budget')
 pp=Path('/private/tmp/hf-openrouter-account-audit-20261104.json')
 fd=os.open(pp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
 with os.fdopen(fd,'w') as f:json.dump(private,f,indent=2)
 if key['http_status']!=200:
  result={'key_query_http_status':key['http_status'],'paid_calls':0,'budget_guaranteed':False,'reason':'Current key read-only query unavailable; no management or alternate credential access attempted.'}
 else:
  records=[]
  for p in sorted((ROOT/'reports/nvidia-translation/switchyard-prep').rglob('*-raw.json')):
   raw=json.loads(p.read_text()).get('response',{});identifier=raw.get('id','')
   if not identifier.startswith('gen-'):continue
   got=get('generation',{'id':identifier});g=got.get('data',{})
   records.append({'local_evidence':str(p.relative_to(ROOT)),'generation_id':identifier,'http_status':got['http_status'],'local_reported_cost':raw.get('usage',{}).get('cost'),'verified':{k:g.get(k) for k in ['id','created_at','model','provider_name','total_cost','is_byok','tokens_prompt','tokens_completion','native_tokens_prompt','native_tokens_completion','native_tokens_cached','upstream_inference_cost','usage']} if got['http_status']==200 else None})
  result={'key_query_http_status':200,'key_usage_fields_available':[k for k in allowed if k in d],'key_limit_remaining_present': 'limit_remaining' in d,'effective_budget_present':'effective_budget' in d,'historical_generations':records,'generation_queries':len(records),'generation_queries_verified':sum(x['http_status']==200 for x in records),'historical_verified_total_cost':sum(x['verified'].get('total_cost') or 0 for x in records if x['verified']),'account_attribution_scope':'Successful generation lookup proves accessible with this existing key; does not establish all account charges, additional experiment-attributable charges, upstream BYOK billing or credit purchase fees.','private_numeric_snapshot':'Stored outside repo with mode 0600; no account balances or key labels in public output.','paid_calls':0,'budget_guaranteed':False,'reason':'Read-only key/generation endpoints do not prove total experiment-attributable non-OpenAI historical costs and purchase fees. No management key or billing changes attempted.'}
 (OUT/'readonly-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ['key_query_http_status','paid_calls','budget_guaranteed']}|{'generation_queries':result.get('generation_queries',0),'verified':result.get('generation_queries_verified',0)}))
if __name__=='__main__':main()
