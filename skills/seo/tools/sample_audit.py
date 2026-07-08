#!/usr/bin/env python3
"""Batch sample auditor for internal SEO fixture/material review.

This is not the PR gate. It evaluates many existing posts, collects their
frontmatter metadata, and writes a compact JSON/Markdown report so the team can
judge whether the SEO rules survive realistic content diversity.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).parent))

from seo_eval import evaluate_path  # noqa: E402
from utils import parse_frontmatter, extract_images, extract_links, extract_headings  # noqa: E402


def _frontmatter_summary(frontmatter: dict[str, Any]) -> dict[str, Any]:
    categories = frontmatter.get("categories", [])
    if isinstance(categories, str):
        categories = [categories]
    return {
        "title": frontmatter.get("title", ""),
        "description": frontmatter.get("description", ""),
        "image": frontmatter.get("image", ""),
        "categories": categories,
        "author": frontmatter.get("author", ""),
        "robots": frontmatter.get("robots", ""),
        "locale": frontmatter.get("locale", ""),
        "source_url": frontmatter.get("source_url", ""),
        "translation_status": frontmatter.get("translation_status", ""),
    }


def _failed_names(checks: Iterable[dict[str, Any]]) -> list[str]:
    return [c["name"] for c in checks if not c.get("passed")]


def audit_post(post: Path, *, target_root: Path | None = None) -> dict[str, Any]:
    text = post.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    result = evaluate_path(post if target_root is None else post.relative_to(target_root), target_root=target_root)

    return {
        "file": str(post.relative_to(target_root) if target_root else post),
        "status": result["gate"]["status"],
        "gate_passed": result["gate"]["passed"],
        "metadata": _frontmatter_summary(frontmatter),
        "shape": {
            "chars": len(body),
            "headings": len(extract_headings(body)),
            "h1_count": sum(1 for level, _ in extract_headings(body) if level == 1),
            "image_count": len(extract_images(body)),
            "link_count": len(extract_links(body)),
        },
        "failures": {
            "blockers": _failed_names(result.get("blockers", {}).get("checks", [])),
            "required": _failed_names(result["deterministic"]["required"]["checks"]),
            "frontmatter": _failed_names(result["frontmatter_advisory"]["checks"]),
        },
    }


def audit_posts(posts_dir: Path, *, target_root: Path | None = None, limit: int | None = None) -> dict[str, Any]:
    posts = sorted(posts_dir.glob("*.md"))
    if limit is not None:
        posts = posts[:limit]

    rows = [audit_post(post, target_root=target_root) for post in posts]
    status_counts = Counter(row["status"] for row in rows)
    metadata_missing = Counter()
    required_failures = Counter()
    blocker_failures = Counter()

    for row in rows:
        for field in ["description", "image", "author"]:
            if not row["metadata"].get(field):
                metadata_missing[field] += 1
        if not row["metadata"].get("categories"):
            metadata_missing["categories"] += 1
        required_failures.update(row["failures"]["required"])
        blocker_failures.update(row["failures"]["blockers"])

    return {
        "summary": {
            "total": len(rows),
            "status_counts": dict(status_counts),
            "metadata_missing": dict(metadata_missing),
            "required_failures": dict(required_failures),
            "blocker_failures": dict(blocker_failures),
        },
        "posts": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Internal SEO Sample Audit",
        "",
        f"- Total posts: {summary['total']}",
        f"- Status counts: `{summary['status_counts']}`",
        f"- Missing metadata: `{summary['metadata_missing']}`",
        f"- Required failures: `{summary['required_failures']}`",
        f"- Blocker failures: `{summary['blocker_failures']}`",
        "",
        "## Posts",
        "",
        "| File | Status | Metadata gaps | Required failures | Shape |",
        "|---|---|---|---|---|",
    ]
    for row in report["posts"]:
        metadata_gaps = [
            key for key in ["description", "image", "categories", "author"]
            if not row["metadata"].get(key)
        ]
        shape = row["shape"]
        lines.append(
            "| "
            + " | ".join([
                f"`{row['file']}`",
                row["status"],
                ", ".join(metadata_gaps) or "-",
                ", ".join(row["failures"]["required"] + row["failures"]["blockers"]) or "-",
                f"{shape['chars']} chars, H1 {shape['h1_count']}, img {shape['image_count']}, links {shape['link_count']}",
            ])
            + " |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit many SEO sample posts.")
    parser.add_argument("--posts-dir", required=True, help="Directory containing Markdown posts.")
    parser.add_argument("--target-root", help="Target repository root for local link/image resolution.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--json", required=True, help="JSON output path.")
    parser.add_argument("--markdown", required=True, help="Markdown output path.")
    args = parser.parse_args(argv)

    target_root = Path(args.target_root).resolve() if args.target_root else None
    report = audit_posts(Path(args.posts_dir).resolve(), target_root=target_root, limit=args.limit)

    json_path = Path(args.json)
    md_path = Path(args.markdown)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote sample audit JSON: {json_path}")
    print(f"Wrote sample audit markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
