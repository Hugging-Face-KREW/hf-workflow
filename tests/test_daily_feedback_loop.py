from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hf_agent.daily_feedback_loop import build_pending_report, feedback_comments_from_json
from hf_agent.feedback_state import FeedbackState


def test_feedback_comments_from_pr_143_fixture_filters_preview_bot() -> None:
    pr_json = {
        "comments": [
            {
                "id": "IC_preview",
                "author": {"login": "github-actions"},
                "body": "Preview bot comment",
                "createdAt": "2026-06-10T04:48:41Z",
                "updatedAt": "2026-06-10T04:48:41Z",
            }
        ]
    }
    review_comments_json: list[dict] = []

    comments = feedback_comments_from_json(pr_json, review_comments_json)
    report = build_pending_report(
        target_repo="Hugging-Face-KREW/hugging-face-krew.github.io",
        pr_number="143",
        pr_url="https://github.com/Hugging-Face-KREW/hugging-face-krew.github.io/pull/143",
        comments=comments,
        state=FeedbackState(),
    )

    assert report["pending_count"] == 0
    assert report["pending"] == []


def test_build_pending_report_includes_new_and_edited_feedback() -> None:
    old_body = "기존 피드백"
    state = FeedbackState(
        processed_comments={
            "issue:1": {
                "body_hash": "not-current",
                "updated_at": "2026-06-15T00:00:00Z",
                "status": "applied",
            }
        }
    )
    pr_json = {
        "comments": [
            {
                "id": "1",
                "author": {"login": "reviewer"},
                "body": old_body,
                "createdAt": "2026-06-15T00:00:00Z",
                "updatedAt": "2026-06-15T00:10:00Z",
            },
            {
                "id": "2",
                "author": {"login": "reviewer"},
                "body": "새 피드백입니다.",
                "createdAt": "2026-06-15T00:11:00Z",
                "updatedAt": "2026-06-15T00:11:00Z",
            },
        ]
    }
    review_comments_json = [
        {
            "id": 9,
            "user": {"login": "reviewer"},
            "body": "라인 피드백입니다.",
            "created_at": "2026-06-15T00:12:00Z",
            "updated_at": "2026-06-15T00:12:00Z",
            "path": "_posts/example.md",
            "line": 10,
        }
    ]

    report = build_pending_report(
        target_repo="o/r",
        pr_number="143",
        pr_url="https://github.com/o/r/pull/143",
        comments=feedback_comments_from_json(pr_json, review_comments_json),
        state=state,
    )

    assert report["pending_count"] == 3
    statuses = {item["key"]: item["status"] for item in report["pending"]}
    assert statuses == {"issue:1": "edited", "issue:2": "new", "review:9": "new"}
    assert json.dumps(report, ensure_ascii=False)

