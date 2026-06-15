from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from hf_agent.manifest import build_manifest_text, choose_translation_file, read_simple_manifest
from hf_agent.publish_pr_comment import build_comment_body, build_comment_body_from_markdown, extract_result_json, pr_number_from_url


def translated_markdown() -> str:
    body = "\n\n".join(
        [
            "# 한국어 제목",
            "## 소개",
            "이 문서는 허깅페이스 블로그 번역 테스트를 위한 한국어 본문입니다. "
            "기술 독자를 위한 자연스러운 한국어 문장을 충분히 포함합니다.",
            "## 세부 내용",
            "모델 이름과 API 이름은 유지하면서 설명 문장은 한국어로 번역합니다. "
            "링크와 코드 블록은 원문 구조를 보존해야 합니다.",
            "## 마무리",
            "이 단락은 품질 리포트의 본문 길이 기준을 넘기기 위한 내용입니다. " * 8,
        ]
    )
    return f"""---
layout: post
title: "한국어 제목"
author: dailybot
categories: [Translation, HuggingFace]
slug: "sample-post"
source_url: "https://huggingface.co/blog/sample-post"
source_published_date: "2026-06-01"
source_published_at: "2026-06-01T00:00:00+00:00"
locale: "ko"
translation_status: "draft"
translator: "test"
---

> Source: https://huggingface.co/blog/sample-post

_이 글은 Hugging Face 블로그의 [Sample Source Title](https://huggingface.co/blog/sample-post)를 한국어로 번역한 글입니다._

{body}
"""


def test_build_manifest_text_from_pr_json() -> None:
    pr_json = {
        "number": 141,
        "url": "https://github.com/Hugging-Face-KREW/hugging-face-krew.github.io/pull/141",
        "title": "Translate Hugging Face blog post: Sample",
        "headRefName": "translate/sample-post",
        "files": [{"path": "_posts/2026-06-08-sample-post.md"}],
    }

    file_path = choose_translation_file(pr_json)
    manifest = build_manifest_text(
        pr_json=pr_json,
        target_repo="Hugging-Face-KREW/hugging-face-krew.github.io",
        file_path=file_path,
        markdown=translated_markdown(),
    )

    assert "id: pr-141-sample-post" in manifest
    assert "branch: translate/sample-post" in manifest
    assert "file_path: _posts/2026-06-08-sample-post.md" in manifest
    assert 'title: "Sample Source Title"' in manifest
    assert "skills:" in manifest
    assert "handoff:" not in manifest


def test_read_simple_manifest_flattens_skill_config(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        """version: 1

translation:
  file_path: _posts/2026-06-08-sample-post.md

skills:
  seo:
    enabled: false
    config:
      primary_keyword: "sample"
  quality:
    enabled: true
"""
    )

    parsed = read_simple_manifest(manifest)

    assert parsed["translation.file_path"] == "_posts/2026-06-08-sample-post.md"
    assert parsed["skills.seo.enabled"] == "false"
    assert parsed["skills.seo.config.primary_keyword"] == "sample"
    assert parsed["skills.quality.enabled"] == "true"


def test_run_skill_review_writes_skill_result_json(tmp_path: Path) -> None:
    target_root = tmp_path / "target"
    translation_file = target_root / "_posts" / "2026-06-08-sample-post.md"
    translation_file.parent.mkdir(parents=True)
    translation_file.write_text(translated_markdown())

    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        """version: 1

run:
  id: pr-141-sample-post
  created_at: 2026-06-08T00:00:00+00:00
  target_date: 2026-06-08

source:
  feed_url: https://huggingface.co/blog/feed.xml
  url: https://huggingface.co/blog/sample-post
  slug: sample-post
  title: "Sample Source Title"
  published_date: 2026-06-01
  published_at: 2026-06-01T00:00:00+00:00
  language: en

translation:
  target_repo: Hugging-Face-KREW/hugging-face-krew.github.io
  branch: translate/sample-post
  file_path: _posts/2026-06-08-sample-post.md
  pr_url: https://github.com/Hugging-Face-KREW/hugging-face-krew.github.io/pull/141
  locale: ko

skills:
  seo:
    enabled: true
  quality:
    enabled: true
"""
    )

    result_json = tmp_path / "skill-result.json"
    report_md = tmp_path / "skill-report.md"
    subprocess.run(
        [
            "python3",
            "scripts/hf_agent/run_skill_review.py",
            "--manifest",
            str(manifest),
            "--target-root",
            str(target_root),
            "--stage",
            "all",
            "--result-json",
            str(result_json),
            "--report-md",
            str(report_md),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    result = json.loads(result_json.read_text())
    assert result["schema_version"] == "hf.agent.skill_run.v1"
    assert result["stage"] == "all"
    assert result["target_repo"] == "Hugging-Face-KREW/hugging-face-krew.github.io"
    assert [item["skill"]["id"] for item in result["skills"]] == ["seo", "quality"]
    assert all(item["schema_version"] == "hf.skill.result.v1" for item in result["skills"])
    report = report_md.read_text()
    assert "# HF Agent Skill Report" in report
    assert "<!-- hf-agent-skill-result-json" in report
    assert extract_result_json(report)["schema_version"] == "hf.agent.skill_run.v1"
    assert not (tmp_path / "reports" / "pr-141" / "run.json").exists()
    assert not (tmp_path / "reports" / "pr-141" / "seo-report.md").exists()


def test_comment_body_uses_stable_marker() -> None:
    run_state = {
        "schema_version": "hf.agent.skill_run.v1",
        "stage": "all",
        "conclusion": "needs_action",
        "translation_file": "_posts/2026-06-08-sample-post.md",
        "manifest": "reports/pr-141/manifest.yaml",
        "skills": [
            {
                "schema_version": "hf.skill.result.v1",
                "skill": {"id": "seo", "version": "0.1.0"},
                "conclusion": "pass",
                "summary": "seo completed with 0 warning(s).",
                "findings": [],
            },
            {
                "schema_version": "hf.skill.result.v1",
                "skill": {"id": "quality", "version": "0.1.0"},
                "conclusion": "needs_action",
                "summary": "quality completed with 1 warning(s).",
                "findings": [
                    {
                        "severity": "warning",
                        "path": "_posts/2026-06-08-sample-post.md",
                        "line": 12,
                        "message": "translation body is too short",
                    }
                ],
            },
        ],
    }

    body = build_comment_body("Hugging-Face-KREW/hugging-face-krew.github.io", "141", run_state)

    assert "<!-- hf-workflow:skill-report repo=Hugging-Face-KREW/hugging-face-krew.github.io pr=141 -->" in body
    assert "<!-- hf-agent-skill-result-json" in body
    assert "HF Agent Skill Report" in body
    assert "## seo" in body
    assert "## quality" in body
    assert "translation body is too short" in body


def test_comment_body_can_use_markdown_report() -> None:
    markdown = "\n".join(
        [
            "<!-- hf-agent-skill-result-json",
            json.dumps({"target_repo": "o/r", "pr_url": "https://github.com/o/r/pull/1"}),
            "-->",
            "# HF Agent Skill Report",
            "",
            "- Conclusion: `pass`",
        ]
    )

    body = build_comment_body_from_markdown("o/r", "1", markdown)

    assert body.startswith("<!-- hf-workflow:skill-report repo=o/r pr=1 -->")
    assert "# HF Agent Skill Report" in body


def test_pr_number_from_url() -> None:
    assert pr_number_from_url("https://github.com/o/r/pull/141") == "141"
    assert pr_number_from_url("https://github.com/o/r/pull/141#issuecomment-1") == "141"
    assert pr_number_from_url("") == ""
