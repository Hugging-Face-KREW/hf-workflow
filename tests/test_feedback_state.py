from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hf_agent.feedback_state import (
    FeedbackComment,
    FeedbackState,
    classify_pending_feedback,
    comment_key,
    stable_body_hash,
)


def test_comment_key_separates_issue_and_review_comments() -> None:
    assert comment_key("issue", "123") == "issue:123"
    assert comment_key("review", 456) == "review:456"


def test_stable_body_hash_normalizes_line_endings_and_edges() -> None:
    assert stable_body_hash(" hello\r\n") == stable_body_hash("hello\n")


def test_classify_pending_feedback_filters_bots_and_processed_comments() -> None:
    existing_hash = stable_body_hash("이미 반영된 피드백")
    state = FeedbackState(
        version=1,
        processed_comments={
            "issue:1": {
                "body_hash": existing_hash,
                "updated_at": "2026-06-15T00:00:00Z",
                "status": "applied",
            }
        },
    )
    comments = [
        FeedbackComment(
            kind="issue",
            comment_id="preview",
            author="github-actions",
            body="preview bot",
            created_at="2026-06-15T00:00:00Z",
            updated_at="2026-06-15T00:00:00Z",
        ),
        FeedbackComment(
            kind="issue",
            comment_id="1",
            author="reviewer",
            body="이미 반영된 피드백",
            created_at="2026-06-15T00:00:00Z",
            updated_at="2026-06-15T00:00:00Z",
        ),
        FeedbackComment(
            kind="issue",
            comment_id="2",
            author="reviewer",
            body="이 문단은 번역투라 자연스럽게 고쳐주세요.",
            created_at="2026-06-15T00:01:00Z",
            updated_at="2026-06-15T00:01:00Z",
        ),
    ]

    pending = classify_pending_feedback(comments, state, bot_logins={"github-actions"})

    assert [item.key for item in pending] == ["issue:2"]
    assert pending[0].status == "new"


def test_classify_pending_feedback_reopens_edited_comment() -> None:
    state = FeedbackState(
        version=1,
        processed_comments={
            "review:77": {
                "body_hash": stable_body_hash("원래 피드백"),
                "updated_at": "2026-06-15T00:00:00Z",
                "status": "applied",
            }
        },
    )
    comments = [
        FeedbackComment(
            kind="review",
            comment_id="77",
            author="reviewer",
            body="수정된 피드백입니다. 원문 의미를 더 살려주세요.",
            created_at="2026-06-15T00:00:00Z",
            updated_at="2026-06-15T00:10:00Z",
            path="_posts/2026-06-09-github-ci-hf-jobs.md",
            line=42,
        )
    ]

    pending = classify_pending_feedback(comments, state)

    assert [item.key for item in pending] == ["review:77"]
    assert pending[0].status == "edited"
    assert pending[0].path == "_posts/2026-06-09-github-ci-hf-jobs.md"
    assert pending[0].line == 42

