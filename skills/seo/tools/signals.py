"""Raw SEO evidence signals.

Signals are deterministic observations, not pass/fail judgments. They give the
policy/rubric layer and human reviewers enough context to decide whether a
finding is actually important for the page type.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from render_signals import extract_render_signals
from utils import (
    check_citations,
    count_chars,
    extract_headings,
    extract_images,
    extract_links,
    get_opening_paragraphs,
)


def collect_signals(
    content: str,
    body: str,
    frontmatter: dict[str, Any],
    *,
    target_root: Path | None = None,
    post_path: str | None = None,
) -> Dict[str, Any]:
    headings = extract_headings(body)
    images = extract_images(body)
    links = extract_links(body)
    opening_one = get_opening_paragraphs(content, 1)
    opening_three = get_opening_paragraphs(content, 3)
    render = extract_render_signals(content)

    local_image_missing: list[str] = []
    if target_root is not None:
        for img in images:
            src = img["src"].split("#", 1)[0].split("?", 1)[0]
            if not src or src.startswith(("http://", "https://", "data:")):
                continue
            if src.startswith("/"):
                candidate = target_root / src.lstrip("/")
            else:
                base = (target_root / post_path).parent if post_path else target_root
                candidate = base / src
            if not candidate.exists():
                local_image_missing.append(img["src"])

    empty_alt = [img["src"] for img in images if not img.get("alt", "").strip()]
    filename_like_alt = [
        img["alt"] for img in images
        if img.get("alt", "").strip().lower() in {
            Path(img.get("src", "")).name.lower(),
            Path(img.get("src", "")).stem.lower(),
        }
    ]

    internal_links = [
        link for link in links
        if link.startswith("/") or link.startswith("./") or link.startswith("../")
    ]
    external_links = [link for link in links if link.startswith(("http://", "https://"))]

    title_text = str(frontmatter.get("title") or "")[:240]
    description_text = str(frontmatter.get("description") or "")[:320]
    rendered_h1 = render["effective_h1"][:5]

    return {
        "frontmatter": {
            "title_present": bool(frontmatter.get("title")),
            "title_text": title_text,
            "title_chars": count_chars(str(frontmatter.get("title") or "")),
            "description_present": bool(frontmatter.get("description")),
            "description_text": description_text,
            "description_chars": count_chars(str(frontmatter.get("description") or "")),
            "author_present": bool(frontmatter.get("author")),
            "categories_count": (
                len(frontmatter.get("categories") or [])
                if not isinstance(frontmatter.get("categories"), str)
                else 1
            ),
            "canonical_present": bool(frontmatter.get("canonical") or frontmatter.get("permalink")),
            "robots": str(frontmatter.get("robots") or ""),
        },
        "opening": {
            "first_real_paragraph_chars": count_chars(opening_one),
            "first_three_paragraph_chars": count_chars(opening_three),
            "first_real_paragraph": opening_one[:240],
        },
        "headings": {
            "markdown_h1_count": sum(1 for level, _ in headings if level == 1),
            "markdown_heading_count": len(headings),
            "markdown_headings": [{"level": level, "text": text} for level, text in headings[:20]],
            "rendered_effective_h1_count": render["effective_h1_count"],
            "layout_title_used_as_h1": render["layout_title_used_as_h1"],
            "rendered_effective_h1": render["effective_h1"],
        },
        "semantic_review": {
            "title_text": title_text,
            "description_text": description_text,
            "opening_text": opening_one[:320],
            "rendered_h1_texts": rendered_h1,
            "canonical": str(frontmatter.get("canonical") or frontmatter.get("permalink") or ""),
            "source_url_hint": "",
            "review_instruction": (
                "Compare title, description, rendered H1, and opening text for meaning consistency. "
                "This packet is evidence only; it does not decide pass/fail."
            ),
        },
        "links": {
            "total_count": len(links),
            "internal_count": len(internal_links),
            "external_count": len(external_links),
            "citation_signal_count": check_citations(body),
        },
        "images": {
            "total_count": len(images),
            "image_details": [
                {
                    "src": img.get("src", "")[:220],
                    "alt": img.get("alt", "")[:220],
                }
                for img in images[:30]
            ],
            "empty_alt_count": len(empty_alt),
            "empty_alt_sources": empty_alt[:20],
            "filename_like_alt_count": len(filename_like_alt),
            "filename_like_alt_values": filename_like_alt[:20],
            "missing_local_file_count": len(local_image_missing),
            "missing_local_file_sources": local_image_missing[:20],
        },
    }
