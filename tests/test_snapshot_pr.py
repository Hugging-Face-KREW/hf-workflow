from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hf_agent.lifecycle import Feedback, feedback_revision
from hf_agent.snapshot_pr import load_pr_snapshot


def test_snapshot_uses_current_head_and_trusted_feedback_only() -> None:
    responses = {
        "/repos/owner/repo/pulls/161": {
            "head": {"sha": "abc123", "ref": "translate/post", "repo": {"full_name": "owner/repo"}},
            "labels": [{"name": "hf-agent:managed"}],
            "state": "open",
        },
        "/repos/owner/repo/pulls/161/files?per_page=100": [
            {"filename": "_posts/2026-01-01-post.md"}
        ],
        "/repos/owner/repo/issues/161/comments?per_page=100": [
            {
                "id": 10,
                "updated_at": "2026-07-04T01:00:00Z",
                "body": "Trusted feedback",
                "user": {"login": "reviewer", "type": "User"},
            },
            {
                "id": 11,
                "updated_at": "2026-07-04T01:01:00Z",
                "body": "Untrusted feedback",
                "user": {"login": "reader", "type": "User"},
            },
        ],
        "/repos/owner/repo/pulls/161/reviews?per_page=100": [],
        "/repos/owner/repo/pulls/161/comments?per_page=100": [],
        "/repos/owner/repo/collaborators/reviewer/permission": {"permission": "write"},
        "/repos/owner/repo/collaborators/reader/permission": {"permission": "read"},
    }

    def requester(method, path, token, payload=None):
        return responses[path]

    snapshot = load_pr_snapshot(
        repository="owner/repo",
        pr_number=161,
        token="token",
        requester=requester,
    )

    expected_revision = feedback_revision(
        [Feedback("issue_comment", "10", "2026-07-04T01:00:00Z", "Trusted feedback")]
    )
    assert snapshot == {
        "branch": "translate/post",
        "feedback_revision": expected_revision,
        "file_path": "_posts/2026-01-01-post.md",
        "head_sha": "abc123",
        "managed": True,
        "pr_number": 161,
    }
