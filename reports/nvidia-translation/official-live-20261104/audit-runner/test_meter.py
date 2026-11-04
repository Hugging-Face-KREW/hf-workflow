from pathlib import Path
import json
import pytest
from meter import Meter,BlockedProvider,usage_cost

def test_cache_write_breakdown_and_no_reasoning_double_count():
 raw={'service_tier':'default','usage':{'input_tokens':12000,'output_tokens':100,'input_tokens_details':{'cached_tokens':4000,'cache_write_tokens':7000,'cache_write_tokens_details':{'ttl_30m_tokens':3000,'ttl_12h_tokens':4000}},'output_tokens_details':{'reasoning_tokens':80}}}
 d=usage_cost(raw,'gpt-5.6-luna')
 assert d['estimated_usd']==pytest.approx(.00315)
 assert d['reasoning_tokens']==80 and d['cache_write_12h_tokens']==4000
 assert not d['cost_is_billing_confirmed']

def test_long_context_and_unknown_tier_are_not_underpriced():
 for raw in [{'service_tier':'default','usage':{'input_tokens':300000,'output_tokens':100}}, {'service_tier':'priority','usage':{'input_tokens':100,'output_tokens':10}}]:
  assert usage_cost(raw,'gpt-5.6-luna')['estimated_usd'] is None

def test_non_openai_arm_blocks_without_network(monkeypatch):
 import requests
 monkeypatch.setattr(requests,'post',lambda *a,**kw:pytest.fail('Network forbidden'))
 with pytest.raises(BlockedProvider):Meter('test').chat('blocked',{'model':'qwen/qwen3.7-flash'},'openrouter',[.2,.8])

def test_sdk_tags_are_stable_across_request_order(monkeypatch):
 import openai,meter
 original=openai.OpenAI;monkeypatch.setattr(openai,'OpenAI',original)
 monkeypatch.setattr(meter,'credentials',lambda:'unit-test-not-real')
 monkeypatch.setattr(meter.os,'environ',{})
 tags=[]
 def fake(self,tag,payload,endpoint='responses'):
  tags.append((payload['input'],tag));return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'ok'}]}]}
 monkeypatch.setattr(Meter,'request',fake)
 m=Meter('test');m.install_sdk();client=openai.OpenAI()
 for value in ['segment-a','segment-b','segment-b','segment-a']:
  assert client.responses.create(model='gpt-5.6-luna',input=value).output_text=='ok'
 assert tags[0][1]==tags[3][1] and tags[1][1]==tags[2][1] and tags[0][1]!=tags[1][1]
