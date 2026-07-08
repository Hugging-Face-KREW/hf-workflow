"""Internal sample coverage from real HFKREW posts and deliberate mutations.

These samples are not meant to make every current blog post pass. They document
how the evaluator behaves across realistic shapes: short guide posts, long
translation posts, image-heavy posts, missing metadata, and explicit blockers.
"""
from pathlib import Path

from seo_eval import evaluate_path


REAL_EXPECTATIONS = {
    "2024-09-16-how-to-contribute.md": "PASS",
    "2025-05-31-2025-PseudoCon-recap.md": "PASS",
    "2025-06-22-HuggingFace-Docs-Translation-Guide.md": "PASS",
    "2025-09-14-Implementing-MCP-Servers-in-Python.md": "PASS",
    "2025-09-14-python-tiny-agents-ko.md": "PASS",
    "2025-10-12-vlm-explained-ko.md": "PASS",
    "2025-10-20-2025-VLM.md": "NEEDS_CHANGES",
    "2025-11-17-hf_translation_hub_mcp_design_and_tooling.md": "PASS",
    "2025-12-01-rteb.md": "PASS",
    "2025-12-15-ai-agents-are-here.md": "NEEDS_CHANGES",
    "2025-12-22-smolvla.md": "PASS",
    "2025-12-28-translation-mcp-project-overview.md": "PASS",
    "2026-01-05-hf-translation-mcp-n8n.md": "PASS",
}


MUTATED_EXPECTATIONS = {
    "empty-body.md": "BLOCKED",
    "heading-skip.md": "NEEDS_CHANGES",
    "layout-title-no-body-h1.md": "PASS",
    "missing-description.md": "PASS",
    "missing-alt.md": "FAIL",
    "missing-h1-no-title.md": "PASS",
    "multiple-h1.md": "PASS",
    "no-citation.md": "PASS",
    "noindex.md": "BLOCKED",
    "short-opening.md": "PASS",
    "toc-before-opening.md": "PASS",
}


CURATED_EXPECTATIONS = {
    "hreflang-policy-positive.md": "PASS",
    "metadata-policy-positive.md": "PASS",
    "realistic-positive-no-image.md": "PASS",
    # Body gate can pass even when metadata meaning is wrong. This is an
    # intentional dataset case for the future policy/rubric layer.
    "semantic-negative-description.md": "PASS",
    "semantic-negative-title.md": "PASS",
}


def test_real_hfkrew_samples_cover_expected_statuses(fixtures_dir):
    real_dir = fixtures_dir / "real"
    seen_statuses = set()

    for filename, expected in REAL_EXPECTATIONS.items():
        result = evaluate_path(real_dir / filename)
        seen_statuses.add(result["gate"]["status"])
        assert result["gate"]["status"] == expected, filename

    assert {"PASS", "NEEDS_CHANGES"} <= seen_statuses


def test_mutated_samples_cover_expected_statuses(fixtures_dir):
    mutated_dir = fixtures_dir / "mutated"

    for filename, expected in MUTATED_EXPECTATIONS.items():
        result = evaluate_path(mutated_dir / filename)
        assert result["gate"]["status"] == expected, filename


def test_curated_samples_document_positive_and_semantic_gap(fixtures_dir):
    curated_dir = fixtures_dir / "curated"

    for filename, expected in CURATED_EXPECTATIONS.items():
        result = evaluate_path(curated_dir / filename)
        assert result["gate"]["status"] == expected, filename

    semantic_negative = evaluate_path(curated_dir / "semantic-negative-description.md")
    assert semantic_negative["frontmatter_advisory"]["passed"] is True
    assert semantic_negative["signals"]["frontmatter"]["description_present"] is True

    title_negative = evaluate_path(curated_dir / "semantic-negative-title.md")
    assert "GPU 클러스터" in title_negative["signals"]["frontmatter"]["title_text"]
    assert "HFKREW 번역 글" in title_negative["signals"]["opening"]["first_real_paragraph"]


def test_missing_description_is_metadata_advisory_not_body_gate(fixtures_dir):
    result = evaluate_path(fixtures_dir / "mutated" / "missing-description.md")
    failed_frontmatter = [
        c["name"] for c in result["frontmatter_advisory"]["checks"] if not c["passed"]
    ]

    assert result["gate"]["status"] == "PASS"
    assert "description" in failed_frontmatter


def test_broken_internal_link_blocks_when_target_root_is_available(tmp_path, fixtures_dir):
    target_root = tmp_path / "target"
    post_dir = target_root / "_posts"
    post_dir.mkdir(parents=True)
    post_path = post_dir / "2026-01-01-broken-internal-link.md"
    post_path.write_text(
        (fixtures_dir / "mutated" / "broken-internal-link.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    assets = target_root / "assets" / "images" / "rteb"
    assets.mkdir(parents=True)
    (assets / "thumbnail.png").write_bytes(b"placeholder")

    result = evaluate_path(Path("_posts/2026-01-01-broken-internal-link.md"), target_root=target_root)
    blocker_fails = [c["name"] for c in result["blockers"]["checks"] if not c["passed"]]

    assert result["gate"]["status"] == "BLOCKED"
    assert blocker_fails == ["internal_links_resolve"]


def test_broken_local_image_blocks_when_target_root_is_available(tmp_path, fixtures_dir):
    target_root = tmp_path / "target"
    post_dir = target_root / "_posts"
    post_dir.mkdir(parents=True)
    post_path = post_dir / "2026-01-01-broken-image-path.md"
    post_path.write_text(
        (fixtures_dir / "mutated" / "broken-image-path.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = evaluate_path(Path("_posts/2026-01-01-broken-image-path.md"), target_root=target_root)
    blocker_fails = [c["name"] for c in result["blockers"]["checks"] if not c["passed"]]

    assert result["gate"]["status"] == "BLOCKED"
    assert blocker_fails == ["local_images_resolve"]
