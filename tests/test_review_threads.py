from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hf_agent.review_threads import (
    find_thread_id,
    list_unresolved_threads,
    reply_and_resolve,
    thread_gate,
)


def test_list_unresolved_threads_filters_resolved_nodes() -> None:
    calls = []

    def requester(method, path, token, payload=None):
        calls.append((method, path, payload))
        return {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [
                                {"id": "open", "isResolved": False, "path": "post.md", "line": 4},
                                {"id": "done", "isResolved": True, "path": "post.md", "line": 8},
                            ]
                        }
                    }
                }
            }
        }

    threads = list_unresolved_threads(
        repository="owner/repo",
        pr_number=161,
        token="token",
        requester=requester,
    )

    assert [thread["id"] for thread in threads] == ["open"]
    assert calls[0][0:2] == ("POST", "/graphql")
    assert calls[0][2]["variables"] == {"name": "repo", "number": 161, "owner": "owner"}


def test_reply_and_resolve_keeps_evidence_order() -> None:
    calls = []

    def requester(method, path, token, payload=None):
        calls.append(payload)
        return {"data": {}}

    reply_and_resolve(
        thread_id="thread-id",
        body="Addressed in abc123 after verification.",
        token="token",
        requester=requester,
    )

    assert "addPullRequestReviewThreadReply" in calls[0]["query"]
    assert calls[0]["variables"]["body"] == "Addressed in abc123 after verification."
    assert "resolveReviewThread" in calls[1]["query"]


def test_thread_gate_returns_the_unresolved_count() -> None:
    count = thread_gate(
        repository="owner/repo",
        pr_number=161,
        token="token",
        loader=lambda **_: [{"id": "one"}, {"id": "two"}],
    )

    assert count == 2


def test_find_thread_id_matches_the_rest_comment_database_id() -> None:
    threads = [
        {"id": "thread-one", "comments": {"nodes": [{"databaseId": 41}]}},
        {"id": "thread-two", "comments": {"nodes": [{"databaseId": 42}]}},
    ]

    assert find_thread_id(threads, comment_id=42) == "thread-two"
