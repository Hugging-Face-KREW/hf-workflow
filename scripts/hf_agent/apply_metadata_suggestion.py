from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SEO_TOOLS = REPO_ROOT / "skills" / "seo" / "tools"
sys.path.insert(0, str(SEO_TOOLS))

from metadata import MetadataPlan, apply as apply_metadata  # noqa: E402


SAFE_PARTIAL_FIELDS = ("title", "description", "categories", "image")
POLICY_FIELDS = (
    "target_url",
    "source_url",
    "canonical_policy",
    "translation_indexing",
    "target_locale",
    "source_locale",
)


def _resolve_post(target_root: Path, file_path: str) -> Path:
    relative = Path(file_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Metadata suggestion file_path must be repo-relative")
    if relative.suffix != ".md" or not relative.parts or relative.parts[0] != "_posts":
        raise ValueError("Metadata suggestion can only update one _posts/*.md file")
    return target_root / relative


def _candidate_fields(candidate: dict[str, Any]) -> list[str]:
    fields = []
    for field in ("title", "description", "categories", "image", "canonical", "hreflang", "json_ld"):
        value = candidate.get(field)
        if value not in ("", None, [], {}):
            fields.append(field)
    return fields


def _plan(candidate: dict[str, Any]) -> MetadataPlan:
    categories = candidate.get("categories") or []
    if isinstance(categories, str):
        categories = [categories]
    return MetadataPlan(
        title=str(candidate.get("title") or ""),
        description=str(candidate.get("description") or ""),
        categories=list(categories),
        image=str(candidate.get("image") or ""),
        canonical=str(candidate.get("canonical") or ""),
        hreflang=dict(candidate.get("hreflang") or {}),
        json_ld=dict(candidate.get("json_ld") or {}),
    )


def _safe_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {field: candidate.get(field) for field in SAFE_PARTIAL_FIELDS}


def _with_policy(candidate: dict[str, Any], policy: dict[str, str]) -> dict[str, Any]:
    updated = dict(candidate)
    target_url = policy.get("target_url", "").strip()
    source_url = policy.get("source_url", "").strip()
    target_locale = policy.get("target_locale", "").strip()
    source_locale = policy.get("source_locale", "").strip()
    canonical_policy = policy.get("canonical_policy", "").strip()
    if canonical_policy == "self" and target_url:
        updated["canonical"] = target_url
    elif canonical_policy == "source" and source_url:
        updated["canonical"] = source_url
    if target_url and source_url and target_locale and source_locale:
        updated["hreflang"] = {
            target_locale: target_url,
            source_locale: source_url,
        }
    return updated


def _remaining_policy_decisions(
    suggestion: dict[str, Any],
    policy_overrides: dict[str, str],
) -> list[str]:
    missing = []
    for field in suggestion.get("needs_policy_decision", []) or []:
        if field in POLICY_FIELDS and policy_overrides.get(field):
            continue
        missing.append(str(field))
    return missing


def _has_candidate(candidate: dict[str, Any]) -> bool:
    return bool(_candidate_fields(candidate))


def apply_suggestion(
    *,
    target_root: Path,
    suggestion_path: Path,
    allow_partial_safe_fields: bool = False,
    policy_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not suggestion_path.exists():
        return {
            "kind": "seo_metadata_apply_result",
            "status": "SKIPPED",
            "changed": False,
            "file_path": "",
            "applied_fields": [],
            "reason": "Metadata suggestion file was not produced",
        }

    suggestion = json.loads(suggestion_path.read_text(encoding="utf-8"))
    if suggestion.get("kind") != "seo_metadata_suggestion":
        raise ValueError("Unsupported metadata suggestion kind")

    file_path = str(suggestion.get("file_path") or "")
    apply_info = suggestion.get("apply", {}) or {}
    policy_overrides = policy_overrides or {}
    base_candidate = suggestion.get("candidate", {}) or {}
    remaining_policy = _remaining_policy_decisions(suggestion, policy_overrides)
    policy_ready = (
        suggestion.get("status") in {"READY", "PARTIAL"}
        and not remaining_policy
        and bool(policy_overrides)
        and bool(base_candidate.get("title"))
        and bool(base_candidate.get("description"))
    )
    approved_ready = (
        suggestion.get("status") == "READY"
        and apply_info.get("allowed") is True
        and apply_info.get("requires_human") is False
        and not suggestion.get("needs_policy_decision")
    )
    partial_safe = (
        allow_partial_safe_fields
        and suggestion.get("status") == "PARTIAL"
        and _has_candidate(_safe_candidate(base_candidate))
    )
    if approved_ready or policy_ready:
        candidate = _with_policy(base_candidate, policy_overrides)
        reason = "Applied approved SEO metadata suggestion"
    elif partial_safe:
        candidate = _safe_candidate(base_candidate)
        reason = "Applied safe SEO metadata fields from a partial suggestion"
    else:
        return {
            "kind": "seo_metadata_apply_result",
            "status": "SKIPPED",
            "changed": False,
            "file_path": file_path,
            "applied_fields": [],
            "reason": "Metadata suggestion is not approved for write-back",
        }

    post_path = _resolve_post(target_root, file_path)
    before = post_path.read_text(encoding="utf-8")
    apply_metadata(_plan(candidate), post_path)
    after = post_path.read_text(encoding="utf-8")
    changed = before != after
    return {
        "kind": "seo_metadata_apply_result",
        "status": "APPLIED" if changed else "NO_CHANGE",
        "changed": changed,
        "file_path": file_path,
        "applied_fields": _candidate_fields(candidate) if changed else [],
        "reason": (
            reason
            if changed
            else "SEO metadata suggestion produced no file change"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply an approved SEO metadata suggestion.")
    parser.add_argument("--target-root", required=True, type=Path)
    parser.add_argument("--suggestion", required=True, type=Path)
    parser.add_argument("--result-json", required=True, type=Path)
    parser.add_argument("--allow-partial-safe-fields", action="store_true")
    for field in POLICY_FIELDS:
        parser.add_argument(f"--{field.replace('_', '-')}")
    args = parser.parse_args()

    policy_overrides = {
        field: str(getattr(args, field) or "").strip()
        for field in POLICY_FIELDS
        if str(getattr(args, field) or "").strip()
    }
    result = apply_suggestion(
        target_root=args.target_root,
        suggestion_path=args.suggestion,
        allow_partial_safe_fields=args.allow_partial_safe_fields,
        policy_overrides=policy_overrides,
    )
    args.result_json.parent.mkdir(parents=True, exist_ok=True)
    args.result_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Metadata suggestion: {result['status']} ({result['reason']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
