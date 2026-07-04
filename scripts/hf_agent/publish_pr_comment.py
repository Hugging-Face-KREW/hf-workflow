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


def render_report(results: list[dict[str, Any]], *, head_sha: str) -> str:
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
    body = render_report(load_results(args.results), head_sha=args.head_sha)
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
