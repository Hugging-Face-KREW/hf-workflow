from __future__ import annotations

import json
import urllib.request
from typing import Any, Callable

from hf_agent.lifecycle import LifecycleState


API_ROOT = "https://api.github.com"
API_VERSION = "2022-11-28"
LIFECYCLE_CONTEXT = "HF Agent / Lifecycle Gate"
USER_AGENT = "hf-pr-agent/1.0"
Requester = Callable[[str, str, str, dict[str, Any] | None], Any]


def request_json(
    method: str,
    path: str,
    token: str,
    payload: dict[str, Any] | None = None,
) -> Any:
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"{API_ROOT}{path}",
        data=data,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": API_VERSION,
        },
        method=method,
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read()
        return json.loads(body) if body else None


def upsert_issue_comment(
    *,
    repository: str,
    issue_number: int,
    marker: str,
    body: str,
    token: str,
    requester: Requester = request_json,
) -> None:
    comments = requester(
        "GET",
        f"/repos/{repository}/issues/{issue_number}/comments?per_page=100",
        token,
        None,
    )
    existing = next(
        (comment for comment in comments if str(comment.get("body", "")).startswith(marker)),
        None,
    )
    if existing:
        path = f"/repos/{repository}/issues/comments/{existing['id']}"
        requester("PATCH", path, token, {"body": body})
    else:
        path = f"/repos/{repository}/issues/{issue_number}/comments"
        requester("POST", path, token, {"body": body})


def publish_commit_status(
    *,
    repository: str,
    sha: str,
    state: LifecycleState,
    description: str,
    token: str,
    target_url: str = "",
) -> None:
    payload: dict[str, Any] = {
        "context": LIFECYCLE_CONTEXT,
        "description": description,
        "state": state,
    }
    if target_url:
        payload["target_url"] = target_url
    request = urllib.request.Request(
        f"{API_ROOT}/repos/{repository}/statuses/{sha}",
        data=json.dumps(payload).encode(),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": API_VERSION,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 201:
            raise RuntimeError(f"GitHub returned HTTP {response.status} while publishing status")
