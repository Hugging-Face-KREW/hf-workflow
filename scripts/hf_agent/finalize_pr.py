from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Callable

from hf_agent.github_api import publish_commit_status
from hf_agent.lifecycle import Snapshot, lifecycle_state
from hf_agent.snapshot_pr import load_pr_snapshot


StatusPublisher = Callable[..., None]
SnapshotLoader = Callable[..., dict[str, object]]


def finalize(
    *,
    snapshot_path: Path,
    repository: str,
    token: str,
    pr_number: int | None = None,
    target_url: str = "",
    publisher: StatusPublisher = publish_commit_status,
    snapshot_loader: SnapshotLoader = load_pr_snapshot,
) -> int:
    snapshot = Snapshot(**json.loads(snapshot_path.read_text()))
    if pr_number is not None:
        current = snapshot_loader(
            repository=repository,
            pr_number=pr_number,
            token=token,
        )
        snapshot = snapshot.with_updates(
            head_sha=str(current["head_sha"]),
            feedback_revision=str(current["feedback_revision"]),
        )
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
    parser.add_argument("--pr-number", type=int)
    parser.add_argument("--target-url", default="")
    args = parser.parse_args()
    token = os.getenv("GITHUB_TOKEN", "")
    if not args.repository or not token:
        parser.error("GITHUB_REPOSITORY and GITHUB_TOKEN are required")
    return finalize(
        snapshot_path=args.snapshot,
        repository=args.repository,
        pr_number=args.pr_number,
        token=token,
        target_url=args.target_url,
    )


if __name__ == "__main__":
    raise SystemExit(main())
