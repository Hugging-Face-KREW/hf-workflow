from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Callable

from hf_agent.github_api import publish_commit_status
from hf_agent.lifecycle import Snapshot, lifecycle_state


StatusPublisher = Callable[..., None]


def finalize(
    *,
    snapshot_path: Path,
    repository: str,
    token: str,
    target_url: str = "",
    publisher: StatusPublisher = publish_commit_status,
) -> int:
    snapshot = Snapshot(**json.loads(snapshot_path.read_text()))
    state, description = lifecycle_state(snapshot)
    publisher(
        repository=repository,
        sha=snapshot.head_sha,
        state=state,
        description=description,
        token=token,
        target_url=target_url,
    )
    print(f"Lifecycle Gate: {state} ({description})")
    return 0 if state == "success" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the canonical PR lifecycle status.")
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY", ""))
    parser.add_argument("--target-url", default="")
    args = parser.parse_args()
    token = os.getenv("GITHUB_TOKEN", "")
    if not args.repository or not token:
        parser.error("GITHUB_REPOSITORY and GITHUB_TOKEN are required")
    return finalize(
        snapshot_path=args.snapshot,
        repository=args.repository,
        token=token,
        target_url=args.target_url,
    )


if __name__ == "__main__":
    raise SystemExit(main())
