"""Freeze only 16 previously blocked Qwen arms; no API calls on preparation."""
from pathlib import Path
import ast,hashlib,json,sys,io
from contextlib import redirect_stdout
ROOT=Path('/Users/simso/Project/hf-workflow')
BASE=ROOT/'experiments/nvidia_translation';PRIOR=ROOT/'reports/nvidia-translation/official-live-20261104'
OUT=ROOT/'reports/nvidia-translation/openrouter-resume-20261104';OUT.mkdir(parents=True,exist_ok=True)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,data):Path(p).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def b_prompts():
 source=BASE/'workflow_pilot/run_bcd_v2.py';tree=ast.parse(source.read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='b')
 text=ast.get_source_segment(source.read_text(),fn)
 # Redirect precisely the historical OUT.parent default to the newly reviewed examples.
 original="(OUT.parent/'dd-reviewed.json')"
 assert original in text
 text=text.replace(original,'EXAMPLES')
 labels=json.loads((ROOT/'reports/nvidia-translation/pr-label-review/labels-final.json').read_text())
 held=[r for r in labels if r['split']=='heldout' and r['eligible_for_pilot']];dev=[r for r in labels if r['split']=='development' and r['eligible_for_pilot']]
 examples=PRIOR/'L07/dd-reviewed.json';reviewed=json.loads(examples.read_text());assert len(reviewed)==8 and sum(x['usable'] for x in reviewed)==6
 captured=[]
 def invoke(tag,prompt):captured.append({'id':tag,'family':'L07','prompt':prompt,'max_tokens':6500,'expected_ids':[r['id'] for r in held]});return {'prepared_only':True}
 scope={'json':json,'OUT':OUT,'EXAMPLES':examples,'dev':dev,'held':held,'invoke':invoke,'save':lambda *a:None}
 exec(compile(text,str(source),'exec'),scope)
 with redirect_stdout(io.StringIO()):scope['b']()
 save(OUT/'L07-input-provenance.json',{'examples':str(examples.relative_to(ROOT)),'examples_sha256':digest(examples),'accepted_ids':[x['id'] for x in reviewed if x['usable']],'accepted_count':6,'old_runner_sha256':digest(source),'labels_sha256':digest(ROOT/'reports/nvidia-translation/pr-label-review/labels-final.json'),'default_parent_path_used':False,'connection':'Existing b() body, only examples path explicitly redirected; baseline/plan_real/plan_dd preserved. Historical heldout name is reused input, not newly held-out.'})
 return captured

def main():
 plan=b_prompts()
 # For C/D preserve actual frozen routing decision and original pre-generation payload.
 for identifier,prefix in [('L08','C'),('L09','D')]:
  for f in sorted((PRIOR/identifier).glob(prefix+'-*.json')):
   if '-input-' in f.name:continue
   d=json.loads(f.read_text())
   if d.get('selected')!='cheap' or not d.get('failed'):continue
   # Original call was blocked before raw request persistence. Freeze the exact
   # existing invoke prompt by executing original c/d against a capture-only invoke.
   plan.append({'id':identifier+'-'+f.stem,'family':identifier,'frozen_blocked_output':str(f.relative_to(ROOT)),'frozen_blocked_sha256':digest(f),'routing_decision':d.get('routing'),'status':'payload_captured_below'})
 # Capture c/d prompts from source functions, no router/API invocation.
 source=BASE/'workflow_pilot/run_bcd_v2.py';tree=ast.parse(source.read_text());labels=json.loads((ROOT/'reports/nvidia-translation/pr-label-review/labels-final.json').read_text());held=[r for r in labels if r['split']=='heldout' and r['eligible_for_pilot']]
 for identifier,fnname in [('L08','c'),('L09','d')]:
  captures={}
  def invoke(tag,prompt,chosen='cheap',route=False,cap=6500):
   captures[tag]=(prompt,cap);return {'failed':True,'prepared_only':True}
  fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==fnname)
  scope={'json':json,'OUT':OUT,'held':held,'invoke':invoke,'save':lambda *a:None}
  exec(compile(ast.get_source_segment(source.read_text(),fn),str(source),'exec'),scope)
  with redirect_stdout(io.StringIO()):scope[fnname]()
  for row in plan:
   if row['family']!=identifier:continue
   stem=Path(row['frozen_blocked_output']).stem
   if identifier=='L08':tag='wp-c-v2-switchyard-'+stem.removeprefix('C-switchyard-')
   else:tag='wp-d-v2-'+stem.split('-')[1]+'-partial_switchyard'
   prompt,cap=captures[tag];row.update(prompt=prompt,max_tokens=cap,status='prepared_not_sent')
 # L06 uses fixed source docs and original request builder, extracted without
 # running module setup; same blocked selection, no reclassification.
 s=BASE/'switchyard_prep/run.py';tree=ast.parse(s.read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='request')
 policy_a=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='POLICY' for t in n.targets))
 scope={'json':json,'POLICY':policy_a};exec(compile(ast.get_source_segment(s.read_text(),fn),str(s),'exec'),scope)
 docs={x['id']:x for x in json.loads((PRIOR/'L06/documents.json').read_text())}
 for row in json.loads((PRIOR/'L06/results.json').read_text()):
  if row['selected']!='cheap':continue
  req=scope['request'](docs[row['document']]['source'])
  messages=[]
  for m in req.get('instructions',[])+req.get('messages',[]):
   c=m.get('content','');content='\n'.join(x['text'] for x in c) if isinstance(c,list) else c
   messages.append({'role':m.get('role','system'),'content':content})
  plan.append({'id':'L06-'+row['document']+'-'+row['arm'],'family':'L06','messages':messages,'max_tokens':req.get('output',{}).get('max_output_tokens') or 8192,'frozen_routing':row['routing'],'source_hash':row['source_hash'],'status':'prepared_not_sent'})
 # Store exact payloads as prepared; provider pin cannot be added until verified.
 policy_source=BASE/'workflow_pilot/run_bcd_v2.py';tree=ast.parse(policy_source.read_text());policy=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='POLICY' for t in n.targets))
 for row in plan:
  messages=row.get('messages') or [{'role':'user','content':policy+'\n'+row['prompt']}]
  row['payload']={'model':'qwen/qwen3.7-flash','messages':messages,'max_tokens':row['max_tokens'],'reasoning':{'enabled':False}}
  if row['family']!='L06':row['payload']['response_format']={'type':'json_object'}
  row['payload_sha256']=hashlib.sha256(json.dumps(row['payload'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
  row['status']='prepared_not_sent';row['provider_price_contract']='unverified; paid call blocked'
 counts={n:sum(x['family']==n for x in plan) for n in ['L06','L07','L08','L09']}
 assert counts=={'L06':6,'L07':3,'L08':5,'L09':2},counts
 save(OUT/'prepared-arms.json',{'new_execution_id':'openrouter-resume-20261104','paid_calls':0,'model':'qwen/qwen3.7-flash','counts':counts,'arms':plan})
 print(json.dumps(counts))
if __name__=='__main__':main()
