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
    assert workflow.count("if: ${{ always() }}") >= 2
    assert "statuses: write" in workflow


def test_unresolved_review_threads_are_a_blocking_gate() -> None:
    workflow = WORKFLOW.read_text()

    assert "review_threads:" in workflow
    assert "name: HF Agent / Review Threads" in workflow
    assert "python -m hf_agent.review_threads" in workflow
    assert "unresolved_threads:" in workflow
    assert "needs: [review, verifier, report, review_threads, repair]" in workflow


def test_discord_merge_request_runs_only_after_ready() -> None:
    workflow = WORKFLOW.read_text()

    assert "DISCORD_WEBHOOK_URL:" in workflow
    assert "notify_ready:" in workflow
    assert "needs: finalize" in workflow
    assert "--ready-pr-url" in workflow


def test_failed_gates_trigger_a_bounded_repair() -> None:
    workflow = WORKFLOW.read_text()

    assert "repair:" in workflow
    assert "name: HF Agent / Repair Failed Gates" in workflow
    assert "max_repair_attempts:" in workflow
    assert "python -m hf_agent.repair_gates" in workflow
    assert "🐛 Repair failed PR gates" in workflow
    assert "steps.verify.outcome == 'failure'" in workflow


def test_private_workflow_checkout_uses_the_bot_token() -> None:
    workflow = WORKFLOW.read_text()

    assert workflow.count("token: ${{ secrets.KREW_BOT_TOKEN }}") >= 5


def test_reports_are_published_without_ephemeral_artifacts() -> None:
    workflow = WORKFLOW.read_text()

    assert "upload-artifact" not in workflow
    assert "download-artifact" not in workflow
    assert "Generate comment reports" in workflow
