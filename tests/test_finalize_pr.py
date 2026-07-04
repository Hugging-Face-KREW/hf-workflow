from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hf_agent.finalize_pr import finalize
from hf_agent.github_api import publish_commit_status


def test_publish_commit_status_targets_the_exact_sha(monkeypatch) -> None:
    captured = {}

    class Response:
        status = 201

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self) -> bytes:
            return b"{}"

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data)
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    publish_commit_status(
        repository="owner/repo",
        sha="abc123",
        state="pending",
        description="Reviewing trusted feedback",
        token="secret-token",
        target_url="https://github.com/owner/repo/actions/runs/1",
    )

    assert captured == {
        "url": "https://api.github.com/repos/owner/repo/statuses/abc123",
        "headers": {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer secret-token",
            "Content-type": "application/json",
            "User-agent": "hf-pr-agent/1.0",
            "X-github-api-version": "2022-11-28",
        },
        "payload": {
            "context": "HF Agent / Lifecycle Gate",
            "description": "Reviewing trusted feedback",
            "state": "pending",
            "target_url": "https://github.com/owner/repo/actions/runs/1",
        },
        "timeout": 20,
    }


def test_finalize_publishes_success_for_an_unchanged_ready_snapshot(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(
        json.dumps(
            {
                "head_sha": "abc123",
                "feedback_revision": "feedback",
                "expected_head_sha": "abc123",
                "expected_feedback_revision": "feedback",
                "gates_passed": True,
                "verifier_passed": True,
                "report_published": True,
            }
        )
    )
    published = []

    result = finalize(
        snapshot_path=snapshot,
        repository="owner/repo",
        token="token",
        publisher=lambda **status: published.append(status),
    )

    assert result == 0
    assert published == [
        {
            "repository": "owner/repo",
            "sha": "abc123",
            "state": "success",
            "description": "Ready for human merge",
            "token": "token",
            "target_url": "",
        }
    ]


def test_finalize_returns_nonzero_when_feedback_changed(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(
        json.dumps(
            {
                "head_sha": "abc123",
                "feedback_revision": "new",
                "expected_head_sha": "abc123",
                "expected_feedback_revision": "old",
            }
        )
    )
    published = []

    result = finalize(
        snapshot_path=snapshot,
        repository="owner/repo",
        token="token",
        publisher=lambda **status: published.append(status),
    )

    assert result == 1
    assert published[0]["state"] == "pending"
