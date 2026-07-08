"""Rendered HTML signal extraction for dataset validation.

This is not a full Jekyll build. It mirrors the HFKREW post layout's key SEO
signal: `_layouts/post.html` renders `page.title` as
`<h1 class="posttitle">{{ page.title }}</h1>`, then appends markdown content.
"""
from __future__ import annotations

from typing import Any, Dict

import markdown
from bs4 import BeautifulSoup

from utils import parse_frontmatter


def extract_render_signals(markdown_content: str) -> Dict[str, Any]:
    frontmatter, body = parse_frontmatter(markdown_content)
    html = markdown.markdown(body, extensions=["extra"])
    soup = BeautifulSoup(html, "html.parser")

    body_h1 = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
    layout_title = str(frontmatter.get("title") or "").strip()
    effective_h1 = ([layout_title] if layout_title else []) + body_h1

    title = layout_title
    description = str(frontmatter.get("description") or "").strip()
    canonical = str(frontmatter.get("canonical") or frontmatter.get("permalink") or "").strip()

    return {
        "title": title,
        "description": description,
        "canonical": canonical,
        "body_h1_count": len(body_h1),
        "body_h1": body_h1,
        "layout_title_used_as_h1": bool(layout_title),
        "effective_h1_count": len(effective_h1),
        "effective_h1": effective_h1,
        "meta_description_present": bool(description),
    }
