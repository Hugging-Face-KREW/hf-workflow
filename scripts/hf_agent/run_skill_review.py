from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hf_agent.manifest import read_simple_manifest


VALID_STAGES = {"manifest", "seo", "quality", "all"}
SKILL_ORDER = ["seo", "quality"]
SKILL_COMMANDS = {
    "seo": ["python3", "skills/seo/tools/simple_seo_report.py"],
    "quality": ["python3", "skills/quality/tools/simple_quality_report.py"],
}
RESULT_JSON_MARKER_START = "<!-- hf-agent-skill-result-json"
RESULT_JSON_MARKER_END = "-->"


def run(cmd: list[str], cwd: Path) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def is_skill_enabled(manifest: dict[str, str], skill_id: str) -> bool:
    value = manifest.get(f"skills.{skill_id}.enabled")
    if value == "":
        return True
    return value.lower() not in {"false", "no", "0", "off"}


def selected_skills(manifest: dict[str, str], stage: str) -> list[str]:
    if stage == "manifest":
        return []
    if stage != "all":
        return [stage] if is_skill_enabled(manifest, stage) else []
    return [skill_id for skill_id in SKILL_ORDER if is_skill_enabled(manifest, skill_id)]


def parse_markdown_result(skill_id: str, markdown: str, file_path: str) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    check_count = 0
    warning_count = 0
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        body = stripped[2:]
        if body.startswith("PASS:"):
            check_count += 1
            continue
        if body.startswith("WARN:"):
            check_count += 1
            warning_count += 1
            message = body.removeprefix("WARN:").strip()
            findings.append(
                {
                    "id": f"{skill_id}:warning:{warning_count}",
                    "severity": "warning",
                    "category": "check",
                    "path": file_path,
                    "line": None,
                    "end_line": None,
                    "side": "RIGHT",
                    "message": message,
                    "suggestion": None,
                    "action": {"type": "review"},
                    "confidence": 1.0,
                    "dedupe_key": f"{skill_id}:{message}",
                }
            )
    conclusion = "needs_action" if findings else "pass"
    return {
        "schema_version": "hf.skill.result.v1",
        "skill": {"id": skill_id, "version": "0.1.0"},
        "conclusion": conclusion,
        "summary": f"{skill_id} completed with {len(findings)} warning(s).",
        "findings": findings,
        "metrics": {
            "check_count": check_count,
            "warning_count": warning_count,
        },
    }


def run_skill(
    *,
    skill_id: str,
    manifest_path: Path,
    target_root: Path,
    repo_root: Path,
    file_path: str,
) -> dict[str, Any]:
    command = SKILL_COMMANDS[skill_id]
    with tempfile.TemporaryDirectory(prefix=f"hf-agent-{skill_id}-") as tmp:
        output = Path(tmp) / f"{skill_id}.md"
        run(
            [
                *command,
                "--manifest",
                str(manifest_path),
                "--target-root",
                str(target_root),
                "--output",
                str(output),
            ],
            cwd=repo_root,
        )
        return parse_markdown_result(skill_id, output.read_text(), file_path)


def aggregate_conclusion(results: list[dict[str, Any]]) -> str:
    order = {"error": 4, "blocked": 3, "needs_action": 2, "comment": 1, "pass": 0}
    if not results:
        return "pass"
    return max((str(result.get("conclusion") or "pass") for result in results), key=lambda item: order.get(item, 0))


def result_json_marker(result: dict[str, Any]) -> str:
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True).replace("--", "\\u002d\\u002d")
    return f"{RESULT_JSON_MARKER_START}\n{payload}\n{RESULT_JSON_MARKER_END}"


def finding_lines(skill_result: dict[str, Any], max_items: int = 20) -> list[str]:
    findings = skill_result.get("findings") or []
    if not findings:
        return ["_No findings._"]
    lines: list[str] = []
    for finding in findings[:max_items]:
        severity = str(finding.get("severity") or "info").upper()
        message = str(finding.get("message") or "").strip()
        path = str(finding.get("path") or "").strip()
        line = finding.get("line")
        location = f" `{path}`" if path else ""
        if line:
            location += f":{line}"
        lines.append(f"- {severity}:{location} {message}".rstrip())
    if len(findings) > max_items:
        lines.append(f"- ...and {len(findings) - max_items} more finding(s).")
    return lines


def render_markdown_report(result: dict[str, Any]) -> str:
    parts = [
        result_json_marker(result),
        "# HF Agent Skill Report",
        "",
        f"- Stage: `{result.get('stage', '')}`",
        f"- Conclusion: `{result.get('conclusion', '')}`",
        f"- Translation file: `{result.get('translation_file', '')}`",
        f"- Manifest: `{result.get('manifest', '')}`",
        f"- Created at: `{result.get('created_at', '')}`",
        "",
    ]
    for skill_result in result.get("skills") or []:
        skill = skill_result.get("skill") or {}
        skill_id = str(skill.get("id") or "unknown")
        parts += [
            f"## {skill_id}",
            "",
            f"- Conclusion: `{skill_result.get('conclusion', '')}`",
            f"- Summary: {skill_result.get('summary', '')}",
            "",
            "### Findings",
            "",
            *finding_lines(skill_result),
            "",
        ]
    return "\n".join(parts).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run enabled skills from a translation manifest.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--target-root", required=True)
    parser.add_argument("--stage", choices=sorted(VALID_STAGES), default="all")
    parser.add_argument("--result-json", default="", help="Optional path for machine-readable skill result JSON.")
    parser.add_argument("--report-md", default="", help="Optional path for the Markdown skill report.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    manifest_path = Path(args.manifest).resolve()
    target_root = Path(args.target_root).resolve()
    manifest = read_simple_manifest(manifest_path)
    file_path = manifest.get("translation.file_path", "")
    skills = selected_skills(manifest, args.stage)
    results = [
        run_skill(
            skill_id=skill_id,
            manifest_path=manifest_path,
            target_root=target_root,
            repo_root=repo_root,
            file_path=file_path,
        )
        for skill_id in skills
    ]
    result = {
        "schema_version": "hf.agent.skill_run.v1",
        "stage": args.stage,
        "conclusion": aggregate_conclusion(results),
        "target_repo": manifest.get("translation.target_repo", ""),
        "pr_url": manifest.get("translation.pr_url", ""),
        "translation_file": manifest.get("translation.file_path", ""),
        "manifest": str(manifest_path),
        "skills": results,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    result_json = Path(args.result_json) if args.result_json else None
    if result_json:
        result_json.parent.mkdir(parents=True, exist_ok=True)
        result_json.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        print(f"Wrote skill result: {result_json}")
    if args.report_md:
        report_md = Path(args.report_md)
        report_md.parent.mkdir(parents=True, exist_ok=True)
        report_md.write_text(render_markdown_report(result))
        print(f"Wrote skill report: {report_md}")
    if not result_json and not args.report_md:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
