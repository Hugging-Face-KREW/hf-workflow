#!/usr/bin/env python3
"""Generate a metadata suggestion JSON from an SEO eval result.

This module is intentionally read-only. It proposes frontmatter metadata for a
later repair/apply step, but it never edits the post or commits changes.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import yaml  # noqa: E402

from metadata import build_plan  # noqa: E402
from openai_integration import (  # noqa: E402
    has_openai_failure,
    make_openai_metadata_generator,
)
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


def _candidate_fields(candidate: dict[str, Any]) -> list[str]:
    fields: list[str] = []
    for field in ("title", "description", "categories", "image", "canonical", "hreflang", "json_ld"):
        value = candidate.get(field)
        if value not in ("", None, [], {}):
            fields.append(field)
    return fields


def _apply_contract(status: str, candidate: dict[str, Any], needs_policy_decision: list[str]) -> dict[str, Any]:
    allowed = status == "READY" and not needs_policy_decision
    contract: dict[str, Any] = {
        "allowed": allowed,
        "mode": "frontmatter_only",
        "requires_human": not allowed,
    }
    if allowed:
        contract["target_files"] = [
            {
                "path": "",
                "operation": "update_frontmatter",
                "fields": _candidate_fields(candidate),
            }
        ]
        contract["commit_message"] = "🔧 Update SEO metadata"
    return contract


def build_suggestion(
    *,
    file_path: str,
    target_root: Path | None,
    eval_json: Path,
    manifest_path: Path | None = None,
    report_path: Path | None = None,
    openai_required: bool = False,
    openai_model: str = "",
    allow_deterministic_fallback: bool = False,
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
    generator = make_openai_metadata_generator(
        model=openai_model,
        allow_deterministic_fallback=allow_deterministic_fallback,
    ) if openai_required or os.getenv("OPENAI_API_KEY") else None
    result = build_plan(
        body,
        frontmatter,
        manifest,
        source_url=str(inp.get("source_url") or ""),
        primary_keyword=str(inp.get("primary_keyword") or ""),
        generator=generator,
    )
    payload = result.to_dict()
    status = str(payload["status"])
    warnings = payload["warnings"]
    openai_failed = has_openai_failure(warnings)
    if openai_required and openai_failed:
        status = "ERROR"
    candidate = payload["candidate"]
    needs_policy_decision = payload["needs_policy_decision"]
    apply_contract = _apply_contract(status, candidate, needs_policy_decision)
    if apply_contract.get("target_files"):
        apply_contract["target_files"][0]["path"] = file_path
    return {
        "schema_version": 1,
        "kind": "seo_metadata_suggestion",
        "status": status,
        "file_path": file_path,
        "source_eval": source_eval,
        "candidate": candidate,
        "apply": apply_contract,
        "needs_policy_decision": needs_policy_decision,
        "warnings": warnings,
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
    parser.add_argument("--openai-required", action="store_true",
                        help="require OpenAI metadata generation")
    parser.add_argument("--openai-model", default=os.getenv("OPENAI_MODEL", ""),
                        help="OpenAI model for metadata generation")
    parser.add_argument("--allow-deterministic-fallback", action="store_true",
                        help="allow local deterministic fallback when OpenAI is unavailable")
    args = parser.parse_args(argv)
    env_required = os.getenv("SEO_OPENAI_REQUIRED", "").strip().lower()
    openai_required = args.openai_required or env_required in {"1", "true", "yes", "on"}

    suggestion = build_suggestion(
        file_path=args.file,
        target_root=args.target_root,
        eval_json=args.eval_json,
        manifest_path=args.manifest,
        report_path=args.report_path,
        openai_required=openai_required,
        openai_model=args.openai_model,
        allow_deterministic_fallback=args.allow_deterministic_fallback,
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
