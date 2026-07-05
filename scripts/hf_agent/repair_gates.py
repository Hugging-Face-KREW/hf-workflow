from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from hf_agent.github_api import Requester, request_json


REPAIR_COMMIT = "🐛 Repair failed PR gates"
MAX_FEEDBACK_CHARS = 12_000


def build_gate_feedback(results_root: Path) -> str:
    sections: list[str] = []
    for result_path in sorted(results_root.glob("**/*.json")):
        result = json.loads(result_path.read_text())
        if result.get("conclusion") != "fail" or not result.get("skill"):
            continue
        skill = str(result["skill"])
        report_path = result_path.with_name(f"{skill}.md")
        if report_path.exists():
            report = report_path.read_text().strip()
            sections.append(f"{skill.upper()} gate failed:\n{report}")
    if not sections:
        raise ValueError("No failed gate report was found")
    return (
        "This is an automated PR gate repair, not an open-ended human review comment.\n"
        "Fix only the blocking findings in these automated gate reports with the smallest safe edit.\n"
        "If a report says TODO markers remain, remove placeholder TODO markers or comments from the translated post.\n"
        "Only return needs-human when the report cannot be resolved safely from the file content alone.\n\n"
        + "\n\n".join(sections)
    )[:MAX_FEEDBACK_CHARS]


def count_trailing_repairs(commits: list[dict[str, Any]]) -> int:
    count = 0
    for item in reversed(commits):
        message = str(item.get("commit", {}).get("message", ""))
        if not message.startswith(REPAIR_COMMIT):
            break
        count += 1
    return count


def prepare_repair(
    *,
    results_root: Path,
    repository: str,
    pr_number: int,
    max_attempts: int,
    token: str,
    requester: Requester = request_json,
) -> tuple[bool, int, str]:
    commits = requester(
        "GET",
        f"/repos/{repository}/pulls/{pr_number}/commits?per_page=100",
        token,
        None,
    )
    attempts = count_trailing_repairs(commits)
    return attempts < max_attempts, attempts, build_gate_feedback(results_root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a bounded failed-gate repair")
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr-number", required=True, type=int)
    parser.add_argument("--max-attempts", required=True, type=int)
    parser.add_argument("--feedback-file", required=True, type=Path)
    parser.add_argument("--result-json", required=True, type=Path)
    args = parser.parse_args()
    allowed, attempts, feedback = prepare_repair(
        results_root=args.results,
        repository=args.repository,
        pr_number=args.pr_number,
        max_attempts=args.max_attempts,
        token=os.environ["GITHUB_TOKEN"],
    )
    args.feedback_file.write_text(feedback)
    args.result_json.write_text(
        json.dumps({"allowed": allowed, "attempts": attempts}, sort_keys=True) + "\n"
    )
    print(f"Repair attempts: {attempts}/{args.max_attempts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
