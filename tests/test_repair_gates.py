from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hf_agent.repair_gates import (
    build_gate_feedback,
    count_trailing_repairs,
    has_incomplete_quality_evaluation,
    prepare_repair,
)


def test_build_gate_feedback_includes_only_failed_reports(tmp_path: Path) -> None:
    seo = tmp_path / "seo"
    quality = tmp_path / "quality"
    seo.mkdir()
    quality.mkdir()
    (seo / "seo.json").write_text(json.dumps({"skill": "seo", "conclusion": "fail"}))
    (seo / "seo.md").write_text("Missing description")
    (quality / "quality.json").write_text(
        json.dumps({"skill": "quality", "conclusion": "pass"})
    )
    (quality / "quality.md").write_text("Everything is fine")
    (tmp_path / "metadata-suggestion.json").write_text(
        json.dumps({
            "kind": "seo_metadata_suggestion",
            "status": "PARTIAL",
            "candidate": {"title": "Candidate"},
        })
    )

    feedback = build_gate_feedback(tmp_path)

    assert "automated PR gate repair" in feedback
    assert "Only return needs-human" in feedback
    assert "SEO gate failed" in feedback
    assert "Missing description" in feedback
    assert "Everything is fine" not in feedback
    assert "Candidate" not in feedback


def test_count_trailing_repairs_stops_at_non_repair_commit() -> None:
    commits = [
        {"commit": {"message": "Initial translation"}},
        {"commit": {"message": "🐛 Address PR feedback"}},
        {"commit": {"message": "🐛 Repair failed PR gates\n\nAttempt one"}},
        {"commit": {"message": "🐛 Repair failed PR gates"}},
    ]

    assert count_trailing_repairs(commits) == 2


def test_incomplete_quality_evaluation_blocks_automatic_repair(tmp_path: Path) -> None:
    quality = tmp_path / "quality"
    quality.mkdir()
    (quality / "quality.json").write_text(
        json.dumps({"skill": "quality", "conclusion": "fail"})
    )
    (quality / "quality.md").write_text("Semantic adequacy evaluation is incomplete.")
    (quality / "quality-eval.json").write_text(
        json.dumps(
            {
                "metadata": {"semantic_evaluation_complete": False},
                "mqm_judge": {"contract_incomplete_segment_count": 2},
            }
        )
    )
    requester_called = False

    def requester(*_: object) -> list[dict[str, object]]:
        nonlocal requester_called
        requester_called = True
        return []

    allowed, attempts, feedback, reason = prepare_repair(
        results_root=tmp_path,
        repository="owner/repo",
        pr_number=1,
        max_attempts=3,
        token="token",
        requester=requester,
    )

    assert has_incomplete_quality_evaluation(tmp_path) is True
    assert allowed is False
    assert attempts == 0
    assert reason == "incomplete_quality_evaluation"
    assert "QUALITY gate failed" in feedback
    assert requester_called is False
