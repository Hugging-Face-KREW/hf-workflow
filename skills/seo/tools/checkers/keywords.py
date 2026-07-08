"""Keyword placement checker (D5 / D10).

Uses manifest's handoff.seo.primary_keyword and secondary_keywords. Keyword
matching is case-insensitive and whitespace-insensitive so that a Korean
keyword written with different spacing still matches.
"""
from __future__ import annotations
from typing import Dict, Any, List
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import extract_headings, get_opening_paragraphs


def _tokens(text: str) -> List[str]:
    """Content tokens, lowercased. Splits on whitespace and strips trailing
    Korean particles so '모델의'/'모델은' still match '모델'."""
    raw = re.findall(r'[A-Za-z0-9]+|[가-힣]+', text.lower())
    out = []
    for tok in raw:
        # strip common 1-char Korean particles from a multi-syllable token
        if re.search(r'[가-힣]$', tok) and len(tok) > 1 and tok[-1] in '은는이가을를의에도와과로':
            tok = tok[:-1]
        out.append(tok)
    return out


def _contains(haystack: str, needle: str) -> bool:
    """True if every content token of `needle` appears in `haystack`
    (order-agnostic, Korean-particle tolerant). reference_02 #3 is about
    topical/intent consistency, not literal string repetition, so token
    coverage is the faithful test — not contiguous substring."""
    if not needle:
        return False
    need = set(_tokens(needle))
    if not need:
        return False
    return need.issubset(set(_tokens(haystack)))


def check_keywords(
    body: str,
    primary_keyword: str = "",
    secondary_keywords: List[str] | None = None,
) -> Dict[str, Any]:
    """Check primary keyword placement (REQUIRED) and secondary coverage
    (RECOMMENDED). If no primary keyword is supplied, the gate degrades to an
    info note rather than a hard failure."""
    secondary_keywords = secondary_keywords or []
    checks: List[Dict[str, Any]] = []

    if not primary_keyword:
        return {
            'passed': True,
            'score': 1.0,
            'checks': [{
                'name': 'primary_keyword',
                'passed': True,
                'severity': 'info',
                'message': 'No primary_keyword in manifest — keyword check skipped',
                'value': None,
            }],
            'summary': {'required': '0/0', 'recommended': '0/0'},
        }

    headings = extract_headings(body)
    h1_texts = [t for lvl, t in headings if lvl == 1]
    opening = get_opening_paragraphs(body, 3)

    in_h1 = any(_contains(t, primary_keyword) for t in h1_texts)
    in_opening = _contains(opening, primary_keyword)

    placements = {'H1': in_h1, 'first paragraph': in_opening}
    missing = [k for k, v in placements.items() if not v]

    # D5 REQUIRED: title-H1-first-paragraph consistency (reference_02 #3).
    # Eval is body-only, so H1 stands in for the title promise; the metadata
    # writer later generates `title` to match this H1. Subheading keyword
    # placement is intentionally NOT required here — reference_01's checklist
    # treats H2/H3 as "question-form OR keyword", which D8 (question_headings)
    # already covers; mandating verbatim keyword in subheadings has no source
    # and runs against current Google guidance.
    checks.append({
        'name': 'primary_keyword',
        'passed': in_h1 and in_opening,
        'severity': 'required',
        'message': (
            f'Primary keyword "{primary_keyword}" in H1+first paragraph: '
            f'{"consistent" if not missing else "missing in " + ", ".join(missing)}'
        ),
        'value': placements,
    })

    # D10 RECOMMENDED: at least half of secondary keywords appear in body
    if secondary_keywords:
        found = [k for k in secondary_keywords if _contains(body, k)]
        ratio = len(found) / len(secondary_keywords)
        checks.append({
            'name': 'secondary_keywords',
            'passed': ratio >= 0.5,
            'severity': 'recommended',
            'message': f'Secondary keywords in body: {len(found)}/{len(secondary_keywords)} ({ratio:.0%}, ≥50% recommend)',
            'value': found,
        })

    required = [c for c in checks if c['severity'] == 'required']
    recommended = [c for c in checks if c['severity'] == 'recommended']
    req_pass = sum(1 for c in required if c['passed'])
    rec_pass = sum(1 for c in recommended if c['passed'])

    score = 0.0
    if required:
        score += 0.8 * (req_pass / len(required))
    if recommended:
        score += 0.2 * (rec_pass / len(recommended))
    elif required:
        score += 0.2  # no secondary keywords configured -> don't penalize

    return {
        'passed': all(c['passed'] for c in required),
        'score': score,
        'checks': checks,
        'summary': {
            'required': f'{req_pass}/{len(required)}',
            'recommended': f'{rec_pass}/{len(recommended)}',
        },
    }
