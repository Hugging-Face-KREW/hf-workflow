"""Functional tests for the content-structure checker (D1-D4, D8, D9, D11)."""
from checkers import check_content_structure


def _by_name(result):
    return {c["name"]: c for c in result["checks"]}


def test_h1_count_exactly_one():
    body = "# Only One\n## sub\ncontent"
    assert _by_name(check_content_structure(body, body))["h1_count"]["passed"]
    two = "# One\n# Two\ntext"
    c = _by_name(check_content_structure(two, two))["h1_count"]
    assert not c["passed"] and c["value"] == 2


def test_heading_hierarchy_skip_detected():
    body = "# H1\n### H3 skip"
    assert not _by_name(check_content_structure(body, body))["heading_hierarchy"]["passed"]


def test_opening_korean_uses_char_threshold():
    short = "# 제목\n\n짧은 한국어 도입부입니다."
    c = _by_name(check_content_structure(short, short))["opening_summary"]
    assert not c["passed"]
    long_ko = "# 제목\n\n" + ("한국어 도입부 문장입니다. " * 12)
    c2 = _by_name(check_content_structure(long_ko, long_ko))["opening_summary"]
    assert c2["passed"] and "chars" in c2["message"]


def test_opening_english_uses_word_threshold():
    body = "# Title\n\n" + ("word " * 60)
    c = _by_name(check_content_structure(body, body))["opening_summary"]
    assert c["passed"] and "words" in c["message"]


def test_citations_required_counts_external_link():
    body = "# T\n\nclaim [src](https://example.com/a) supports this."
    assert _by_name(check_content_structure(body, body))["citations"]["passed"]


def test_keyword_subheading_branch_d8():
    body = "# 모델 최적화\n\n도입 문단.\n\n## 모델 최적화 기법\n\n내용"
    without = _by_name(check_content_structure(body, body))["question_headings"]
    assert not without["passed"]  # no '?' and no keyword supplied
    withkw = _by_name(
        check_content_structure(body, body, primary_keyword="모델 최적화")
    )["question_headings"]
    assert withkw["passed"]
