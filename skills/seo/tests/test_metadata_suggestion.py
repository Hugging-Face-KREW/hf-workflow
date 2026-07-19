import json
from pathlib import Path

import metadata_suggestion
from metadata_suggestion import build_suggestion, main


POST = """---
title: 검색 임베딩 벤치마크 입문
categories:
  - Translation
image: /assets/images/sample/exists.png
---
# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델의 실제 검색 정확도를 평가하는 방법입니다.
공개 데이터셋과 비공개 데이터셋을 함께 사용하면 일반화 성능을 더 공정하게 확인할 수 있습니다.
"""


def test_metadata_suggestion_skips_when_seo_gate_fails(tmp_path: Path) -> None:
    eval_json = tmp_path / "seo-eval.json"
    eval_json.write_text(json.dumps({
        "gate": {"passed": False, "status": "BLOCKED"},
        "input": {"source_url": "", "primary_keyword": ""},
    }))

    suggestion = build_suggestion(
        file_path="_posts/post.md",
        target_root=tmp_path,
        eval_json=eval_json,
    )

    assert suggestion["status"] == "SKIPPED"
    assert suggestion["candidate"] == {}
    assert suggestion["apply"]["allowed"] is False
    assert "skill" not in suggestion
    assert "conclusion" not in suggestion


def test_metadata_suggestion_generates_candidate_without_writing_post(
    tmp_path: Path,
) -> None:
    post = tmp_path / "_posts" / "post.md"
    post.parent.mkdir()
    post.write_text(POST, encoding="utf-8")
    original = post.read_text(encoding="utf-8")
    eval_json = tmp_path / "seo-eval.json"
    eval_json.write_text(json.dumps({
        "gate": {"passed": True, "status": "PASS"},
        "input": {
            "source_url": "https://huggingface.co/blog/rteb",
            "primary_keyword": "검색 임베딩 벤치마크",
        },
    }))

    suggestion = build_suggestion(
        file_path="_posts/post.md",
        target_root=tmp_path,
        eval_json=eval_json,
    )

    assert suggestion["kind"] == "seo_metadata_suggestion"
    assert suggestion["status"] == "PARTIAL"
    assert suggestion["candidate"]["title"] == "검색 임베딩 벤치마크 입문"
    assert suggestion["candidate"]["description"]
    assert suggestion["apply"] == {
        "allowed": False,
        "mode": "frontmatter_only",
        "requires_human": True,
    }
    assert "skill" not in suggestion
    assert "conclusion" not in suggestion
    assert post.read_text(encoding="utf-8") == original


def test_metadata_suggestion_uses_openai_generator_when_required(
    tmp_path: Path,
    monkeypatch,
) -> None:
    post = tmp_path / "_posts" / "post.md"
    post.parent.mkdir()
    post.write_text(POST, encoding="utf-8")
    eval_json = tmp_path / "seo-eval.json"
    eval_json.write_text(json.dumps({
        "gate": {"passed": True, "status": "PASS"},
        "input": {
            "source_url": "https://huggingface.co/blog/rteb",
            "primary_keyword": "검색 임베딩 벤치마크",
        },
    }))

    def fake_generator_factory(**kwargs):
        def fake_generator(evidence):
            return {
                "candidate": {
                    "title": "OpenAI 생성 제목",
                    "description": "OpenAI 생성 설명입니다.",
                    "categories": ["Translation"],
                    "image": "",
                },
                "warnings": [],
            }
        return fake_generator

    monkeypatch.setattr(
        metadata_suggestion,
        "make_openai_metadata_generator",
        fake_generator_factory,
    )

    suggestion = build_suggestion(
        file_path="_posts/post.md",
        target_root=tmp_path,
        eval_json=eval_json,
        openai_required=True,
        openai_model="gpt-test",
    )

    assert suggestion["status"] == "PARTIAL"
    assert suggestion["candidate"]["title"] == "OpenAI 생성 제목"
    assert suggestion["candidate"]["description"] == "OpenAI 생성 설명입니다."


def test_metadata_suggestion_marks_openai_failure_as_error(tmp_path: Path) -> None:
    post = tmp_path / "_posts" / "post.md"
    post.parent.mkdir()
    post.write_text(POST, encoding="utf-8")
    eval_json = tmp_path / "seo-eval.json"
    eval_json.write_text(json.dumps({
        "gate": {"passed": True, "status": "PASS"},
        "input": {},
    }))

    suggestion = build_suggestion(
        file_path="_posts/post.md",
        target_root=tmp_path,
        eval_json=eval_json,
        openai_required=True,
        openai_model="gpt-test",
    )

    assert suggestion["status"] == "ERROR"
    assert any(w.startswith("openai_unavailable:") for w in suggestion["warnings"])


def test_metadata_suggestion_cli_writes_json(tmp_path: Path) -> None:
    post = tmp_path / "_posts" / "post.md"
    post.parent.mkdir()
    post.write_text(POST, encoding="utf-8")
    eval_json = tmp_path / "seo-eval.json"
    output = tmp_path / "metadata-suggestion.json"
    eval_json.write_text(json.dumps({
        "gate": {"passed": False, "status": "FAIL"},
        "input": {},
    }))

    assert main([
        "--file", "_posts/post.md",
        "--target-root", str(tmp_path),
        "--eval-json", str(eval_json),
        "--output", str(output),
    ]) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "SKIPPED"
    assert payload["kind"] == "seo_metadata_suggestion"


def test_metadata_suggestion_marks_ready_candidate_as_applyable(tmp_path: Path) -> None:
    post = tmp_path / "_posts" / "post.md"
    post.parent.mkdir()
    post.write_text(POST, encoding="utf-8")
    manifest = tmp_path / "manifest.yml"
    manifest.write_text(
        """
handoff:
  seo:
    metadata_policy:
      target_url: https://hugging-face-krew.github.io/sample/
      source_url: https://huggingface.co/blog/sample
      canonical_policy: self
      translation_indexing: independent
      target_locale: ko
      source_locale: en
""",
        encoding="utf-8",
    )
    eval_json = tmp_path / "seo-eval.json"
    eval_json.write_text(json.dumps({
        "gate": {"passed": True, "status": "PASS"},
        "input": {
            "source_url": "https://huggingface.co/blog/sample",
            "primary_keyword": "검색 임베딩 벤치마크",
        },
    }))

    suggestion = build_suggestion(
        file_path="_posts/post.md",
        target_root=tmp_path,
        eval_json=eval_json,
        manifest_path=manifest,
    )

    assert suggestion["status"] == "READY"
    assert suggestion["apply"]["allowed"] is True
    assert suggestion["apply"]["requires_human"] is False
    assert suggestion["apply"]["target_files"] == [
        {
            "path": "_posts/post.md",
            "operation": "update_frontmatter",
            "fields": ["title", "description", "categories", "image", "canonical", "hreflang"],
        }
    ]
