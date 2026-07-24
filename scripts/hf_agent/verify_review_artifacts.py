from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


REQUIRED_ARTIFACTS = (
    "quality.json",
    "quality.md",
    "quality-eval.json",
    "seo.json",
    "seo.md",
    "seo-eval.json",
)
PASSING_QUALITY_STATUSES = {"auto_pass", "review_required"}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid review artifact JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Invalid review artifact JSON object: {path.name}")
    return value


def _require_artifacts(results_root: Path) -> None:
    for name in REQUIRED_ARTIFACTS:
        if not (results_root / name).is_file():
            raise ValueError(f"Missing review artifact: {name}")


def _verify_quality(
    results_root: Path,
    target_root: Path,
    file_path: str,
    *,
    expected_provider: str,
    expected_model: str,
) -> None:
    wrapper = _load_json(results_root / "quality.json")
    report = _load_json(results_root / "quality-eval.json")
    status = str(report.get("status") or "")
    expected_conclusion = "pass" if status in PASSING_QUALITY_STATUSES else "fail"
    if wrapper.get("skill") != "quality" or wrapper.get("conclusion") != expected_conclusion:
        raise ValueError("quality wrapper conclusion does not match structured status")

    metadata = report.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("quality report metadata is missing")
    reported_target_path = str(metadata.get("target_path") or "")
    requested_parts = Path(file_path).parts
    reported_parts = Path(reported_target_path).parts
    if not requested_parts or reported_parts[-len(requested_parts) :] != requested_parts:
        raise ValueError("quality target path does not match requested file")
    target_path = target_root / file_path
    if not target_path.is_file():
        raise ValueError(f"Reviewed target file is missing: {file_path}")
    target_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()
    if metadata.get("target_hash") != target_hash:
        raise ValueError("quality target hash does not match reviewed content")

    mqm = report.get("mqm_judge")
    if not isinstance(mqm, dict):
        raise ValueError("quality MQM result is missing")
    if mqm.get("provider") != expected_provider:
        raise ValueError("quality judge provider does not match workflow configuration")
    if mqm.get("model") != expected_model:
        raise ValueError("quality judge model does not match workflow configuration")
    if not mqm.get("prompt_hash"):
        raise ValueError("quality judge prompt hash is missing")

    if expected_conclusion == "fail":
        return
    if not metadata.get("semantic_evaluation_complete"):
        raise ValueError("successful quality result has incomplete semantic evaluation")
    if not mqm.get("enabled"):
        raise ValueError("successful quality result did not enable the MQM judge")

    alignment = report.get("segment_alignment")
    segments = mqm.get("segments")
    if not isinstance(alignment, list) or not isinstance(segments, list):
        raise ValueError("successful quality result has invalid MQM segment coverage")
    expected_ids = [str(item.get("target_id") or "") for item in alignment if isinstance(item, dict)]
    actual_ids = [str(item.get("segment_id") or "") for item in segments if isinstance(item, dict)]
    coverage_complete = (
        bool(expected_ids)
        and not any(not value for value in expected_ids + actual_ids)
        and int(mqm.get("skipped_segment_count", 0)) == 0
        and int(mqm.get("segment_count", 0)) == len(expected_ids)
        and len(actual_ids) == len(expected_ids)
        and len(set(actual_ids)) == len(actual_ids)
        and set(actual_ids) == set(expected_ids)
    )
    if not coverage_complete:
        raise ValueError("successful quality result has invalid MQM segment coverage")


def _verify_seo(results_root: Path) -> None:
    wrapper = _load_json(results_root / "seo.json")
    report = _load_json(results_root / "seo-eval.json")
    gate = report.get("gate")
    if not isinstance(gate, dict) or not isinstance(gate.get("passed"), bool):
        raise ValueError("SEO structured gate result is missing")
    expected_conclusion = "pass" if gate["passed"] else "fail"
    if wrapper.get("skill") != "seo" or wrapper.get("conclusion") != expected_conclusion:
        raise ValueError("SEO wrapper conclusion does not match structured gate result")


def verify_review_artifacts(
    results_root: Path,
    target_root: Path,
    file_path: str,
    *,
    expected_provider: str,
    expected_model: str,
) -> None:
    _require_artifacts(results_root)
    _verify_quality(
        results_root,
        target_root,
        file_path,
        expected_provider=expected_provider,
        expected_model=expected_model,
    )
    _verify_seo(results_root)


def verify_checkout_head(target_root: Path, expected_head_sha: str) -> None:
    actual = subprocess.check_output(
        ["git", "-C", str(target_root), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if actual != expected_head_sha:
        raise ValueError("checked-out candidate does not match expected head SHA")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify trusted PR review artifacts")
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--target-root", required=True, type=Path)
    parser.add_argument("--file", required=True)
    parser.add_argument("--expected-head-sha", required=True)
    parser.add_argument("--expected-provider", required=True)
    parser.add_argument("--expected-model", required=True)
    args = parser.parse_args()
    verify_checkout_head(args.target_root, args.expected_head_sha)
    verify_review_artifacts(
        args.results,
        args.target_root,
        args.file,
        expected_provider=args.expected_provider,
        expected_model=args.expected_model,
    )
    print("Review artifacts verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
