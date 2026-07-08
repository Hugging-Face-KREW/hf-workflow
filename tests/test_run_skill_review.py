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


def test_quality_runner_treats_report_warnings_as_failure(tmp_path: Path) -> None:
    result_path = tmp_path / "result.json"
    report_path = tmp_path / "quality.md"

    def warn_quality(command, cwd, check):
        report_path.write_text("# Quality Report\n\n- WARN: TODO marker remains\n")
        return subprocess.CompletedProcess(command, 0)

    exit_code = run_skill(
        skill="quality",
        file_path="_posts/example.md",
        target_root=tmp_path / "target",
        report_path=report_path,
        result_path=result_path,
        runner=warn_quality,
    )

    assert exit_code == 1
    assert json.loads(result_path.read_text())["conclusion"] == "fail"


def test_quality_runner_passes_a_clean_report(tmp_path: Path) -> None:
    report_path = tmp_path / "quality.md"

    def pass_quality(command, cwd, check):
        report_path.write_text("# Quality Report\n\n- PASS: source attribution exists\n")
        return subprocess.CompletedProcess(command, 0)

    assert run_skill(
        skill="quality",
        file_path="_posts/example.md",
        target_root=tmp_path / "target",
        report_path=report_path,
        result_path=tmp_path / "result.json",
        runner=pass_quality,
    ) == 0
