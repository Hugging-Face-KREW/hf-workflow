from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from hf_agent.handle_pr_feedback import route_feedback


def main() -> int:
    parser = argparse.ArgumentParser(description="Authorize and route one PR feedback event.")
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--event-path", type=Path, required=True)
    parser.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY", ""))
    parser.add_argument("--result-json", type=Path, required=True)
    args = parser.parse_args()
    token = os.getenv("GITHUB_TOKEN", "")
    if not args.repository or not token:
        parser.error("GITHUB_REPOSITORY and GITHUB_TOKEN are required")
    result = route_feedback(
        event_name=args.event_name,
        payload=json.loads(args.event_path.read_text()),
        repository=args.repository,
        token=token,
    )
    args.result_json.parent.mkdir(parents=True, exist_ok=True)
    args.result_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
