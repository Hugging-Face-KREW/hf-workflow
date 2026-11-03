from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


SPEC = importlib.util.spec_from_file_location(
    "translation_experiment", Path(__file__).resolve().parents[1] / "scripts/translation_experiment.py"
)
lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lab)


def git(path, *args):
    return subprocess.run(["git", *args], cwd=path, text=True, capture_output=True, check=True).stdout.strip()


@pytest.fixture
def prepared(tmp_path):
    repo = tmp_path / "blog"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Experiment test")
    git(repo, "remote", "add", "origin", "git@github.com-personal:owner/blog.git")
    (repo / "README.md").write_text("baseline\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "base")
    plan = {
        "run_id": "smoke-001", "document_id": "article", "target_repo": "owner/blog",
        "blog_base_sha": git(repo, "rev-parse", "HEAD"), "workflow_sha": "b" * 40,
        "source_url": "https://huggingface.co/blog/article", "title": "Article",
        "post_path": "_posts/2026-11-03-article.md", "budget_usd": 1,
        "arms": [{"id": "baseline", "settings": {"backend": "fake"}}],
    }
    plan_file = tmp_path / "plan.json"
    lab.write(plan_file, plan)
    source = tmp_path / "source.md"
    source.write_text("# Source\n\n[reference](https://example.com)\n")
    run = tmp_path / "run"
    lab.prepare(plan_file, source, run)
    return tmp_path, repo, run, plan, plan_file, source


def stage(prepared):
    tmp, repo, run, *_ = prepared
    candidate = tmp / "candidate.md"
    candidate.write_bytes("---\r\ntitle: 번역\r\n---\r\n\r\n번역문\r\n".encode())
    state = lab.stage(run, "baseline", repo, candidate)
    return state, candidate


def test_frozen_input_and_no_overwrite(prepared):
    _, _, run, _, plan_file, source = prepared
    with pytest.raises(FileExistsError):
        lab.prepare(plan_file, source, run)
    (run / "source.md").write_text("changed")
    with pytest.raises(ValueError, match="snapshot has changed"):
        lab.load_run(run)


@pytest.mark.parametrize("field,value", [
    ("blog_base_sha", "main"), ("workflow_sha", "latest"),
    ("post_path", "_posts/../../secret.md"), ("budget_usd", -1),
    ("run_id", "../run"), ("budget_usd", float("nan")),
])
def test_invalid_plans_rejected(prepared, field, value):
    plan = dict(prepared[3], **{field: value})
    with pytest.raises(ValueError):
        lab.validate_plan(plan)


def test_stage_keeps_original_checkout_and_fixed_base(prepared):
    _, repo, run, plan, *_ = prepared
    state, candidate = stage(prepared)
    assert git(repo, "rev-parse", "HEAD") == plan["blog_base_sha"]
    assert git(repo, "status", "--porcelain") == ""
    worktree = Path(state["worktree"])
    assert git(worktree, "rev-parse", "HEAD^") == plan["blog_base_sha"]
    assert (worktree / plan["post_path"]).read_bytes() == candidate.read_bytes()
    assert git(worktree, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD") == plan["post_path"]
    with pytest.raises(ValueError, match="already staged"):
        lab.stage(run, "baseline", repo, candidate)


def evidence(prepared, state):
    tmp, _, run, *_ = prepared
    evaluation, usage = tmp / "evaluation.json", tmp / "usage.json"
    lab.write(evaluation, {
        "head_sha": state["initial_sha"], "source_sha256": lab.load_run(run)["source_sha256"],
        "target_sha256": state["target_sha256"], "summary": "Fake backend integration check only",
    })
    lab.write(usage, {"head_sha": state["initial_sha"], "calls": [
        {"phase": "evaluation", "model": "fake", "cost_usd": None},
    ]})
    return evaluation, usage


def test_revision_evidence_is_hash_bound_and_immutable(prepared):
    _, repo, run, *_ = prepared
    state, _ = stage(prepared)
    evaluation, usage = evidence(prepared, state)
    # CRLF candidate must retain the exact bytes for the evidence hash.
    lab.record(run, "baseline", state["initial_sha"], repo, evaluation, usage)
    saved = lab.read(run / "arms/baseline/revisions" / state["initial_sha"] / "usage.json")
    assert saved["calls"][0]["cost_usd"] is None
    with pytest.raises(ValueError, match="already recorded"):
        lab.record(run, "baseline", state["initial_sha"], repo, evaluation, usage)


@pytest.mark.parametrize("key", ["head_sha", "source_sha256", "target_sha256"])
def test_stale_evaluation_rejected(prepared, key):
    _, repo, run, *_ = prepared
    state, _ = stage(prepared)
    evaluation, usage = evidence(prepared, state)
    report = lab.read(evaluation)
    report[key] = "wrong"
    lab.write(evaluation, report)
    with pytest.raises(ValueError, match=key):
        lab.record(run, "baseline", state["initial_sha"], repo, evaluation, usage)


def test_publish_records_initial_sha_before_enabling_loop(prepared, monkeypatch):
    _, _, run, plan, *_ = prepared
    state, _ = stage(prepared)
    calls = []
    original = lab.command

    def fake(*args, **kwargs):
        calls.append(args)
        if args[:3] == ("git", "push", "-u"):
            return ""
        if args[:2] == ("git", "rev-parse") or args[:2] == ("git", "status"):
            return original(*args, **kwargs)
        if args[:2] == ("gh", "api"):
            text = f"ref: {plan['workflow_sha']}\nuses: owner/workflow.yml@{plan['workflow_sha']}\nworkflow_ref: {plan['workflow_sha']}"
            return json.dumps({"content": lab.base64.b64encode(text.encode()).decode()})
        if args[:3] == ("gh", "pr", "list"):
            return "[]"
        if args[:3] == ("gh", "pr", "create"):
            assert "--draft" in args and "hf-agent:managed" not in args
            return "https://github.com/owner/blog/pull/1"
        if args[:3] == ("gh", "pr", "edit"):
            persisted = lab.read(run / "arms/baseline/pr.json")
            assert persisted["initial_sha"] == state["initial_sha"]
            assert persisted["pr_url"] == "https://github.com/owner/blog/pull/1"
        return ""

    monkeypatch.setattr(lab, "command", fake)
    assert lab.publish(run, "baseline", True).endswith("/1")
    assert calls[-1][-1] == "hf-agent:managed"


def test_loop_does_not_start_on_old_deployment(prepared, monkeypatch):
    _, _, run, *_ = prepared
    stage(prepared)
    calls = []

    def fake(*args, **kwargs):
        calls.append(args)
        return json.dumps({"content": lab.base64.b64encode(b"workflow_ref: old-version").decode()})

    monkeypatch.setattr(lab, "command", fake)
    with pytest.raises(ValueError, match="consistently reference"):
        lab.publish(run, "baseline", True)
    assert len(calls) == 1


def test_bundle_excludes_git_worktrees_and_unrelated_files(prepared):
    tmp, repo, run, *_ = prepared
    state, _ = stage(prepared)
    evaluation, usage = evidence(prepared, state)
    lab.record(run, "baseline", state["initial_sha"], repo, evaluation, usage)
    (run / "private-notes.txt").write_text("not an experiment artifact")
    output = tmp / "evidence.zip"
    lab.bundle(run, output)
    with lab.zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        assert "source.md" in names
        assert f"arms/baseline/revisions/{state['initial_sha']}/candidate.md" in names
        assert not any("worktree" in n or ".git" in n or "private-notes" in n for n in names)
    with pytest.raises(FileExistsError):
        lab.bundle(run, output)


def test_result_comment_reuses_own_sha_marker_not_copied_marker(prepared, monkeypatch):
    _, repo, run, *_ = prepared
    state, _ = stage(prepared)
    evaluation, usage = evidence(prepared, state)
    lab.record(run, "baseline", state["initial_sha"], repo, evaluation, usage)
    state["pr_url"] = "https://github.com/owner/blog/pull/1"
    lab.write(run / "arms/baseline/pr.json", state)
    marker = f"<!-- hf-agent-experiment-result:smoke-001:baseline:{state['initial_sha']} -->"
    calls = []

    def fake(*args, **kwargs):
        calls.append(args)
        if "--slurp" in args:
            return json.dumps([
                [{"id": 10, "body": marker, "user": {"login": "other-user"}}],
                [{"id": 20, "body": marker, "user": {"login": "current-user"}}],
            ])
        if args[2] == "user":
            return "current-user"
        assert "PATCH" in args and "repos/owner/blog/issues/comments/20" in args
        payload = lab.read(Path(args[-1]))
        assert "비용 미확인 호출: 1개" in payload["body"]
        assert "artifact" in payload["body"]
        return json.dumps({"html_url": "https://github.com/owner/blog/pull/1#issuecomment-20"})

    monkeypatch.setattr(lab, "command", fake)
    assert lab.comment(run, "baseline", state["initial_sha"], "https://github.com/owner/blog/actions/runs/1#artifact").endswith("20")
    assert len(calls) == 3


def test_publish_retries_reuse_existing_pr_without_duplicate_creation(prepared, monkeypatch):
    _, _, run, *_ = prepared
    state, _ = stage(prepared)
    original = lab.command
    calls = []

    def fake(*args, **kwargs):
        calls.append(args)
        if args[:3] == ("gh", "pr", "list"):
            return json.dumps([{"url": "https://github.com/owner/blog/pull/1", "headRefOid": state["initial_sha"]}])
        if args[:3] == ("git", "push", "-u"):
            return ""
        return original(*args, **kwargs)

    monkeypatch.setattr(lab, "command", fake)
    assert lab.publish(run, "baseline").endswith("/1")
    assert not any(c[:3] == ("gh", "pr", "create") for c in calls)
    assert "pr_url: https://github.com/owner/blog/pull/1" in (run / "arms/baseline/manifest.yaml").read_text()
    calls.clear()
    assert lab.publish(run, "baseline").endswith("/1")
    assert not calls
