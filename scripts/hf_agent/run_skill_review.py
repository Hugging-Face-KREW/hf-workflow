from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Callable


Runner = Callable[..., subprocess.CompletedProcess]
REPO_ROOT = Path(__file__).resolve().parents[2]


def _source_url(post_path: Path) -> str:
    if not post_path.exists():
        return ""
    match = re.search(r'^source_url:\s*["\']?([^"\'\n]+)', post_path.read_text(), re.MULTILINE)
    return match.group(1).strip() if match else ""


def _quality_manifest(file_path: str, target_root: Path) -> str:
    source_url = _source_url(target_root / file_path)
    return (
        "source:\n"
        f"  url: {source_url}\n"
        "translation:\n"
        f"  file_path: {file_path}\n"
    )


def _write_metadata_error(
    *,
    path: Path,
    file_path: str,
    eval_json_path: Path,
    report_path: Path,
    returncode: int,
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "seo_metadata_suggestion",
                "status": "ERROR",
                "file_path": file_path,
                "source_eval": {
                    "report_path": str(report_path),
                    "eval_json_path": str(eval_json_path),
                },
                "candidate": {},
                "apply": {
                    "allowed": False,
                    "mode": "frontmatter_only",
                    "requires_human": True,
                },
                "needs_policy_decision": [],
                "warnings": ["metadata_suggestion_generation_failed"],
                "reason": f"metadata suggestion command exited with {returncode}",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def run_skill(
    *,
    skill: str,
    file_path: str,
    target_root: Path,
    report_path: Path,
    result_path: Path,
    runner: Runner = subprocess.run,
) -> int:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_manifest: Path | None = None

    if skill == "seo":
        eval_json_path = report_path.with_name("seo-eval.json")
        command = [
            "python3",
            "skills/seo/tools/seo_eval.py",
            "--file",
            file_path,
            "--target-root",
            str(target_root),
            "--output",
            str(report_path),
            "--json",
            str(eval_json_path),
        ]
    elif skill == "quality":
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yaml",
            delete=False,
            dir=report_path.parent,
        ) as handle:
            handle.write(_quality_manifest(file_path, target_root))
            temporary_manifest = Path(handle.name)
        command = [
            "python3",
            "skills/quality/tools/simple_quality_report.py",
            "--manifest",
            str(temporary_manifest),
            "--target-root",
            str(target_root),
            "--output",
            str(report_path),
        ]
    else:
        raise ValueError(f"Unsupported skill: {skill}")

    try:
        completed = runner(command, cwd=REPO_ROOT, check=False)
    finally:
        if temporary_manifest:
            temporary_manifest.unlink(missing_ok=True)

    passed = completed.returncode == 0
    if skill == "quality" and report_path.exists():
        passed = passed and "- WARN:" not in report_path.read_text()

    if skill == "seo":
        suggestion_path = report_path.with_name("metadata-suggestion.json")
        if eval_json_path.exists():
            metadata_completed = runner(
                [
                    "python3",
                    "skills/seo/tools/metadata_suggestion.py",
                    "--file",
                    file_path,
                    "--target-root",
                    str(target_root),
                    "--eval-json",
                    str(eval_json_path),
                    "--output",
                    str(suggestion_path),
                    "--report-path",
                    str(report_path),
                ],
                cwd=REPO_ROOT,
                check=False,
            )
            if metadata_completed.returncode != 0 or not suggestion_path.exists():
                _write_metadata_error(
                    path=suggestion_path,
                    file_path=file_path,
                    eval_json_path=eval_json_path,
                    report_path=report_path,
                    returncode=metadata_completed.returncode,
                )

    result = {
        "conclusion": "pass" if passed else "fail",
        "report_path": str(report_path),
        "skill": skill,
    }
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one existing PR review skill.")
    parser.add_argument("--skill", choices=["seo", "quality"], required=True)
    parser.add_argument("--file", required=True)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--result-json", type=Path, required=True)
    args = parser.parse_args()
    return run_skill(
        skill=args.skill,
        file_path=args.file,
        target_root=args.target_root,
        report_path=args.report,
        result_path=args.result_json,
    )


if __name__ == "__main__":
    raise SystemExit(main())
