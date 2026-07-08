"""Frontmatter validation checker"""
from typing import Dict, Any, List


def check_frontmatter(frontmatter: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check frontmatter fields for SEO compliance.

    Returns:
        {
            'passed': bool,
            'score': float,  # 0-1
            'checks': [
                {
                    'name': str,
                    'passed': bool,
                    'severity': 'required'|'recommended'|'optional',
                    'message': str,
                    'value': Any
                }
            ]
        }
    """
    checks = []

    # 1. Title check (REQUIRED)
    title = frontmatter.get('title', '')
    title_len = len(title)
    checks.append({
        'name': 'title',
        'passed': bool(title) and title_len <= 60,
        'severity': 'required',
        'message': f'Title: {title_len} chars (recommend ≤60)' if title else 'Title is missing',
        'value': title
    })

    # 2. Description check (REQUIRED)
    # Search engines may use meta descriptions as snippet candidates, but there
    # is no official fixed character count. Gate on presence only; semantic
    # quality is reviewed through the evidence packet in `signals`.
    description = frontmatter.get('description', '')
    desc_len = len(description)
    checks.append({
        'name': 'description',
        'passed': bool(description),
        'severity': 'required',
        'message': (
            f'Description: {desc_len} chars (semantic quality reviewed separately)'
            if description else 'Description is missing'
        ),
        'value': description
    })

    # 3. Image check (REQUIRED)
    image = frontmatter.get('image', '')
    checks.append({
        'name': 'image',
        'passed': bool(image),
        'severity': 'required',
        'message': f'OG image: {image}' if image else 'OG image is missing',
        'value': image
    })

    # 4. Categories check (RECOMMENDED)
    categories = frontmatter.get('categories', [])
    if isinstance(categories, str):
        categories = [categories]
    cat_count = len(categories)
    checks.append({
        'name': 'categories',
        'passed': 2 <= cat_count <= 3,
        'severity': 'recommended',
        'message': f'Categories: {cat_count} (recommend 2-3)',
        'value': categories
    })

    # 5. Author check (RECOMMENDED)
    author = frontmatter.get('author', '')
    checks.append({
        'name': 'author',
        'passed': bool(author),
        'severity': 'recommended',
        'message': f'Author: {author}' if author else 'Author is missing',
        'value': author
    })

    # Calculate score
    required_checks = [c for c in checks if c['severity'] == 'required']
    recommended_checks = [c for c in checks if c['severity'] == 'recommended']

    required_passed = sum(1 for c in required_checks if c['passed'])
    recommended_passed = sum(1 for c in recommended_checks if c['passed'])

    # Score: required 80%, recommended 20%
    score = 0.0
    if required_checks:
        score += 0.8 * (required_passed / len(required_checks))
    if recommended_checks:
        score += 0.2 * (recommended_passed / len(recommended_checks))

    passed = all(c['passed'] for c in required_checks)

    return {
        'passed': passed,
        'score': score,
        'checks': checks,
        'summary': {
            'required': f'{required_passed}/{len(required_checks)}',
            'recommended': f'{recommended_passed}/{len(recommended_checks)}'
        }
    }
