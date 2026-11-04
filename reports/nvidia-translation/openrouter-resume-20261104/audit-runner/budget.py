"""Separate local non-OpenAI ledger. Unknown history/prices => fail closed.

This is not an account-wide distributed budget or billing attestation service.
The production evidence file remains unapproved; fixtures are not approvals.
"""
from contextlib import contextmanager
from decimal import Decimal,InvalidOperation
from pathlib import Path
import fcntl,hashlib,json,os,tempfile,threading
LIMIT=Decimal('10')
LOCK=threading.RLock()
class Blocked(RuntimeError):pass

def money(value):
 if isinstance(value,bool):raise Blocked('Invalid monetary bound')
 try:d=Decimal(str(value))
 except InvalidOperation:raise Blocked('Missing monetary bound') from None
 if not d.is_finite() or d<0:raise Blocked('Nonnegative finite bound required')
 return d

def write(path,data):
 path=Path(path)
 with tempfile.NamedTemporaryFile('w',dir=path.parent,delete=False) as f:
  json.dump(data,f,indent=2);f.flush();os.fsync(f.fileno());temp=f.name
 os.replace(temp,path)

class Ledger:
 def __init__(self,path):self.path=Path(path)
 @contextmanager
 def transaction(self):
  self.path.parent.mkdir(parents=True,exist_ok=True)
  with LOCK,self.path.with_suffix('.lock').open('a') as f:
   fcntl.flock(f,fcntl.LOCK_EX)
   d=json.loads(self.path.read_text()) if self.path.exists() else None
   yield d
   if d is not None:write(self.path,d)
 def initialize(self,evidence):
  self.path.parent.mkdir(parents=True,exist_ok=True)
  with LOCK,self.path.with_suffix('.lock').open('a') as f:
   fcntl.flock(f,fcntl.LOCK_EX)
   if self.path.exists():raise Blocked('Existing ledger cannot be reset')
   # Evidence supplied by a separately reviewed reconciliation; never infer it
   # from balance, key usage, or an incomplete local mixed-provider ledger.
   write(self.path,{'limit_usd':'10','evidence':evidence,'requests':[]})
 def reserve(self,identifier,fingerprint,upper):
  upper=money(upper)
  if not identifier or upper==0:raise Blocked('Explicit nonzero reservation and ID required')
  with self.transaction() as d:
   if d is None:raise Blocked('Ledger not initialized')
   e=d['evidence']
   if e.get('reconciled_experiment_non_openai_history_and_fees') is not True or e.get('local_runner_scope_controlled') is not True:
    raise Blocked('Experiment historical costs/fees or local runner scope unresolved')
   historical=money(e.get('historical_upper_usd'))
   if any(r['id']==identifier for r in d['requests']):raise Blocked('Duplicate ID; no retry of uncertain call')
   committed=sum((money(r['reserved_upper_usd']) for r in d['requests']),Decimal(0))
   if historical+committed+upper>LIMIT:raise Blocked('Non-OpenAI total budget exhausted')
   d['requests'].append({'id':identifier,'request_sha256':fingerprint,'reserved_upper_usd':str(upper),'status':'reserved_uncertain','attempt':1,'automatic_retries':0})
 def finish(self,identifier,raw_usage,complete):
  # Keep full reservation even on success, error, invalid JSON or timeout.
  with self.transaction() as d:
   r=next(x for x in d['requests'] if x['id']==identifier)
   if r['status']!='reserved_uncertain':raise Blocked('Duplicate settlement')
   r.update(status='completed' if complete else 'failed_reservation_retained',raw_usage=raw_usage)
   cost=raw_usage.get('cost') if isinstance(raw_usage,dict) else None
   if cost is not None and money(cost)>money(r['reserved_upper_usd']):
    d['evidence']['reconciled_experiment_non_openai_history_and_fees']=False
    r['status']='bound_breach_stop'
    write(self.path,d)
    raise Blocked('Provider cost exceeded reservation; stop all calls')

def quote(payload,contract):
 if payload.get('model')!='qwen/qwen3.7-flash':raise Blocked('Only fixed Qwen comparison model allowed')
 if not contract.get('allowed_response_models') or not set(contract['allowed_response_models']) <= {'qwen/qwen3.7-flash','qwen/qwen3.7-flash-20260727'}:raise Blocked('Verified alias/canonical allowlist required')
 if contract.get('verified_price_and_token_bounds') is not True:raise Blocked('Provider price/token/cache/fee upper bounds unverified')
 if set(payload)-{'model','messages','max_tokens','response_format','reasoning','provider','temperature','seed'}:raise Blocked('Unpriced request features')
 messages=payload.get('messages',[])
 if not messages or any(set(m)!={'role','content'} or m['role'] not in ('system','user','assistant') or not isinstance(m['content'],str) for m in messages):raise Blocked('Only plain text messages allowed')
 cap=payload.get('max_tokens');context=contract.get('context_token_upper')
 if isinstance(cap,bool) or not isinstance(cap,int) or not 1<=cap<=16384:raise Blocked('Explicit output cap required')
 if isinstance(context,bool) or not isinstance(context,int) or not cap<=context<=2000000:raise Blocked('Verified context token ceiling required')
 if len(json.dumps(messages,ensure_ascii=False).encode())>350000:raise Blocked('Input byte bound exceeded')
 provider=contract.get('provider_slug')
 if not isinstance(provider,str) or not provider or not contract.get('response_provider_name'):raise Blocked('Pinned provider and response identity required')
 pmax=money(contract.get('prompt_usd_per_million'));omax=money(contract.get('completion_usd_per_million'))
 if pmax>Decimal('.2') or omax>Decimal('.8'):raise Blocked('Original price ceilings exceeded')
 # Full context charged at worst of uncached/read/write rates; no savings assumed.
 rates=[pmax,money(contract.get('cache_read_usd_per_million')),money(contract.get('cache_write_usd_per_million'))]
 request=money(contract.get('request_fee_upper_usd'));ancillary=money(contract.get('ancillary_fee_upper_usd'))
 provider_options={'only':[provider],'allow_fallbacks':False,'require_parameters':True,'max_price':{'prompt':float(pmax),'completion':float(omax),'request':float(request),'image':0}}
 if contract.get('provider_ignore'):provider_options['ignore']=contract['provider_ignore']
 if payload.get('provider')!=provider_options:raise Blocked('Provider pin/price cap/fallback contract mismatch')
 if payload.get('reasoning')!={'enabled':False}:raise Blocked('Reasoning configuration changed')
 # Reasoning must be included in enforced output cap, otherwise contract unverified.
 if contract.get('reasoning_in_output_cap') is not True or contract.get('byok_disabled_confirmed') is not True:raise Blocked('Reasoning/BYOK cost scope unverified')
 return (context*max(rates)+cap*omax)/Decimal(1000000)+request+ancillary
