from __future__ import annotations

from pathlib import Path

import yaml

from tools.translation_quality_harness import build_report


TEST_ROOT = Path(__file__).parent


def run_case(case: dict[str, object], tmp_path: Path) -> dict[str, object]:
    manifest = tmp_path / f"{case['id']}.yaml"
    source = (TEST_ROOT / str(case["source"])).resolve()
    target = (TEST_ROOT / str(case["target"])).resolve()
    manifest.write_text(
        f"version: 1\nsource:\n  file_path: {source}\ntranslation:\n  file_path: {target}\n",
        encoding="utf-8",
    )
    gates_config_path = None
    if gates_config := case.get("gates_config"):
        gates_config_path = tmp_path / f"{case['id']}-gates.yml"
        gates_config_path.write_text(yaml.safe_dump({"version": 1, **gates_config}), encoding="utf-8")
    return build_report(manifest, Path("/"), source_path=source, gates_config_path=gates_config_path)


def test_challenge_set_contract_is_executed(tmp_path: Path) -> None:
    suite = yaml.safe_load((TEST_ROOT / "challenge_set.yml").read_text(encoding="utf-8"))
    critical_cases = 0
    critical_detections = 0

    for case in suite["fixtures"]:
        report = run_case(case, tmp_path)
        categories = {issue["category"] for issue in report["issues"]}
        guide_rules = {issue["guide_rule"] for issue in report["issues"] if issue["guide_rule"]}
        assert report["status"] == case["expected_status"], case["id"]
        assert set(case.get("expected_categories", [])) <= categories, case["id"]
        assert set(case.get("expected_guide_rules", [])) <= guide_rules, case["id"]
        for expected in case.get("expected_issues", []):
            detected = any(
                issue["message"] == expected["message"] and issue["severity"] == expected["severity"]
                for issue in report["issues"]
            )
            assert detected, f"{case['id']}: {expected}"
            if expected["severity"] == "critical":
                critical_cases += 1
                critical_detections += int(detected)

    assert critical_cases > 0
    assert critical_detections / critical_cases >= 0.90


def test_golden_set_false_reject_rate_is_at_most_ten_percent(tmp_path: Path) -> None:
    suite = yaml.safe_load((TEST_ROOT / "golden_set.yml").read_text(encoding="utf-8"))
    cases = suite["fixtures"]

    assert len(cases) >= 5
    reports = []
    for case in cases:
        report = run_case(case, tmp_path)
        reports.append(report)
        assert report["status"] in case["allowed_statuses"], case["id"]
        if case.get("forbid_hard_failures"):
            assert report["hard_failures"] == [], case["id"]

    false_rejects = [report for report in reports if report["status"] == "reject"]

    assert len(false_rejects) / len(reports) <= 0.10
