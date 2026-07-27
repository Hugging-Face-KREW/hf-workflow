from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hf_agent.verify_review_artifacts import verify_review_artifacts


POST_PATH = "_posts/example.md"


def write_review_results(
    root: Path,
    target_root: Path,
    *,
    quality_status: str = "auto_pass",
    quality_conclusion: str = "pass",
    model: str = "gpt-5.6-luna",
    skipped_segments: int = 0,
    mqm_segment_ids: tuple[str, ...] = ("target-001", "target-002"),
) -> None:
    root.mkdir()
    target = target_root / POST_PATH
    target.parent.mkdir(parents=True)
    target.write_text("# 번역\n\n본문입니다.\n")
    target_hash = hashlib.sha256(target.read_bytes()).hexdigest()

    (root / "quality.json").write_text(
        json.dumps({"skill": "quality", "conclusion": quality_conclusion})
    )
    (root / "quality.md").write_text("# Quality Report\n")
    (root / "quality-eval.json").write_text(
        json.dumps(
            {
                "status": quality_status,
                "metadata": {
                    "target_path": str(target_root / POST_PATH),
                    "target_hash": target_hash,
                    "source_available": True,
                    "semantic_evaluation_complete": quality_status == "auto_pass",
                },
                "segment_alignment": [
                    {"target_id": "target-001"},
                    {"target_id": "target-002"},
                ],
                "mqm_judge": {
                    "enabled": True,
                    "provider": "openai",
                    "model": model,
                    "segment_count": len(mqm_segment_ids),
                    "skipped_segment_count": skipped_segments,
                    "segments": [
                        {"segment_id": segment_id} for segment_id in mqm_segment_ids
                    ],
                    "prompt_hash": "prompt-sha256",
                },
            }
        )
    )

    (root / "seo.json").write_text(json.dumps({"skill": "seo", "conclusion": "pass"}))
    (root / "seo.md").write_text("# SEO Report\n")
    (root / "seo-eval.json").write_text(
        json.dumps({"gate": {"passed": True, "status": "PASS"}})
    )


def verify(root: Path, target_root: Path) -> None:
    verify_review_artifacts(
        root,
        target_root,
        POST_PATH,
        expected_provider="openai",
        expected_model="gpt-5.6-luna",
    )


def test_verifies_complete_review_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "results"
    target_root = tmp_path / "target"
    write_review_results(root, target_root)

    verify(root, target_root)


def test_accepts_review_required_with_incomplete_semantic_evaluation(tmp_path: Path) -> None:
    root = tmp_path / "results"
    target_root = tmp_path / "target"
    write_review_results(root, target_root, quality_status="review_required")

    verify(root, target_root)


def test_accepts_review_required_when_mqm_judge_is_skipped(tmp_path: Path) -> None:
    root = tmp_path / "results"
    target_root = tmp_path / "target"
    write_review_results(
        root,
        target_root,
        quality_status="review_required",
        mqm_segment_ids=(),
    )
    report_path = root / "quality-eval.json"
    report = json.loads(report_path.read_text())
    report["mqm_judge"]["prompt_hash"] = ""
    report_path.write_text(json.dumps(report))

    verify(root, target_root)


def test_rejects_review_required_judge_results_without_prompt_hash(
    tmp_path: Path,
) -> None:
    root = tmp_path / "results"
    target_root = tmp_path / "target"
    write_review_results(root, target_root, quality_status="review_required")
    report_path = root / "quality-eval.json"
    report = json.loads(report_path.read_text())
    report["mqm_judge"]["prompt_hash"] = ""
    report_path.write_text(json.dumps(report))

    with pytest.raises(ValueError, match="prompt hash"):
        verify(root, target_root)


def test_accepts_runner_relative_target_path(tmp_path: Path) -> None:
    root = tmp_path / "results"
    target_root = tmp_path / "target"
    write_review_results(root, target_root)
    report_path = root / "quality-eval.json"
    report = json.loads(report_path.read_text())
    report["metadata"]["target_path"] = f"../target/{POST_PATH}"
    report_path.write_text(json.dumps(report))

    verify(root, target_root)


def test_accepts_well_formed_quality_rejection(tmp_path: Path) -> None:
    root = tmp_path / "results"
    target_root = tmp_path / "target"
    write_review_results(
        root,
        target_root,
        quality_status="reject",
        quality_conclusion="fail",
        skipped_segments=2,
        mqm_segment_ids=(),
    )

    verify(root, target_root)


def test_rejects_missing_required_artifact(tmp_path: Path) -> None:
    root = tmp_path / "results"
    target_root = tmp_path / "target"
    write_review_results(root, target_root)
    (root / "quality.md").unlink()

    with pytest.raises(ValueError, match="Missing review artifact: quality.md"):
        verify(root, target_root)


def test_rejects_target_hash_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "results"
    target_root = tmp_path / "target"
    write_review_results(root, target_root)
    (target_root / POST_PATH).write_text("# 변조됨\n")

    with pytest.raises(ValueError, match="target hash"):
        verify(root, target_root)


def test_rejects_wrapper_status_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "results"
    target_root = tmp_path / "target"
    write_review_results(root, target_root, quality_conclusion="fail")

    with pytest.raises(ValueError, match="quality wrapper conclusion"):
        verify(root, target_root)


def test_rejects_wrong_llm_model(tmp_path: Path) -> None:
    root = tmp_path / "results"
    target_root = tmp_path / "target"
    write_review_results(root, target_root, model="gpt-5-nano")

    with pytest.raises(ValueError, match="quality judge model"):
        verify(root, target_root)


@pytest.mark.parametrize(
    ("skipped_segments", "segment_ids"),
    [
        (1, ("target-001",)),
        (0, ("target-001", "target-001")),
        (0, ("target-001",)),
        (0, ("target-001", "target-002", "target-003")),
    ],
)
def test_rejects_incomplete_successful_mqm_coverage(
    tmp_path: Path,
    skipped_segments: int,
    segment_ids: tuple[str, ...],
) -> None:
    root = tmp_path / "results"
    target_root = tmp_path / "target"
    write_review_results(
        root,
        target_root,
        skipped_segments=skipped_segments,
        mqm_segment_ids=segment_ids,
    )

    with pytest.raises(ValueError, match="MQM segment coverage"):
        verify(root, target_root)
