from __future__ import annotations

import difflib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


Disposition = Literal["actionable", "addressed", "no-change", "needs-human"]
TRUSTED_PERMISSIONS = {"write", "maintain", "admin"}


@dataclass(frozen=True)
class FeedbackEvent:
    event_name: str
    pr_number: int
    comment_id: str
    author: str
    body: str


@dataclass(frozen=True)
class ApplyResult:
    disposition: Disposition
    reason: str
    content: str


def parse_feedback_event(
    event_name: str,
    payload: dict[str, Any],
    *,
    permission: str,
) -> FeedbackEvent:
    if permission not in TRUSTED_PERMISSIONS:
        raise ValueError("Feedback author is not a trusted reviewer")
    if event_name == "issue_comment":
        pull_request = payload.get("issue", {})
        comment = payload.get("comment", {})
        if "pull_request" not in pull_request:
            raise ValueError("Issue comment is not attached to a pull request")
    elif event_name == "pull_request_review":
        pull_request = payload.get("pull_request", {})
        comment = payload.get("review", {})
    elif event_name == "pull_request_review_comment":
        pull_request = payload.get("pull_request", {})
        comment = payload.get("comment", {})
    else:
        raise ValueError(f"Unsupported feedback event: {event_name}")

    labels = {item.get("name", "") for item in pull_request.get("labels", [])}
    if pull_request.get("state") != "open" or "hf-agent:managed" not in labels:
        raise ValueError("Pull request is not open and managed")
    if "hf-agent:paused" in labels:
        raise ValueError("Pull request automation is paused")

    author = comment.get("user", {})
    body = str(comment.get("body") or "").strip()
    if author.get("type") == "Bot" or "<!-- hf-agent-" in body:
        raise ValueError("Bot and marker comments do not trigger feedback")
    if not body:
        raise ValueError("Feedback body is empty")

    return FeedbackEvent(
        event_name=event_name,
        pr_number=int(pull_request["number"]),
        comment_id=str(comment["id"]),
        author=str(author["login"]),
        body=body,
    )


def resolve_translation_path(target_root: Path, file_path: str) -> Path:
    relative = Path(file_path)
    candidate = (target_root / relative).resolve()
    posts_root = (target_root / "_posts").resolve()
    if relative.suffix != ".md" or posts_root not in candidate.parents:
        raise ValueError("Feedback can only change one translation post")
    return candidate


def apply_model_response(
    original: str,
    response: str,
    *,
    max_changed_lines: int,
) -> ApplyResult:
    payload = json.loads(response)
    disposition = payload.get("disposition")
    if disposition not in {"actionable", "addressed", "no-change", "needs-human"}:
        raise ValueError("Model returned an invalid disposition")
    reason = str(payload.get("reason") or "").strip()
    content = str(payload.get("content") or original)

    if disposition == "actionable":
        if content == original:
            raise ValueError("Actionable feedback produced no change")
        changed_lines = sum(
            line.startswith(("+ ", "- "))
            for line in difflib.ndiff(original.splitlines(), content.splitlines())
        )
        if changed_lines > max_changed_lines:
            raise ValueError("Change exceeds the changed-line limit")
    else:
        content = original

    return ApplyResult(disposition=disposition, reason=reason, content=content)
