#!/usr/bin/env python3
"""Simulate severity-policy variants against SEO fixtures and optional posts.

This tool does not change checker behavior. It reclassifies the already
collected deterministic checks to test whether a proposed policy would overblock
real posts or underblock known negative fixtures.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).parent))

from seo_eval import evaluate_path  # noqa: E402


VARIANTS: dict[str, set[str]] = {
    "current": set(),
    "demote_h1": {"h1_count"},
    "demote_contextual": {"h1_count", "opening_summary", "citations"},
    "blockers_plus_structural": {"h1_count", "opening_summary", "citations"},
    "blockers_only": {
        "h1_count",
        "opening_summary",
        "citations",
        "heading_hierarchy",
        "alt_text_coverage",
        "descriptive_alt_text",
        "primary_keyword",
    },
}


def _status_for_variant(result: dict[str, Any], demoted: set[str]) -> str:
    if not result["blockers"]["passed"]:
        return "BLOCKED"
    required = result["deterministic"]["required"]["checks"]
    failed_required = [
        check for check in required
        if not check.get("passed") and check.get("name") not in demoted
    ]
    if not failed_required:
        return "PASS"
    return "NEEDS_CHANGES" if len(failed_required) == 1 else "FAIL"


def _evaluate_case(path: Path, target_root: Path | None) -> dict[str, Any]:
    if target_root is not None:
        return evaluate_path(path, target_root=target_root.resolve())
    return evaluate_path(path)


def _fixture_cases(manifest_path: Path) -> list[dict[str, Any]]:
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    base = manifest_path.parent
    cases = []
    for case in manifest.get("cases", []):
        item = dict(case)
        item["absolute_path"] = str((base / case["path"]).resolve())
        cases.append(item)
    return cases


def _post_cases(posts_dir: Path) -> list[dict[str, Any]]:
    return [
        {
            "id": path.name,
            "path": str(path),
            "absolute_path": str(path.resolve()),
            "source_type": "real_post",
            "label": "unlabeled",
        }
        for path in sorted(posts_dir.glob("*.md"))
    ]


def _run_group(cases: list[dict[str, Any]], target_root: Path | None) -> dict[str, Any]:
    summary = {name: Counter() for name in VARIANTS}
    details = []

    for case in cases:
        path = Path(case["absolute_path"])
        result = _evaluate_case(path, target_root)
        statuses = {}
        failed_required = [
            check["name"]
            for check in result["deterministic"]["required"]["checks"]
            if not check.get("passed")
        ]
        for name, demoted in VARIANTS.items():
            status = _status_for_variant(result, demoted)
            statuses[name] = status
            summary[name][status] += 1
        details.append({
            "id": case.get("id", path.name),
            "path": case.get("path", str(path)),
            "label": case.get("label"),
            "source_type": case.get("source_type"),
            "failed_required": failed_required,
            "blockers_passed": result["blockers"]["passed"],
            "statuses": statuses,
        })

    return {
        "summary": {name: dict(counts) for name, counts in summary.items()},
        "details": details,
    }


def _risks(fixture_result: dict[str, Any]) -> list[dict[str, Any]]:
    risks = []
    for item in fixture_result["details"]:
        label = item.get("label")
        if label not in {"negative", "blocker"}:
            continue
        for variant, status in item["statuses"].items():
            if status == "PASS":
                risks.append({
                    "id": item["id"],
                    "label": label,
                    "variant": variant,
                    "failed_required": item["failed_required"],
                    "blockers_passed": item["blockers_passed"],
                })
    return risks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("skills/seo/tests/fixtures/evaluation_manifest.yml"),
    )
    parser.add_argument("--posts-dir", type=Path)
    parser.add_argument(
        "--fixture-target-root",
        type=Path,
        help="Optional target root for fixture link/image resolution.",
    )
    parser.add_argument(
        "--posts-target-root",
        type=Path,
        help="Optional target root for posts-dir link/image resolution.",
    )
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()

    fixtures = _run_group(_fixture_cases(args.manifest), args.fixture_target_root)
    result: dict[str, Any] = {
        "fixtures": fixtures,
        "risks_negative_or_blocker_as_pass": _risks(fixtures),
    }

    if args.posts_dir:
        result["posts"] = _run_group(_post_cases(args.posts_dir), args.posts_target_root)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# SEO Policy Variant Simulation", ""]
        lines.append("## Fixtures")
        lines.extend([f"- `{k}`: `{v}`" for k, v in fixtures["summary"].items()])
        if "posts" in result:
            lines.extend(["", "## Posts"])
            lines.extend([f"- `{k}`: `{v}`" for k, v in result["posts"]["summary"].items()])
        lines.extend(["", "## Negative/blocker PASS risks"])
        if result["risks_negative_or_blocker_as_pass"]:
            for risk in result["risks_negative_or_blocker_as_pass"]:
                lines.append(
                    f"- `{risk['variant']}` makes `{risk['id']}` "
                    f"({risk['label']}) PASS; failed `{risk['failed_required']}`"
                )
        else:
            lines.append("- None")
        args.markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
