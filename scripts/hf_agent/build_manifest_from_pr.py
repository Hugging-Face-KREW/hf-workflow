from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hf_agent.manifest import DEFAULT_FEED_URL, build_manifest_text, choose_translation_file


def gh_pr_view(target_repo: str, pr_number: str) -> dict:
    result = subprocess.run(
        [
            "gh",
            "pr",
            "view",
            pr_number,
            "--repo",
            target_repo,
            "--json",
            "number,url,title,body,headRefName,files",
        ],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a translation-flow manifest from an open translation PR.")
    parser.add_argument("--target-repo", required=True, help="GitHub repo in OWNER/REPO form.")
    parser.add_argument("--pr-number", required=True, help="Pull request number.")
    parser.add_argument("--target-root", required=True, help="Checked-out target repo root.")
    parser.add_argument("--output", required=True, help="Manifest YAML path to write.")
    parser.add_argument("--file-path", default="", help="Translation file path. Auto-detected from PR files when omitted.")
    parser.add_argument("--feed-url", default=DEFAULT_FEED_URL)
    parser.add_argument("--pr-json", default="", help="Local PR JSON fixture for tests or offline debugging.")
    args = parser.parse_args()

    pr_json = json.loads(Path(args.pr_json).read_text()) if args.pr_json else gh_pr_view(args.target_repo, args.pr_number)
    file_path = choose_translation_file(pr_json, args.file_path)
    translation_path = Path(args.target_root) / file_path
    if not translation_path.exists():
        raise FileNotFoundError(f"Translation file does not exist: {translation_path}")

    manifest = build_manifest_text(
        pr_json=pr_json,
        target_repo=args.target_repo,
        file_path=file_path,
        markdown=translation_path.read_text(),
        feed_url=args.feed_url,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(manifest)
    print(f"Wrote manifest: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
