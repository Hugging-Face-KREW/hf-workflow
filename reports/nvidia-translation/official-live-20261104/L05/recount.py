"""Recompute public report counts; standard library only, no API or writes."""
from pathlib import Path
from collections import Counter
import json
def recount(d):
 if d['experiment']=='L04':
  rows=d['evaluation_rows'];generated=d['generation_rows']
  for x in rows:
   a=x['baseline_assessment'];assert x['baseline_pass']==(a['acceptable'] and not a['uncertain'] and not a['findings'])
   assert x['policy_pass']==(x['policy_initial_decision']=='pass_candidate')
  return {'evaluation_inputs':len(rows),'labelled_bad':sum(x['expected_bad'] for x in rows),'labelled_good':sum(not x['expected_bad'] for x in rows),'initial_checks':{key:{'false_pass':sum(x['expected_bad'] and x[key] for x in rows),'false_block':sum(not x['expected_bad'] and not x[key] for x in rows)} for key in ['baseline_pass','policy_pass']},'final_decisions':dict(Counter(x['final_decision'] for x in rows)),'repairs':sum(x['repairs'] for x in rows),'generation':{arm:{'n':sum(x['arm']==arm for x in generated),'mechanical_clean':sum(x['arm']==arm and x['candidate_exists'] and not x['mechanical'] for x in generated),'untranslated_labels':sum(len(x['remaining_labels']) for x in generated if x['arm']==arm)} for arm in sorted({x['arm'] for x in generated})}}
 truth={x['id']:x for x in d['dataset']};rows=d['decision_rows'];repairs=d['repair_rows']
 for x in repairs:
  rule=truth[x['id']]['invariants'];text=x['candidate']
  measured=all(any(s in text for s in group) for group in rule['require_any']) and not any(s in text for s in rule['forbid'])
  assert measured==x['invariant_ok'];assert x['repair_attempted']==(not x['initial_pass'])
 return {'inputs':len(truth),'labelled_bad':sum(x['expected_bad'] for x in truth.values()),'labelled_good':sum(not x['expected_bad'] for x in truth.values()),'decisions':len(rows),'checks':{arm:{'n':sum(x['arm']==arm for x in rows),'false_pass':sum(x['arm']==arm and truth[x['id']]['expected_bad'] and x['passed'] for x in rows),'false_block':sum(x['arm']==arm and not truth[x['id']]['expected_bad'] and not x['passed'] for x in rows)} for arm in sorted({x['arm'] for x in rows})},'repair_pipelines':{arm:{'n':sum(x['arm']==arm for x in repairs),'repair_attempted':sum(x['arm']==arm and x['repair_attempted'] for x in repairs),'approved':sum(x['arm']==arm and x['approved'] for x in repairs),'approved_invariant_violation':sum(x['arm']==arm and x['approved'] and not x['invariant_ok'] for x in repairs)} for arm in sorted({x['arm'] for x in repairs})}}
if __name__=='__main__':
 here=Path(__file__).resolve().parent;measured=recount(json.loads((here/'comparison-evidence.json').read_text()));expected=json.loads((here/'recomputed-metrics.json').read_text());assert measured==expected
 print(json.dumps(measured,ensure_ascii=False,indent=2));print('Saved counts match; no API calls or files modified.')
