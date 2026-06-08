from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from hf_agent.manifest import build_manifest_text, choose_translation_file
from hf_agent.publish_pr_comment import build_comment_body, pr_number_from_url


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


def test_run_skill_review_writes_reports_and_state(tmp_path: Path) -> None:
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
"""
    )

    reports_root = tmp_path / "reports"
    subprocess.run(
        [
            "python3",
            "scripts/hf_agent/run_skill_review.py",
            "--manifest",
            str(manifest),
            "--target-root",
            str(target_root),
            "--reports-root",
            str(reports_root),
            "--stage",
            "all",
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    report_dir = reports_root / "pr-141"
    run_state = json.loads((report_dir / "run.json").read_text())
    assert (report_dir / "seo-report.md").exists()
    assert (report_dir / "quality-report.md").exists()
    assert run_state["lifecycle"] == "finished"
    assert run_state["reports"]["seo"].endswith("seo-report.md")


def test_comment_body_uses_stable_marker(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports" / "pr-141"
    report_dir.mkdir(parents=True)
    (report_dir / "seo-report.md").write_text("# SEO Report\n\n- PASS: frontmatter title exists\n")
    (report_dir / "quality-report.md").write_text("# Quality Report\n\n- PASS: translation body is not empty\n")
    run_state = {
        "stage": "all",
        "lifecycle": "finished",
        "translation_file": "_posts/2026-06-08-sample-post.md",
        "manifest": str(report_dir / "manifest.yaml"),
        "report_dir": str(report_dir),
    }

    body = build_comment_body("Hugging-Face-KREW/hugging-face-krew.github.io", "141", run_state)

    assert "<!-- hf-workflow:skill-report repo=Hugging-Face-KREW/hugging-face-krew.github.io pr=141 -->" in body
    assert "HF Agent Skill Report" in body
    assert "frontmatter title exists" in body
    assert "translation body is not empty" in body


def test_pr_number_from_url() -> None:
    assert pr_number_from_url("https://github.com/o/r/pull/141") == "141"
    assert pr_number_from_url("https://github.com/o/r/pull/141#issuecomment-1") == "141"
    assert pr_number_from_url("") == ""
