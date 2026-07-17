from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.refresh_translation_info import (  # noqa: E402
    list_open_translation_prs,
    normalize_thumbnail_url,
    parse_pr_numbers,
    refresh_translation_markdown,
    translation_files,
)


def test_parse_pr_numbers() -> None:
    assert parse_pr_numbers("154, 163,167") == {154, 163, 167}


def test_parse_pr_numbers_rejects_invalid_values() -> None:
    import pytest

    with pytest.raises(ValueError, match="abc"):
        parse_pr_numbers("154,abc")


def test_normalize_thumbnail_url() -> None:
    assert normalize_thumbnail_url("/blog/assets/example/thumbnail.png") == (
        "https://huggingface.co/blog/assets/example/thumbnail.png"
    )
    assert normalize_thumbnail_url('"/blog/assets/example.png"') == (
        "https://huggingface.co/blog/assets/example.png"
    )
    assert normalize_thumbnail_url("https://cdn.example.com/image.png") == (
        "https://cdn.example.com/image.png"
    )
    assert normalize_thumbnail_url("assets/example.png") == "assets/example.png"


def test_refresh_translation_markdown_preserves_translation_body() -> None:
    original = """---
layout: post
thumbnail: "/blog/assets/example/thumbnail.png"
source_url: "https://huggingface.co/blog/example"
---

> Source: https://huggingface.co/blog/example

* TOC

_이 글은 Hugging Face 블로그의 [Example](https://huggingface.co/blog/example)를 한국어로 번역한 글입니다._

---

# 사람이 수정한 번역

본문은 그대로 유지합니다.
"""

    refreshed = refresh_translation_markdown(original)

    assert "thumbnail: https://huggingface.co/blog/assets/example/thumbnail.png" in refreshed
    assert "> Source:" not in refreshed
    assert """_이 글은 Hugging Face 블로그의 [Example](https://huggingface.co/blog/example)를 한국어로 번역한 글입니다._

<!-- Source: https://huggingface.co/blog/example -->

---""" in refreshed
    assert "# 사람이 수정한 번역\n\n본문은 그대로 유지합니다." in refreshed


def test_refresh_translation_markdown_is_idempotent() -> None:
    markdown = """---
thumbnail: https://huggingface.co/blog/assets/example.png
---

<!-- Source: https://huggingface.co/blog/example -->
"""

    assert refresh_translation_markdown(markdown) == markdown


def test_translation_files_only_returns_post_markdown() -> None:
    pull = {
        "files": [
            {"path": "_posts/2026-07-01-example.md"},
            {"path": "assets/example.png"},
            {"path": "_posts/notes.txt"},
        ]
    }

    assert translation_files(pull) == ["_posts/2026-07-01-example.md"]


def test_list_open_translation_prs_skips_forks_and_non_translation_branches(
    monkeypatch,
) -> None:
    payload = """[
      {"number": 1, "headRefName": "translate/one", "isCrossRepository": false},
      {"number": 2, "headRefName": "translate/fork", "isCrossRepository": true},
      {"number": 3, "headRefName": "fix/layout", "isCrossRepository": false}
    ]"""

    class Result:
        stdout = payload

    monkeypatch.setattr(
        "scripts.refresh_translation_info.run_cmd",
        lambda args: Result(),
    )

    assert [pull["number"] for pull in list_open_translation_prs("owner/repo")] == [1]
    assert [pull["number"] for pull in list_open_translation_prs("owner/repo", {1})] == [1]


def test_list_open_translation_prs_rejects_missing_requested_pr(monkeypatch) -> None:
    class Result:
        stdout = "[]"

    monkeypatch.setattr(
        "scripts.refresh_translation_info.run_cmd",
        lambda args: Result(),
    )

    import pytest

    with pytest.raises(RuntimeError, match=r"#163"):
        list_open_translation_prs("owner/repo", {163})
