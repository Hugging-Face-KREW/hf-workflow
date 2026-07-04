from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from typing import Literal


LifecycleState = Literal["pending", "success", "failure", "error"]


@dataclass(frozen=True)
class Feedback:
    kind: str
    comment_id: str
    updated_at: str
    body: str
    trusted: bool = True
    marker: bool = False


@dataclass(frozen=True)
class Snapshot:
    head_sha: str
    feedback_revision: str
    expected_head_sha: str
    expected_feedback_revision: str
    gates_passed: bool = False
    verifier_passed: bool = False
    report_published: bool = False
    unresolved_threads: int = 0
    needs_human: bool = False

    def with_updates(self, **changes: object) -> "Snapshot":
        return replace(self, **changes)


def feedback_revision(feedback: list[Feedback]) -> str:
    records = sorted(
        "\x1f".join((item.kind, item.comment_id, item.updated_at, item.body))
        for item in feedback
        if item.trusted and not item.marker
    )
    return hashlib.sha256("\x1e".join(records).encode()).hexdigest()


def lifecycle_state(snapshot: Snapshot) -> tuple[LifecycleState, str]:
    if (
        snapshot.head_sha != snapshot.expected_head_sha
        or snapshot.feedback_revision != snapshot.expected_feedback_revision
    ):
        return "pending", "Pull request changed during review"
    if snapshot.needs_human:
        return "failure", "Human decision required"
    if snapshot.unresolved_threads:
        return "failure", "Review threads are unresolved"
    if not snapshot.gates_passed:
        return "failure", "Blocking gates failed"
    if not snapshot.verifier_passed:
        return "failure", "Independent verification failed"
    if not snapshot.report_published:
        return "error", "Review report was not published"
    return "success", "Ready for human merge"
