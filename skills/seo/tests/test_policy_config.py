from pathlib import Path

from seo_eval import evaluate_path


def test_manifest_policy_can_promote_review_signal_to_required(tmp_path):
    post = tmp_path / "post.md"
    post.write_text(
        "---\ntitle: x\n---\n"
        "# 제목\n\n"
        "짧은 도입부입니다.\n\n"
        "## 내용\n\n본문입니다.",
        encoding="utf-8",
    )

    result = evaluate_path(post)
    assert "opening_summary" not in {
        c["name"] for c in result["deterministic"]["required"]["checks"]
    }

    content = post.read_text(encoding="utf-8")
    frontmatter, body = __import__("seo_eval").parse_inputs(content)
    inp = {
        "manifest": {
            "handoff": {
                "seo": {
                    "policy": {
                        "severities": {
                            "opening_summary": "required",
                        }
                    }
                }
            }
        },
        "file_path": str(post.name),
        "source_url": "",
        "primary_keyword": "",
        "secondary_keywords": [],
        "mode": "file",
        "target_root": None,
        "post_path": post,
        "content": content,
        "frontmatter": frontmatter,
        "body": body,
    }
    result = __import__("seo_eval").evaluate(inp)
    required = {c["name"] for c in result["deterministic"]["required"]["checks"]}

    assert "opening_summary" in required
    assert result["gate"]["status"] == "NEEDS_CHANGES"


def test_manifest_policy_can_demote_image_alt_to_review(tmp_path):
    post = tmp_path / "post.md"
    post.write_text(
        "---\ntitle: x\n---\n"
        "# 제목\n\n"
        "검색 품질을 설명하는 충분한 도입부입니다. " * 10
        + "\n\n## 내용\n\n![](missing.png)",
        encoding="utf-8",
    )

    content = post.read_text(encoding="utf-8")
    frontmatter, body = __import__("seo_eval").parse_inputs(content)
    inp = {
        "manifest": {
            "handoff": {
                "seo": {
                    "policy": {
                        "severities": {
                            "alt_text_coverage": "review",
                            "descriptive_alt_text": "review",
                        }
                    }
                }
            }
        },
        "file_path": str(post.name),
        "source_url": "",
        "primary_keyword": "",
        "secondary_keywords": [],
        "mode": "file",
        "target_root": None,
        "post_path": post,
        "content": content,
        "frontmatter": frontmatter,
        "body": body,
    }
    result = __import__("seo_eval").evaluate(inp)

    assert result["gate"]["status"] == "PASS"
    advisory = {c["name"]: c for c in result["deterministic"]["advisory"]["checks"]}
    assert advisory["alt_text_coverage"]["severity"] == "review"
