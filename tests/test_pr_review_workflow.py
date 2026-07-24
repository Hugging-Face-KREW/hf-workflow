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
    assert "issues: write" in workflow


def test_unresolved_review_threads_are_a_blocking_gate() -> None:
    workflow = WORKFLOW.read_text()

    assert "review_threads:" in workflow
    assert "name: HF Agent / Review Threads" in workflow
    assert "python -m hf_agent.review_threads" in workflow
    assert "unresolved_threads:" in workflow
    assert "needs: [review, verifier, report, review_threads, repair, metadata_apply]" in workflow


def test_discord_merge_request_runs_only_after_ready() -> None:
    workflow = WORKFLOW.read_text()

    assert "DISCORD_WEBHOOK_URL:" in workflow
    assert "notify_ready:" in workflow
    assert "needs: [finalize, metadata_apply]" in workflow
    assert "needs.metadata_apply.outputs.changed != 'true'" in workflow
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

    assert workflow.count("token: ${{ secrets.KREW_BOT_TOKEN }}") >= 6


def test_review_outputs_are_shared_as_head_bound_artifacts() -> None:
    workflow = WORKFLOW.read_text()

    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in workflow
    assert "actions/download-artifact@634f93cb2916e3fdff6788551b99b062d0335ce0" in workflow
    assert "name: ${{ matrix.skill }}-review-${{ inputs.head_sha }}" in workflow
    assert "retention-days: 1" in workflow
    assert "if-no-files-found: error" in workflow
    assert "merge-multiple: true" in workflow


def test_verifier_and_report_reuse_the_authoritative_review() -> None:
    workflow = WORKFLOW.read_text()
    verifier = workflow.split("\n  verifier:", 1)[1].split("\n  report:", 1)[0]
    report = workflow.split("\n  report:", 1)[1].split("\n  review_threads:", 1)[0]

    assert "python -m hf_agent.verify_review_artifacts" in verifier
    assert "run_skill_review.py" not in verifier
    assert "run_skill_review.py" not in report
    assert "Generate comment reports" not in report
    assert "Publish marker report" in report
    assert "needs.verifier.result == 'success'" in report


def test_repair_reuses_failed_reports_and_only_rechecks_changed_content() -> None:
    workflow = WORKFLOW.read_text()
    repair = workflow.split("\n  repair:", 1)[1].split("\n  metadata_apply:", 1)[0]

    assert "Download review artifacts" in repair
    assert "Generate failed gate reports" not in repair
    assert "Verify repaired content" in repair
    assert "needs.verifier.result == 'success'" in repair
    assert repair.count("run_skill_review.py") == 1
    assert workflow.count("run_skill_review.py") == 4


def test_review_runtime_installs_seo_dependencies() -> None:
    workflow = WORKFLOW.read_text()

    assert workflow.count("markdown beautifulsoup4") >= 2


def test_review_workflow_enables_quality_llm_judge_by_default() -> None:
    workflow = WORKFLOW.read_text()

    assert workflow.count(
        "QUALITY_LLM_JUDGE_PROVIDER: ${{ vars.QUALITY_LLM_JUDGE_PROVIDER || 'openai' }}"
    ) >= 3
    assert workflow.count("LLM_JUDGE_MODEL: ${{ vars.LLM_JUDGE_MODEL || 'gpt-5.6-luna' }}") >= 3
    assert workflow.count(
        "QUALITY_LLM_JUDGE_MAX_SEGMENTS: ${{ vars.QUALITY_LLM_JUDGE_MAX_SEGMENTS || '0' }}"
    ) >= 2


def test_ready_lifecycle_clears_stale_human_needed_label() -> None:
    workflow = WORKFLOW.read_text()

    assert "name: Clear stale human-needed label" in workflow
    assert "GH_TOKEN: ${{ secrets.KREW_BOT_TOKEN }}" in workflow
    assert 'grep -Fxq "hf-agent:needs-human"' in workflow
    assert 'gh pr edit "${{ inputs.pr_number }}"' in workflow
    assert '--remove-label "hf-agent:needs-human"' in workflow
    assert "Publish lifecycle status" in workflow


def test_review_workflow_installs_seo_runtime_dependencies() -> None:
    workflow = WORKFLOW.read_text()

    assert "markdown beautifulsoup4" in workflow


def test_cross_repo_api_writes_use_the_bot_token() -> None:
    workflow = WORKFLOW.read_text()

    assert "GITHUB_TOKEN: ${{ secrets.KREW_BOT_TOKEN }}" in workflow


def test_metadata_suggestion_is_applied_after_green_gates() -> None:
    workflow = WORKFLOW.read_text()

    assert "metadata_apply:" in workflow
    assert "HF Agent / Apply Metadata Suggestion" in workflow
    assert "python -m hf_agent.apply_metadata_suggestion" in workflow
    assert "🔧 Update SEO metadata" in workflow
    assert "SEO_RUBRIC_OPENAI_REQUIRED" in workflow
    assert "SEO_OPENAI_REQUIRED" not in workflow


def test_metadata_apply_does_not_rerun_openai_rubric_gate() -> None:
    workflow = WORKFLOW.read_text()
    metadata_section = workflow.split("metadata_apply:", 1)[1].split("finalize:", 1)[0]

    assert 'SEO_RUBRIC_OPENAI_REQUIRED: "0"' in metadata_section


def test_metadata_apply_is_deterministic_and_applies_safe_frontmatter() -> None:
    workflow = WORKFLOW.read_text()
    metadata_section = workflow.split("metadata_apply:", 1)[1].split("finalize:", 1)[0]

    assert "OPENAI_API_KEY" not in metadata_section
    assert "OPENAI_MODEL" not in metadata_section
    assert "--allow-partial-safe-fields" in metadata_section
