from __future__ import annotations

import json
import sys
import urllib.error
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from notify_discord import (
    DISCORD_USER_AGENT,
    build_discord_payload,
    build_ready_payload,
    main,
    notify_discord,
)


@pytest.mark.parametrize(
    ("title", "labels", "suppressed"),
    [
        ("[실험][chunked] 번역", [], True),
        ("번역 [테스트]", [], True),
        ("[EXPERIMENT] translation", [], True),
        ("[Test] translation", [], True),
        ("일반 번역", [{"name": "hf-agent:experiment"}], True),
        ("일반 번역", [{"name": "hf-agent:test"}], True),
        ("Latest test results 번역", [{"name": "hf-agent:managed"}], False),
        ("[testing] translation", [{"name": "test-results"}], False),
        ("일반 번역", [], False),
    ],
)
def test_ready_notification_filters_test_prs(
    tmp_path: Path, monkeypatch, title: str, labels: list, suppressed: bool
) -> None:
    metadata = tmp_path / "pr.json"
    metadata.write_text(json.dumps({"title": title, "labels": labels}))
    monkeypatch.setattr(sys, "argv", [
        "notify_discord.py", "--ready-pr-url", "https://github.com/o/r/pull/161",
        "--head-sha", "abcdef1234567890", "--pr-metadata", str(metadata),
    ])
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.example/webhook")
    sent = []
    monkeypatch.setattr("notify_discord.notify_payload", lambda *args: sent.append(args) or 0)

    assert main() == 0
    assert len(sent) == (0 if suppressed else 1)
    if sent:
        assert sent[0][1] == build_ready_payload(
            pr_url="https://github.com/o/r/pull/161", head_sha="abcdef1234567890"
        )


def test_ready_notification_requires_pr_metadata(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", [
        "notify_discord.py", "--ready-pr-url", "https://github.com/o/r/pull/161",
        "--head-sha", "abcdef1234567890",
    ])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_build_discord_payload_uses_created_prs_only() -> None:
    payload = build_discord_payload(
        {
            "results": [
                {"status": "skipped", "slug": "old", "pr_url": ""},
                {"status": "created", "slug": "new-post", "pr_url": "https://github.com/o/r/pull/1"},
            ]
        }
    )

    assert payload == {
        "content": "HF Blog Korean translation PR created.\n- [new-post](https://github.com/o/r/pull/1)"
    }


def test_notify_discord_treats_http_error_as_non_blocking(tmp_path: Path, monkeypatch) -> None:
    summary = tmp_path / "run-summary.json"
    summary.write_text(
        json.dumps(
            {
                "results": [
                    {"status": "created", "slug": "new-post", "pr_url": "https://github.com/o/r/pull/1"}
                ]
            }
        )
    )

    def raise_forbidden(request, *args, **kwargs):
        assert request.get_header("User-agent") == DISCORD_USER_AGENT
        raise urllib.error.HTTPError(
            url="https://discord.example/webhook",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=None,
        )

    monkeypatch.setattr("urllib.request.urlopen", raise_forbidden)

    assert notify_discord("https://discord.example/webhook", summary) == 0


def test_notify_discord_skips_missing_summary(tmp_path: Path) -> None:
    assert notify_discord("https://discord.example/webhook", tmp_path / "missing.json") == 0


def test_build_ready_payload_requests_human_merge_for_exact_sha() -> None:
    assert build_ready_payload(
        pr_url="https://github.com/o/r/pull/161",
        head_sha="abcdef1234567890",
    ) == {
        "content": (
            "HF Agent gates are green. Human merge approval requested.\n"
            "- [PR #161](https://github.com/o/r/pull/161) at `abcdef1`"
        )
    }
