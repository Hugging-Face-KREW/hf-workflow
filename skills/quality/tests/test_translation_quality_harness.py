from __future__ import annotations

import json
import hashlib
import sys
import threading
import time
import types
from pathlib import Path

import pytest

from tools.translation_quality_harness import (
    DEFAULT_MQM_PROMPT_PATH,
    DEFAULT_MQM_SCHEMA_PATH,
    DEFAULT_STYLE_GUIDE_PATH,
    Issue,
    MetricConfig,
    align_segments,
    apply_unregistered_terminology_consistency_issues,
    build_report,
    deduplicate_detector_issues,
    llm_judge_model_from_env,
    load_mqm_prompt,
    main,
    markdown_doc,
    metric_cache_key,
    mqm_cache_namespace,
    mqm_response_format,
    normalized_numbers,
    normalize_link_targets_for_comparison,
    normalize_mqm_result,
    openai_mqm_task,
    parse_json_object,
    run_openai_mqm_judge,
    style_guide_digest,
)


FIXTURES = Path(__file__).parent / "fixtures" / "translation_quality_harness"


def no_unregistered_terms() -> dict[str, object]:
    return {"status": "not_applicable", "unregistered_terms": []}


def manifest_for(tmp_path: Path, target_name: str) -> Path:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        f"""version: 1
source:
  url: https://huggingface.co/blog/testing-spaces
  title: Testing Hugging Face Spaces
translation:
  file_path: {target_name}
handoff:
  quality:
    enabled: true
    checks:
      - hard_gates
""",
        encoding="utf-8",
    )
    return manifest


def manifest_with_source_hash(tmp_path: Path, target_name: str, source_hash: str) -> Path:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        f"""version: 1
source:
  url: https://huggingface.co/blog/testing-spaces
  title: Testing Hugging Face Spaces
  hash: {source_hash}
translation:
  file_path: {target_name}
handoff:
  quality:
    enabled: true
    checks:
      - hard_gates
      - segments
      - glossary
""",
        encoding="utf-8",
    )
    return manifest


def test_harness_routes_good_translation_to_review_without_semantic_evaluation(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md")

    assert report["status"] == "review_required"
    assert report["hard_failures"] == []
    assert report["dimension_scores"]["publishing_integrity"] == 100.0
    assert report["metadata"]["source_segment_count"] == report["metadata"]["target_segment_count"]
    assert report["metadata"]["aligned_segment_count"] == report["metadata"]["source_segment_count"]
    assert report["metadata"]["target_source_length_ratio"] > 0
    assert report["segments"]["source"]
    assert report["segments"]["target"]
    assert report["segment_alignment"]


def test_harness_rejects_when_source_is_unavailable(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")

    report = build_report(manifest, FIXTURES, fetch_source_url=False)

    assert report["status"] == "reject"
    assert report["metadata"]["source_available"] is False
    assert any("Source document is unavailable" in issue["message"] for issue in report["hard_failures"])


def test_harness_does_not_auto_pass_unrelated_same_length_korean(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    source.write_text(
        """---
title: Original
---

# Technical update

This article explains a reliable process for teams working together in demanding production environments.
""",
        encoding="utf-8",
    )
    target.write_text(
        """---
title: 오늘의 점심 메뉴
---

# 주말 여행 계획

이번 글에서는 가족과 함께 떠나는 여름 바다 여행과 맛있는 지역 음식점에 관한 즐거운 경험을 자세히 소개합니다.
""",
        encoding="utf-8",
    )
    manifest.write_text(
        """version: 1
source:
  file_path: source.md
translation:
  file_path: target.md
""",
        encoding="utf-8",
    )

    report = build_report(manifest, tmp_path)

    assert report["metrics"]["summary"]["qe_average"] == 1.0
    assert report["status"] == "review_required"
    assert report["metadata"]["semantic_evaluation_complete"] is False


def test_harness_loads_evaluation_thresholds_from_config(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")
    config = tmp_path / "eval-config.yml"
    config.write_text(
        """version: 1
language:
  min_korean_letter_ratio: 0.99
""",
        encoding="utf-8",
    )

    report = build_report(
        manifest,
        FIXTURES,
        source_path=FIXTURES / "source.md",
        evaluation_config_path=config,
    )

    assert any("Korean letter ratio is low" in issue["message"] for issue in report["issues"])
    assert report["metadata"]["evaluation_config_path"] == str(config)


def test_harness_loads_number_gate_from_config(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    gates = tmp_path / "gates.yml"
    source.write_text("---\ntitle: Numbers\n---\n\nThe system uses 3 workers.\n", encoding="utf-8")
    target.write_text("---\ntitle: 숫자\n---\n\n시스템은 4개의 워커를 사용합니다.\n", encoding="utf-8")
    manifest.write_text(
        "version: 1\nsource:\n  file_path: source.md\ntranslation:\n  file_path: target.md\n",
        encoding="utf-8",
    )
    gates.write_text(
        "version: 1\nhard_gates:\n  numbers:\n    status: reject\n",
        encoding="utf-8",
    )

    report = build_report(manifest, tmp_path, gates_config_path=gates)

    assert any("number/unit token" in issue["message"] for issue in report["hard_failures"])
    assert report["metadata"]["gates_config_path"] == str(gates)


def test_harness_applies_configured_korean_ratio_gate_severity(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    gates = tmp_path / "gates.yml"
    source.write_text("---\ntitle: English\n---\n\nA short source paragraph.\n", encoding="utf-8")
    target.write_text("---\ntitle: English\n---\n\nAn untranslated target paragraph.\n", encoding="utf-8")
    manifest.write_text(
        "version: 1\nsource:\n  file_path: source.md\ntranslation:\n  file_path: target.md\n",
        encoding="utf-8",
    )
    gates.write_text(
        "version: 1\nhard_gates:\n  korean_ratio:\n    status: reject\n",
        encoding="utf-8",
    )

    report = build_report(manifest, tmp_path, gates_config_path=gates)

    assert any("Korean letter ratio is low" in issue["message"] for issue in report["hard_failures"])


def test_harness_loads_frontmatter_key_lists_from_gate_policy(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    gates = tmp_path / "gates.yml"
    source.write_text(
        "---\ntitle: Source\nauthors: alice\nthumbnail: original.png\n---\n\nSource text.\n",
        encoding="utf-8",
    )
    target.write_text(
        "---\ntitle: 번역\nauthors: alice\n---\n\n번역문입니다.\n",
        encoding="utf-8",
    )
    manifest.write_text(
        "version: 1\nsource:\n  file_path: source.md\ntranslation:\n  file_path: target.md\n",
        encoding="utf-8",
    )
    gates.write_text(
        """version: 1
hard_gates:
  front_matter:
    status: reject
    required_target_keys:
      - title
      - description
    preserved_source_keys:
      - authors
""",
        encoding="utf-8",
    )

    report = build_report(manifest, tmp_path, gates_config_path=gates)
    messages = [issue["message"] for issue in report["issues"]]

    assert "Target front matter is missing required key: description." in messages
    assert not any("thumbnail" in message for message in messages)


def test_harness_preserves_source_frontmatter_by_default(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    source.write_text(
        "---\ntitle: Source\nauthors:\n  - user: upstream\nthumbnail: /blog/assets/source.png\ntags:\n  - source-tag\nblog: source-blog\n---\n\nSource text.\n",
        encoding="utf-8",
    )
    target.write_text(
        "---\ntitle: 번역\nauthors:\n  - user: dailybot\nthumbnail: assets/images/local.png\ntags:\n  - target-tag\nblog: target-blog\n---\n\n번역문입니다.\n",
        encoding="utf-8",
    )
    manifest.write_text(
        "version: 1\nsource:\n  file_path: source.md\ntranslation:\n  file_path: target.md\n",
        encoding="utf-8",
    )

    report = build_report(manifest, tmp_path)

    messages = [issue["message"] for issue in report["hard_failures"]]
    for key in ("authors", "thumbnail", "tags", "blog"):
        assert any(f"Front matter key `{key}`" in message for message in messages)


def test_default_gate_policy_accepts_localized_frontmatter_alias(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    source.write_text(
        "---\ntitle: Source\nthumbnail: /blog/assets/post/thumbnail.png\n---\n\nSource text.\n",
        encoding="utf-8",
    )
    target.write_text(
        "---\ntitle: 번역\nimage: assets/images/blog/posts/post/thumbnail.png\n---\n\n번역문입니다.\n",
        encoding="utf-8",
    )
    manifest.write_text(
        "version: 1\nsource:\n  file_path: source.md\ntranslation:\n  file_path: target.md\n",
        encoding="utf-8",
    )

    report = build_report(manifest, tmp_path)

    assert not any(
        "Front matter key `thumbnail`" in issue["message"] for issue in report["hard_failures"]
    )


def test_harness_rejects_missing_localized_frontmatter_alias_target(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    gates = tmp_path / "gates.yml"
    source.write_text(
        "---\ntitle: Source\nthumbnail: /blog/assets/post/thumbnail.png\n---\n\nSource text.\n",
        encoding="utf-8",
    )
    target.write_text("---\ntitle: 번역\n---\n\n번역문입니다.\n", encoding="utf-8")
    manifest.write_text(
        "version: 1\nsource:\n  file_path: source.md\ntranslation:\n  file_path: target.md\n",
        encoding="utf-8",
    )
    gates.write_text(
        """version: 1
hard_gates:
  front_matter:
    status: reject
    preserved_source_keys:
      - thumbnail
    localized_source_key_aliases:
      thumbnail: image
""",
        encoding="utf-8",
    )

    report = build_report(manifest, tmp_path, gates_config_path=gates)

    assert any(
        "Front matter key `thumbnail` must be represented by target key `image`."
        in issue["message"]
        for issue in report["hard_failures"]
    )


def test_harness_respects_disabled_exact_match_gate_option(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    gates = tmp_path / "gates.yml"
    source.write_text("---\ntitle: S\n---\n\n[docs](https://example.com/a)\n", encoding="utf-8")
    target.write_text("---\ntitle: T\n---\n\n[문서](https://example.com/b)\n", encoding="utf-8")
    manifest.write_text(
        "version: 1\nsource:\n  file_path: source.md\ntranslation:\n  file_path: target.md\n",
        encoding="utf-8",
    )
    gates.write_text(
        "version: 1\nhard_gates:\n  links:\n    status: reject\n    exact_target_match: false\n",
        encoding="utf-8",
    )

    report = build_report(manifest, tmp_path, gates_config_path=gates)

    assert not any("link target mismatch" in issue["message"] for issue in report["issues"])


def test_harness_loads_todo_markers_from_gate_policy(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    gates = tmp_path / "gates.yml"
    source.write_text("---\ntitle: S\n---\n\nComplete source.\n", encoding="utf-8")
    target.write_text("---\ntitle: T\n---\n\nREPLACE_ME before publishing.\n", encoding="utf-8")
    manifest.write_text(
        "version: 1\nsource:\n  file_path: source.md\ntranslation:\n  file_path: target.md\n",
        encoding="utf-8",
    )
    gates.write_text(
        """version: 1
hard_gates:
  todo_markers:
    status: reject
    markers:
      - REPLACE_ME
""",
        encoding="utf-8",
    )

    report = build_report(manifest, tmp_path, gates_config_path=gates)

    assert any("unresolved placeholder" in issue["message"] for issue in report["hard_failures"])


def test_harness_allows_todo_when_source_contains_same_marker(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    source.write_text("---\ntitle: S\n---\n\nThere is a TODO in the upstream PR.\n", encoding="utf-8")
    target.write_text("---\ntitle: T\n---\n\n업스트림 PR에는 `TODO`가 있습니다.\n", encoding="utf-8")
    manifest.write_text(
        "version: 1\nsource:\n  file_path: source.md\ntranslation:\n  file_path: target.md\n",
        encoding="utf-8",
    )

    report = build_report(manifest, tmp_path)

    assert not any("unresolved placeholder" in issue["message"] for issue in report["hard_failures"])


def test_harness_still_rejects_template_braces_even_when_source_contains_them(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    source.write_text("---\ntitle: S\n---\n\nTemplate {{value}}.\n", encoding="utf-8")
    target.write_text("---\ntitle: T\n---\n\n템플릿 {{value}}.\n", encoding="utf-8")
    manifest.write_text(
        "version: 1\nsource:\n  file_path: source.md\ntranslation:\n  file_path: target.md\n",
        encoding="utf-8",
    )

    report = build_report(manifest, tmp_path)

    assert any("unresolved placeholder" in issue["message"] for issue in report["hard_failures"])


def test_harness_applies_markdown_parse_policy_to_source_errors(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    gates = tmp_path / "gates.yml"
    source.write_text("---\ntitle: S\n---\n\n```python\nprint('open')\n", encoding="utf-8")
    target.write_text("---\ntitle: T\n---\n\n번역문입니다.\n", encoding="utf-8")
    manifest.write_text(
        "version: 1\nsource:\n  file_path: source.md\ntranslation:\n  file_path: target.md\n",
        encoding="utf-8",
    )
    gates.write_text(
        """version: 1
review_gates:
  markdown_parse:
    status: review_required
hard_gates:
  code_blocks:
    status: reject
    compare_hashes: false
""",
        encoding="utf-8",
    )

    report = build_report(manifest, tmp_path, gates_config_path=gates)
    parse_issues = [issue for issue in report["issues"] if "Unclosed fenced code block" in issue["message"]]

    assert parse_issues
    assert all(issue["severity"] == "major" for issue in parse_issues)


def test_harness_rejects_code_mutation(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_bad_code.md")

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md")

    assert report["status"] == "reject"
    categories = {issue["category"] for issue in report["hard_failures"]}
    assert "technical" in categories


def test_harness_routes_number_mutation_to_review(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    source.write_text(
        """---
title: "Number Review"
---

# Number Review

The model has 3 layers and 20 checkpoints.
""",
        encoding="utf-8",
    )
    target.write_text(
        """---
title: "숫자 리뷰"
---

# 숫자 리뷰

이 모델에는 4개의 레이어와 20개의 체크포인트가 있습니다.
""",
        encoding="utf-8",
    )
    manifest.write_text(
        """version: 1
source:
  url: https://huggingface.co/blog/number-review
  title: Number Review
translation:
  file_path: target.md
""",
        encoding="utf-8",
    )

    report = build_report(manifest, tmp_path, source_path=source)

    assert report["status"] == "review_required"
    assert any("number/unit token" in issue["message"] for issue in report["issues"])
    assert not any("number/unit token" in issue["message"] for issue in report["hard_failures"])


def test_number_extraction_does_not_fold_next_word_into_unit() -> None:
    text = "56 Skill runs, 14 simulated rooms, 200 benchmarks, Step 2 should pass, 45s, 65B, 30%"

    assert normalized_numbers(text) == ["56", "14", "200", "2", "45s", "65B", "30%"]


def test_markdown_doc_numbers_ignore_links_code_and_html_attributes() -> None:
    doc = markdown_doc(
        """
[paper](https://arxiv.org/abs/2602.04998)
<div style="font-size: 1.1rem; padding: 1.5rem">Shown 30%</div>
`dev0`
"""
    )

    assert doc.link_targets == ["https://arxiv.org/abs/2602.04998"]
    assert doc.urls == []
    assert doc.numbers == ["30%"]


@pytest.mark.parametrize("attribution_ending", ["글입니다._", "글입니다_."])
def test_markdown_doc_ignores_hfkrew_translation_boilerplate(attribution_ending: str) -> None:
    doc = markdown_doc(
        f"""---
title: 번역 제목
---

* TOC
{{:toc}}
<!--toc-->
_이 글은 Hugging Face 블로그의 [Source Title](https://huggingface.co/blog/source-title)를 한국어로 번역한 {attribution_ending}

<!-- Source: https://huggingface.co/blog/source-title -->

---

<!--
Review instructions:
- Preserve technical meaning.
-->

# 번역 제목

본문입니다.
"""
    )

    assert [segment.text for segment in doc.segments] == ["번역 제목", "본문입니다."]
    assert doc.urls == []


def test_markdown_doc_strips_heading_anchors_before_segmenting() -> None:
    doc = markdown_doc(
        """
## 섹션 제목 {#section-1}

본문입니다.
"""
    )

    assert [segment.text for segment in doc.segments] == ["섹션 제목", "본문입니다."]


def test_markdown_doc_ignores_placeholder_markers_inside_code_blocks() -> None:
    doc = markdown_doc(
        """
```python
payload = {"extra_body": {"enable_thinking": False}}
```

This prose still has {{ unresolved marker.
"""
    )

    assert doc.todo_markers == ["{{"]


def test_harness_rejects_link_and_image_mutation(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_bad_link.md")

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md")

    assert report["status"] == "reject"
    messages = "\n".join(issue["message"] for issue in report["hard_failures"])
    assert "link target mismatch" in messages
    assert "image target mismatch" in messages


def test_normalizes_hf_profile_absolute_link_when_source_uses_relative_target() -> None:
    source, target = normalize_link_targets_for_comparison(
        ["ariG23498"],
        ["https://huggingface.co/ariG23498"],
    )

    assert source == target == ["ariG23498"]


def test_keeps_full_hf_url_when_source_uses_full_target() -> None:
    source, target = normalize_link_targets_for_comparison(
        ["https://huggingface.co/kernels"],
        ["https://huggingface.co/kernels"],
    )

    assert source == target == ["https://huggingface.co/kernels"]


def test_harness_rejects_frontmatter_mutation(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_bad_frontmatter.md")
    gates = tmp_path / "gates.yml"
    gates.write_text(
        """version: 1
hard_gates:
  front_matter:
    status: reject
    required_target_keys:
      - title
    preserved_source_keys:
      - authors
      - thumbnail
""",
        encoding="utf-8",
    )

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md", gates_config_path=gates)

    assert report["status"] == "reject"
    assert any("Front matter key `authors`" in issue["message"] for issue in report["hard_failures"])
    assert any("Front matter key `thumbnail`" in issue["message"] for issue in report["hard_failures"])


def test_harness_rejects_table_and_latex_mutation(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_bad_table_latex.md")

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md")

    assert report["status"] == "reject"
    messages = "\n".join(issue["message"] for issue in report["hard_failures"])
    assert "Markdown table shape mismatch" in messages
    assert "LaTeX token mismatch" in messages


def test_cli_writes_markdown_and_json_reports(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")
    output_md = tmp_path / "quality-report.md"
    output_json = tmp_path / "quality-report.json"

    exit_code = main(
        [
            "--manifest",
            str(manifest),
            "--target-root",
            str(FIXTURES),
            "--source",
            str(FIXTURES / "source.md"),
            "--output-md",
            str(output_md),
            "--output-json",
            str(output_json),
            "--fail-on-reject",
        ]
    )

    assert exit_code == 0
    assert "Status: review_required" in output_md.read_text(encoding="utf-8")
    loaded = json.loads(output_json.read_text(encoding="utf-8"))
    assert loaded["status"] == "review_required"


def test_cli_fail_on_reject_returns_nonzero(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_bad_code.md")

    exit_code = main(
        [
            "--manifest",
            str(manifest),
            "--target-root",
            str(FIXTURES),
            "--source",
            str(FIXTURES / "source.md"),
            "--output-md",
            str(tmp_path / "quality-report.md"),
            "--output-json",
            str(tmp_path / "quality-report.json"),
            "--fail-on-reject",
        ]
    )

    assert exit_code == 1


def test_cli_fail_on_reject_also_blocks_source_changed(tmp_path: Path) -> None:
    manifest = manifest_with_source_hash(tmp_path, "target_good.md", "stale-source-hash")

    exit_code = main(
        [
            "--manifest",
            str(manifest),
            "--target-root",
            str(FIXTURES),
            "--source",
            str(FIXTURES / "source.md"),
            "--output-md",
            str(tmp_path / "quality-report.md"),
            "--output-json",
            str(tmp_path / "quality-report.json"),
            "--fail-on-reject",
        ]
    )

    assert exit_code == 1


def test_harness_reports_glossary_violation_as_terminology(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_bad_glossary.md")

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md")

    assert report["status"] == "review_required"
    assert any(issue["category"] == "terminology" for issue in report["issues"])
    assert report["dimension_scores"]["terminology"] < 100.0


def test_harness_rejects_japanese_punctuation_in_korean_prose(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    source.write_text(
        "---\ntitle: Source\n---\n\nThis sentence uses punctuation.\n\n```text\ncode。、\n```\n",
        encoding="utf-8",
    )
    target.write_text(
        "---\ntitle: 번역\n---\n\n이 문장에는 일본어 온점。그리고 쉼표、가 있습니다.\n\n```text\ncode。、\n```\n",
        encoding="utf-8",
    )
    manifest.write_text(
        "version: 1\nsource:\n  file_path: source.md\ntranslation:\n  file_path: target.md\n",
        encoding="utf-8",
    )

    report = build_report(manifest, tmp_path)

    locale_failures = [
        item
        for item in report["hard_failures"]
        if item["message"] == "Japanese punctuation found in Korean prose."
    ]
    assert report["status"] == "reject"
    assert {item["reason"].split("`")[1] for item in locale_failures} == {"。", "、"}
    assert all("code。、" not in item["target_span"] for item in locale_failures)


def test_harness_allows_japanese_punctuation_inside_protected_code(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    markdown = "---\ntitle: Example\n---\n\n문장입니다. `inline。、` [링크](https://example.com/。、)\n\n```text\ncode。、\n```\n"
    source.write_text(markdown, encoding="utf-8")
    target.write_text(markdown.replace("Example", "예시"), encoding="utf-8")
    manifest.write_text(
        "version: 1\nsource:\n  file_path: source.md\ntranslation:\n  file_path: target.md\n",
        encoding="utf-8",
    )

    report = build_report(manifest, tmp_path)

    assert not any(
        item["message"] == "Japanese punctuation found in Korean prose."
        for item in report["issues"]
    )


def test_harness_detects_additional_and_duplicate_segments(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_bad_addition_duplicate.md")

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md")

    assert report["status"] == "review_required"
    messages = "\n".join(issue["message"] for issue in report["issues"])
    assert "Target has additional text segments" in messages
    assert "Duplicate target segments detected" in messages
    assert report["dimension_scores"]["completeness"] < 100.0


def test_harness_detects_omitted_segments(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_bad_omission.md")

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md")

    messages = "\n".join(issue["message"] for issue in report["issues"])
    assert "Source segment coverage is low" in messages


def test_harness_reports_source_changed_from_manifest_hash(tmp_path: Path) -> None:
    manifest = manifest_with_source_hash(tmp_path, "target_good.md", "not-the-current-source-hash")

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md")

    assert report["status"] == "source_changed"
    assert report["metadata"]["source_changed"] is True
    assert any("Source hash changed" in issue["message"] for issue in report["issues"])


def test_harness_accepts_matching_manifest_source_hash(tmp_path: Path) -> None:
    source_text = (FIXTURES / "source.md").read_text(encoding="utf-8")
    source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    manifest = manifest_with_source_hash(tmp_path, "target_good.md", source_hash)

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md")

    assert report["status"] == "review_required"
    assert report["metadata"]["source_changed"] is False


def test_harness_fetches_source_url_when_source_file_is_absent(tmp_path: Path) -> None:
    source_url = (FIXTURES / "source.md").resolve().as_uri()
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        f"""version: 1
source:
  url: {source_url}
  title: Testing Hugging Face Spaces
translation:
  file_path: target_good.md
""",
        encoding="utf-8",
    )

    report = build_report(manifest, FIXTURES)

    assert report["status"] == "review_required"
    assert report["metadata"]["source_available"] is True
    assert report["metadata"]["source_format"] == "url_markdown"
    assert report["metadata"]["source_path"] == source_url
    assert report["segment_alignment"]


def test_cli_writes_segment_jsonl_and_reads_translation_memory(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")
    output_source_segments = tmp_path / "source-segments.jsonl"
    output_target_segments = tmp_path / "target-segments.jsonl"
    output_json = tmp_path / "quality-report.json"

    exit_code = main(
        [
            "--manifest",
            str(manifest),
            "--target-root",
            str(FIXTURES),
            "--source",
            str(FIXTURES / "source.md"),
            "--translation-memory",
            str(FIXTURES / "translation_memory.jsonl"),
            "--output-md",
            str(tmp_path / "quality-report.md"),
            "--output-json",
            str(output_json),
            "--output-source-segments",
            str(output_source_segments),
            "--output-target-segments",
            str(output_target_segments),
        ]
    )

    assert exit_code == 0
    assert output_source_segments.read_text(encoding="utf-8").strip()
    assert output_target_segments.read_text(encoding="utf-8").strip()
    loaded = json.loads(output_json.read_text(encoding="utf-8"))
    assert loaded["metadata"]["translation_memory_entry_count"] == 2
    assert loaded["metadata"]["translation_memory_match_count"] >= 1


def write_metric_fixture(tmp_path: Path, target_body: str) -> tuple[Path, Path]:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    manifest = tmp_path / "manifest.yaml"
    source.write_text(
        """---
title: "Simple Review"
---

# Simple Review

This article explains a careful review process for a long technical post.

The workflow helps reviewers find risky segments before publication.
""",
        encoding="utf-8",
    )
    target.write_text(
        f"""---
title: "간단한 리뷰"
---

{target_body}
""",
        encoding="utf-8",
    )
    manifest.write_text(
        """version: 1
source:
  url: https://huggingface.co/blog/simple-review
  title: Simple Review
translation:
  file_path: target.md
""",
        encoding="utf-8",
    )
    return manifest, source


def test_qe_metric_can_be_disabled(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")

    report = build_report(
        manifest,
        FIXTURES,
        source_path=FIXTURES / "source.md",
        metric_config=MetricConfig(qe_metric="off", enable_embedding_similarity=False),
    )

    assert report["status"] == "review_required"
    assert report["metrics"]["summary"]["qe_enabled"] is False
    assert report["metrics"]["summary"]["embedding_similarity_enabled"] is False
    assert all("QE metric score is low" not in issue["message"] for issue in report["issues"])


def test_low_qe_segment_routes_to_review_required(tmp_path: Path) -> None:
    manifest, source = write_metric_fixture(
        tmp_path,
        """# 간단한 리뷰

짧음.

부족.
""",
    )

    report = build_report(manifest, tmp_path, source_path=source, metric_config=MetricConfig(qe_review_threshold=0.70))

    assert report["status"] == "review_required"
    assert report["metrics"]["summary"]["qe_enabled"] is True
    assert report["metrics"]["summary"]["qe_min"] < 0.70
    assert any(issue["message"] == "QE metric score is low." for issue in report["issues"])


def test_metric_cache_records_hits_on_second_run(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")
    cache_path = tmp_path / "metric-cache.json"
    config = MetricConfig(metric_cache_path=cache_path)

    first = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md", metric_config=config)
    second = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md", metric_config=config)

    assert cache_path.exists()
    assert first["metrics"]["summary"]["cache_misses"] > 0
    assert second["metrics"]["summary"]["cache_hits"] > 0


def test_chrf_reference_metric_is_reported(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")
    config = MetricConfig(enable_chrf=True, reference_path=FIXTURES / "target_good.md")

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md", metric_config=config)

    assert report["metrics"]["summary"]["chrf_enabled"] is True
    assert report["metrics"]["summary"]["chrf_average"] == 1.0


def test_cometkiwi_wrapper_falls_back_without_breaking_deterministic_gates(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")
    config = MetricConfig(qe_metric="cometkiwi")

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md", metric_config=config)

    assert report["status"] == "review_required"
    assert report["metrics"]["summary"]["qe_metric"] == "cometkiwi"
    assert "qe_average" in report["metrics"]["summary"]
    assert report["metrics"]["summary"]["warnings"]


def write_mqm_fixture(tmp_path: Path) -> Path:
    fixture = tmp_path / "mqm-fixture.jsonl"
    fixture.write_text(
        json.dumps(
            {
                "segment_id": "p_002",
                "adequacy_score": 0.41,
                "fluency_score": 0.90,
                "technical_score": 0.80,
                "terminology_review": no_unregistered_terms(),
                "errors": [
                    {
                        "guide_rule": "modal_strength",
                        "guide_section": "4. 의미·조건·확신의 강도는 절대 바꾸지 않습니다",
                        "category": "accuracy",
                        "severity": "major",
                        "source_span": "can be used",
                        "target_span": "사용할 수 있습니다",
                        "explanation": "가능성을 단정으로 바꾸었습니다.",
                        "suggested_fix": "사용할 수 있습니다",
                    }
                ],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return fixture


def test_fixture_mqm_judge_routes_feedback_into_report(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")
    fixture = write_mqm_fixture(tmp_path)
    config = MetricConfig(
        qe_metric="off",
        enable_embedding_similarity=False,
        llm_judge_provider="fixture",
        llm_judge_fixture_path=fixture,
        llm_judge_max_segments=3,
    )

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md", metric_config=config)

    assert report["status"] == "review_required"
    assert report["mqm_judge"]["enabled"] is True
    assert report["mqm_judge"]["provider"] == "fixture"
    assert report["mqm_judge"]["requested_segment_count"] == 3
    assert report["mqm_judge"]["segment_count"] == 1
    assert report["mqm_judge"]["error_count"] == 1
    assert report["dimension_scores"]["adequacy"] == 41.0
    assert report["style_guide"]["issue_count"] == 0
    assert any(issue["message"] == "MQM judge reported accuracy issue." for issue in report["issues"])


def test_complete_clean_mqm_evaluation_allows_auto_pass(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")
    source = markdown_doc((FIXTURES / "source.md").read_text(encoding="utf-8"))
    target = markdown_doc((FIXTURES / "target_good.md").read_text(encoding="utf-8"))
    fixture = tmp_path / "complete-mqm-fixture.jsonl"
    fixture.write_text(
        "\n".join(
            json.dumps(
                {
                    "segment_id": item["target_id"],
                    "adequacy_score": 1.0,
                    "fluency_score": 1.0,
                    "technical_score": 1.0,
                    "terminology_review": no_unregistered_terms(),
                    "errors": [],
                },
                ensure_ascii=False,
            )
            for item in align_segments(source, target)
        )
        + "\n",
        encoding="utf-8",
    )
    config = MetricConfig(
        qe_metric="off",
        enable_embedding_similarity=False,
        llm_judge_provider="fixture",
        llm_judge_fixture_path=fixture,
    )

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md", metric_config=config)

    assert report["status"] == "auto_pass"
    assert report["metadata"]["semantic_evaluation_complete"] is True
    assert not any("Semantic adequacy evaluation is incomplete" in issue["message"] for issue in report["issues"])


def test_duplicate_or_unknown_mqm_segment_ids_cannot_auto_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")
    source = markdown_doc((FIXTURES / "source.md").read_text(encoding="utf-8"))
    target = markdown_doc((FIXTURES / "target_good.md").read_text(encoding="utf-8"))
    alignment_count = len(align_segments(source, target))
    invalid_summary = {
        "enabled": True,
        "provider": "openai",
        "requested_segment_count": alignment_count,
        "segment_count": alignment_count,
        "skipped_segment_count": 0,
        "error_count": 0,
        "warnings": [],
        "segments": [
            {
                "segment_id": "wrong-id",
                "adequacy_score": 1.0,
                "fluency_score": 1.0,
                "technical_score": 1.0,
                "terminology_review": no_unregistered_terms(),
                "errors": [],
            }
            for _ in range(alignment_count)
        ],
    }
    monkeypatch.setattr("tools.translation_quality_harness.evaluate_mqm_judge", lambda *_: invalid_summary)

    report = build_report(
        manifest,
        FIXTURES,
        source_path=FIXTURES / "source.md",
        metric_config=MetricConfig(qe_metric="off", enable_embedding_similarity=False, llm_judge_provider="openai"),
    )

    assert report["metadata"]["semantic_evaluation_complete"] is False
    assert report["status"] == "review_required"
    assert any("MQM segment coverage is invalid" in warning for warning in report["mqm_judge"]["warnings"])


def test_mqm_judge_downgrades_wording_only_accuracy_major(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")
    fixture = tmp_path / "mqm-wording-fixture.jsonl"
    fixture.write_text(
        json.dumps(
            {
                "segment_id": "p_002",
                "adequacy_score": 0.92,
                "fluency_score": 0.88,
                "technical_score": 0.95,
                "terminology_review": no_unregistered_terms(),
                "errors": [
                    {
                        "guide_rule": "preserve_meaning",
                        "guide_section": "MQM judge",
                        "category": "accuracy",
                        "severity": "major",
                        "source_span": "can be used",
                        "target_span": "사용할 수 있습니다",
                        "explanation": "의미는 유지되지만 직역이라 다소 어색한 표현입니다.",
                        "suggested_fix": "더 자연스럽게 다듬습니다.",
                    }
                ],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    config = MetricConfig(
        qe_metric="off",
        enable_embedding_similarity=False,
        llm_judge_provider="fixture",
        llm_judge_fixture_path=fixture,
        llm_judge_max_segments=3,
    )

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md", metric_config=config)

    [segment] = report["mqm_judge"]["segments"]
    [error] = segment["errors"]
    assert error["category"] == "fluency"
    assert error["severity"] == "minor"
    assert any("downgraded" in warning for warning in report["mqm_judge"]["warnings"])
    assert any(issue["message"] == "MQM judge reported fluency issue." for issue in report["issues"])


def test_mqm_judge_keeps_modal_strength_accuracy_major() -> None:
    warnings: list[str] = []

    result = normalize_mqm_result(
        {
            "segment_id": "p_002",
            "adequacy_score": 0.92,
            "fluency_score": 0.88,
            "technical_score": 1.0,
            "terminology_review": no_unregistered_terms(),
            "errors": [
                {
                    "guide_rule": "modal_strength",
                    "guide_section": "4. 의미·조건·확신의 강도는 절대 바꾸지 않습니다",
                    "category": "accuracy",
                    "severity": "major",
                    "source_span": "may improve throughput; must set the token",
                    "target_span": "처리량을 개선합니다; 토큰을 설정하는 것이 좋습니다",
                    "explanation": "가능성 표현과 의무 표현의 강도가 달라진 표현입니다.",
                    "suggested_fix": "개선할 수 있습니다. 반드시 토큰을 설정해야 합니다.",
                }
            ],
        },
        "p_002",
        warnings,
    )

    assert result is not None
    [error] = result["errors"]
    assert error["category"] == "accuracy"
    assert error["severity"] == "major"
    assert not warnings


def test_mqm_judge_never_downgrades_critical_accuracy_error() -> None:
    warnings: list[str] = []

    result = normalize_mqm_result(
        {
            "segment_id": "p_002",
            "adequacy_score": 0.99,
            "fluency_score": 0.99,
            "technical_score": 0.99,
            "terminology_review": no_unregistered_terms(),
            "errors": [
                {
                    "guide_rule": "preserve_meaning",
                    "guide_section": "MQM judge",
                    "category": "accuracy",
                    "severity": "critical",
                    "source_span": "The model does not support this format.",
                    "target_span": "이 모델은 이 형식을 지원합니다.",
                    "explanation": "표현의 의미가 반대로 바뀌었습니다.",
                    "suggested_fix": "이 모델은 이 형식을 지원하지 않습니다.",
                }
            ],
        },
        "p_002",
        warnings,
    )

    assert result is not None
    assert result["errors"][0]["severity"] == "critical"
    assert result["errors"][0]["category"] == "accuracy"


def test_mqm_judge_requires_structured_unregistered_terminology_review() -> None:
    warnings: list[str] = []

    result = normalize_mqm_result(
        {
            "segment_id": "p_001",
            "adequacy_score": 1.0,
            "fluency_score": 1.0,
            "technical_score": 1.0,
            "errors": [],
        },
        "p_001",
        warnings,
    )

    assert result is None
    assert any("terminology_review" in warning for warning in warnings)


def test_mqm_judge_accepts_audited_unregistered_technical_term() -> None:
    warnings: list[str] = []
    source = "Speculative decoding improves generation speed."
    target = "추측 디코딩은 생성 속도를 높입니다."

    result = normalize_mqm_result(
        {
            "segment_id": "p_001",
            "adequacy_score": 1.0,
            "fluency_score": 1.0,
            "technical_score": 1.0,
            "terminology_review": {
                "status": "pass",
                "unregistered_terms": [
                    {
                        "source_term": "Speculative decoding",
                        "target_term": "추측 디코딩",
                        "assessment": "acceptable",
                        "explanation": "문맥에 맞고 원문의 기술적 의미를 보존합니다.",
                    }
                ],
            },
            "errors": [],
        },
        "p_001",
        warnings,
        source_text=source,
        target_text=target,
    )

    assert result is not None
    assert result["terminology_review"]["status"] == "pass"
    assert not warnings


def test_mqm_judge_rejects_failed_term_without_linked_terminology_error() -> None:
    warnings: list[str] = []

    result = normalize_mqm_result(
        {
            "segment_id": "p_001",
            "adequacy_score": 0.8,
            "fluency_score": 0.8,
            "technical_score": 0.7,
            "terminology_review": {
                "status": "fail",
                "unregistered_terms": [
                    {
                        "source_term": "speculative decoding",
                        "target_term": "사색 해독",
                        "assessment": "mistranslated",
                        "explanation": "기술적 의미와 다른 한국어 표현으로 번역되었습니다.",
                    }
                ],
            },
            "errors": [],
        },
        "p_001",
        warnings,
        source_text="Use speculative decoding for generation.",
        target_text="생성에 사색 해독을 사용합니다.",
    )

    assert result is None
    assert any("linked terminology error" in warning for warning in warnings)


def test_mqm_judge_accepts_failed_term_with_actionable_terminology_error() -> None:
    warnings: list[str] = []

    result = normalize_mqm_result(
        {
            "segment_id": "p_001",
            "adequacy_score": 0.8,
            "fluency_score": 0.9,
            "technical_score": 0.6,
            "terminology_review": {
                "status": "fail",
                "unregistered_terms": [
                    {
                        "source_term": "speculative decoding",
                        "target_term": "사색 해독",
                        "assessment": "mistranslated",
                        "explanation": "생성 기법의 의미를 전달하지 못하는 잘못된 번역입니다.",
                    }
                ],
            },
            "errors": [
                {
                    "guide_rule": "unregistered_technical_term",
                    "guide_section": "Technical terminology",
                    "category": "terminology",
                    "severity": "major",
                    "source_span": "speculative decoding",
                    "target_span": "사색 해독",
                    "explanation": "생성 기법을 일반적인 사색 행위처럼 잘못 번역했습니다.",
                    "suggested_fix": "문맥에 맞는 기술 용어인 추측 디코딩으로 통일합니다.",
                }
            ],
        },
        "p_001",
        warnings,
        source_text="Use speculative decoding for generation.",
        target_text="생성에 사색 해독을 사용합니다.",
    )

    assert result is not None
    assert result["terminology_review"]["status"] == "fail"
    assert result["errors"][0]["category"] == "terminology"
    assert not warnings


def test_harness_reports_inconsistent_unregistered_term_renderings() -> None:
    issues: list[Issue] = []
    mqm_judge = {
        "segments": [
            {
                "terminology_review": {
                    "status": "pass",
                    "unregistered_terms": [
                        {
                            "source_term": "speculative decoding",
                            "target_term": "추측 디코딩",
                            "assessment": "acceptable",
                            "explanation": "문맥에 맞는 기술 용어 번역입니다.",
                        }
                    ],
                }
            },
            {
                "terminology_review": {
                    "status": "pass",
                    "unregistered_terms": [
                        {
                            "source_term": "Speculative Decoding",
                            "target_term": "예측 디코딩",
                            "assessment": "acceptable",
                            "explanation": "문맥에 맞는 기술 용어 번역입니다.",
                        }
                    ],
                }
            },
        ]
    }

    apply_unregistered_terminology_consistency_issues(issues, mqm_judge)

    assert len(issues) == 1
    assert issues[0].category == "terminology"
    assert issues[0].severity == "major"
    assert issues[0].message == "Unregistered technical term is translated inconsistently."


@pytest.mark.parametrize(
    "payload",
    [
        {"segment_id": "p_001", "errors": []},
        {
            "segment_id": "p_001",
            "adequacy_score": 9,
            "fluency_score": 1,
            "technical_score": 1,
            "terminology_review": no_unregistered_terms(),
            "errors": [],
        },
        {
            "segment_id": "p_001",
            "adequacy_score": 1,
            "fluency_score": 1,
            "technical_score": 1,
            "terminology_review": no_unregistered_terms(),
            "errors": "not-an-array",
        },
    ],
)
def test_mqm_judge_rejects_malformed_result_instead_of_defaulting_to_perfect(payload: dict[str, object]) -> None:
    warnings: list[str] = []

    assert normalize_mqm_result(payload, "p_001", warnings) is None
    assert warnings


@pytest.mark.parametrize(
    "payload",
    [
        {
            "segment_id": "p_001",
            "adequacy_score": 1,
            "fluency_score": 1,
            "technical_score": 1,
            "terminology_review": no_unregistered_terms(),
            "errors": [],
            "unexpected": True,
        },
        {
            "segment_id": "p_001",
            "adequacy_score": 0.8,
            "fluency_score": 0.9,
            "technical_score": 1.0,
            "terminology_review": no_unregistered_terms(),
            "errors": [
                {
                    "guide_rule": "modal_strength",
                    "guide_section": "의미 강도",
                    "category": "accuracy",
                    "severity": "major",
                    "source_span": "must",
                    "target_span": "좋습니다",
                    "explanation": "의무 표현이 권장 표현으로 약해졌습니다.",
                    "suggested_fix": "반드시 해야 합니다.",
                    "unexpected": True,
                }
            ],
        },
    ],
)
def test_mqm_judge_rejects_additional_properties(payload: dict[str, object]) -> None:
    warnings: list[str] = []

    assert normalize_mqm_result(payload, "p_001", warnings) is None
    assert any("unexpected fields" in warning for warning in warnings)


@pytest.mark.parametrize(
    "text",
    [
        '```json\n{"segment_id":"p_001"}\n```',
        'Here is the result: {"segment_id":"p_001"}',
    ],
)
def test_parse_json_object_rejects_non_strict_wrappers(text: str) -> None:
    with pytest.raises(json.JSONDecodeError):
        parse_json_object(text)


def test_mqm_judge_rejects_error_with_hallucinated_span() -> None:
    warnings: list[str] = []
    source = "You must set the HF_TOKEN environment variable."
    target = "HF_TOKEN 환경 변수를 반드시 설정해야 합니다."

    result = normalize_mqm_result(
        {
            "segment_id": "p_001",
            "adequacy_score": 0.8,
            "fluency_score": 0.9,
            "technical_score": 1.0,
            "terminology_review": no_unregistered_terms(),
            "errors": [
                {
                    "guide_rule": "modal_strength",
                    "guide_section": "의미 강도",
                    "category": "accuracy",
                    "severity": "major",
                    "source_span": "You must set the HF_TOKEN environment variable.",
                    "target_span": "HF_TOKEN 환경 변수를 설정하는 것이 좋습니다.",
                    "explanation": "의무 강도가 약해졌습니다.",
                    "suggested_fix": "반드시 설정해야 합니다.",
                }
            ],
        },
        "p_001",
        warnings,
        source_text=source,
        target_text=target,
    )

    assert result is None
    assert any("target_span" in warning for warning in warnings)


def test_mqm_judge_rejects_error_without_substantive_explanation() -> None:
    warnings: list[str] = []

    result = normalize_mqm_result(
        {
            "segment_id": "p_001",
            "adequacy_score": 0.8,
            "fluency_score": 0.9,
            "technical_score": 1.0,
            "terminology_review": no_unregistered_terms(),
            "errors": [
                {
                    "guide_rule": "modal_strength",
                    "guide_section": "의미 강도",
                    "category": "accuracy",
                    "severity": "major",
                    "source_span": "must",
                    "target_span": "좋습니다",
                    "explanation": "원문은",
                    "suggested_fix": "반드시 해야 합니다.",
                }
            ],
        },
        "p_001",
        warnings,
    )

    assert result is None
    assert any("explanation" in warning for warning in warnings)


def test_mqm_response_format_uses_strict_json_schema() -> None:
    response_format = mqm_response_format()

    assert response_format["type"] == "json_schema"
    assert response_format["strict"] is True
    assert response_format["schema"]["additionalProperties"] is False
    assert set(response_format["schema"]["required"]) == {
        "segment_id",
        "adequacy_score",
        "fluency_score",
        "technical_score",
        "terminology_review",
        "errors",
    }


def test_mqm_cache_namespace_changes_with_judge_configuration() -> None:
    prompt_hash = "prompt"
    schema_hash = "schema"
    base = MetricConfig(llm_judge_model="gpt-5-nano-2025-08-07", llm_judge_reasoning_effort="minimal")
    stronger = MetricConfig(llm_judge_model="gpt-5-nano-2025-08-07", llm_judge_reasoning_effort="medium")
    larger_output = MetricConfig(
        llm_judge_model="gpt-5-nano-2025-08-07",
        llm_judge_reasoning_effort="minimal",
        llm_judge_max_output_tokens=4800,
    )

    assert mqm_cache_namespace(base, prompt_hash, schema_hash) != mqm_cache_namespace(
        stronger, prompt_hash, schema_hash
    )
    assert mqm_cache_namespace(base, prompt_hash, schema_hash) != mqm_cache_namespace(
        larger_output, prompt_hash, schema_hash
    )


def test_mqm_default_model_is_calibrated_model() -> None:
    config = MetricConfig()

    assert config.llm_judge_model == "gpt-5.6-luna"
    assert config.llm_judge_reasoning_effort == "none"
    assert config.llm_judge_max_output_tokens == 2400


def test_llm_judge_model_does_not_fall_back_to_translation_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_JUDGE_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "translation-only-model")

    assert llm_judge_model_from_env() == "gpt-5.6-luna"

    monkeypatch.setenv("LLM_JUDGE_MODEL", "explicit-judge-model")
    assert llm_judge_model_from_env() == "explicit-judge-model"


def test_openai_mqm_judge_runs_cache_misses_with_bounded_concurrency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = markdown_doc((FIXTURES / "source.md").read_text(encoding="utf-8"))
    target = markdown_doc((FIXTURES / "target_good.md").read_text(encoding="utf-8"))
    alignment = align_segments(source, target)[:4]
    active = 0
    peak_active = 0
    lock = threading.Lock()

    class FakeResponses:
        def create(self, **kwargs: object) -> object:
            nonlocal active, peak_active
            with lock:
                active += 1
                peak_active = max(peak_active, active)
            try:
                time.sleep(0.02)
                task = json.loads(str(kwargs["input"]))
                output = {
                    "segment_id": task["segment_id"],
                    "adequacy_score": 1.0,
                    "fluency_score": 1.0,
                    "technical_score": 1.0,
                    "terminology_review": no_unregistered_terms(),
                    "errors": [],
                }
                return types.SimpleNamespace(status="completed", output_text=json.dumps(output))
            finally:
                with lock:
                    active -= 1

    class FakeOpenAI:
        def __init__(self, **_: object) -> None:
            self.responses = FakeResponses()

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FakeOpenAI))
    monkeypatch.setenv("HF_WORKFLOW_TEST_OPENAI_KEY", "test-key")
    warnings: list[str] = []
    config = MetricConfig(
        metric_cache_path=tmp_path / "metric-cache.json",
        llm_judge_provider="openai",
        llm_judge_api_key_env="HF_WORKFLOW_TEST_OPENAI_KEY",
        llm_judge_max_concurrency=2,
    )

    results, cache_hits, cache_misses, incomplete_ids = run_openai_mqm_judge(
        alignment,
        config,
        warnings,
    )

    assert peak_active == 2
    assert [result["segment_id"] for result in results] == [item["target_id"] for item in alignment]
    assert cache_hits == 0
    assert cache_misses == len(alignment)
    assert incomplete_ids == []
    assert warnings == []


def test_openai_mqm_judge_quarantines_and_reuses_contract_invalid_responses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = markdown_doc((FIXTURES / "source.md").read_text(encoding="utf-8"))
    target = markdown_doc((FIXTURES / "target_good.md").read_text(encoding="utf-8"))
    alignment = align_segments(source, target)[:1]
    calls = 0

    class FakeResponses:
        def create(self, **kwargs: object) -> object:
            nonlocal calls
            calls += 1
            task = json.loads(str(kwargs["input"]))
            output = {
                "segment_id": task["segment_id"],
                "adequacy_score": 1.0,
                "fluency_score": 1.0,
                "technical_score": 1.0,
                "terminology_review": {"status": "pass", "unregistered_terms": []},
                "errors": [],
            }
            return types.SimpleNamespace(status="completed", output_text=json.dumps(output))

    class FakeOpenAI:
        def __init__(self, **_: object) -> None:
            self.responses = FakeResponses()

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FakeOpenAI))
    monkeypatch.setenv("HF_WORKFLOW_TEST_OPENAI_KEY", "test-key")
    config = MetricConfig(
        metric_cache_path=tmp_path / "metric-cache.json",
        llm_judge_provider="openai",
        llm_judge_api_key_env="HF_WORKFLOW_TEST_OPENAI_KEY",
    )

    first_warnings: list[str] = []
    first = run_openai_mqm_judge(alignment, config, first_warnings)
    second_warnings: list[str] = []
    second = run_openai_mqm_judge(alignment, config, second_warnings)

    target_id = str(alignment[0]["target_id"])
    assert first[:3] == ([], 0, 1)
    assert first[3] == [target_id]
    assert second[:3] == ([], 1, 0)
    assert second[3] == [target_id]
    assert calls == 1
    assert any("empty terminology review" in warning for warning in second_warnings)
    assert any("quarantined" in warning for warning in second_warnings)


def test_scoring_deduplicates_deterministic_issue_already_supported_by_mqm_span() -> None:
    mqm = Issue(
        id="QL-001",
        category="accuracy",
        severity="major",
        message="MQM judge reported accuracy issue.",
        segment_id="p_002",
        source_span="This approach may improve throughput by up to 30%.",
        guide_rule="modal_strength",
    )
    deterministic_duplicate = Issue(
        id="QL-002",
        category="accuracy",
        severity="major",
        message="Modal or certainty strength may have changed.",
        segment_id="p_002",
        source_span="may",
        guide_rule="modal_strength",
    )
    independent = Issue(
        id="QL-003",
        category="style_locale",
        severity="major",
        message="Translation appears stronger or more promotional than the source.",
        segment_id="p_002",
        source_span="may improve",
        guide_rule="overstatement",
    )

    effective = deduplicate_detector_issues([mqm, deterministic_duplicate, independent])

    assert effective == [mqm, independent]


def test_scoring_keeps_higher_severity_deterministic_duplicate() -> None:
    mqm_minor = Issue(
        id="QL-001",
        category="accuracy",
        severity="minor",
        message="MQM judge reported accuracy issue.",
        segment_id="p_002",
        source_span="This approach may improve throughput.",
        guide_rule="modal_strength",
    )
    deterministic_major = Issue(
        id="QL-002",
        category="accuracy",
        severity="major",
        message="Modal or certainty strength may have changed.",
        segment_id="p_002",
        source_span="may",
        guide_rule="modal_strength",
    )

    assert deduplicate_detector_issues([mqm_minor, deterministic_major]) == [deterministic_major]


def test_mqm_judge_rejects_result_without_segment_id() -> None:
    warnings: list[str] = []

    result = normalize_mqm_result(
        {
            "adequacy_score": 1.0,
            "fluency_score": 1.0,
            "technical_score": 1.0,
            "errors": [],
        },
        "p_001",
        warnings,
    )

    assert result is None
    assert any("missing segment_id" in warning for warning in warnings)


def test_report_records_manifest_target_commit_sha(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")
    text = manifest.read_text(encoding="utf-8").replace(
        "translation:\n",
        "translation:\n  commit_sha: evaluated123\n",
    )
    manifest.write_text(text, encoding="utf-8")

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md")

    assert report["metadata"]["target_commit_sha"] == "evaluated123"


def test_openai_mqm_judge_skips_without_api_key(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")
    config = MetricConfig(
        qe_metric="off",
        enable_embedding_similarity=False,
        llm_judge_provider="openai",
        llm_judge_api_key_env="HF_WORKFLOW_TEST_MISSING_OPENAI_KEY",
        llm_judge_max_segments=1,
    )

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md", metric_config=config)

    assert report["status"] == "review_required"
    assert report["mqm_judge"]["enabled"] is True
    assert report["mqm_judge"]["provider"] == "openai"
    assert report["mqm_judge"]["reasoning_effort"] == "none"
    assert report["mqm_judge"]["segment_count"] == 0
    assert any("HF_WORKFLOW_TEST_MISSING_OPENAI_KEY" in warning for warning in report["mqm_judge"]["warnings"])


def test_openai_mqm_task_requests_json_object() -> None:
    task = openai_mqm_task(
        {
            "target_id": "p_001",
            "source_text": "The model can run locally.",
            "target_text": "모델은 로컬에서 실행할 수 있습니다.",
        }
    )

    assert "JSON object" in task
    assert "output_contract" in task
    assert "terminology_review" in task


def test_mqm_prompt_embeds_translation_guide_digest() -> None:
    prompt = load_mqm_prompt(DEFAULT_MQM_PROMPT_PATH, DEFAULT_STYLE_GUIDE_PATH)
    digest, digest_hash = style_guide_digest(DEFAULT_STYLE_GUIDE_PATH)

    assert "Embedded Korean Translation Guide Digest" in prompt
    assert digest_hash in prompt
    assert "의미·조건·확신의 강도" in prompt
    assert "Hugging Face Space" in prompt
    assert "copied verbatim" in prompt
    assert "Registered Project Glossary" in prompt
    assert "model card\t모델 카드\trequired" in prompt
    assert "terminology_review.unregistered_terms" in prompt
    assert "Return strict JSON only" in prompt
    assert digest


def test_openai_mqm_judge_reuses_cached_segments_without_api_key(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")
    cache_path = tmp_path / "metric-cache.json"
    source = markdown_doc((FIXTURES / "source.md").read_text(encoding="utf-8"))
    target = markdown_doc((FIXTURES / "target_good.md").read_text(encoding="utf-8"))
    first_alignment = align_segments(source, target)[0]
    prompt_hash = hashlib.sha256(load_mqm_prompt(DEFAULT_MQM_PROMPT_PATH, DEFAULT_STYLE_GUIDE_PATH).encode("utf-8")).hexdigest()
    config = MetricConfig(
        qe_metric="off",
        enable_embedding_similarity=False,
        metric_cache_path=cache_path,
        llm_judge_provider="openai",
        llm_judge_api_key_env="HF_WORKFLOW_TEST_MISSING_OPENAI_KEY",
        llm_judge_max_segments=1,
    )
    schema_hash = hashlib.sha256(DEFAULT_MQM_SCHEMA_PATH.read_bytes()).hexdigest()
    cache_key = metric_cache_key(
        mqm_cache_namespace(config, prompt_hash, schema_hash),
        str(first_alignment["source_hash"]),
        str(first_alignment["target_hash"]),
    )
    cache_path.write_text(
        json.dumps(
            {
                cache_key: {
                    "segment_id": first_alignment["target_id"],
                    "adequacy_score": 1.0,
                    "fluency_score": 1.0,
                    "technical_score": 1.0,
                    "terminology_review": no_unregistered_terms(),
                    "errors": [],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "source.md", metric_config=config)

    assert report["status"] == "review_required"
    assert report["mqm_judge"]["segment_count"] == 1
    assert report["mqm_judge"]["cache_hits"] == 1
    assert report["mqm_judge"]["cache_misses"] == 0
    assert report["mqm_judge"]["style_guide_hash"] == style_guide_digest(DEFAULT_STYLE_GUIDE_PATH)[1]
    assert any("MQM segment coverage is invalid" in warning for warning in report["mqm_judge"]["warnings"])


def test_cli_writes_mqm_judge_outputs(tmp_path: Path) -> None:
    manifest = manifest_for(tmp_path, "target_good.md")
    fixture = write_mqm_fixture(tmp_path)
    output_json = tmp_path / "quality-report.json"
    output_md = tmp_path / "quality-report.md"
    output_mqm = tmp_path / "mqm-judge.jsonl"

    exit_code = main(
        [
            "--manifest",
            str(manifest),
            "--target-root",
            str(FIXTURES),
            "--source",
            str(FIXTURES / "source.md"),
            "--output-md",
            str(output_md),
            "--output-json",
            str(output_json),
            "--output-mqm-judge-jsonl",
            str(output_mqm),
            "--qe-metric",
            "off",
            "--disable-embedding-similarity",
            "--llm-judge-provider",
            "fixture",
            "--llm-judge-fixture",
            str(fixture),
            "--llm-judge-max-segments",
            "3",
        ]
    )

    assert exit_code == 0
    assert "## MQM Judge" in output_md.read_text(encoding="utf-8")
    assert output_mqm.read_text(encoding="utf-8").strip()
    loaded = json.loads(output_json.read_text(encoding="utf-8"))
    assert loaded["mqm_judge"]["segment_count"] == 1


def style_manifest_for(tmp_path: Path, target_name: str) -> Path:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        f"""version: 1
source:
  url: https://huggingface.co/blog/style-guide
  title: A simple guide to fine-tuning
translation:
  file_path: {target_name}
handoff:
  quality:
    enabled: true
    checks:
      - style_guide
""",
        encoding="utf-8",
    )
    return manifest


def test_style_guide_good_translation_requires_semantic_review(tmp_path: Path) -> None:
    manifest = style_manifest_for(tmp_path, "style_target_good.md")

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "style_source.md")

    assert report["status"] == "review_required"
    assert report["style_guide"]["enabled"] is True
    assert report["style_guide"]["issue_count"] == 0
    assert report["dimension_scores"]["style_locale"] == 100.0
    assert report["metadata"]["style_guide_path"].endswith("hf-blog-ko-translation-guide.md")
    assert report["metadata"]["style_policy_version"] == 1


def test_style_guide_bad_translation_reports_guide_rules(tmp_path: Path) -> None:
    manifest = style_manifest_for(tmp_path, "style_target_bad.md")

    report = build_report(manifest, FIXTURES, source_path=FIXTURES / "style_source.md")

    assert report["status"] == "review_required"
    assert report["style_guide"]["issue_count"] >= 8
    assert report["dimension_scores"]["style_locale"] < 100.0
    rules = {issue["guide_rule"] for issue in report["issues"] if issue["guide_rule"]}
    assert {
        "modal_strength",
        "overstatement",
        "translationese",
        "emoji_delta",
        "list_consistency",
        "title_quality",
        "alt_text_caption",
        "link_text_translation",
        "first_mention_bilingual",
        "information_addition",
    }.issubset(rules)
    for issue in report["issues"]:
        if issue["guide_rule"]:
            assert issue["guide_section"]


def test_style_guide_can_be_disabled(tmp_path: Path) -> None:
    manifest = style_manifest_for(tmp_path, "style_target_bad.md")

    report = build_report(
        manifest,
        FIXTURES,
        source_path=FIXTURES / "style_source.md",
        metric_config=MetricConfig(enable_style_guide=False),
    )

    assert report["style_guide"]["enabled"] is False
    assert all(not issue["guide_rule"] for issue in report["issues"])


def test_cli_writes_style_guide_section(tmp_path: Path) -> None:
    manifest = style_manifest_for(tmp_path, "style_target_bad.md")
    output_md = tmp_path / "quality-report.md"
    output_json = tmp_path / "quality-report.json"
    output_pr_comment = tmp_path / "pr-comment.md"

    exit_code = main(
        [
            "--manifest",
            str(manifest),
            "--target-root",
            str(FIXTURES),
            "--source",
            str(FIXTURES / "style_source.md"),
            "--output-md",
            str(output_md),
            "--output-json",
            str(output_json),
            "--output-pr-comment",
            str(output_pr_comment),
        ]
    )

    assert exit_code == 0
    markdown = output_md.read_text(encoding="utf-8")
    assert "## Style Guide" in markdown
    assert "## Style Guide Findings" in markdown
    loaded = json.loads(output_json.read_text(encoding="utf-8"))
    assert loaded["style_guide"]["issue_count"] >= 8
    pr_comment = output_pr_comment.read_text(encoding="utf-8")
    assert "Top Style Guide Findings" in pr_comment
    assert "modal_strength" in pr_comment
