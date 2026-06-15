from __future__ import annotations

import json
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from notify_discord import build_discord_payload, notify_discord


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

    def raise_forbidden(*args, **kwargs):
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
