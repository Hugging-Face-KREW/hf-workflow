from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hf_agent.github_api import upsert_issue_comment
from hf_agent.publish_pr_comment import REPORT_MARKER, load_results, render_report


def test_render_report_uses_compact_skill_rows(tmp_path: Path) -> None:
    (tmp_path / "seo.json").write_text(
        json.dumps({"skill": "seo", "conclusion": "pass", "report_path": "seo.md"})
    )
    quality = tmp_path / "nested" / "quality.json"
    quality.parent.mkdir()
    quality.write_text(
        json.dumps({"skill": "quality", "conclusion": "fail", "report_path": "quality.md"})
    )
    (tmp_path / "metadata-suggestion.json").write_text(
        json.dumps({
            "kind": "seo_metadata_suggestion",
            "status": "PARTIAL",
            "candidate": {"title": "Metadata candidate"},
        })
    )
    (tmp_path / "seo.md").write_text("# SEO Report\n\nAll required checks passed.")
    (quality.parent / "quality.md").write_text("# Quality Report\n\n- WARN: TODO remains")

    results = load_results(tmp_path)
    report = render_report(results, head_sha="abc123")

    assert {result["skill"] for result in results} == {"seo", "quality"}
    assert report.startswith(REPORT_MARKER)
    assert "| SEO | ✅ Pass |" in report
    assert "| Quality | ❌ Fail |" in report
    assert "Head SHA: `abc123`" in report
    assert "<details>" in report
    assert "<summary>SEO report — ✅ Pass</summary>" in report
    assert "All required checks passed." in report
    assert "<summary>Quality report — ❌ Fail</summary>" in report
    assert "- WARN: TODO remains" in report
    assert "Metadata candidate" not in report


def test_upsert_issue_comment_updates_the_existing_marker() -> None:
    calls = []

    def requester(method, path, token, payload=None):
        calls.append((method, path, payload))
        if method == "GET":
            return [
                {"id": 1, "body": "Unrelated"},
                {"id": 2, "body": f"{REPORT_MARKER}\nOld report"},
            ]
        return {"id": 2}

    upsert_issue_comment(
        repository="owner/repo",
        issue_number=7,
        marker=REPORT_MARKER,
        body=f"{REPORT_MARKER}\nNew report",
        token="token",
        requester=requester,
    )

    assert calls[-1] == (
        "PATCH",
        "/repos/owner/repo/issues/comments/2",
        {"body": f"{REPORT_MARKER}\nNew report"},
    )


def test_upsert_issue_comment_creates_a_missing_marker() -> None:
    calls = []

    def requester(method, path, token, payload=None):
        calls.append((method, path, payload))
        return [] if method == "GET" else {"id": 3}

    upsert_issue_comment(
        repository="owner/repo",
        issue_number=7,
        marker=REPORT_MARKER,
        body=f"{REPORT_MARKER}\nReport",
        token="token",
        requester=requester,
    )

    assert calls[-1] == (
        "POST",
        "/repos/owner/repo/issues/7/comments",
        {"body": f"{REPORT_MARKER}\nReport"},
    )
