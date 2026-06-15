from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local SEO and quality review from a manifest.")
    parser.add_argument("--manifest", required=True, help="Path to translation-flow manifest YAML.")
    parser.add_argument("--target-root", required=True, help="Path to the translated blog repository.")
    parser.add_argument("--stage", choices=["manifest", "seo", "quality", "all"], default="all")
    parser.add_argument("--result-json", default="", help="Optional path for hf.agent.skill_run.v1 JSON.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    result_json = Path(args.result_json) if args.result_json else Path(tempfile.mkdtemp()) / "hf-agent-skill-result.json"
    subprocess.run(
        [
            "python3",
            "scripts/hf_agent/run_skill_review.py",
            "--manifest",
            args.manifest,
            "--target-root",
            args.target_root,
            "--stage",
            args.stage,
            "--result-json",
            str(result_json),
        ],
        cwd=repo_root,
        check=True,
    )
    print(f"Wrote skill result JSON: {result_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
