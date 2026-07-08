"""Blocking publish-safety checks.

These checks are intentionally narrow. They catch conditions that should stop a
post from moving forward regardless of body quality, while ordinary SEO quality
issues remain in the deterministic content/image/keyword gate.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import extract_images, extract_links  # noqa: E402


def _is_internal(link: str) -> bool:
    return (
        link.startswith("/")
        or link.startswith("../")
        or link.startswith("./")
        or (
            not link.startswith(("http://", "https://", "mailto:", "tel:", "#"))
            and "://" not in link
        )
    )


def _resolve_internal_link(target_root: Path, post_path: str | None, link: str) -> Path:
    clean = link.split("#", 1)[0].split("?", 1)[0]
    if clean.endswith("/"):
        clean += "index.html"
    if clean.startswith("/"):
        return target_root / clean.lstrip("/")
    base = (target_root / post_path).parent if post_path else target_root
    return base / clean


def _resolve_local_asset(target_root: Path, post_path: str | None, src: str) -> Path:
    clean = src.split("#", 1)[0].split("?", 1)[0]
    if clean.startswith("/"):
        return target_root / clean.lstrip("/")
    base = (target_root / post_path).parent if post_path else target_root
    return base / clean


def check_blockers(
    frontmatter: Dict[str, Any],
    body: str,
    target_root: Path | None = None,
    post_path: str | None = None,
) -> Dict[str, Any]:
    checks = []

    checks.append({
        "name": "body_not_empty",
        "passed": bool(body.strip()),
        "severity": "blocker",
        "message": "Body is not empty" if body.strip() else "Body is empty",
        "value": len(body.strip()),
    })

    robots = str(frontmatter.get("robots", "") or "").lower()
    checks.append({
        "name": "robots_indexable",
        "passed": "noindex" not in robots,
        "severity": "blocker",
        "message": (
            "Robots is indexable"
            if "noindex" not in robots
            else "Frontmatter robots contains noindex"
        ),
        "value": robots,
    })

    if target_root is not None:
        missing = []
        for link in extract_links(body):
            if not _is_internal(link):
                continue
            clean = link.split("#", 1)[0].split("?", 1)[0]
            if not clean:
                continue
            candidate = _resolve_internal_link(target_root, post_path, link)
            if not candidate.exists():
                missing.append(link)
        checks.append({
            "name": "internal_links_resolve",
            "passed": not missing,
            "severity": "blocker",
            "message": (
                "All internal links resolve"
                if not missing
                else f"{len(missing)} internal link(s) do not resolve: {', '.join(missing[:3])}"
            ),
            "value": missing,
        })

        missing_images = []
        for image in extract_images(body):
            src = image.get("src", "")
            if not src or src.startswith(("http://", "https://", "data:")):
                continue
            candidate = _resolve_local_asset(target_root, post_path, src)
            if not candidate.exists():
                missing_images.append(src)
        checks.append({
            "name": "local_images_resolve",
            "passed": not missing_images,
            "severity": "blocker",
            "message": (
                "All local images resolve"
                if not missing_images
                else f"{len(missing_images)} local image(s) do not resolve: {', '.join(missing_images[:3])}"
            ),
            "value": missing_images,
        })

    passed = all(c["passed"] for c in checks)
    return {
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "checks": checks,
        "summary": {
            "blocker": f"{sum(1 for c in checks if c['passed'])}/{len(checks)}",
        },
    }
