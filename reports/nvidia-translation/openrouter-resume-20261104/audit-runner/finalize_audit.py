"""Interpret preserved read-only experiment evidence; no HTTP calls."""
from pathlib import Path
from datetime import datetime
import json
ROOT=Path('/Users/simso/Project/hf-workflow');OUT=ROOT/'reports/nvidia-translation/openrouter-resume-20261104'
p=OUT/'readonly-audit.json';d=json.loads(p.read_text());rows=d.get('historical_generations',[])
for r in rows:
 local=json.loads((ROOT/r['local_evidence']).read_text())['response'];verified=r['verified']
 if not verified:continue
 r['identity_matches']=verified['id']==local['id'] and verified['model']==local['model']
 r['cost_matches']=abs(float(verified.get('total_cost') or 0)-float(r['local_reported_cost'] or 0))<1e-9
 r['created_timestamp_difference_seconds']=abs(datetime.fromisoformat(verified['created_at'].replace('Z','+00:00')).timestamp()-local['created'])
private=json.loads(Path('/private/tmp/hf-openrouter-account-audit-20261104.json').read_text());usage=private['fields'].get('usage')
d['key_usage_matches_26_experiment_generations']=usage is not None and abs(usage-d['historical_verified_total_cost'])<1e-8
d['verified_non_byok_generations']=sum(r['verified'].get('is_byok') is False for r in rows if r['verified'])
d['generation_identity_matches']=sum(r.get('identity_matches',False) for r in rows)
d['generation_cost_matches']=sum(r.get('cost_matches',False) for r in rows)
d['time_comparison_max_difference_seconds']=max(r.get('created_timestamp_difference_seconds',0) for r in rows)
d['minimum_information_needed']=['A confirmed or conservative upper bound, in USD, for additional experiment-attributable non-OpenAI charges and credit-purchase/processing/tax fees beyond the verified $0.01228904. Unrelated account activity is outside scope.']
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('Generation evidence finalized without HTTP or paid calls')
