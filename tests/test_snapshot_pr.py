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


def test_snapshot_allows_non_translation_files_for_unmanaged_pr() -> None:
    responses = {
        "/repos/owner/repo/pulls/164": {
            "head": {"sha": "infra", "ref": "infra", "repo": {"full_name": "owner/repo"}},
            "labels": [],
            "state": "open",
        },
        "/repos/owner/repo/pulls/164/files?per_page=100": [
            {"filename": ".github/workflows/hf-agent-review.yml"}
        ],
        "/repos/owner/repo/issues/164/comments?per_page=100": [],
        "/repos/owner/repo/pulls/164/reviews?per_page=100": [],
        "/repos/owner/repo/pulls/164/comments?per_page=100": [],
    }

    snapshot = load_pr_snapshot(
        repository="owner/repo",
        pr_number=164,
        token="token",
        requester=lambda method, path, token, payload=None: responses[path],
    )

    assert snapshot["managed"] is False
    assert snapshot["file_path"] == ""


def test_snapshot_paginates_files_and_rejects_a_second_post() -> None:
    first_page = [{"filename": f"docs/file-{index}.md"} for index in range(99)]
    first_page.append({"filename": "_posts/2026-01-01-first.md"})
    responses = {
        "/repos/owner/repo/pulls/165": {
            "head": {"sha": "abc123", "ref": "translate/posts", "repo": {"full_name": "owner/repo"}},
            "labels": [{"name": "hf-agent:managed"}],
            "state": "open",
        },
        "/repos/owner/repo/pulls/165/files?per_page=100": first_page,
        "/repos/owner/repo/pulls/165/files?per_page=100&page=2": [
            {"filename": "_posts/2026-01-02-second.md"}
        ],
    }

    def requester(method, path, token, payload=None):
        return responses[path]

    try:
        load_pr_snapshot(
            repository="owner/repo",
            pr_number=165,
            token="token",
            requester=requester,
        )
    except ValueError as exc:
        assert str(exc) == "Managed pull requests must change exactly one _posts Markdown file"
    else:
        raise AssertionError("second-page post must reject the managed pull request")


def test_snapshot_paginates_trusted_feedback() -> None:
    first_comments = [
        {
            "id": index,
            "updated_at": f"2026-07-04T01:{index % 60:02d}:00Z",
            "body": f"Trusted feedback {index}",
            "user": {"login": "reviewer", "type": "User"},
        }
        for index in range(100)
    ]
    responses = {
        "/repos/owner/repo/pulls/166": {
            "head": {"sha": "abc123", "ref": "translate/post", "repo": {"full_name": "owner/repo"}},
            "labels": [{"name": "hf-agent:managed"}],
            "state": "open",
        },
        "/repos/owner/repo/pulls/166/files?per_page=100": [
            {"filename": "_posts/2026-01-01-post.md"}
        ],
        "/repos/owner/repo/issues/166/comments?per_page=100": first_comments,
        "/repos/owner/repo/issues/166/comments?per_page=100&page=2": [
            {
                "id": 100,
                "updated_at": "2026-07-04T03:00:00Z",
                "body": "Second-page feedback",
                "user": {"login": "reviewer", "type": "User"},
            }
        ],
        "/repos/owner/repo/pulls/166/reviews?per_page=100": [],
        "/repos/owner/repo/pulls/166/comments?per_page=100": [],
        "/repos/owner/repo/collaborators/reviewer/permission": {"permission": "write"},
    }

    snapshot = load_pr_snapshot(
        repository="owner/repo",
        pr_number=166,
        token="token",
        requester=lambda method, path, token, payload=None: responses[path],
    )

    expected_feedback = [
        Feedback(
            "issue_comment",
            str(item["id"]),
            str(item["updated_at"]),
            str(item["body"]),
        )
        for item in [*first_comments, responses["/repos/owner/repo/issues/166/comments?per_page=100&page=2"][0]]
    ]
    assert snapshot["feedback_revision"] == feedback_revision(expected_feedback)
