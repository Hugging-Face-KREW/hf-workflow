from __future__ import annotations

import json
import urllib.request
from typing import Any

from hf_agent.lifecycle import LifecycleState


API_ROOT = "https://api.github.com"
API_VERSION = "2022-11-28"
LIFECYCLE_CONTEXT = "HF Agent / Lifecycle Gate"
USER_AGENT = "hf-pr-agent/1.0"


def publish_commit_status(
    *,
    repository: str,
    sha: str,
    state: LifecycleState,
    description: str,
    token: str,
    target_url: str = "",
) -> None:
    payload: dict[str, Any] = {
        "context": LIFECYCLE_CONTEXT,
        "description": description,
        "state": state,
    }
    if target_url:
        payload["target_url"] = target_url
    request = urllib.request.Request(
        f"{API_ROOT}/repos/{repository}/statuses/{sha}",
        data=json.dumps(payload).encode(),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": API_VERSION,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 201:
            raise RuntimeError(f"GitHub returned HTTP {response.status} while publishing status")
