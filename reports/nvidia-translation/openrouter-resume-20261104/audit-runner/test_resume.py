import copy,json,multiprocessing
from pathlib import Path
from decimal import Decimal
import pytest
from budget import Ledger,Blocked,quote
from transport import RouterMeter

EVIDENCE={'reconciled_experiment_non_openai_history_and_fees':True,'local_runner_scope_controlled':True,'historical_upper_usd':'8'}
CONTRACT={'verified_price_and_token_bounds':True,'allowed_response_models':['qwen/qwen3.7-flash','qwen/qwen3.7-flash-20260727'],'context_token_upper':262144,'provider_slug':'qwen','response_provider_name':'Qwen','prompt_usd_per_million':'.2','completion_usd_per_million':'.8','cache_read_usd_per_million':'.2','cache_write_usd_per_million':'.2','request_fee_upper_usd':'0','ancillary_fee_upper_usd':'.01','reasoning_in_output_cap':True,'byok_disabled_confirmed':True}
PAYLOAD={'model':'qwen/qwen3.7-flash','messages':[{'role':'user','content':'Read the [dataset card](https://example.org).'}],'max_tokens':2500,'reasoning':{'enabled':False},'provider':{'only':['qwen'],'allow_fallbacks':False,'require_parameters':True,'max_price':{'prompt':.2,'completion':.8,'request':0.0,'image':0}}}

def ledger(tmp_path,evidence=None):
 l=Ledger(tmp_path/'ledger.json');l.initialize(evidence or EVIDENCE);return l

def test_unknown_history_blocks_before_credential_or_network(tmp_path,monkeypatch):
 l=ledger(tmp_path,{'reconciled_experiment_non_openai_history_and_fees':False})
 def forbidden(*a,**k):pytest.fail('No credential or network access permitted')
 import requests
 monkeypatch.setattr(requests,'post',forbidden)
 m=RouterMeter(l,CONTRACT,forbidden)
 with pytest.raises(Blocked,match='historical'):m.chat('no-call',PAYLOAD)
 assert json.loads(l.path.read_text())['requests']==[]

@pytest.mark.parametrize('value',['NaN','Infinity','-1',None,True])
def test_invalid_history_cannot_enable_calls(tmp_path,value):
 e={**EVIDENCE,'historical_upper_usd':value};l=ledger(tmp_path,e)
 with pytest.raises(Blocked):l.reserve('a','hash','.1')

def test_budget_boundary_duplicate_and_no_reset(tmp_path):
 l=ledger(tmp_path);l.reserve('a','hash','2')
 with pytest.raises(Blocked):l.reserve('b','hash','.000000001')
 with pytest.raises(Blocked):l.reserve('a','different','.1')
 with pytest.raises(Blocked):l.initialize(EVIDENCE)
 l.finish('a',{'cost':'.01'},True)
 with pytest.raises(Blocked):l.reserve('b','hash','.01') # no automatic release

@pytest.mark.parametrize('failure',['timeout','invalid_json','http'])
def test_failed_call_keeps_full_reservation_and_retry_blocked(tmp_path,monkeypatch,failure):
 import requests
 l=ledger(tmp_path)
 def post(*a,**kw):
  assert a[0]=='https://openrouter.ai/api/v1/chat/completions'
  assert kw['allow_redirects'] is False
  if failure=='timeout':raise requests.Timeout()
  class R:
   status_code=503
   def json(self):
    if failure=='invalid_json':raise ValueError()
    return {'error':{'code':503}}
  return R()
 monkeypatch.setattr(requests,'post',post);m=RouterMeter(l,CONTRACT,lambda:'unit-test-not-a-key')
 with pytest.raises(Blocked):m.chat('a',PAYLOAD)
 d=json.loads(l.path.read_text());assert d['requests'][0]['status']=='failed_reservation_retained';assert Decimal(d['requests'][0]['reserved_upper_usd'])==quote(PAYLOAD,CONTRACT)
 with pytest.raises(Blocked,match='Duplicate'):m.chat('a',PAYLOAD)
 assert len(json.loads(l.path.read_text())['requests'])==1

@pytest.mark.parametrize('mutation',[{'model':'other'},{'max_tokens':None},{'max_tokens':65536},{'tools':[]},{'provider':{'allow_fallbacks':True}},{'messages':[{'role':'user','content':[{'type':'image_url'}]}]},{'reasoning':{'enabled':True}}])
def test_unpriced_request_or_changed_model_rejected(mutation):
 with pytest.raises(Blocked):quote({**PAYLOAD,**mutation},CONTRACT)

@pytest.mark.parametrize('field',['verified_price_and_token_bounds','reasoning_in_output_cap','byok_disabled_confirmed'])
def test_unknown_contract_blocks(field):
 with pytest.raises(Blocked):quote(PAYLOAD,{**CONTRACT,field:False})

def test_full_context_and_cache_write_upper_used():
 c={**CONTRACT,'cache_write_usd_per_million':'.5'}
 assert quote(PAYLOAD,c)==Decimal('262144')*Decimal('.5')/1000000+Decimal('2500')*Decimal('.8')/1000000+Decimal('.01')

def reserve_child(path,i):
 try:Ledger(path).reserve(str(i),'hash','.1')
 except Blocked:pass

def test_parallel_processes_cannot_overspend(tmp_path):
 l=ledger(tmp_path);ctx=multiprocessing.get_context('fork')
 workers=[ctx.Process(target=reserve_child,args=(str(l.path),i)) for i in range(30)]
 for w in workers:w.start()
 for w in workers:w.join(10);assert w.exitcode==0
 d=json.loads(l.path.read_text());assert len(d['requests'])==20
 assert len({r['id'] for r in d['requests']})==20
 assert sum(Decimal(r['reserved_upper_usd']) for r in d['requests'])+Decimal('8')==Decimal('10')

def test_bound_breach_disables_new_calls(tmp_path):
 l=ledger(tmp_path);l.reserve('a','h','.1')
 with pytest.raises(Blocked):l.finish('a',{'cost':'.2'},True)
 with pytest.raises(Blocked,match='historical'):l.reserve('b','h','.1')

def test_l07_uses_new_six_examples_and_preserves_arms(monkeypatch):
 import prepare
 monkeypatch.setattr(prepare,'save',lambda *a:None)
 rows=prepare.b_prompts();assert len(rows)==3
 dd=next(x for x in rows if x['id'].endswith('plan_dd'))
 examples=json.loads((prepare.PRIOR/'L07/dd-reviewed.json').read_text());accepted=[x for x in examples if x['usable']]
 for r in accepted:assert json.dumps(r['example'],ensure_ascii=False) in dd['prompt']
 assert 'Additional reviewed synthetic examples:' not in rows[0]['prompt']
 assert 'Additional reviewed synthetic examples:' not in rows[1]['prompt']
 assert len(accepted)==6 and len(dd['expected_ids'])==len(set(dd['expected_ids']))

@pytest.mark.parametrize('model,provider,expected',[('qwen/qwen3.7-flash','Qwen',True),('qwen/qwen3.7-flash-20260727','Qwen',True),('other','Qwen',False),('qwen/qwen3.7-flash','other',False)])
def test_actual_response_identity_and_usage_checked(tmp_path,monkeypatch,model,provider,expected):
 import requests
 l=ledger(tmp_path)
 class R:
  status_code=200
  def json(self):return {'model':model,'provider':provider,'usage':{'cost':.0001,'prompt_tokens':10,'completion_tokens':3},'choices':[{'finish_reason':'stop','message':{'content':'translated'}}]}
 monkeypatch.setattr(requests,'post',lambda *a,**kw:R())
 m=RouterMeter(l,CONTRACT,lambda:'unit-test-not-a-key')
 if expected:assert m.chat('a',PAYLOAD)['text']=='translated'
 else:
  with pytest.raises(Blocked):m.chat('a',PAYLOAD)
 r=json.loads(l.path.read_text())['requests'][0];assert (r['status']=='completed')==expected
 assert r['raw_usage']['cost']==.0001 and Decimal(r['reserved_upper_usd'])>0

def test_full_preparation_freezes_only_previously_blocked_arms(tmp_path,monkeypatch):
 import prepare
 monkeypatch.setattr(prepare,'OUT',tmp_path)
 prepare.main()
 d=json.loads((tmp_path/'prepared-arms.json').read_text())
 assert d['counts']=={'L06':6,'L07':3,'L08':5,'L09':2}
 assert len({r['id'] for r in d['arms']})==16
 assert all(r['payload']['model']=='qwen/qwen3.7-flash' and r['status']=='prepared_not_sent' for r in d['arms'])
 assert all(r['payload']['max_tokens']==16384 for r in d['arms'] if r['family']=='L06')
 assert d['paid_calls']==0
