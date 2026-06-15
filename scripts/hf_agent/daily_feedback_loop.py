from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hf_agent.feedback_apply import build_feedback_prompt, rewrite_with_openai
from hf_agent.feedback_state import (
    FeedbackComment,
    FeedbackState,
    classify_pending_feedback,
    parse_state_comment,
    render_state_comment,
)
from hf_agent.manifest import read_simple_manifest


STATE_COMMENT_MARKER = "<!-- hf-agent-state"


def run_json(cmd: list[str]) -> Any:
    result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, text=True)
    return json.loads(result.stdout) if result.stdout.strip() else None


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def feedback_comments_from_json(pr_json: dict[str, Any], review_comments_json: list[dict[str, Any]]) -> list[FeedbackComment]:
    comments: list[FeedbackComment] = []
    for item in pr_json.get("comments") or []:
        comments.append(
            FeedbackComment(
                kind="issue",
                comment_id=str(item.get("id") or ""),
                author=str((item.get("author") or {}).get("login") or ""),
                body=str(item.get("body") or ""),
                created_at=str(item.get("createdAt") or item.get("created_at") or ""),
                updated_at=str(item.get("updatedAt") or item.get("updated_at") or item.get("createdAt") or ""),
            )
        )
    for item in review_comments_json:
        comments.append(
            FeedbackComment(
                kind="review",
                comment_id=str(item.get("id") or ""),
                author=str((item.get("user") or {}).get("login") or ""),
                body=str(item.get("body") or ""),
                created_at=str(item.get("created_at") or ""),
                updated_at=str(item.get("updated_at") or item.get("created_at") or ""),
                path=str(item.get("path") or ""),
                line=item.get("line") or item.get("original_line"),
            )
        )
    return comments


def state_from_pr_comments(pr_json: dict[str, Any]) -> FeedbackState:
    for item in pr_json.get("comments") or []:
        body = str(item.get("body") or "")
        if STATE_COMMENT_MARKER in body:
            return parse_state_comment(body)
    return FeedbackState()


def build_pending_report(
    *,
    target_repo: str,
    pr_number: str,
    pr_url: str,
    comments: list[FeedbackComment],
    state: FeedbackState,
) -> dict[str, Any]:
    pending = classify_pending_feedback(comments, state)
    return {
        "target_repo": target_repo,
        "pr_number": pr_number,
        "pr_url": pr_url,
        "pending_count": len(pending),
        "pending": [
            {
                "key": item.key,
                "status": item.status,
                "author": item.comment.author,
                "updated_at": item.comment.updated_at,
                "path": item.path,
                "line": item.line,
                "body": item.body,
            }
            for item in pending
        ],
    }


def fetch_pr_json(target_repo: str, pr_number: str) -> dict[str, Any]:
    return run_json(
        [
            "gh",
            "pr",
            "view",
            pr_number,
            "--repo",
            target_repo,
            "--json",
            "number,url,title,body,headRefName,state,labels,files,comments",
        ]
    )


def fetch_review_comments(target_repo: str, pr_number: str) -> list[dict[str, Any]]:
    data = run_json(["gh", "api", f"repos/{target_repo}/pulls/{pr_number}/comments", "--paginate"])
    return data or []


def upsert_state_comment(target_repo: str, pr_number: str, state: FeedbackState) -> None:
    body = render_state_comment(state)
    comments = run_json(["gh", "api", f"repos/{target_repo}/issues/{pr_number}/comments?per_page=100"]) or []
    existing_id = ""
    for item in comments:
        if STATE_COMMENT_MARKER in str(item.get("body") or ""):
            existing_id = str(item.get("id") or "")
            break
    if existing_id:
        run(["gh", "api", f"repos/{target_repo}/issues/comments/{existing_id}", "-X", "PATCH", "-f", f"body={body}"])
    else:
        run(["gh", "api", f"repos/{target_repo}/issues/{pr_number}/comments", "-X", "POST", "-f", f"body={body}"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect and optionally apply daily PR feedback.")
    parser.add_argument("--target-repo", required=True)
    parser.add_argument("--pr-number", required=True)
    parser.add_argument("--target-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--openai-model", default="gpt-5-nano")
    args = parser.parse_args()

    target_root = Path(args.target_root).resolve()
    manifest_path = Path(args.manifest).resolve()
    manifest = read_simple_manifest(manifest_path)
    file_path = manifest.get("translation.file_path", "")
    translation_path = target_root / file_path
    if not translation_path.exists():
        raise FileNotFoundError(f"Translation file does not exist: {translation_path}")

    pr_json = fetch_pr_json(args.target_repo, args.pr_number)
    review_comments = fetch_review_comments(args.target_repo, args.pr_number)
    comments = feedback_comments_from_json(pr_json, review_comments)
    state = state_from_pr_comments(pr_json)
    pending = classify_pending_feedback(comments, state)
    report = build_pending_report(
        target_repo=args.target_repo,
        pr_number=args.pr_number,
        pr_url=str(pr_json.get("url") or ""),
        comments=comments,
        state=state,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(f"Wrote pending feedback report: {output}")

    if not args.apply or not pending:
        return 0

    markdown = translation_path.read_text()
    prompt = build_feedback_prompt(manifest=manifest, markdown=markdown, pending=pending)
    updated = rewrite_with_openai(prompt, args.openai_model)
    if updated == markdown:
        print("Feedback application produced no changes.")
        return 0

    translation_path.write_text(updated)
    run(["git", "add", file_path], cwd=target_root)
    run(["git", "commit", "-m", f"Apply daily feedback for PR #{args.pr_number}"], cwd=target_root)
    applied_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=target_root,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    run(["git", "push"], cwd=target_root)

    from hf_agent.feedback_apply import mark_feedback_applied

    updated_state = mark_feedback_applied(
        state,
        pending,
        applied_sha=applied_sha,
        run_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    upsert_state_comment(args.target_repo, args.pr_number, updated_state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

