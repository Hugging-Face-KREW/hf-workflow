from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path


API_ROOT = "https://api.github.com"


def marker(target_repo: str, pr_number: str) -> str:
    return f"<!-- hf-workflow:skill-report repo={target_repo} pr={pr_number} -->"


def pr_number_from_url(pr_url: str) -> str:
    match = re.search(r"/pull/(\d+)(?:$|[/?#])", pr_url)
    return match.group(1) if match else ""


def report_excerpt(path: Path, max_lines: int = 18) -> str:
    if not path.exists():
        return "_Not generated in this run._"
    lines = path.read_text().splitlines()
    selected: list[str] = []
    for line in lines:
        if line.startswith("# "):
            continue
        selected.append(line)
        if len(selected) >= max_lines:
            break
    return "\n".join(selected).strip() or "_Report is empty._"


def display_path(path_value: str) -> str:
    path = Path(path_value)
    if not path.is_absolute():
        return path_value
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return path.name


def build_comment_body(target_repo: str, pr_number: str, run_state: dict) -> str:
    report_dir = Path(run_state["report_dir"])
    parts = [
        marker(target_repo, pr_number),
        "# HF Agent Skill Report",
        "",
        f"- Stage: `{run_state.get('stage', '')}`",
        f"- Lifecycle: `{run_state.get('lifecycle', '')}`",
        f"- Translation file: `{run_state.get('translation_file', '')}`",
        f"- Manifest: `{display_path(str(run_state.get('manifest', '')))}`",
        "",
        "## SEO",
        "",
        report_excerpt(report_dir / "seo-report.md"),
        "",
        "## Quality",
        "",
        report_excerpt(report_dir / "quality-report.md"),
        "",
        "## Humanize Korean",
        "",
        report_excerpt(report_dir / "humanize-report.md"),
        "",
    ]
    return "\n".join(parts)


def gh_api(method: str, path: str, token: str, payload: dict | None = None) -> dict | list:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        f"{API_ROOT}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "hf-agent-workflow",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {path} failed: HTTP {exc.code}: {detail}") from exc
    return json.loads(raw) if raw else {}


def find_existing_comment(target_repo: str, pr_number: str, token: str) -> int | None:
    wanted = marker(target_repo, pr_number)
    comments = gh_api("GET", f"/repos/{target_repo}/issues/{pr_number}/comments?per_page=100", token)
    if not isinstance(comments, list):
        return None
    for comment in comments:
        body = str(comment.get("body") or "")
        if wanted in body:
            return int(comment["id"])
    return None


def upsert_comment(target_repo: str, pr_number: str, body: str, token: str) -> str:
    existing_id = find_existing_comment(target_repo, pr_number, token)
    if existing_id is None:
        gh_api("POST", f"/repos/{target_repo}/issues/{pr_number}/comments", token, {"body": body})
        return "created"
    gh_api("PATCH", f"/repos/{target_repo}/issues/comments/{existing_id}", token, {"body": body})
    return "updated"


def gh_cli_comment(target_repo: str, pr_number: str, body_file: Path) -> None:
    subprocess.run(
        ["gh", "pr", "comment", pr_number, "--repo", target_repo, "--body-file", str(body_file)],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish or update the HF agent skill report PR comment.")
    parser.add_argument("--target-repo", default="", help="Target repo. Defaults to run.json target_repo.")
    parser.add_argument("--pr-number", default="", help="Target PR number. Defaults to run.json pr_url.")
    parser.add_argument("--run-json", required=True)
    parser.add_argument("--body-output", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--create-only", action="store_true", help="Use gh pr comment without marker upsert.")
    args = parser.parse_args()

    run_state = json.loads(Path(args.run_json).read_text())
    target_repo = args.target_repo or str(run_state.get("target_repo") or "")
    pr_number = args.pr_number or pr_number_from_url(str(run_state.get("pr_url") or ""))
    if not target_repo:
        raise RuntimeError("target_repo is required in run.json or --target-repo.")
    if not pr_number:
        raise RuntimeError("PR number is required in run.json pr_url or --pr-number.")

    body = build_comment_body(target_repo, pr_number, run_state)
    body_output = Path(args.body_output) if args.body_output else Path(run_state["report_dir"]) / "comment.md"
    body_output.parent.mkdir(parents=True, exist_ok=True)
    body_output.write_text(body)

    if args.dry_run:
        print(f"Wrote comment body without publishing: {body_output}")
        return 0

    if args.create_only:
        gh_cli_comment(target_repo, pr_number, body_output)
        print("Created PR comment with gh CLI.")
        return 0

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GH_TOKEN or GITHUB_TOKEN is required to upsert a PR comment.")
    result = upsert_comment(target_repo, pr_number, body, token)
    print(f"PR comment {result}: {target_repo}#{pr_number}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
