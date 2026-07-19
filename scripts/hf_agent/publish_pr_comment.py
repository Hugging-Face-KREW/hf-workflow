from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from hf_agent.github_api import upsert_issue_comment


REPORT_MARKER = "<!-- hf-agent-report -->"
MAX_REPORT_CHARS = 24_000


def load_results(root: Path) -> list[dict[str, Any]]:
    results = []
    for path in root.glob("**/*.json"):
        result = json.loads(path.read_text())
        if {"skill", "conclusion"} <= result.keys():
            report_path = path.with_name(f"{result['skill']}.md")
            result["report"] = (
                report_path.read_text()[:MAX_REPORT_CHARS]
                if report_path.exists()
                else "Detailed report was not produced."
            )
            results.append(result)
    return sorted(results, key=lambda result: result["skill"])


def load_metadata_suggestion(root: Path) -> dict[str, Any] | None:
    for path in root.glob("**/metadata-suggestion.json"):
        suggestion = json.loads(path.read_text())
        if suggestion.get("kind") == "seo_metadata_suggestion":
            return suggestion
    return None


def _metadata_summary(suggestion: dict[str, Any] | None) -> list[str]:
    if not suggestion:
        return []

    candidate = suggestion.get("candidate", {}) or {}
    apply_info = suggestion.get("apply", {}) or {}
    needs_policy_decision = suggestion.get("needs_policy_decision", []) or []
    warnings = suggestion.get("warnings", []) or []
    candidate_rows = []
    for field in ("title", "description", "categories", "image", "canonical"):
        value = candidate.get(field)
        if value in ("", None, [], {}):
            continue
        candidate_rows.append(f"- `{field}`: {value}")
    if not candidate_rows:
        candidate_rows.append("- No metadata candidate fields were produced.")

    policy_rows = (
        [f"- `{field}`" for field in needs_policy_decision]
        if needs_policy_decision
        else ["- None"]
    )
    warning_rows = [f"- {warning}" for warning in warnings] if warnings else ["- None"]

    return [
        "<details>",
        f"<summary>SEO metadata suggestion — {suggestion.get('status', 'UNKNOWN')}</summary>",
        "",
        "This is a suggestion. SEO is applied only when the post frontmatter is updated.",
        "To apply safe fields from a partial suggestion, leave a trusted PR comment: `metadata apply`.",
        "",
        f"- Auto apply: `{bool(apply_info.get('allowed'))}`",
        f"- Requires human: `{bool(apply_info.get('requires_human', True))}`",
        f"- Mode: `{apply_info.get('mode', '')}`",
        f"- Reason: {suggestion.get('reason', '')}",
        "",
        "### Candidate",
        "",
        *candidate_rows,
        "",
        "### Needs policy decision",
        "",
        *policy_rows,
        "",
        "### Warnings",
        "",
        *warning_rows,
        "",
        "</details>",
        "",
    ]


def render_report(
    results: list[dict[str, Any]],
    *,
    head_sha: str,
    metadata_suggestion: dict[str, Any] | None = None,
) -> str:
    rows = []
    details = []
    for result in results:
        passed = result["conclusion"] == "pass"
        outcome = "✅ Pass" if passed else "❌ Fail"
        name = "SEO" if result["skill"] == "seo" else result["skill"].title()
        rows.append(f"| {name} | {outcome} |")
        details.extend(
            [
                "<details>",
                f"<summary>{name} report — {outcome}</summary>",
                "",
                str(result.get("report", "Detailed report was not produced.")),
                "",
                "</details>",
                "",
            ]
        )
    details.extend(_metadata_summary(metadata_suggestion))
    return "\n".join(
        [
            REPORT_MARKER,
            "## HF Agent Review",
            "",
            "| Gate | Result |",
            "|---|---|",
            *rows,
            "",
            f"Head SHA: `{head_sha}`",
            "",
            *details,
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the compact PR review report.")
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY", ""))
    parser.add_argument("--pr-number", type=int, required=True)
    parser.add_argument("--head-sha", required=True)
    args = parser.parse_args()
    token = os.getenv("GITHUB_TOKEN", "")
    if not args.repository or not token:
        parser.error("GITHUB_REPOSITORY and GITHUB_TOKEN are required")
    body = render_report(
        load_results(args.results),
        head_sha=args.head_sha,
        metadata_suggestion=load_metadata_suggestion(args.results),
    )
    upsert_issue_comment(
        repository=args.repository,
        issue_number=args.pr_number,
        marker=REPORT_MARKER,
        body=body,
        token=token,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
