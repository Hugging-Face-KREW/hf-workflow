#!/usr/bin/env python3
"""Generate a metadata suggestion JSON from an SEO eval result.

This module is intentionally read-only. It proposes frontmatter metadata for a
later repair/apply step, but it never edits the post or commits changes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import yaml  # noqa: E402

from metadata import build_plan  # noqa: E402
from utils import parse_frontmatter  # noqa: E402


def _load_yaml(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def _post_path(file_path: str, target_root: Path | None) -> Path:
    path = Path(file_path)
    if path.is_absolute():
        return path
    return (target_root / path) if target_root else path


def _source_eval(
    eval_result: dict[str, Any],
    eval_json: Path,
    report_path: Path | None,
) -> dict[str, Any]:
    gate = eval_result.get("gate", {}) or {}
    return {
        "status": gate.get("status") or ("PASS" if gate.get("passed") else "FAIL"),
        "passed": bool(gate.get("passed")),
        "report_path": str(report_path) if report_path else "",
        "eval_json_path": str(eval_json),
    }


def build_suggestion(
    *,
    file_path: str,
    target_root: Path | None,
    eval_json: Path,
    manifest_path: Path | None = None,
    report_path: Path | None = None,
) -> dict[str, Any]:
    eval_result = json.loads(eval_json.read_text(encoding="utf-8"))
    source_eval = _source_eval(eval_result, eval_json, report_path)
    if not source_eval["passed"]:
        return {
            "schema_version": 1,
            "kind": "seo_metadata_suggestion",
            "status": "SKIPPED",
            "file_path": file_path,
            "source_eval": source_eval,
            "candidate": {},
            "apply": {
                "allowed": False,
                "mode": "frontmatter_only",
                "requires_human": True,
            },
            "needs_policy_decision": [],
            "warnings": ["seo_gate_did_not_pass"],
            "reason": "metadata suggestion skipped because SEO gate did not pass",
        }

    post_path = _post_path(file_path, target_root)
    content = post_path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)
    manifest = _load_yaml(manifest_path)
    if not manifest:
        inp = eval_result.get("input", {}) or {}
        manifest = {
            "source": {"url": inp.get("source_url", "")},
            "translation": {"file_path": file_path},
        }

    inp = eval_result.get("input", {}) or {}
    result = build_plan(
        body,
        frontmatter,
        manifest,
        source_url=str(inp.get("source_url") or ""),
        primary_keyword=str(inp.get("primary_keyword") or ""),
    )
    payload = result.to_dict()
    status = str(payload["status"])
    return {
        "schema_version": 1,
        "kind": "seo_metadata_suggestion",
        "status": status,
        "file_path": file_path,
        "source_eval": source_eval,
        "candidate": payload["candidate"],
        "apply": {
            "allowed": False,
            "mode": "frontmatter_only",
            "requires_human": True,
        },
        "needs_policy_decision": payload["needs_policy_decision"],
        "warnings": payload["warnings"],
        "reason": payload["reason"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate metadata suggestion JSON.")
    parser.add_argument("--file", required=True, help="Post path within --target-root.")
    parser.add_argument("--target-root", type=Path, help="Translated blog repository root.")
    parser.add_argument("--eval-json", type=Path, required=True, help="SEO eval JSON path.")
    parser.add_argument("--output", type=Path, required=True, help="Suggestion JSON output path.")
    parser.add_argument("--manifest", type=Path, help="Optional translation-flow manifest YAML.")
    parser.add_argument("--report-path", type=Path, help="Optional SEO markdown report path.")
    args = parser.parse_args(argv)

    suggestion = build_suggestion(
        file_path=args.file,
        target_root=args.target_root,
        eval_json=args.eval_json,
        manifest_path=args.manifest,
        report_path=args.report_path,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(suggestion, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote metadata suggestion JSON: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
