"""Validate contradictions that previously caused incomplete MQM coverage.

jsonschema is optional for the repository runtime; installed explicitly for
this schema contract validation and the experiment audit environment.
"""
import json
from pathlib import Path
import pytest

jsonschema = pytest.importorskip('jsonschema')
SCHEMA = json.loads((Path(__file__).parents[1] / 'schemas/mqm_judge.schema.json').read_text())
TERM = {'source_term': 'device', 'target_term': '디바이스',
        'assessment': 'acceptable', 'explanation': 'Contextually appropriate technical term.'}

@pytest.mark.parametrize('status,terms,valid', [
    ('not_applicable', [], True),
    ('pass', [TERM], True),
    ('fail', [{**TERM, 'assessment': 'mistranslated'}], True),
    ('pass', [], False),
    ('fail', [], False),
    ('not_applicable', [TERM], False),
    ('pass', [{**TERM, 'assessment': 'inconsistent'}], False),
])
def test_terminology_status_constrains_evidence(status, terms, valid):
    payload = {'segment_id': 'p001', 'adequacy_score': 1,
               'fluency_score': 1, 'technical_score': 1, 'errors': [],
               'terminology_review': {'status': status, 'unregistered_terms': terms}}
    errors = list(jsonschema.Draft202012Validator(SCHEMA).iter_errors(payload))
    assert (not errors) == valid
