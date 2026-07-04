from __future__ import annotations

from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/reusable-pr-mutate.yml"


def test_mutation_workflow_serializes_each_pull_request() -> None:
    workflow = WORKFLOW.read_text()

    assert "group: hf-agent-mutate-${{ inputs.target_repo }}-${{ inputs.pr_number }}" in workflow
    assert "cancel-in-progress: false" in workflow


def test_mutation_workflow_checks_the_expected_head_before_writing() -> None:
    workflow = WORKFLOW.read_text()

    assert "ref: ${{ inputs.expected_head_sha }}" in workflow
    assert "name: Reject a stale candidate" in workflow
    assert '"${{ inputs.expected_head_sha }}"' in workflow


def test_mutation_workflow_does_not_interpolate_feedback_as_code() -> None:
    workflow = WORKFLOW.read_text()

    assert "HF_FEEDBACK: ${{ inputs.feedback }}" in workflow
    assert '--feedback "$HF_FEEDBACK"' in workflow
    assert "pull_request_target" not in workflow


def test_mutation_workflow_resolves_handled_inline_threads() -> None:
    workflow = WORKFLOW.read_text()

    assert "review_comment_id:" in workflow
    assert "Resolve the handled review thread" in workflow
    assert "--resolve-comment-id" in workflow
    assert "steps.apply.outputs.disposition != 'needs-human'" in workflow


def test_private_workflow_checkout_uses_the_bot_token() -> None:
    workflow = WORKFLOW.read_text()

    assert "token: ${{ secrets.KREW_BOT_TOKEN }}" in workflow
