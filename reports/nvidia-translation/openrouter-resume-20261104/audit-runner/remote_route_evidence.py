"""Read preserved pinned configuration, not credential values or secrets."""
from pathlib import Path
import hashlib,json
ROOT=Path('/Users/simso/Project/hf-workflow');CODE=Path('/private/tmp/hf-workflow-smoke-20261104');OUT=ROOT/'reports/nvidia-translation/openrouter-resume-20261104'
files=[Path('/private/tmp/hf-blog-workflow-ref-update-20261103/.github/workflows/hf-agent-review.yml'),CODE/'.github/workflows/reusable-pr-review.yml',CODE/'scripts/hf_agent/run_skill_review.py',CODE/'skills/quality/tools/translation_quality_harness.py',CODE/'skills/seo/tools/openai_integration.py']
notes={
'hf-agent-review.yml':'Caller pins workflow 3f1035c; explicitly maps OPENAI_API_KEY. No base URL secret/input/env mapped.',
'reusable-pr-review.yml':'Hosted Ubuntu review matrix; maps OPENAI_API_KEY and model/provider vars. No OPENAI_BASE_URL or OpenRouter endpoint override.',
'run_skill_review.py':'Quality subprocess command has no --llm-judge-base-url argument; no dotenv loader.',
 'translation_quality_harness.py':'CLI default base URL comes only from OPENAI_BASE_URL env; empty default means standard OpenAI SDK. No dotenv loader.',
'openai_integration.py':'SEO creates OpenAI(api_key=...) with no base_url argument or dotenv loader.'}
evidence=[{'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'finding':notes[p.name]} for p in files]
result={'pinned_workflow_ref':'3f1035c7f759b1538a4132b4edc89bdc4e57d391','caller_ref':'96e45b2a563efdacf7884ef57a6536919f24fd0c','source':'Preserved pinned checkouts and artifacts; no secret values queried','review_runs':['41670309598','41670317634','41670353774','41670356554','41670728736'],'classification':'Configured official OpenAI SDK default route; no non-OpenAI override evidence in inspected execution configuration','billing_proof':'Configuration inference, not captured network destination or invoice. SDK route classified from explicit configuration; not from model name or secret name alone. No extra experiment-attributable non-OpenAI invocation found in inspected local ledger/configuration.','evidence':evidence,'paid_calls':0,'unrelated_account_spend_in_scope':False}
(OUT/'remote-route-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
