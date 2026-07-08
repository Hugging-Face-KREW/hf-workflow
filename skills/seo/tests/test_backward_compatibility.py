"""Backward-compatibility checks for public SEO skill seams."""

from metadata import apply, build_plan
from rubric import PASS_MEAN, PASS_MIN, RUBRIC_ITEMS, RubricResult


def test_rubric_score_based_passed_contract_is_preserved():
    assert RUBRIC_ITEMS["R1"]
    assert PASS_MEAN == 4.0
    assert PASS_MIN == 3

    passing = RubricResult(
        available=True,
        scores={"R1": 4, "R2": 4, "R3": 5},
    )
    failing = RubricResult(
        available=True,
        scores={"R1": 5, "R2": 2, "R3": 5},
    )

    assert passing.passed is True
    assert failing.passed is False
    assert passing.to_dict()["scores"]["R3"] == 5


def test_build_plan_result_still_behaves_like_metadata_plan(tmp_path, fixtures_dir):
    source = fixtures_dir / "curated" / "realistic-positive-no-image.md"
    content = source.read_text(encoding="utf-8")
    frontmatter, body = __import__("seo_eval").parse_inputs(content)
    post = tmp_path / "post.md"
    post.write_text(content, encoding="utf-8")

    plan_like = build_plan(
        body,
        frontmatter,
        {
            "handoff": {
                "seo": {
                    "metadata_policy": {
                        "target_url": "https://hugging-face-krew.github.io/example-ko/",
                        "source_url": "https://huggingface.co/blog/example",
                        "canonical_policy": "self",
                        "translation_indexing": "independent",
                        "target_locale": "ko",
                        "source_locale": "en",
                    }
                }
            }
        },
    )

    assert plan_like.title == plan_like.candidate.title
    assert plan_like.description == plan_like.candidate.description

    apply(plan_like, post)

    updated_frontmatter, _ = __import__("seo_eval").parse_inputs(
        post.read_text(encoding="utf-8")
    )
    assert updated_frontmatter["title"] == plan_like.title
    assert updated_frontmatter["canonical"] == plan_like.canonical
