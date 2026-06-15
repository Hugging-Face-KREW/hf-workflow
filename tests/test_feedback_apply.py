from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hf_agent.feedback_apply import build_feedback_prompt, mark_feedback_applied
from hf_agent.feedback_state import FeedbackComment, FeedbackState, PendingFeedback, stable_body_hash


def test_build_feedback_prompt_contains_manifest_file_and_comments() -> None:
    pending = [
        PendingFeedback(
            key="issue:2",
            status="new",
            comment=FeedbackComment(
                kind="issue",
                comment_id="2",
                author="reviewer",
                body="첫 문단 번역투를 자연스럽게 고쳐주세요.",
                created_at="2026-06-15T00:00:00Z",
                updated_at="2026-06-15T00:00:00Z",
            ),
        ),
        PendingFeedback(
            key="review:7",
            status="edited",
            comment=FeedbackComment(
                kind="review",
                comment_id="7",
                author="reviewer",
                body="이 문장은 원문의 CI 의미가 약해졌습니다.",
                created_at="2026-06-15T00:00:00Z",
                updated_at="2026-06-15T00:05:00Z",
                path="_posts/2026-06-09-github-ci-hf-jobs.md",
                line=88,
            ),
        ),
    ]

    prompt = build_feedback_prompt(
        manifest={"translation.file_path": "_posts/2026-06-09-github-ci-hf-jobs.md"},
        markdown="번역 본문",
        pending=pending,
    )

    assert "_posts/2026-06-09-github-ci-hf-jobs.md" in prompt
    assert "첫 문단 번역투" in prompt
    assert "review:7" in prompt
    assert "line 88" in prompt
    assert "Return only the full updated markdown" in prompt


def test_mark_feedback_applied_records_hashes_and_sha() -> None:
    state = FeedbackState()
    pending = [
        PendingFeedback(
            key="issue:2",
            status="new",
            comment=FeedbackComment(
                kind="issue",
                comment_id="2",
                author="reviewer",
                body="반영할 피드백",
                created_at="2026-06-15T00:00:00Z",
                updated_at="2026-06-15T00:01:00Z",
            ),
        )
    ]

    updated = mark_feedback_applied(
        state,
        pending,
        applied_sha="abc123",
        run_at="2026-06-15T01:00:00Z",
    )

    assert updated.last_applied_sha == "abc123"
    assert updated.last_run_at == "2026-06-15T01:00:00Z"
    assert updated.processed_comments["issue:2"]["body_hash"] == stable_body_hash("반영할 피드백")
    assert updated.processed_comments["issue:2"]["status"] == "applied"

