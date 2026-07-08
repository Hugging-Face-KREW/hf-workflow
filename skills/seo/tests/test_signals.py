"""Raw signal collection tests."""
from pathlib import Path

from signals import collect_signals
from utils import parse_frontmatter


def _signals(path: Path, *, target_root=None, post_path=None):
    content = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)
    return collect_signals(content, body, frontmatter, target_root=target_root, post_path=post_path)


def test_signals_capture_layout_h1_ambiguity(fixtures_dir):
    sig = _signals(fixtures_dir / "mutated" / "layout-title-no-body-h1.md")

    assert sig["headings"]["markdown_h1_count"] == 0
    assert sig["headings"]["layout_title_used_as_h1"] is True
    assert sig["headings"]["rendered_effective_h1_count"] == 1


def test_signals_capture_semantic_negative_evidence(fixtures_dir):
    sig = _signals(fixtures_dir / "mutated" / "meaningless-alt.md")

    assert sig["images"]["total_count"] == 1
    assert sig["images"]["image_details"] == [
        {"src": "/assets/images/rteb/thumbnail.png", "alt": "image-1"}
    ]
    assert sig["images"]["empty_alt_count"] == 0
    assert sig["images"]["filename_like_alt_count"] == 0
    assert sig["frontmatter"]["description_present"] is True
    assert "검색 임베딩 벤치마크" in sig["frontmatter"]["title_text"]
    assert "검색 임베딩 벤치마크" in sig["frontmatter"]["description_text"]
    assert "검색 임베딩 벤치마크" in sig["opening"]["first_real_paragraph"]
    assert sig["semantic_review"]["title_text"] == sig["frontmatter"]["title_text"]
    assert sig["semantic_review"]["description_text"] == sig["frontmatter"]["description_text"]
    assert "pass/fail" in sig["semantic_review"]["review_instruction"]


def test_signals_package_title_body_mismatch_for_review(fixtures_dir):
    sig = _signals(fixtures_dir / "curated" / "semantic-negative-title.md")

    assert "GPU 클러스터" in sig["semantic_review"]["title_text"]
    assert "HFKREW 번역 글" in sig["semantic_review"]["opening_text"]
    assert any("HFKREW 번역 글" in h for h in sig["semantic_review"]["rendered_h1_texts"])


def test_signals_capture_missing_local_image(tmp_path, fixtures_dir):
    target_root = tmp_path / "repo"
    post_dir = target_root / "_posts"
    post_dir.mkdir(parents=True)
    post = post_dir / "2026-01-01-broken-image.md"
    post.write_text(
        (fixtures_dir / "mutated" / "broken-image-path.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    content = post.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)
    sig = collect_signals(
        content,
        body,
        frontmatter,
        target_root=target_root,
        post_path="_posts/2026-01-01-broken-image.md",
    )

    assert sig["images"]["missing_local_file_count"] == 1
    assert sig["images"]["missing_local_file_sources"] == ["/assets/images/rteb/missing-thumbnail.png"]
