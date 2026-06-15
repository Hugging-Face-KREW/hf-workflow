from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local SEO and quality review from a manifest.")
    parser.add_argument("--manifest", required=True, help="Path to translation-flow manifest YAML.")
    parser.add_argument("--target-root", required=True, help="Path to the translated blog repository.")
    parser.add_argument("--reports-root", default="reports", help="Directory where reports are written.")
    parser.add_argument("--stage", choices=["manifest", "seo", "quality", "humanize", "all", "comment"], default="all")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [
            "python3",
            "scripts/hf_agent/run_skill_review.py",
            "--manifest",
            args.manifest,
            "--target-root",
            args.target_root,
            "--reports-root",
            args.reports_root,
            "--stage",
            args.stage,
        ],
        cwd=repo_root,
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
