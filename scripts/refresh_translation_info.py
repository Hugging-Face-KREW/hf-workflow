from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse


DEFAULT_BLOG_ORIGIN = "https://huggingface.co"
FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
THUMBNAIL_RE = re.compile(r"^(?P<prefix>thumbnail:\s*)(?P<value>.+?)\s*$", re.MULTILINE)
VISIBLE_SOURCE_RE = re.compile(r"^>\s*Source:\s*(?P<url>https?://\S+)[^\S\r\n]*$")
SOURCE_COMMENT_RE = re.compile(
    r"^<!--\s*Source:\s*(?P<url>https?://\S+)\s*-->[^\S\r\n]*$"
)


def log(message: str) -> None:
    print(f"[refresh-translation-info] {message}", flush=True)


def run_cmd(
    args: list[str],
    cwd: Optional[Path] = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        command = " ".join(args)
        raise RuntimeError(
            f"Command failed: {command}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def parse_pr_numbers(raw: str) -> set[int]:
    values = [value.strip() for value in raw.split(",") if value.strip()]
    numbers: set[int] = set()
    for value in values:
        if not value.isdecimal():
            raise ValueError(f"Invalid PR number: {value}")
        numbers.add(int(value))
    return numbers


def unquote_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def normalize_thumbnail_url(thumbnail: str) -> str:
    value = unquote_yaml_scalar(thumbnail)
    if not value:
        return value
    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        return value
    if value.startswith("/"):
        return f"{DEFAULT_BLOG_ORIGIN}{value}"
    return value


def refresh_translation_markdown(markdown: str) -> str:
    normalized = markdown.replace("\r\n", "\n").replace("\r", "\n")
    frontmatter_match = FRONTMATTER_RE.match(normalized)
    if frontmatter_match:
        frontmatter = frontmatter_match.group("body")

        def replace_thumbnail(match: re.Match[str]) -> str:
            return f"{match.group('prefix')}{normalize_thumbnail_url(match.group('value'))}"

        refreshed_frontmatter = THUMBNAIL_RE.sub(replace_thumbnail, frontmatter)
        normalized = (
            "---\n"
            + refreshed_frontmatter
            + "\n---\n"
            + normalized[frontmatter_match.end() :]
        )

    lines = normalized.splitlines()
    source_index: Optional[int] = None
    source_url = ""
    for index, line in enumerate(lines):
        match = VISIBLE_SOURCE_RE.match(line) or SOURCE_COMMENT_RE.match(line)
        if match:
            source_index = index
            source_url = match.group("url")
            break

    if source_index is None:
        return normalized

    lines.pop(source_index)
    if (
        0 < source_index < len(lines)
        and not lines[source_index - 1].strip()
        and not lines[source_index].strip()
    ):
        lines.pop(source_index)

    attribution_index = next(
        (index for index, line in enumerate(lines) if line.startswith("_이 글은 Hugging Face 블로그의 [")),
        None,
    )
    source_comment = f"<!-- Source: {source_url} -->"
    if attribution_index is None:
        lines.insert(source_index, source_comment)
    else:
        suffix_index = attribution_index + 1
        while suffix_index < len(lines) and not lines[suffix_index].strip():
            suffix_index += 1
        lines[attribution_index + 1 : suffix_index] = ["", source_comment, ""]

    return "\n".join(lines) + ("\n" if normalized.endswith("\n") else "")


def list_open_translation_prs(
    target_repo: str,
    pr_numbers: Optional[set[int]] = None,
) -> list[dict[str, Any]]:
    result = run_cmd(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            target_repo,
            "--state",
            "open",
            "--limit",
            "100",
            "--json",
            "number,headRefName,isCrossRepository,files,url",
        ]
    )
    pulls = json.loads(result.stdout)
    translation_pulls = [
        pull
        for pull in pulls
        if pull.get("headRefName", "").startswith("translate/")
        and not pull.get("isCrossRepository", False)
    ]
    if pr_numbers is not None:
        translation_pulls = [
            pull for pull in translation_pulls if pull.get("number") in pr_numbers
        ]
        found_numbers = {pull["number"] for pull in translation_pulls}
        missing_numbers = sorted(pr_numbers - found_numbers)
        if missing_numbers:
            formatted = ", ".join(f"#{number}" for number in missing_numbers)
            raise RuntimeError(
                f"Open same-repository translation PRs were not found: {formatted}"
            )
    return translation_pulls


def translation_files(pull: dict[str, Any]) -> list[str]:
    return [
        item["path"]
        for item in pull.get("files", [])
        if item.get("path", "").startswith("_posts/") and item["path"].endswith(".md")
    ]


def refresh_pull(
    worktree: Path,
    pull: dict[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    branch = pull["headRefName"]
    number = pull["number"]
    files = translation_files(pull)
    if not files:
        return {"status": "skipped", "pr_number": number, "branch": branch, "files": []}

    run_cmd(["git", "fetch", "origin", branch], cwd=worktree)
    run_cmd(["git", "switch", "--detach", "FETCH_HEAD"], cwd=worktree)

    changed_files: list[str] = []
    for file_path in files:
        path = worktree / file_path
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8")
        refreshed = refresh_translation_markdown(original)
        if refreshed == original:
            continue
        changed_files.append(file_path)
        if not dry_run:
            path.write_text(refreshed, encoding="utf-8")

    if not changed_files:
        status = "unchanged"
    elif dry_run:
        status = "would_update"
    else:
        run_cmd(["git", "add", *changed_files], cwd=worktree)
        run_cmd(
            ["git", "commit", "-m", "🔧 Refresh translation info"],
            cwd=worktree,
        )
        run_cmd(["git", "push", "origin", f"HEAD:refs/heads/{branch}"], cwd=worktree)
        status = "updated"

    log(f"PR #{number} {branch}: {status} ({', '.join(changed_files) or 'no changes'})")
    return {
        "status": status,
        "pr_number": number,
        "branch": branch,
        "pr_url": pull.get("url", ""),
        "files": changed_files,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Refresh generated translation info without retranslating body content."
    )
    parser.add_argument("--target-worktree", required=True)
    parser.add_argument("--target-repo", required=True)
    parser.add_argument("--pr-numbers", default="")
    parser.add_argument("--run-summary", default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    worktree = Path(args.target_worktree).expanduser().resolve()
    if not worktree.exists():
        raise RuntimeError(f"Target worktree does not exist: {worktree}")

    base_branch = run_cmd(["git", "branch", "--show-current"], cwd=worktree).stdout.strip()
    if not base_branch:
        raise RuntimeError("Target worktree must start on a named base branch")

    pr_numbers = parse_pr_numbers(args.pr_numbers) if args.pr_numbers else None
    results: list[dict[str, Any]] = []
    try:
        for pull in list_open_translation_prs(args.target_repo, pr_numbers):
            results.append(refresh_pull(worktree, pull, args.dry_run))
    finally:
        run_cmd(["git", "switch", base_branch], cwd=worktree)

    if args.run_summary:
        summary_path = Path(args.run_summary)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps({"results": results}, indent=2) + "\n")
        log(f"Wrote run summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
