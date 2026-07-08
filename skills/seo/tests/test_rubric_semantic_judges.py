"""Schema-bound rubric judge integration tests.

These tests do not call an LLM. They inject fixed judge responses and verify
that the harness maps semantic judge outputs into gate behavior correctly.
"""
from seo_eval import evaluate_path


def test_semantic_metadata_judge_can_fail_required_gate(fixtures_dir):
    def judge(name, payload):
        if name == "alt_semantics":
            return {
                "status": "PASS",
                "alt_usefulness_score": 100,
                "problem_images": [],
                "reason": "no alt issue",
            }
        assert name == "semantic_metadata"
        assert "GPU 클러스터" in payload["frontmatter"]["title"]
        return {
            "status": "FAIL",
            "semantic_alignment_score": 20,
            "issues": ["title promises a GPU cluster guide but body is about SEO review"],
            "evidence": ["title", "opening"],
            "reason": "title/body semantic mismatch",
        }

    result = evaluate_path(
        fixtures_dir / "curated" / "semantic-negative-title.md",
        rubric_judge=judge,
    )

    assert result["rubric"]["available"] is True
    assert result["rubric"]["passed"] is False
    assert result["rubric"]["checks"][0]["name"] == "semantic_metadata"
    assert result["rubric"]["checks"][0]["severity"] == "required"
    assert result["gate"]["status"] == "NEEDS_CHANGES"


def test_alt_semantics_review_does_not_block_gate(fixtures_dir):
    def judge(name, payload):
        if name == "semantic_metadata":
            return {
                "status": "PASS",
                "semantic_alignment_score": 95,
                "issues": [],
                "evidence": [],
                "reason": "metadata is aligned",
            }
        assert name == "alt_semantics"
        assert payload["images"][0]["alt"] == "image-1"
        return {
            "status": "FAIL",
            "alt_usefulness_score": 10,
            "problem_images": [
                {
                    "src": payload["images"][0]["src"],
                    "alt": "image-1",
                    "reason": "generic image label",
                }
            ],
            "reason": "non-empty alt is not meaningful",
        }

    result = evaluate_path(
        fixtures_dir / "mutated" / "meaningless-alt.md",
        rubric_judge=judge,
    )

    assert result["rubric"]["available"] is True
    assert result["rubric"]["passed"] is True
    checks = {check["name"]: check for check in result["rubric"]["checks"]}
    assert checks["semantic_metadata"]["passed"] is True
    assert checks["alt_semantics"]["severity"] == "review"
    assert checks["alt_semantics"]["passed"] is False
    assert result["gate"]["status"] == "PASS"


def test_alt_semantics_can_be_promoted_to_required(fixtures_dir):
    def judge(name, payload):
        if name == "semantic_metadata":
            return {
                "status": "PASS",
                "semantic_alignment_score": 95,
                "issues": [],
                "evidence": [],
                "reason": "metadata is aligned",
            }
        return {
            "status": "FAIL",
            "alt_usefulness_score": 10,
            "problem_images": [
                {"src": "x", "alt": "image-1", "reason": "generic image label"}
            ],
            "reason": "non-empty alt is not meaningful",
        }

    content = (fixtures_dir / "mutated" / "meaningless-alt.md").read_text(encoding="utf-8")
    frontmatter, body = __import__("seo_eval").parse_inputs(content)
    inp = {
        "manifest": {
            "handoff": {
                "seo": {
                    "policy": {
                        "llm_judges": {
                            "alt_semantics": {"enabled": True, "severity": "required"}
                        }
                    }
                }
            }
        },
        "file_path": "meaningless-alt.md",
        "source_url": "",
        "primary_keyword": "",
        "secondary_keywords": [],
        "mode": "file",
        "target_root": None,
        "post_path": fixtures_dir / "mutated" / "meaningless-alt.md",
        "content": content,
        "frontmatter": frontmatter,
        "body": body,
    }

    result = __import__("seo_eval").evaluate(inp, rubric_judge=judge)

    checks = {check["name"]: check for check in result["rubric"]["checks"]}
    assert checks["alt_semantics"]["severity"] == "required"
    assert result["rubric"]["passed"] is False
    assert result["gate"]["status"] == "NEEDS_CHANGES"
