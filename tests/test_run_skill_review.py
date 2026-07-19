from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hf_agent.run_skill_review import run_skill


def test_seo_runner_preserves_the_existing_gate_exit_code(tmp_path: Path) -> None:
    result_path = tmp_path / "result.json"
    report_path = tmp_path / "seo.md"
    calls = []

    def fail_seo(command, cwd, check):
        calls.append((command, cwd, check))
        report_path.write_text("# SEO Report\n\nMissing alt text.\n")
        return subprocess.CompletedProcess(command, 1)

    exit_code = run_skill(
        skill="seo",
        file_path="_posts/example.md",
        target_root=tmp_path / "target",
        report_path=report_path,
        result_path=result_path,
        runner=fail_seo,
    )

    assert exit_code == 1
    assert calls[0][0][1:3] == ["skills/seo/tools/seo_eval.py", "--file"]
    assert json.loads(result_path.read_text()) == {
        "conclusion": "fail",
        "report_path": str(report_path),
        "skill": "seo",
    }


def test_seo_runner_writes_eval_and_metadata_outputs_without_changing_wrapper(
    tmp_path: Path,
) -> None:
    result_path = tmp_path / "seo.json"
    report_path = tmp_path / "seo.md"
    calls = []

    def pass_seo_and_metadata(command, cwd, check):
        calls.append(command)
        if command[1] == "skills/seo/tools/seo_eval.py":
            report_path.write_text("# SEO Eval Report\n\nPass.\n")
            eval_json = Path(command[command.index("--json") + 1])
            eval_json.write_text(
                json.dumps({"gate": {"passed": True, "status": "PASS"}, "input": {}})
            )
            return subprocess.CompletedProcess(command, 0)
        if command[1] == "skills/seo/tools/metadata_suggestion.py":
            output = Path(command[command.index("--output") + 1])
            output.write_text(
                json.dumps({
                    "schema_version": 1,
                    "kind": "seo_metadata_suggestion",
                    "status": "PARTIAL",
                })
            )
            return subprocess.CompletedProcess(command, 0)
        raise AssertionError(f"unexpected command: {command}")

    exit_code = run_skill(
        skill="seo",
        file_path="_posts/example.md",
        target_root=tmp_path / "target",
        report_path=report_path,
        result_path=result_path,
        runner=pass_seo_and_metadata,
    )

    assert exit_code == 0
    assert json.loads(result_path.read_text()) == {
        "conclusion": "pass",
        "report_path": str(report_path),
        "skill": "seo",
    }
    assert (tmp_path / "seo-eval.json").exists()
    suggestion = json.loads((tmp_path / "metadata-suggestion.json").read_text())
    assert suggestion["kind"] == "seo_metadata_suggestion"
    assert "skill" not in suggestion
    assert "conclusion" not in suggestion
    assert [call[1] for call in calls] == [
        "skills/seo/tools/seo_eval.py",
        "skills/seo/tools/metadata_suggestion.py",
    ]


def test_seo_runner_records_metadata_generation_error_without_changing_gate(
    tmp_path: Path,
) -> None:
    result_path = tmp_path / "seo.json"
    report_path = tmp_path / "seo.md"

    def pass_seo_but_fail_metadata(command, cwd, check):
        if command[1] == "skills/seo/tools/seo_eval.py":
            report_path.write_text("# SEO Eval Report\n\nPass.\n")
            eval_json = Path(command[command.index("--json") + 1])
            eval_json.write_text(
                json.dumps({"gate": {"passed": True, "status": "PASS"}, "input": {}})
            )
            return subprocess.CompletedProcess(command, 0)
        if command[1] == "skills/seo/tools/metadata_suggestion.py":
            return subprocess.CompletedProcess(command, 2)
        raise AssertionError(f"unexpected command: {command}")

    exit_code = run_skill(
        skill="seo",
        file_path="_posts/example.md",
        target_root=tmp_path / "target",
        report_path=report_path,
        result_path=result_path,
        runner=pass_seo_but_fail_metadata,
    )

    assert exit_code == 0
    assert json.loads(result_path.read_text()) == {
        "conclusion": "pass",
        "report_path": str(report_path),
        "skill": "seo",
    }
    suggestion = json.loads((tmp_path / "metadata-suggestion.json").read_text())
    assert suggestion["status"] == "ERROR"
    assert suggestion["warnings"] == ["metadata_suggestion_generation_failed"]
    assert suggestion["candidate"] == {}


def test_seo_runner_keeps_metadata_generation_non_blocking_when_openai_required(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SEO_OPENAI_REQUIRED", "1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    result_path = tmp_path / "seo.json"
    report_path = tmp_path / "seo.md"
    calls = []

    def pass_seo_but_error_metadata(command, cwd, check):
        calls.append(command)
        if command[1] == "skills/seo/tools/seo_eval.py":
            assert "--openai-required" in command
            assert command[command.index("--openai-model") + 1] == "gpt-test"
            report_path.write_text("# SEO Eval Report\n\nPass.\n")
            eval_json = Path(command[command.index("--json") + 1])
            eval_json.write_text(
                json.dumps({"gate": {"passed": True, "status": "PASS"}, "input": {}})
            )
            return subprocess.CompletedProcess(command, 0)
        if command[1] == "skills/seo/tools/metadata_suggestion.py":
            assert "--openai-required" in command
            output = Path(command[command.index("--output") + 1])
            output.write_text(
                json.dumps({
                    "schema_version": 1,
                    "kind": "seo_metadata_suggestion",
                    "status": "ERROR",
                    "candidate": {},
                })
            )
            return subprocess.CompletedProcess(command, 0)
        raise AssertionError(f"unexpected command: {command}")

    exit_code = run_skill(
        skill="seo",
        file_path="_posts/example.md",
        target_root=tmp_path / "target",
        report_path=report_path,
        result_path=result_path,
        runner=pass_seo_but_error_metadata,
    )

    assert exit_code == 0
    assert json.loads(result_path.read_text())["conclusion"] == "pass"
    assert [call[1] for call in calls] == [
        "skills/seo/tools/seo_eval.py",
        "skills/seo/tools/metadata_suggestion.py",
    ]


def test_quality_runner_uses_translation_quality_harness(tmp_path: Path) -> None:
    result_path = tmp_path / "result.json"
    report_path = tmp_path / "quality.md"
    calls = []

    def pass_quality(command, cwd, check):
        calls.append((command, cwd, check))
        report_path.write_text("# Quality Report\n\nStatus: review_required\n")
        return subprocess.CompletedProcess(command, 0)

    exit_code = run_skill(
        skill="quality",
        file_path="_posts/example.md",
        target_root=tmp_path / "target",
        report_path=report_path,
        result_path=result_path,
        runner=pass_quality,
    )

    command = calls[0][0]
    assert exit_code == 0
    assert command[1] == "skills/quality/tools/translation_quality_harness.py"
    assert "--output-md" in command
    assert command[command.index("--output-md") + 1] == str(report_path)
    assert "--output-json" in command
    assert command[command.index("--output-json") + 1] == str(tmp_path / "quality-eval.json")
    assert "--output-pr-comment" in command
    assert "--llm-judge-model" in command
    assert command[command.index("--llm-judge-model") + 1] == "gpt-5.6-luna"
    assert "--fail-on-reject" in command
    assert json.loads(result_path.read_text())["conclusion"] == "pass"


def test_quality_runner_uses_explicit_llm_judge_model(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("LLM_JUDGE_MODEL", "explicit-judge-model")
    result_path = tmp_path / "result.json"
    report_path = tmp_path / "quality.md"

    def pass_quality(command, cwd, check):
        assert command[command.index("--llm-judge-model") + 1] == "explicit-judge-model"
        report_path.write_text("# Quality Report\n\nStatus: pass\n")
        return subprocess.CompletedProcess(command, 0)

    assert run_skill(
        skill="quality",
        file_path="_posts/example.md",
        target_root=tmp_path / "target",
        report_path=report_path,
        result_path=result_path,
        runner=pass_quality,
    ) == 0


def test_quality_runner_fails_when_harness_rejects(tmp_path: Path) -> None:
    result_path = tmp_path / "result.json"
    report_path = tmp_path / "quality.md"

    def reject_quality(command, cwd, check):
        report_path.write_text("# Quality Report\n\nStatus: reject\n")
        return subprocess.CompletedProcess(command, 1)

    assert run_skill(
        skill="quality",
        file_path="_posts/example.md",
        target_root=tmp_path / "target",
        report_path=report_path,
        result_path=result_path,
        runner=reject_quality,
    ) == 1
    assert json.loads(result_path.read_text())["conclusion"] == "fail"
