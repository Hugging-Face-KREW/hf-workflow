"""Quality-level expectations for SEO fixtures.

These tests define what the harness is supposed to distinguish. They are more
semantic than the golden snapshots: excellent/good should proceed, medium should
return actionable changes, poor should fail the body-quality gate, and blocked
should stop before metadata generation.
"""
import pytest

from seo_eval import evaluate_path


@pytest.mark.parametrize(
    ("fixture", "expected_status", "expected_passed"),
    [
        ("excellent-post.md", "PASS", True),
        ("good-post.md", "PASS", True),
        ("medium-post.md", "PASS", True),
        ("poor-post.md", "FAIL", False),
        ("blocked-post.md", "BLOCKED", False),
    ],
)
def test_generated_fixture_quality_statuses(generated_dir, fixture, expected_status, expected_passed):
    result = evaluate_path(generated_dir / fixture)

    assert result["gate"]["status"] == expected_status
    assert result["gate"]["passed"] is expected_passed


def test_medium_keeps_citation_gap_as_review_evidence(generated_dir):
    result = evaluate_path(generated_dir / "medium-post.md")
    failed = [c["name"] for c in result["deterministic"]["advisory"]["checks"] if not c["passed"]]

    assert result["gate"]["status"] == "PASS"
    assert "citations" in failed


def test_blocked_is_caused_by_blocker_not_body_quality(generated_dir):
    result = evaluate_path(generated_dir / "blocked-post.md")
    blocker_fails = [c["name"] for c in result["blockers"]["checks"] if not c["passed"]]

    assert result["gate"]["status"] == "BLOCKED"
    assert result["gate"]["blockers_passed"] is False
    assert blocker_fails == ["robots_indexable"]
