"""Official OpenRouter-only route; separate ledger; no redirects/retries/fallback."""
import hashlib,json
import requests
from budget import Ledger,Blocked,quote
URL='https://openrouter.ai/api/v1/chat/completions'
class RouterMeter:
 def __init__(self,ledger,contract,credential):self.ledger=ledger;self.contract=contract;self.credential=credential
 def chat(self,identifier,payload,provider='openrouter',rates=None):
  if provider!='openrouter':raise Blocked('Dedicated OpenRouter route only')
  upper=quote(payload,self.contract)
  fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
  self.ledger.reserve(identifier,fingerprint,upper)
  try:
   r=requests.post(URL,headers={'Authorization':'Bearer '+self.credential()},json=payload,timeout=120,allow_redirects=False)
   data=r.json()
  except (requests.RequestException,ValueError):
   self.ledger.finish(identifier,{},False);raise Blocked('Uncertain response; reservation retained, no retry') from None
  choice=(data.get('choices') or [{}])[0];text=choice.get('message',{}).get('content')
  identity_ok=data.get('model') in self.contract['allowed_response_models'] and data.get('provider')==self.contract['response_provider_name']
  complete=identity_ok and isinstance(data.get('usage'),dict) and data['usage'].get('cost') is not None and r.status_code==200 and choice.get('finish_reason')=='stop' and isinstance(text,str) and bool(text.strip())
  self.ledger.finish(identifier,data.get('usage',{}),complete)
  if not complete:raise Blocked('Failed/incomplete response; reservation retained')
  return {'text':text,'raw':data,'request':payload,'request_sha256':fingerprint,'reserved_upper_usd':str(upper)}
