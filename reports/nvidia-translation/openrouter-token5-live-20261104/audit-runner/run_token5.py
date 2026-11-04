"""Explicit one-pilot then bounded remaining 15 Qwen arms; latest user token cap."""
from pathlib import Path
from decimal import Decimal
import argparse,copy,hashlib,json,sys,time
from budget import Ledger,quote,Blocked
from transport import RouterMeter
ROOT=Path('/Users/simso/Project/hf-workflow');PREP=ROOT/'reports/nvidia-translation/openrouter-resume-20261104';PRIOR=ROOT/'reports/nvidia-translation/official-live-20261104';OUT=ROOT/'reports/nvidia-translation/openrouter-token5-live-20261104'
OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'experiments/nvidia_translation/switchyard_prep'))
# Import existing credentials helper explicitly, avoiding same-name transport.
import importlib.util
spec=importlib.util.spec_from_file_location('legacy_or_credentials',ROOT/'experiments/nvidia_translation/switchyard_prep/transport.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)

def save(p,d):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def build():
 plan=json.loads((PREP/'prepared-arms.json').read_text());contract=json.loads((PREP/'provider-contract.json').read_text());contract.update(verified_price_and_token_bounds=True,token_only_scope_authorized=True,request_fee_upper_usd='0',ancillary_fee_upper_usd='0',reasoning_in_output_cap=True,status='Token-only cap authorized by direct user; known catalog token bounds and provider price/ignore contract pinned; account compatibility tested by bounded pilot',fee_note='Purchase/processing/BYOK platform fees excluded from latest user token-only budget; max_price.request=0 prevents priced request surcharge; not a statement fees globally zero.',reasoning_source='https://openrouter.ai/docs/guides/best-practices/reasoning-tokens')
 total=Decimal(0)
 for r in plan['arms']:
  p=r['payload'];p['provider']={'only':['alibaba'],'ignore':['alibaba/us-east-1'],'allow_fallbacks':False,'require_parameters':True,'max_price':{'prompt':.2,'completion':.8,'request':0.0,'image':0}}
  r['reserved_token_upper_usd']=str(quote(p,contract));total+=Decimal(r['reserved_token_upper_usd'])
 assert total+Decimal('.01228904')<=5
 save(OUT/'provider-contract.json',contract);save(OUT/'execution-plan.json',{'policy':'Latest direct user: token costs at most $5; credit purchase fees excluded. Official OpenAI direct still exempt.','run_id':OUT.name,'historical_openrouter_token_cost_included_usd':'.01228904','planned_calls':16,'planned_token_upper_usd':str(total),'with_historical_upper_usd':str(total+Decimal('.01228904')),'automatic_retries':0,'no_new_proposals':True,'arms':plan['arms']})
 ledger=Ledger(OUT/'token-budget.json')
 if not ledger.path.exists():ledger.initialize({'policy':'user_20261104_token_only_5usd','reconciled_experiment_token_history':True,'local_runner_scope_controlled':True,'historical_upper_usd':'.01228904','historical_scope':'26 OpenRouter generations Nov1; current key usage matches. Remote prior jobs configured official OpenAI; unrelated spending outside scope.','fees_excluded_by_latest_user':True},'5')
 def sink(identifier,d):save(OUT/'raw'/(identifier+'.json'),d)
 return plan,RouterMeter(ledger,contract,lambda:legacy.credentials('openrouter'),sink)

def execute(row,meter):
 identifier=OUT.name+'-'+row['id'];path=OUT/'outputs'/(row['id']+'.json')
 if path.exists():return json.loads(path.read_text())
 response=meter.chat(identifier,row['payload']);text=response['text'];parsed=None;coverage=[]
 if row['family']!='L06':
  try:parsed=json.loads(text)
  except ValueError:coverage=['invalid_json']
  if parsed is not None:
   if not isinstance(parsed,dict) or not isinstance(parsed.get('translations'),list):coverage=['missing_translations']
   else:
    if row['family']=='L07':expected=set(row['expected_ids'])
    elif row['family']=='L08':expected={Path(row['frozen_blocked_output']).stem.removeprefix('C-switchyard-')}
    else:
     scenario=Path(row['frozen_blocked_output']).stem.split('-')[1];dinput=json.loads((PRIOR/'L09'/f'D-input-{scenario}.json').read_text());expected={dinput['changed_id']}
    actual=[x.get('id') for x in parsed['translations']]
    if len(actual)!=len(expected) or set(actual)!=expected:coverage=['id_coverage_or_duplicates']
    if any(not isinstance(x.get('text'),str) or not x['text'].strip() for x in parsed['translations']):coverage.append('empty_or_nonstring_translation')
    if row['family']=='L09' and not coverage:
     original_model_output=copy.deepcopy(parsed);new={x['id']:x['text'] for x in parsed['translations']};old={x['id']:x['target'] for x in dinput['old']}
     parsed['translations']=[{'id':x['id'],'text':new[x['id']] if x['id']==dinput['changed_id'] else old[x['id']]} for x in dinput['sources']]
     save(OUT/'L09'/f'D-input-{scenario}.json',dinput);save(OUT/'L09'/(row['id']+'-preassembly.json'),original_model_output)
 result={'id':row['id'],'family':row['family'],'status':'completed' if not coverage else 'invalid_output','requested_model':row['payload']['model'],'resolved_model':response['raw']['model'],'provider':response['raw'].get('provider'),'usage':response['raw'].get('usage'),'request_sha256':response['request_sha256'],'reserved_upper_usd':response['reserved_upper_usd'],'text':text,'result':parsed,'coverage_failures':coverage,'routing_reused':row.get('frozen_routing',row.get('routing_decision')),'human_approved':False}
 save(path,result);print(row['id'],result['status'],flush=True);return result

def main():
 args=argparse.ArgumentParser();args.add_argument('phase',choices=['prepare','pilot','remaining']);a=args.parse_args();plan,meter=build();arms=plan['arms'];pilot=next(r for r in arms if r['family']=='L08')
 if a.phase=='prepare':print('Prepared token upper',sum(Decimal(r['reserved_token_upper_usd']) for r in arms));return
 if a.phase=='pilot':
  r=execute(pilot,meter);save(OUT/'pilot.json',{'id':r['id'],'completed':r['status']=='completed','usage':r['usage'],'resolved_model':r['resolved_model'],'provider':r['provider'],'coverage_failures':r['coverage_failures'],'approved_to_continue':False});return
 proof=json.loads((OUT/'pilot.json').read_text())
 if proof.get('approved_to_continue') is not True:raise Blocked('Pilot must be reviewed before remaining calls')
 for row in arms:execute(row,meter)
 save(OUT/'execution-complete.json',{'planned':16,'outputs':len(list((OUT/'outputs').glob('*.json'))),'paid_upstream_attempts':len(json.loads(meter.ledger.path.read_text())['requests']),'automatic_retries':0})
if __name__=='__main__':main()
