from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any


STATE_MARKER_START = "<!-- hf-agent-state"
STATE_MARKER_END = "-->"


@dataclass(frozen=True)
class FeedbackComment:
    kind: str
    comment_id: str
    author: str
    body: str
    created_at: str
    updated_at: str
    path: str = ""
    line: int | None = None


@dataclass(frozen=True)
class PendingFeedback:
    key: str
    status: str
    comment: FeedbackComment

    @property
    def body(self) -> str:
        return self.comment.body

    @property
    def path(self) -> str:
        return self.comment.path

    @property
    def line(self) -> int | None:
        return self.comment.line


@dataclass
class FeedbackState:
    version: int = 1
    mode: str = "daily-autopilot"
    last_run_at: str = ""
    last_applied_sha: str = ""
    processed_comments: dict[str, dict[str, str]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FeedbackState":
        return cls(
            version=int(data.get("version") or 1),
            mode=str(data.get("mode") or "daily-autopilot"),
            last_run_at=str(data.get("last_run_at") or ""),
            last_applied_sha=str(data.get("last_applied_sha") or ""),
            processed_comments=dict(data.get("processed_comments") or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "mode": self.mode,
            "last_run_at": self.last_run_at,
            "last_applied_sha": self.last_applied_sha,
            "processed_comments": self.processed_comments,
        }


def comment_key(kind: str, comment_id: str | int) -> str:
    return f"{kind}:{comment_id}"


def stable_body_hash(body: str) -> str:
    normalized = "\n".join(line.rstrip() for line in body.strip().replace("\r\n", "\n").split("\n"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def is_agent_marker_comment(body: str) -> bool:
    return "<!-- hf-workflow:skill-report" in body or STATE_MARKER_START in body


def classify_pending_feedback(
    comments: list[FeedbackComment],
    state: FeedbackState,
    bot_logins: set[str] | None = None,
) -> list[PendingFeedback]:
    bots = bot_logins or {"github-actions", "github-actions[bot]", "dependabot[bot]"}
    pending: list[PendingFeedback] = []
    for comment in comments:
        if comment.author in bots or comment.author.endswith("[bot]"):
            continue
        if is_agent_marker_comment(comment.body):
            continue
        if not comment.body.strip():
            continue

        key = comment_key(comment.kind, comment.comment_id)
        body_hash = stable_body_hash(comment.body)
        processed = state.processed_comments.get(key)
        if not processed:
            pending.append(PendingFeedback(key=key, status="new", comment=comment))
            continue
        if processed.get("body_hash") != body_hash:
            pending.append(PendingFeedback(key=key, status="edited", comment=comment))
    return pending


def parse_state_comment(body: str) -> FeedbackState:
    if STATE_MARKER_START not in body:
        return FeedbackState()
    match = re.search(
        re.escape(STATE_MARKER_START) + r"\s*(\{.*?\})\s*" + re.escape(STATE_MARKER_END),
        body,
        flags=re.DOTALL,
    )
    if not match:
        return FeedbackState()
    return FeedbackState.from_dict(json.loads(match.group(1)))


def render_state_comment(state: FeedbackState) -> str:
    payload = json.dumps(state.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
    return f"{STATE_MARKER_START}\n{payload}\n{STATE_MARKER_END}"

