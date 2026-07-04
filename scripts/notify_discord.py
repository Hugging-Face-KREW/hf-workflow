from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DISCORD_USER_AGENT = "DiscordBot (https://github.com/Hugging-Face-KREW/hf-workflow, 1.0)"


def build_discord_payload(summary: dict[str, Any]) -> dict[str, str] | None:
    created = [
        result
        for result in summary.get("results", [])
        if result.get("status") == "created" and result.get("pr_url")
    ]
    if not created:
        return None

    lines = [
        f"- [{result.get('slug') or result['pr_url']}]({result['pr_url']})"
        for result in created
    ]
    return {
        "content": "\n".join(
            [
                "HF Blog Korean translation PR created.",
                *lines,
            ]
        )
    }


def build_ready_payload(*, pr_url: str, head_sha: str) -> dict[str, str]:
    pr_number = pr_url.rstrip("/").rsplit("/", 1)[-1]
    return {
        "content": "\n".join(
            [
                "HF Agent gates are green. Human merge approval requested.",
                f"- [PR #{pr_number}]({pr_url}) at `{head_sha[:7]}`",
            ]
        )
    }


def notify_payload(webhook_url: str, payload: dict[str, str]) -> int:
    if not webhook_url:
        print("DISCORD_WEBHOOK_URL is empty; skipping Discord notification.")
        return 0
    request = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": DISCORD_USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            print(f"Discord notification sent: HTTP {response.status}")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"Discord notification failed; continuing workflow: {exc}")
    return 0


def notify_discord(webhook_url: str, summary_path: Path) -> int:
    if not webhook_url:
        print("DISCORD_WEBHOOK_URL is empty; skipping Discord notification.")
        return 0
    if not summary_path.exists():
        print("No run summary found; skipping Discord notification.")
        return 0

    summary = json.loads(summary_path.read_text())
    payload = build_discord_payload(summary)
    if not payload:
        print("No created PR URL found; skipping Discord notification.")
        return 0

    return notify_payload(webhook_url, payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a non-blocking Discord workflow notification.")
    parser.add_argument("--summary", default="run-summary.json")
    parser.add_argument("--ready-pr-url")
    parser.add_argument("--head-sha")
    args = parser.parse_args()
    if args.ready_pr_url:
        if not args.head_sha:
            parser.error("--head-sha is required with --ready-pr-url")
        return notify_payload(
            os.environ.get("DISCORD_WEBHOOK_URL", ""),
            build_ready_payload(pr_url=args.ready_pr_url, head_sha=args.head_sha),
        )
    return notify_discord(os.environ.get("DISCORD_WEBHOOK_URL", ""), Path(args.summary))


if __name__ == "__main__":
    raise SystemExit(main())
