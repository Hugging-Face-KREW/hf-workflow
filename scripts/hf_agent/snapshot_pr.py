from __future__ import annotations

import argparse
import json
import os
from pathlib import PurePosixPath
from typing import Any

from hf_agent.github_api import Requester, request_json
from hf_agent.lifecycle import Feedback, feedback_revision

TRUSTED_PERMISSIONS = {"admin", "maintain", "write"}
MANAGED_LABEL = "hf-agent:managed"
PAUSED_LABEL = "hf-agent:paused"
MARKER_PREFIX = "<!-- hf-agent-"
PAGE_SIZE = 100


def _load_all_pages(
    *,
    path: str,
    token: str,
    requester: Requester,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page = 1
    while True:
        page_path = path if page == 1 else f"{path}&page={page}"
        batch = requester("GET", page_path, token, None)
        if not isinstance(batch, list):
            raise TypeError(f"Expected a paginated list from GitHub: {page_path}")
        items.extend(batch)
        if len(batch) < PAGE_SIZE:
            return items
        page += 1


def _trusted_feedback(
    *,
    repository: str,
    token: str,
    requester: Requester,
    items: list[dict[str, Any]],
    kind: str,
    permission_cache: dict[str, str],
) -> list[Feedback]:
    feedback: list[Feedback] = []
    for item in items:
        user = item.get("user") or {}
        login = str(user.get("login", ""))
        body = str(item.get("body", "")).strip()
        if not login or not body or user.get("type") == "Bot" or MARKER_PREFIX in body:
            continue
        if login not in permission_cache:
            result = requester(
                "GET",
                f"/repos/{repository}/collaborators/{login}/permission",
                token,
                None,
            )
            permission_cache[login] = str(result.get("permission", "none"))
        if permission_cache[login] not in TRUSTED_PERMISSIONS:
            continue
        feedback.append(
            Feedback(
                kind=kind,
                comment_id=str(item["id"]),
                updated_at=str(item.get("updated_at") or item.get("submitted_at") or ""),
                body=body,
            )
        )
    return feedback


def load_pr_snapshot(
    *,
    repository: str,
    pr_number: int,
    token: str,
    requester: Requester = request_json,
) -> dict[str, Any]:
    pull = requester("GET", f"/repos/{repository}/pulls/{pr_number}", token, None)
    files = _load_all_pages(
        path=f"/repos/{repository}/pulls/{pr_number}/files?per_page={PAGE_SIZE}",
        token=token,
        requester=requester,
    )
    labels = {str(label["name"]) for label in pull.get("labels", [])}
    head = pull.get("head") or {}
    head_repo = head.get("repo") or {}
    managed = (
        pull.get("state") == "open"
        and head_repo.get("full_name") == repository
        and MANAGED_LABEL in labels
        and PAUSED_LABEL not in labels
    )

    post_files = [
        str(item["filename"])
        for item in files
        if PurePosixPath(str(item.get("filename", ""))).match("_posts/*.md")
    ]
    if managed and len(post_files) != 1:
        raise ValueError("Managed pull requests must change exactly one _posts Markdown file")

    sources = (
        (
            "issue_comment",
            f"/repos/{repository}/issues/{pr_number}/comments?per_page=100",
        ),
        ("review", f"/repos/{repository}/pulls/{pr_number}/reviews?per_page=100"),
        (
            "review_comment",
            f"/repos/{repository}/pulls/{pr_number}/comments?per_page=100",
        ),
    )
    permission_cache: dict[str, str] = {}
    feedback: list[Feedback] = []
    for kind, path in sources:
        items = _load_all_pages(path=path, token=token, requester=requester)
        feedback.extend(
            _trusted_feedback(
                repository=repository,
                token=token,
                requester=requester,
                items=items,
                kind=kind,
                permission_cache=permission_cache,
            )
        )

    return {
        "branch": str(head["ref"]),
        "feedback_revision": feedback_revision(feedback),
        "file_path": post_files[0] if len(post_files) == 1 else "",
        "head_sha": str(head["sha"]),
        "managed": managed,
        "pr_number": pr_number,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture a trusted pull request snapshot")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr-number", required=True, type=int)
    parser.add_argument("--result-json", required=True)
    args = parser.parse_args()

    snapshot = load_pr_snapshot(
        repository=args.repository,
        pr_number=args.pr_number,
        token=os.environ["GITHUB_TOKEN"],
    )
    with open(args.result_json, "w", encoding="utf-8") as output:
        json.dump(snapshot, output, sort_keys=True)


if __name__ == "__main__":
    main()
