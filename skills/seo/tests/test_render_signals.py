"""Rendered HTML-ish signal checks.

These tests cover the central HFKREW ambiguity: raw markdown may have no body
H1 because the Jekyll layout renders frontmatter `title` as the page H1.
"""
from pathlib import Path

from render_signals import extract_render_signals


def test_layout_title_can_supply_effective_h1(fixtures_dir):
    content = (fixtures_dir / "mutated" / "layout-title-no-body-h1.md").read_text(encoding="utf-8")
    signals = extract_render_signals(content)

    assert signals["body_h1_count"] == 0
    assert signals["layout_title_used_as_h1"] is True
    assert signals["effective_h1_count"] == 1
    assert signals["effective_h1"] == ["검색 임베딩 벤치마크 입문"]


def test_missing_title_and_body_h1_has_no_effective_h1(fixtures_dir):
    content = (fixtures_dir / "mutated" / "missing-h1-no-title.md").read_text(encoding="utf-8")
    signals = extract_render_signals(content)

    assert signals["body_h1_count"] == 0
    assert signals["layout_title_used_as_h1"] is False
    assert signals["effective_h1_count"] == 0


def test_real_positive_candidate_has_renderable_h1(real_dir):
    content = (real_dir / "2025-10-12-vlm-explained-ko.md").read_text(encoding="utf-8")
    signals = extract_render_signals(content)

    assert signals["layout_title_used_as_h1"] is True
    assert signals["effective_h1_count"] >= 1
    assert signals["effective_h1"][0]


def test_body_h1_adds_to_layout_h1(fixtures_dir):
    content = (fixtures_dir / "mutated" / "multiple-h1.md").read_text(encoding="utf-8")
    signals = extract_render_signals(content)

    assert signals["layout_title_used_as_h1"] is True
    assert signals["body_h1_count"] == 2
    assert signals["effective_h1_count"] == 3
