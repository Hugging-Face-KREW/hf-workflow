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


def apply_suggestion(*, target_root: Path, suggestion_path: Path) -> dict[str, Any]:
    suggestion = json.loads(suggestion_path.read_text(encoding="utf-8"))
    if suggestion.get("kind") != "seo_metadata_suggestion":
        raise ValueError("Unsupported metadata suggestion kind")

    file_path = str(suggestion.get("file_path") or "")
    apply_info = suggestion.get("apply", {}) or {}
    allowed = (
        suggestion.get("status") == "READY"
        and apply_info.get("allowed") is True
        and apply_info.get("requires_human") is False
        and not suggestion.get("needs_policy_decision")
    )
    if not allowed:
        return {
            "kind": "seo_metadata_apply_result",
            "status": "SKIPPED",
            "changed": False,
            "file_path": file_path,
            "applied_fields": [],
            "reason": "Metadata suggestion is not approved for automatic write-back",
        }

    post_path = _resolve_post(target_root, file_path)
    before = post_path.read_text(encoding="utf-8")
    candidate = suggestion.get("candidate", {}) or {}
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
            "Applied approved SEO metadata suggestion"
            if changed
            else "Approved SEO metadata suggestion produced no file change"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply an approved SEO metadata suggestion.")
    parser.add_argument("--target-root", required=True, type=Path)
    parser.add_argument("--suggestion", required=True, type=Path)
    parser.add_argument("--result-json", required=True, type=Path)
    args = parser.parse_args()

    result = apply_suggestion(target_root=args.target_root, suggestion_path=args.suggestion)
    args.result_json.parent.mkdir(parents=True, exist_ok=True)
    args.result_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Metadata suggestion: {result['status']} ({result['reason']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
