from pathlib import Path
from datetime import datetime,timezone
import importlib.util,json,sys,subprocess,os,hashlib
from meter import Meter,OUT,ROOT,save,sha
CODE=Path('/private/tmp/hf-workflow-night-safety')
DEST=OUT/'L11';DEST.mkdir(exist_ok=True)
TARGET=DEST/'target';TARGET.mkdir(exist_ok=True)
POST='_posts/2026-11-04-local-smoke.md'
sys.path[:0]=[str(CODE/'scripts'),str(CODE/'translation-flow/scripts')]

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def git(*args):return subprocess.check_output(['git',*args],cwd=TARGET,text=True).strip()

def commit(message):
 git('add','--',POST);git('commit','-m',message);return git('rev-parse','HEAD')

def main():
 if (DEST/'result.json').exists():print('L11 already completed');return
 source=ROOT/'reports/nvidia-translation/pr-lab/20261104-smoke01/source.md'
 (DEST/'source.md').write_bytes(source.read_bytes())
 if not (TARGET/'.git').exists():
  git('init','-b','local-experiment');git('config','user.email','experiment@localhost');git('config','user.name','Local Experiment')
 import create_translation_pr as gen
 from translation_adapters import OpenAITranslationAdapter,TranslationRequest
 if not (TARGET/POST).exists():
  meter=Meter('L11-generation');meter.install_sdk()
  front,body=gen.split_source_frontmatter(source.read_text())
  translated=OpenAITranslationAdapter(model='gpt-5.6-luna').translate(TranslationRequest('Does Your Model Run on AWS Trainium? Look It Up','https://huggingface.co/blog/torch-neuronx-model-support',body))
  translated=gen.stabilize_manual_toc(gen.normalize_escaped_newlines(translated));gen.enforce_structure_preservation(body,translated)
  post=gen.FeedPost('Does Your Model Run on AWS Trainium? Look It Up','https://huggingface.co/blog/torch-neuronx-model-support',datetime(2026,10,23,tzinfo=timezone.utc),'local-smoke')
  target=TARGET/POST;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(gen.build_translation_markdown(post,translated,'openai',post.url,source_frontmatter=front))
  commit('Initial local whole translation')
 q=load('official_live_quality',CODE/'skills/quality/tools/translation_quality_harness.py')
 # Protocol-only schema hardening, raw failed attempts retained separately.
 schema=json.loads(q.DEFAULT_MQM_SCHEMA_PATH.read_text())
 import copy
 base=schema['properties']['terminology_review']
 branches=[]
 for status in ('not_applicable','pass','fail'):
  branch=copy.deepcopy(base);branch['properties']['status']['enum']=[status]
  terms=branch['properties']['unregistered_terms']
  if status=='not_applicable':terms['maxItems']=0
  else:terms['minItems']=1
  if status=='pass':terms['items']['properties']['assessment']['enum']=['acceptable']
  branches.append(branch)
 schema['properties']['terminology_review']={'anyOf':branches}
 schema_path=DEST/'protocol-v2.schema.json';save(schema_path,schema)
 q.DEFAULT_MQM_SCHEMA_PATH=schema_path
 sys.path.insert(0,str(CODE/'skills/seo/tools'))
 import seo_eval
 from hf_agent.verify_review_artifacts import verify_review_artifacts
 from hf_agent.handle_pr_feedback import apply_feedback,call_openai
 def evaluate(stage):
  directory=DEST/stage;directory.mkdir(exist_ok=True)
  if (directory/'outcome.json').exists():return json.loads((directory/'outcome.json').read_text())
  current=git('rev-parse','HEAD')
  manifest=directory/'manifest.yaml'
  manifest.write_text(f'source:\n  url: https://huggingface.co/blog/torch-neuronx-model-support\n  file_path: {source}\n  hash: {sha(source.read_text())}\ntranslation:\n  file_path: {POST}\n  commit_sha: {current}\n')
  reports=[]
  for attempt in range(3):
   Meter(f'L11-{stage}-mqm-{attempt}').install_sdk()
   cfg=q.MetricConfig(llm_judge_provider='openai',llm_judge_model='gpt-5.6-luna',llm_judge_prompt_path=Path('/private/tmp/hf-mqm-protocol-prompt-20261104.md'),llm_judge_max_concurrency=3,llm_judge_max_segments=0,metric_cache_path=DEST/'mqm-cache.json')
   report=q.build_report(manifest,TARGET,source_path=source,metric_config=cfg,fetch_source_url=False)
   save(directory/f'quality-attempt-{attempt}.json',report);reports.append(report)
   if report['metadata']['semantic_evaluation_complete']:break
  report=reports[-1];save(directory/'quality-eval.json',report)
  (directory/'quality.md').write_text(q.markdown_report(report))
  targethash=hashlib.sha256((TARGET/POST).read_bytes()).hexdigest()
  save(directory/'quality.json',{'skill':'quality','conclusion':'pass' if report['status'] in {'auto_pass','review_required'} else 'fail','file_path':POST,'head_sha':current,'target_hash':targethash})
  Meter(f'L11-{stage}-seo').install_sdk()
  code=seo_eval.main(['--file',POST,'--target-root',str(TARGET),'--output',str(directory/'seo.md'),'--json',str(directory/'seo-eval.json'),'--openai-required','--openai-model','gpt-5-nano'])
  save(directory/'seo.json',{'skill':'seo','conclusion':'pass' if code==0 else 'fail','file_path':POST,'head_sha':current,'target_hash':targethash})
  try:verify_review_artifacts(directory,TARGET,POST,expected_provider='openai',expected_model='gpt-5.6-luna',expected_head_sha=current);verified=True;reason='Verified exact local SHA/source/target'
  except ValueError as exc:verified=False;reason=str(exc)
  outcome={'sha':current,'semantic_complete':report['metadata']['semantic_evaluation_complete'],'quality_status':report['status'],'quality_score':report['quality_score'],'segments_requested':report['mqm_judge']['requested_segment_count'],'segments_evaluated':report['mqm_judge']['segment_count'],'verifier_passed':verified,'reason':reason,'seo_exit':code,'mqm_attempts':len(reports),'prompt_source':'existing unmerged PR35, commit 973b75b6952a456a0f7944239b8bc657f1892f52; prompt only reused','review_source':'frozen snapshot, no source fetch'}
  save(directory/'outcome.json',outcome);return outcome
 initial=evaluate('protocol-v2-initial')
 if not initial['verifier_passed'] or not initial['semantic_complete']:
  save(DEST/'result.json',{'status':'initial_validation_failed_safely','initial':initial,'feedback_executed':False});return
 # Controlled editorial request, not a fabricated quality finding or human approval.
 header=next(x for x in (TARGET/POST).read_text().splitlines() if x.startswith('# '))
 feedback=f'로컬 피드백 처리 연결 테스트입니다. 본문 H1 줄 `{header}`만 `# AWS Trainium 모델 지원 결과 확인하기`로 바꿔 주세요. frontmatter와 다른 본문·코드·링크는 그대로 두세요. 사실 오류 진단이 아니라 명시적인 편집 요청입니다.'
 import hf_agent.handle_pr_feedback as feedback_handler
 feedback_handler.MAX_REPAIR_OUTPUT_TOKENS=8000 # local run bound, production default unchanged
 Meter('L11-local-feedback').install_sdk()
 result=apply_feedback(target_root=TARGET,file_path=POST,feedback=feedback,max_changed_lines=8,model_call=lambda prompt:call_openai(prompt,model='gpt-5-nano'))
 save(DEST/'feedback.json',{'feedback':feedback,'disposition':result.disposition,'reason':result.reason,'scope':'local production handler; no GitHub authorization/dispatch was exercised'})
 if result.disposition=='actionable':commit('Apply local editorial feedback')
 after=evaluate('after-feedback') if result.disposition=='actionable' else initial
 save(DEST/'result.json',{'status':'local_pipeline_completed' if after['verifier_passed'] and after['semantic_complete'] else 'recheck_failed_safely','initial':initial,'feedback_disposition':result.disposition,'after_feedback':after,'remote_pr_mutated':False,'remote_loop_restarted':False,'body_quality_repair_claim':False})
 print('L11',json.loads((DEST/'result.json').read_text())['status'],flush=True)
if __name__=='__main__':main()
