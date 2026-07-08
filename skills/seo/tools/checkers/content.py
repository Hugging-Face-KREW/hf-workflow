"""Content structure validation checker"""
from typing import Dict, Any
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (
    extract_headings,
    get_opening_paragraphs,
    check_citations,
    extract_links,
    count_words,
    count_chars,
    is_mostly_korean,
)


def check_content_structure(content: str, body: str, primary_keyword: str = "") -> Dict[str, Any]:
    """
    Check content structure for SEO/GEO compliance.

    Args:
        content: Full markdown content (with frontmatter)
        body: Body content (without frontmatter)
        primary_keyword: optional; enables the D8 "keyword subheading" branch

    Returns:
        {
            'passed': bool,
            'score': float,
            'checks': [...]
        }
    """
    checks = []

    # 1. Opening paragraphs check (REVIEW) — useful evidence, not a universal gate.
    opening = get_opening_paragraphs(content, 3)
    if is_mostly_korean(opening):
        opening_metric = count_chars(opening)
        opening_passed = opening_metric >= 150
        opening_msg = f'Opening 3 paragraphs: {opening_metric} chars (recommend ≥150 for KO/GEO)'
    else:
        opening_metric = count_words(opening)
        opening_passed = opening_metric >= 50
        opening_msg = f'Opening 3 paragraphs: {opening_metric} words (recommend ≥50 for GEO)'
    checks.append({
        'name': 'opening_summary',
        'passed': opening_passed,
        'severity': 'review',
        'message': opening_msg,
        'value': opening[:200] + '...' if len(opening) > 200 else opening
    })

    # 2. Heading hierarchy check (REQUIRED)
    headings = extract_headings(body)
    hierarchy_valid = True
    hierarchy_issues = []

    if headings:
        prev_level = 0
        for level, text in headings:
            if prev_level > 0 and level > prev_level + 1:
                hierarchy_valid = False
                hierarchy_issues.append(f'Skip from H{prev_level} to H{level}: "{text}"')
            prev_level = level

    checks.append({
        'name': 'heading_hierarchy',
        'passed': hierarchy_valid,
        'severity': 'required',
        'message': f'Heading hierarchy: {"Valid" if hierarchy_valid else "Invalid - " + "; ".join(hierarchy_issues)}',
        'value': headings
    })

    # 3. Raw markdown H1 check (REVIEW)
    # Final H1 count depends on the site renderer/layout. Treat this as evidence
    # until a rendered HTML pass is available.
    h1_count = sum(1 for level, _ in headings if level == 1)
    checks.append({
        'name': 'h1_count',
        'passed': h1_count == 1,
        'severity': 'review',
        'message': f'Markdown H1 count: {h1_count} (review against rendered layout)',
        'value': h1_count
    })

    # 4. Citations check (REVIEW)
    # Citation need depends on page type. Count it deterministically, but let
    # policy/rubric decide whether the absence is blocking for this article.
    citation_count = check_citations(body)
    checks.append({
        'name': 'citations',
        'passed': citation_count >= 1,
        'severity': 'review',
        'message': f'Citations/statistics: {citation_count} (recommend ≥1 for GEO)',
        'value': citation_count
    })

    # 5. Question-form OR keyword headings (RECOMMENDED, D8)
    # reference_01 L246 treats subheadings as "question-form OR keyword"; the
    # keyword branch only activates when a primary keyword is supplied.
    kw_norm = ''.join(primary_keyword.lower().split())
    question_headings = []
    keyword_headings = []
    for level, text in headings:
        if level not in (2, 3):
            continue
        is_question = '?' in text or any(
            kw in text.lower() for kw in ['무엇', '어떻게', '왜', 'what', 'how', 'why']
        )
        if is_question:
            question_headings.append(text)
        elif kw_norm and kw_norm in ''.join(text.lower().split()):
            keyword_headings.append(text)

    scannable = question_headings + keyword_headings
    checks.append({
        'name': 'question_headings',
        'passed': len(scannable) >= 1,
        'severity': 'recommended',
        'message': (
            f'Scannable H2/H3 (question or keyword): {len(scannable)} '
            f'({len(question_headings)} question, {len(keyword_headings)} keyword)'
        ),
        'value': scannable
    })

    # 6. Internal links check (RECOMMENDED)
    links = extract_links(body)
    internal_links = [l for l in links if not l.startswith('http') or 'hugging-face-krew.github.io' in l or l.startswith('/')]
    checks.append({
        'name': 'internal_links',
        'passed': len(internal_links) >= 2,
        'severity': 'recommended',
        'message': f'Internal links: {len(internal_links)} (recommend 2-3)',
        'value': internal_links
    })

    # 7. Content length check (OPTIONAL) — language-aware threshold (D11)
    if is_mostly_korean(body):
        length_metric = count_chars(body)
        length_passed = length_metric >= 800
        length_msg = f'Body length: {length_metric} chars (recommend ≥800 for KO)'
    else:
        length_metric = count_words(body)
        length_passed = length_metric >= 300
        length_msg = f'Word count: {length_metric} (recommend ≥300)'
    checks.append({
        'name': 'word_count',
        'passed': length_passed,
        'severity': 'optional',
        'message': length_msg,
        'value': length_metric
    })

    # Calculate score
    required_checks = [c for c in checks if c['severity'] == 'required']
    recommended_checks = [c for c in checks if c['severity'] == 'recommended']
    optional_checks = [c for c in checks if c['severity'] == 'optional']

    required_passed = sum(1 for c in required_checks if c['passed'])
    recommended_passed = sum(1 for c in recommended_checks if c['passed'])
    optional_passed = sum(1 for c in optional_checks if c['passed'])

    # Score: required 70%, recommended 25%, optional 5%
    score = 0.0
    if required_checks:
        score += 0.7 * (required_passed / len(required_checks))
    if recommended_checks:
        score += 0.25 * (recommended_passed / len(recommended_checks))
    if optional_checks:
        score += 0.05 * (optional_passed / len(optional_checks))

    passed = all(c['passed'] for c in required_checks)

    return {
        'passed': passed,
        'score': score,
        'checks': checks,
        'summary': {
            'required': f'{required_passed}/{len(required_checks)}',
            'recommended': f'{recommended_passed}/{len(recommended_checks)}',
            'optional': f'{optional_passed}/{len(optional_checks)}'
        }
    }
