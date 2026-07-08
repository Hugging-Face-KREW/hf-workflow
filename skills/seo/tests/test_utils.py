"""Functional unit tests for utils — parsing and metric helpers."""
from utils import (
    parse_frontmatter,
    extract_links,
    extract_images,
    extract_headings,
    check_citations,
    count_chars,
    is_mostly_korean,
)


def test_parse_frontmatter_block_list():
    fm, body = parse_frontmatter(
        '---\ntitle: "T"\ncategories: [A, B]\n---\n# H\nbody\n')
    assert fm["title"] == "T"
    assert fm["categories"] == ["A", "B"]
    assert body.strip().startswith("# H")


def test_parse_frontmatter_absent():
    fm, body = parse_frontmatter("no frontmatter here")
    assert fm == {}
    assert body == "no frontmatter here"


def test_extract_links_excludes_images():
    # D4/D9 regression: an image embed must NOT be counted as a link.
    md = "see [src](https://a.com/x) and ![alt](https://img.com/y.png)"
    links = extract_links(md)
    assert links == ["https://a.com/x"]


def test_check_citations_ignores_image_urls():
    # Only the real external link counts, not the embedded image.
    md = "![alt](https://img.com/a.png) text [ref](https://src.com/p)"
    assert check_citations(md) == 1


def test_is_mostly_korean():
    assert is_mostly_korean("한국어가 대부분인 문장입니다 with few ascii")
    assert not is_mostly_korean("Mostly english text with 한 단어")


def test_count_chars_strips_whitespace():
    assert count_chars("  abc  ") == 3


def test_extract_headings_levels():
    h = extract_headings("# A\n## B\n### C\nnot heading")
    assert h == [(1, "A"), (2, "B"), (3, "C")]


def test_extract_images_markdown_and_html():
    body = ('![alt one](a.png)\n'
            '<img src="b.png" alt="alt two">\n'
            '<img alt="alt three" src="c.png">')
    srcs = {i["src"] for i in extract_images(body)}
    assert {"a.png", "b.png", "c.png"} <= srcs
