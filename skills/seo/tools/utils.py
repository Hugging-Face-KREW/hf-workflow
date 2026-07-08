"""Utility functions for SEO skill"""
import re
from pathlib import Path
from typing import Dict, Any

import yaml


def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """
    Parse Jekyll frontmatter from markdown content.

    Uses a real YAML parser so multi-line block lists, quoted strings, and
    nested structures round-trip correctly (the previous hand-rolled parser
    broke on block-style `categories:` lists).

    Returns:
        (frontmatter_dict, body_content)
    """
    pattern = r'^---\s*\n(.*?)\n---\s*\n?(.*)$'
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return {}, content

    yaml_content, body = match.group(1), match.group(2)
    try:
        frontmatter = yaml.safe_load(yaml_content) or {}
    except yaml.YAMLError:
        frontmatter = {}
    if not isinstance(frontmatter, dict):
        frontmatter = {}

    return frontmatter, body


def count_chars(text: str) -> int:
    """Unicode codepoint count (the right SERP-truncation proxy for Korean;
    byte length would unfairly penalize CJK at 3 bytes/char)."""
    return len(text.strip())


def is_mostly_korean(text: str) -> bool:
    """True if Hangul outweighs ASCII letters — used to pick language-aware
    length thresholds."""
    hangul = len(re.findall(r'[가-힣]', text))
    ascii_letters = len(re.findall(r'[A-Za-z]', text))
    return hangul >= ascii_letters


def count_words(text: str) -> int:
    """Count words in text"""
    return len(text.split())


def extract_headings(content: str) -> list[tuple[int, str]]:
    """
    Extract headings from markdown content.

    Returns:
        List of (level, text) tuples
    """
    headings = []
    in_fence = False
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith(('```', '~~~')):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            text = line.lstrip('#').strip()
            if text:
                headings.append((level, text))
    return headings


def extract_images(content: str) -> list[Dict[str, str]]:
    """
    Extract images from markdown content.

    Returns:
        List of dicts with 'src' and 'alt' keys
    """
    images = []

    # Markdown images: ![alt](src)
    pattern = r'!\[(.*?)\]\((.*?)\)'
    for match in re.finditer(pattern, content):
        images.append({
            'alt': match.group(1),
            'src': match.group(2)
        })

    # HTML images: <img src="..." alt="...">
    html_pattern = r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*>'
    for match in re.finditer(html_pattern, content):
        images.append({
            'src': match.group(1),
            'alt': match.group(2)
        })

    # HTML images: <img alt="..." src="...">
    html_pattern2 = r'<img[^>]*alt=["\']([^"\']*)["\'][^>]*src=["\']([^"\']*)["\'][^>]*>'
    for match in re.finditer(html_pattern2, content):
        images.append({
            'alt': match.group(1),
            'src': match.group(2)
        })

    return images


def extract_links(content: str) -> list[str]:
    """Extract markdown links from content, excluding image embeds.

    A leading ``!`` (i.e. ``![alt](src)``) marks an image, not a link. Matching
    it here would double-count images as citations (D4) and internal links (D9),
    so the negative lookbehind drops image syntax.
    """
    links = []
    pattern = r'(?<!\!)\[([^\]]+)\]\(([^\)]+)\)'
    for match in re.finditer(pattern, content):
        links.append(match.group(2))
    return links


def check_citations(content: str) -> int:
    """
    Count potential citations in content.
    Looks for:
    - [Source](url)
    - "quote" — Source
    - According to X
    - X% (statistics)
    """
    count = 0

    # Links as citations
    links = extract_links(content)
    count += len([l for l in links if 'http' in l])

    # "According to" patterns
    according_pattern = r'(according to|based on|reported by|study by|research by)'
    count += len(re.findall(according_pattern, content, re.IGNORECASE))

    # Statistics with percentage
    stats_pattern = r'\d+%|\d+\.\d+%'
    count += len(re.findall(stats_pattern, content))

    return count


def get_opening_paragraphs(content: str, num_paragraphs: int = 3) -> str:
    """Get first N paragraphs from markdown content"""
    # Remove frontmatter if exists
    _, body = parse_frontmatter(content)

    # Split by double newline
    paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]

    # Filter out headings and template/navigation markers. HFKREW posts often
    # start with TOC comments; treating those as prose creates false positives.
    ignored_exact = {'* TOC', '{:toc}', '<!--toc-->', '<!-- toc -->'}
    filtered = []
    for p in paragraphs:
        lowered = p.strip().lower()
        if p.startswith('#'):
            continue
        if p in ignored_exact or lowered in ignored_exact:
            continue
        if lowered.startswith('<!--') and lowered.endswith('-->'):
            continue
        if lowered.startswith('{%') and lowered.endswith('%}'):
            continue
        filtered.append(p)

    return '\n\n'.join(filtered[:num_paragraphs])
