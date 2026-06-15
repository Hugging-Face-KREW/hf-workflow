from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
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
SKILL_RESULT_MARKER_START = "<!-- hf-agent-skill-result-json"
SKILL_RESULT_MARKER_END = "-->"
MERGE_READY_MARKER = "<!-- hf-agent-merge-ready"


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


def extract_skill_result_from_body(body: str) -> dict[str, Any] | None:
    if SKILL_RESULT_MARKER_START not in body:
        return None
    match = re.search(
        re.escape(SKILL_RESULT_MARKER_START) + r"\s*(\{.*?\})\s*" + re.escape(SKILL_RESULT_MARKER_END),
        body,
        flags=re.DOTALL,
    )
    if not match:
        return None
    return json.loads(match.group(1))


def latest_skill_result_from_pr_comments(pr_json: dict[str, Any]) -> dict[str, Any] | None:
    results: list[tuple[str, dict[str, Any]]] = []
    for item in pr_json.get("comments") or []:
        result = extract_skill_result_from_body(str(item.get("body") or ""))
        if result is None:
            continue
        updated_at = str(item.get("updatedAt") or item.get("updated_at") or item.get("createdAt") or "")
        results.append((updated_at, result))
    if not results:
        return None
    return sorted(results, key=lambda item: item[0])[-1][1]


def skill_result_is_merge_ready(result: dict[str, Any] | None) -> bool:
    if result is None:
        return False
    if str(result.get("conclusion") or "") != "pass":
        return False
    for skill in result.get("skills") or []:
        if str(skill.get("conclusion") or "") != "pass":
            return False
    return True


def should_apply_label(pr_json: dict[str, Any], required_label: str) -> bool:
    if not required_label:
        return True
    return required_label in {str(item.get("name") or "") for item in pr_json.get("labels") or []}


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
            "number,url,title,body,headRefName,headRefOid,state,labels,files,comments",
        ]
    )


def fetch_review_comments(target_repo: str, pr_number: str) -> list[dict[str, Any]]:
    data = run_json(["gh", "api", f"repos/{target_repo}/pulls/{pr_number}/comments", "--paginate"])
    return data or []


def upsert_state_comment(target_repo: str, pr_number: str, state: FeedbackState) -> None:
    body = render_state_comment(state)
    upsert_issue_comment(target_repo, pr_number, STATE_COMMENT_MARKER, body)


def upsert_issue_comment(target_repo: str, pr_number: str, marker: str, body: str) -> None:
    comments = run_json(["gh", "api", f"repos/{target_repo}/issues/{pr_number}/comments?per_page=100"]) or []
    existing_id = ""
    for item in comments:
        if marker in str(item.get("body") or ""):
            existing_id = str(item.get("id") or "")
            break
    if existing_id:
        run(["gh", "api", f"repos/{target_repo}/issues/comments/{existing_id}", "-X", "PATCH", "-f", f"body={body}"])
    else:
        run(["gh", "api", f"repos/{target_repo}/issues/{pr_number}/comments", "-X", "POST", "-f", f"body={body}"])


def build_merge_ready_comment(
    *,
    target_repo: str,
    pr_number: str,
    head_sha: str,
    skill_result: dict[str, Any],
) -> str:
    skills = ", ".join(
        f"{str((item.get('skill') or {}).get('id') or 'unknown')}={str(item.get('conclusion') or '')}"
        for item in skill_result.get("skills") or []
    )
    checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return "\n".join(
        [
            f"{MERGE_READY_MARKER} repo={target_repo} pr={pr_number} head={head_sha} -->",
            "# HF Agent Merge Ready",
            "",
            "현재 확인 가능한 피드백은 모두 처리되었고, 최신 skill run이 `pass`입니다.",
            "일반 CI와 사람 리뷰 정책을 만족하면 이 번역 PR은 머지할 수 있습니다.",
            "",
            f"- Head SHA: `{head_sha}`",
            f"- Skill conclusion: `{skill_result.get('conclusion', '')}`",
            f"- Skills: `{skills}`",
            f"- Checked at: `{checked_at}`",
            "",
        ]
    )


def upsert_merge_ready_comment(
    *,
    target_repo: str,
    pr_number: str,
    head_sha: str,
    skill_result: dict[str, Any],
) -> None:
    body = build_merge_ready_comment(
        target_repo=target_repo,
        pr_number=pr_number,
        head_sha=head_sha,
        skill_result=skill_result,
    )
    upsert_issue_comment(target_repo, pr_number, MERGE_READY_MARKER, body)


def rerun_skill_review(
    *,
    target_repo: str,
    pr_number: str,
    manifest_path: Path,
    target_root: Path,
) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="hf-agent-skill-rerun-") as tmp:
        result_json = Path(tmp) / "hf-agent-skill-result.json"
        run(
            [
                "python3",
                "scripts/hf_agent/run_skill_review.py",
                "--manifest",
                str(manifest_path),
                "--target-root",
                str(target_root),
                "--stage",
                "all",
                "--result-json",
                str(result_json),
            ],
            cwd=repo_root,
        )
        run(
            [
                "python3",
                "scripts/hf_agent/publish_pr_comment.py",
                "--target-repo",
                target_repo,
                "--pr-number",
                pr_number,
                "--result-json",
                str(result_json),
            ],
            cwd=repo_root,
        )
        return json.loads(result_json.read_text())


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect and optionally apply daily PR feedback.")
    parser.add_argument("--target-repo", required=True)
    parser.add_argument("--pr-number", required=True)
    parser.add_argument("--target-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--required-label", default="")
    parser.add_argument("--openai-model", default="gpt-5-nano")
    parser.add_argument("--skip-skill-rerun", action="store_true")
    args = parser.parse_args()

    target_root = Path(args.target_root).resolve()
    manifest_path = Path(args.manifest).resolve()
    manifest = read_simple_manifest(manifest_path)
    file_path = manifest.get("translation.file_path", "")
    translation_path = target_root / file_path
    if not translation_path.exists():
        raise FileNotFoundError(f"Translation file does not exist: {translation_path}")

    pr_json = fetch_pr_json(args.target_repo, args.pr_number)
    if args.apply and args.required_label and not should_apply_label(pr_json, args.required_label):
        print(f"Skipping apply because PR does not have required label: {args.required_label}")
        args.apply = False

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

    if not pending:
        latest_skill_result = latest_skill_result_from_pr_comments(pr_json)
        if args.apply and skill_result_is_merge_ready(latest_skill_result):
            upsert_merge_ready_comment(
                target_repo=args.target_repo,
                pr_number=args.pr_number,
                head_sha=str(pr_json.get("headRefOid") or ""),
                skill_result=latest_skill_result,
            )
        return 0

    if not args.apply:
        return 0

    run_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    markdown = translation_path.read_text()
    prompt = build_feedback_prompt(manifest=manifest, markdown=markdown, pending=pending)
    updated = rewrite_with_openai(prompt, args.openai_model)
    if updated == markdown:
        print("Feedback application produced no changes.")
        from hf_agent.feedback_apply import mark_feedback_processed

        updated_state = mark_feedback_processed(
            state,
            pending,
            applied_sha="",
            run_at=run_at,
            status="no_changes",
        )
        upsert_state_comment(args.target_repo, args.pr_number, updated_state)
        if not args.skip_skill_rerun:
            skill_result = rerun_skill_review(
                target_repo=args.target_repo,
                pr_number=args.pr_number,
                manifest_path=manifest_path,
                target_root=target_root,
            )
            if skill_result_is_merge_ready(skill_result):
                upsert_merge_ready_comment(
                    target_repo=args.target_repo,
                    pr_number=args.pr_number,
                    head_sha=str(pr_json.get("headRefOid") or ""),
                    skill_result=skill_result,
                )
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
        run_at=run_at,
    )
    upsert_state_comment(args.target_repo, args.pr_number, updated_state)
    if not args.skip_skill_rerun:
        skill_result = rerun_skill_review(
            target_repo=args.target_repo,
            pr_number=args.pr_number,
            manifest_path=manifest_path,
            target_root=target_root,
        )
        if skill_result_is_merge_ready(skill_result):
            upsert_merge_ready_comment(
                target_repo=args.target_repo,
                pr_number=args.pr_number,
                head_sha=applied_sha,
                skill_result=skill_result,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
