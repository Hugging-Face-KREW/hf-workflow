from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hf_agent.repair_gates import build_gate_feedback, count_trailing_repairs


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

    feedback = build_gate_feedback(tmp_path)

    assert "automated PR gate repair" in feedback
    assert "Only return needs-human" in feedback
    assert "SEO gate failed" in feedback
    assert "Missing description" in feedback
    assert "Everything is fine" not in feedback


def test_count_trailing_repairs_stops_at_non_repair_commit() -> None:
    commits = [
        {"commit": {"message": "Initial translation"}},
        {"commit": {"message": "🐛 Address PR feedback"}},
        {"commit": {"message": "🐛 Repair failed PR gates\n\nAttempt one"}},
        {"commit": {"message": "🐛 Repair failed PR gates"}},
    ]

    assert count_trailing_repairs(commits) == 2
