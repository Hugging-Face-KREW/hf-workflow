from __future__ import annotations

from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/reusable-pr-mutate.yml"


def test_mutation_workflow_serializes_each_pull_request() -> None:
    workflow = WORKFLOW.read_text()

    assert "workflow_dispatch:" in workflow
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
    assert "--metadata-suggestion results/metadata-suggestion.json" in workflow
    assert "steps.apply.outputs.intent == 'metadata'" in workflow
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


def test_mutation_runtime_installs_seo_dependencies() -> None:
    workflow = WORKFLOW.read_text()

    assert "markdown beautifulsoup4" in workflow


def test_mutation_workflow_enables_quality_llm_judge_by_default() -> None:
    workflow = WORKFLOW.read_text()

    assert "QUALITY_LLM_JUDGE_PROVIDER: ${{ vars.QUALITY_LLM_JUDGE_PROVIDER || 'openai' }}" in workflow
    assert "LLM_JUDGE_MODEL: ${{ vars.LLM_JUDGE_MODEL || 'gpt-5.6-luna' }}" in workflow
    assert "QUALITY_LLM_JUDGE_MAX_SEGMENTS: ${{ vars.QUALITY_LLM_JUDGE_MAX_SEGMENTS || '0' }}" in workflow


def test_mutation_workflow_generates_metadata_suggestion_without_rerunning_rubric() -> None:
    workflow = WORKFLOW.read_text()
    step = workflow.split("name: Generate metadata suggestion for feedback", 1)[1].split(
        "name: Apply feedback",
        1,
    )[0]

    assert "python scripts/hf_agent/run_skill_review.py" in step
    assert "--skill seo" in step
    assert 'SEO_RUBRIC_OPENAI_REQUIRED: "0"' in step
    assert "SEO_OPENAI_REQUIRED" not in workflow


def test_mutation_workflow_verifies_metadata_changes_deterministically() -> None:
    workflow = WORKFLOW.read_text()
    step = workflow.split("name: Verify changed metadata content", 1)[1].split(
        "name: Verify changed feedback content",
        1,
    )[0]

    assert "steps.apply.outputs.intent == 'metadata'" in step
    assert 'SEO_RUBRIC_OPENAI_REQUIRED: "0"' in step
    assert "🔧 Apply SEO metadata suggestion" in workflow
