"""Functional tests for the keyword checker (D5 / D10), Korean-particle aware."""
from checkers import check_keywords


def _by_name(result):
    return {c["name"]: c for c in result["checks"]}


def test_empty_keyword_is_noninvasive():
    # No manifest keyword -> skip with an info note, never a hard failure.
    r = check_keywords("# 제목\n본문", primary_keyword="")
    assert r["passed"]
    assert _by_name(r)["primary_keyword"]["severity"] == "info"


def test_primary_keyword_in_h1_and_opening_passes():
    body = "# 모델 최적화 기법\n\n모델 최적화 기법은 성능을 높입니다."
    assert check_keywords(body, primary_keyword="모델 최적화")["passed"]


def test_primary_keyword_particle_tolerant():
    # '모델의' should still match the keyword '모델'.
    body = "# 모델 소개\n\n모델의 구조를 설명합니다."
    assert _by_name(check_keywords(body, primary_keyword="모델"))["primary_keyword"]["passed"]


def test_primary_keyword_missing_fails():
    body = "# 다른 제목\n\n관련 없는 내용입니다."
    assert not check_keywords(body, primary_keyword="임베딩 벤치마크")["passed"]


def test_secondary_keyword_coverage():
    body = "# 임베딩\n\n임베딩과 검색을 다룹니다."
    r = check_keywords(body, primary_keyword="임베딩",
                       secondary_keywords=["검색", "양자화"])
    assert _by_name(r)["secondary_keywords"]["value"] == ["검색"]
