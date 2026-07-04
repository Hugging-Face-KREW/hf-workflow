from __future__ import annotations

import hashlib
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hf_agent.lifecycle import Feedback, Snapshot, feedback_revision, lifecycle_state


def test_feedback_revision_uses_trusted_human_input_only() -> None:
    human = Feedback(
        kind="review_comment",
        comment_id="42",
        updated_at="2026-07-04T01:02:03Z",
        body="Please keep the original API name.",
    )
    expected = hashlib.sha256(
        b"review_comment\x1f42\x1f2026-07-04T01:02:03Z\x1fPlease keep the original API name."
    ).hexdigest()

    assert feedback_revision(
        [
            human,
            Feedback(
                kind="issue_comment",
                comment_id="43",
                updated_at="2026-07-04T01:03:00Z",
                body="Agent reply",
                trusted=False,
            ),
            Feedback(
                kind="issue_comment",
                comment_id="44",
                updated_at="2026-07-04T01:04:00Z",
                body="<!-- hf-agent-state {} -->",
                marker=True,
            ),
        ]
    ) == expected


def test_feedback_revision_is_order_independent() -> None:
    first = Feedback("review", "1", "2026-07-04T01:00:00Z", "First")
    second = Feedback("review", "2", "2026-07-04T02:00:00Z", "Second")

    assert feedback_revision([first, second]) == feedback_revision([second, first])


def test_lifecycle_is_pending_when_snapshot_changed() -> None:
    snapshot = Snapshot(
        head_sha="new-head",
        feedback_revision="new-feedback",
        expected_head_sha="old-head",
        expected_feedback_revision="old-feedback",
    )

    assert lifecycle_state(snapshot) == ("pending", "Pull request changed during review")


def test_lifecycle_requires_all_merge_conditions() -> None:
    ready = Snapshot(
        head_sha="abc123",
        feedback_revision="feedback",
        expected_head_sha="abc123",
        expected_feedback_revision="feedback",
        gates_passed=True,
        verifier_passed=True,
        report_published=True,
    )

    assert lifecycle_state(ready) == ("success", "Ready for human merge")
    assert lifecycle_state(ready.with_updates(unresolved_threads=1)) == (
        "failure",
        "Review threads are unresolved",
    )
    assert lifecycle_state(ready.with_updates(needs_human=True)) == (
        "failure",
        "Human decision required",
    )
