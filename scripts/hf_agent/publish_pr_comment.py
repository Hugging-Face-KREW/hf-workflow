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


def result_json_marker(result: dict) -> str:
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True).replace("--", "\\u002d\\u002d")
    return f"<!-- hf-agent-skill-result-json\n{payload}\n-->"


def pr_number_from_url(pr_url: str) -> str:
    match = re.search(r"/pull/(\d+)(?:$|[/?#])", pr_url)
    return match.group(1) if match else ""


def display_path(path_value: str) -> str:
    path = Path(path_value)
    if not path.is_absolute():
        return path_value
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return path.name


def finding_lines(skill_result: dict, max_items: int = 12) -> list[str]:
    findings = skill_result.get("findings") or []
    if not findings:
        return ["_No findings._"]
    lines: list[str] = []
    for finding in findings[:max_items]:
        severity = str(finding.get("severity") or "info").upper()
        message = str(finding.get("message") or "").strip()
        path = str(finding.get("path") or "").strip()
        line = finding.get("line")
        location = f" `{path}`" if path else ""
        if line:
            location += f":{line}"
        lines.append(f"- {severity}:{location} {message}".rstrip())
    if len(findings) > max_items:
        lines.append(f"- ...and {len(findings) - max_items} more finding(s).")
    return lines


def build_comment_body(target_repo: str, pr_number: str, run_state: dict) -> str:
    parts = [
        marker(target_repo, pr_number),
        result_json_marker(run_state),
        "# HF Agent Skill Report",
        "",
        f"- Stage: `{run_state.get('stage', '')}`",
        f"- Conclusion: `{run_state.get('conclusion', '')}`",
        f"- Translation file: `{run_state.get('translation_file', '')}`",
        f"- Manifest: `{display_path(str(run_state.get('manifest', '')))}`",
        "",
    ]
    for skill_result in run_state.get("skills") or []:
        skill = skill_result.get("skill") or {}
        skill_id = str(skill.get("id") or "unknown")
        parts += [
            f"## {skill_id}",
            "",
            f"- Conclusion: `{skill_result.get('conclusion', '')}`",
            f"- Summary: {skill_result.get('summary', '')}",
            "",
            "### Findings",
            "",
            *finding_lines(skill_result),
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
    parser.add_argument("--target-repo", default="", help="Target repo. Defaults to result JSON target_repo.")
    parser.add_argument("--pr-number", default="", help="Target PR number. Defaults to result JSON pr_url.")
    parser.add_argument("--result-json", default="", help="Path to hf.agent.skill_run.v1 JSON.")
    parser.add_argument("--body-output", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--create-only", action="store_true", help="Use gh pr comment without marker upsert.")
    args = parser.parse_args()

    if not args.result_json:
        raise RuntimeError("--result-json is required.")
    run_state = json.loads(Path(args.result_json).read_text())
    target_repo = args.target_repo or str(run_state.get("target_repo") or "")
    pr_number = args.pr_number or pr_number_from_url(str(run_state.get("pr_url") or ""))
    if not target_repo:
        raise RuntimeError("target_repo is required in result JSON or --target-repo.")
    if not pr_number:
        raise RuntimeError("PR number is required in result JSON pr_url or --pr-number.")

    body = build_comment_body(target_repo, pr_number, run_state)
    body_output = Path(args.body_output) if args.body_output else None
    if body_output:
        body_output.parent.mkdir(parents=True, exist_ok=True)
        body_output.write_text(body)

    if args.dry_run:
        if body_output:
            print(f"Wrote comment body without publishing: {body_output}")
        else:
            print(body)
        return 0

    if args.create_only:
        if not body_output:
            body_output = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "hf-agent-comment.md"
            body_output.write_text(body)
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
