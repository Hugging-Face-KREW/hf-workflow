from __future__ import annotations

from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/reusable-pr-review.yml"


def test_review_workflow_runs_existing_skills_without_fail_fast() -> None:
    workflow = WORKFLOW.read_text()

    assert "workflow_call:" in workflow
    assert "fail-fast: false" in workflow
    assert "skill: [seo, quality]" in workflow
    assert workflow.count("contents: read") >= 2


def test_review_workflow_checks_out_the_exact_candidate() -> None:
    workflow = WORKFLOW.read_text()

    assert "name: Checkout candidate" in workflow
    assert "repository: ${{ inputs.target_repo }}" in workflow
    assert "ref: ${{ inputs.head_sha }}" in workflow


def test_verifier_is_read_only_and_waits_for_reviews() -> None:
    workflow = WORKFLOW.read_text()

    assert "verifier:" in workflow
    assert "needs: review" in workflow


def test_report_and_finalizer_run_after_failures() -> None:
    workflow = WORKFLOW.read_text()

    assert "report:" in workflow
    assert "name: HF Agent / Publish Report" in workflow
    assert "finalize:" in workflow
    assert "name: HF Agent / Finalize Lifecycle" in workflow
    assert workflow.count("if: ${{ always() }}") >= 3
    assert "statuses: write" in workflow
