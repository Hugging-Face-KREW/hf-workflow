"""Metadata write-back E2E tests.

The generator is intentionally not implemented yet. These tests cover the
deterministic part we can safely verify now: applying an approved metadata plan
to a post and recording the same plan in the workflow manifest.
"""
import json

import yaml

from metadata import MetadataPlan, apply, build_plan, hreflang_entries
from seo_eval import evaluate_path


def test_apply_metadata_plan_then_re_evaluate(tmp_path, fixtures_dir):
    post = tmp_path / "post.md"
    post.write_text(
        (fixtures_dir / "curated" / "realistic-positive-no-image.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "source": {"url": "https://huggingface.co/blog/example"},
                "translation": {"file_path": "post.md", "locale": "ko"},
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    plan = MetadataPlan(
        title="HFKREW 번역 글의 게시 전 SEO 리뷰 체크리스트",
        description=(
            "HFKREW 번역 글을 게시하기 전에 제목, 도입부, 링크, 메타데이터 정책을 점검하는 실무 체크리스트를 정리하고, 자동 검사와 사람 리뷰가 확인해야 할 구조 문제, 의미 정합성 기준, PR 코멘트 작성 방식, 수정 우선순위와 승인 기준을 실제 실무 중심으로 설명합니다."
        ),
        categories=["SEO", "Community"],
        image="/assets/images/seo-review/checklist.png",
        canonical="https://hugging-face-krew.github.io/seo-review-checklist/",
        hreflang={
            "ko": "https://hugging-face-krew.github.io/seo-review-checklist/",
            "en": "https://huggingface.co/blog/example",
        },
    )

    apply(plan, post, manifest)

    result = evaluate_path(post)
    assert result["gate"]["status"] == "PASS"
    assert result["frontmatter_advisory"]["passed"] is True
    assert result["signals"]["semantic_review"]["canonical"] == plan.canonical
    assert result["signals"]["semantic_review"]["title_text"] == plan.title
    assert result["signals"]["semantic_review"]["description_text"] == plan.description

    updated_manifest = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    candidate = updated_manifest["handoff"]["seo"]["metadata_candidate"]
    assert candidate["canonical"] == plan.canonical
    assert candidate["hreflang"]["en"] == "https://huggingface.co/blog/example"


def test_metadata_plan_to_dict_is_json_serializable():
    plan = MetadataPlan(
        title="제목",
        description="설명",
        categories=["SEO"],
        hreflang={"ko": "https://example.test/ko"},
    )

    assert json.loads(json.dumps(plan.to_dict(), ensure_ascii=False))["title"] == "제목"


def test_build_plan_returns_partial_without_translation_url_policy(fixtures_dir):
    content = (fixtures_dir / "curated" / "realistic-positive-no-image.md").read_text(
        encoding="utf-8"
    )
    frontmatter, body = __import__("seo_eval").parse_inputs(content)

    result = build_plan(body, frontmatter, {"handoff": {"seo": {}}})

    assert result.status == "PARTIAL"
    assert result.candidate.title
    assert result.candidate.description
    assert result.candidate.canonical == ""
    assert set(result.needs_policy_decision) == {
        "target_url",
        "source_url",
        "canonical_policy",
        "translation_indexing",
        "target_locale",
        "source_locale",
    }


def test_build_plan_applies_explicit_self_canonical_policy(fixtures_dir):
    content = (fixtures_dir / "curated" / "realistic-positive-no-image.md").read_text(
        encoding="utf-8"
    )
    frontmatter, body = __import__("seo_eval").parse_inputs(content)
    manifest = {
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
    }

    result = build_plan(body, frontmatter, manifest)

    assert result.status == "READY"
    assert result.needs_policy_decision == []
    assert result.candidate.canonical == "https://hugging-face-krew.github.io/example-ko/"
    assert result.candidate.hreflang == {
        "ko": "https://hugging-face-krew.github.io/example-ko/",
        "en": "https://huggingface.co/blog/example",
    }
    assert hreflang_entries(result.candidate) == [
        {"locale": "en", "url": "https://huggingface.co/blog/example"},
        {"locale": "ko", "url": "https://hugging-face-krew.github.io/example-ko/"},
    ]


def test_build_plan_uses_injected_generator_without_guessing_url_policy(fixtures_dir):
    content = (fixtures_dir / "mutated" / "missing-description.md").read_text(
        encoding="utf-8"
    )
    frontmatter, body = __import__("seo_eval").parse_inputs(content)

    def generator(evidence):
        assert evidence["frontmatter"]["title"]
        return {
            "candidate": {
                "title": "생성된 SEO 제목",
                "description": "생성된 SEO 설명입니다.",
            }
        }

    result = build_plan(body, frontmatter, {"handoff": {"seo": {}}}, generator=generator)

    assert result.status == "PARTIAL"
    assert result.candidate.title == "생성된 SEO 제목"
    assert result.candidate.description == "생성된 SEO 설명입니다."
    assert result.candidate.canonical == ""
