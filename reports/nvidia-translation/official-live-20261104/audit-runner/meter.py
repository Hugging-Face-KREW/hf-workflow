"""Official OpenAI-only experiment transport; no SDK retries or paid fallback."""
from pathlib import Path
from urllib.parse import urlsplit
from types import SimpleNamespace
import fcntl,hashlib,json,os,tempfile,threading,time
import requests
ROOT=Path('/Users/simso/Project/hf-workflow')
OUT=ROOT/'reports/nvidia-translation/official-live-20261104'
OUT.mkdir(exist_ok=True)
LEDGER=OUT/'usage.json'
RATES={'gpt-5.6-luna':(.2,.02,1.2,1.25),'gpt-5-mini-2025-08-07':(.25,.025,2,1),'gpt-5-mini':(.25,.025,2,1),'gpt-5-nano':(.05,.005,.4,1)}
LOCK=threading.RLock()
SEM=threading.BoundedSemaphore(3)

def save(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',dir=path.parent,delete=False) as f:
  json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(f.name,path)

def sha(text):return hashlib.sha256(text.encode()).hexdigest()

def credentials():
 e=dict(x.split('=',1) for x in (ROOT/'experiments/nvidia_translation/.env').read_text().splitlines() if '=' in x and not x.startswith('#'))
 u=urlsplit(e.get('OPENAI_BASE_URL','https://api.openai.com/v1'))
 if u.scheme!='https' or u.hostname!='api.openai.com' or u.username or u.password or u.query or u.fragment or u.path.rstrip('/')!='/v1':raise RuntimeError('Official OpenAI direct endpoint required')
 return e['OPENAI_API_KEY']

def mutate(fn):
 with LOCK, (OUT/'usage.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  data=json.loads(LEDGER.read_text()) if LEDGER.exists() else {'policy':'OpenAI direct excluded from $10; non-OpenAI blocked','max_actual_attempts':1200,'calls':[]}
  result=fn(data);save(LEDGER,data);return result

def usage_cost(raw,requested):
 u=raw.get('usage') or {};i=u.get('input_tokens',u.get('prompt_tokens'));o=u.get('output_tokens',u.get('completion_tokens'))
 details=u.get('input_tokens_details',u.get('prompt_tokens_details',{})) or {}
 od=u.get('output_tokens_details',u.get('completion_tokens_details',{})) or {}
 cache=details.get('cached_tokens',0);write=details.get('cache_write_tokens',0)
 td=details.get('cache_write_tokens_details') or {};w12=td.get('ttl_12h_tokens',0);w30=td.get('ttl_30m_tokens',write-w12)
 tier=raw.get('service_tier');estimate=None
 long_context_unpriced=requested.startswith('gpt-5.6') and i is not None and i>272000
 if not long_context_unpriced and requested in RATES and i is not None and o is not None and tier in (None,'default') and cache+write<=i and w12+w30==write:
  a,c,b,m=RATES[requested]
  estimate=((i-cache-write)*a+cache*c+w30*a*m+w12*a*(2.5 if requested.startswith('gpt-5.6') else 1)+o*b)/1e6
 return {'input_tokens':i,'output_tokens':o,'cache_read_tokens':cache,'cache_write_tokens':write,'cache_write_30m_tokens':w30,'cache_write_12h_tokens':w12,'reasoning_tokens':od.get('reasoning_tokens'),'service_tier':tier,'estimated_usd':estimate,'provider_reported_cost_usd':u.get('cost'),'raw_usage':u,'cost_is_billing_confirmed':False,'estimate_limitation':'long-context tier unpriced' if long_context_unpriced else None}

class BlockedProvider(RuntimeError):pass

class Meter:
 def __init__(self,experiment):self.experiment=experiment;self.count=0
 def request(self,tag,payload,endpoint='responses'):
  if endpoint not in ('responses','chat/completions'):raise RuntimeError('Unsupported endpoint')
  payload=dict(payload);payload.pop('timeout',None)
  model=payload['model']
  if model not in RATES:raise BlockedProvider('Unapproved or non-OpenAI model: '+model)
  payload['service_tier']='default'
  if endpoint=='responses':payload['store']=False
  encoded=json.dumps(payload,ensure_ascii=False,sort_keys=True)
  if len(encoded.encode())>350000:raise RuntimeError('Input bound exceeded')
  cap=payload.get('max_output_tokens',payload.get('max_completion_tokens',payload.get('max_tokens')))
  if not isinstance(cap,int) or not 1<=cap<=16384:raise RuntimeError('Explicit bounded output required')
  identifier=self.experiment+'-'+tag
  key=sha(identifier);path=OUT/'calls'/self.experiment/(key+'.json')
  fingerprint=sha(endpoint+encoded)
  if path.exists():
   cached=json.loads(path.read_text())
   if cached['request_sha256']!=fingerprint:raise RuntimeError('Frozen request changed')
   if cached.get('completed') is not True:raise RuntimeError('Uncertain prior attempt; manual audit required')
   return cached['response']
  api_key=credentials() # validate destination before reservation, never persist key
  def reserve(d):
   if len(d['calls'])>=d['max_actual_attempts']:raise RuntimeError('Bounded run call count exhausted')
   if any(x['id']==identifier for x in d['calls']):raise RuntimeError('Duplicate/uncertain request id; no retry')
   d['calls'].append({'id':identifier,'experiment':self.experiment,'requested_model':model,'api_host':'api.openai.com','endpoint':endpoint,'request_sha256':fingerprint,'status':'started','attempt':1,'sdk_retries':0,'started_at':time.time()})
  mutate(reserve)
  started=time.monotonic()
  try:
   with SEM:
    response=requests.post('https://api.openai.com/v1/'+endpoint,headers={'Authorization':'Bearer '+api_key,'Content-Type':'application/json'},json=payload,timeout=120,allow_redirects=False)
  except requests.RequestException:
   def failed(d):next(x for x in d['calls'] if x['id']==identifier).update(status='network_error_usage_unknown',elapsed_seconds=time.monotonic()-started)
   mutate(failed);raise RuntimeError('Network failure; no automatic retry') from None
  raw=response.json()
  if endpoint=='responses':completed=raw.get('status')=='completed'
  else:completed=(raw.get('choices') or [{}])[0].get('finish_reason')=='stop'
  completed=completed and response.status_code==200
  record={'id':identifier,'request_sha256':fingerprint,'request':payload,'http_status':response.status_code,'response':raw,'completed':completed}
  save(path,record)
  observed=usage_cost(raw,model)
  def done(d):next(x for x in d['calls'] if x['id']==identifier).update(status='completed' if completed else 'error_or_incomplete',http_status=response.status_code,resolved_model=raw.get('model'),response_id=raw.get('id'),elapsed_seconds=time.monotonic()-started,**observed)
  mutate(done)
  if not completed:raise RuntimeError(f"OpenAI request failed/incomplete: HTTP {response.status_code}; no retry")
  print(self.experiment,tag,'completed',flush=True)
  return raw
 def response(self,tag,prompt,shape=None,max_tokens=2048,model='gpt-5-mini-2025-08-07'):
  p={'model':model,'input':prompt,'reasoning':{'effort':'low'},'max_output_tokens':max_tokens}
  if shape:p['text']={'format':{'type':'json_schema','name':'translation_result','strict':True,'schema':shape}}
  raw=self.request(tag,p)
  text=''.join(c['text'] for item in raw.get('output',[]) if item.get('type')=='message' for c in item.get('content',[]) if c.get('type')=='output_text')
  if not text.strip():raise RuntimeError('Empty response')
  return json.loads(text) if shape else text
 def chat(self,tag,payload,provider='openai',rates=None,compat_dir=None):
  if provider!='openai':raise BlockedProvider('Non-OpenAI arm blocked; no model substitution')
  raw=self.request(tag,payload,'chat/completions')
  if compat_dir is not None:save(Path(compat_dir)/'live'/(tag+'-raw.json'),{'request':payload,'response':raw})
  return raw['choices'][0]['message']['content']
 def install_sdk(self):
  import openai
  meter=self
  def factory(*args,**kwargs):
   if kwargs.get('base_url') and urlsplit(str(kwargs['base_url'])).hostname!='api.openai.com':raise BlockedProvider('SDK base_url not official OpenAI')
   def create(**payload):
    payload.setdefault('max_output_tokens',8000)
    payload.setdefault('reasoning',{'effort':'low'})
    stable={k:v for k,v in payload.items() if k!='timeout'}
    key=sha(json.dumps(stable,sort_keys=True,ensure_ascii=False))[:32]
    raw=meter.request('sdk-'+key,payload)
    text=''.join(c['text'] for item in raw.get('output',[]) if item.get('type')=='message' for c in item.get('content',[]) if c.get('type')=='output_text')
    return SimpleNamespace(output_text=text,status=raw.get('status'),incomplete_details=raw.get('incomplete_details'),model_dump=lambda **kw:raw)
   return SimpleNamespace(responses=SimpleNamespace(create=create))
  openai.OpenAI=factory
  os.environ['OPENAI_API_KEY']=credentials()
  os.environ['OPENAI_BASE_URL']='https://api.openai.com/v1'
