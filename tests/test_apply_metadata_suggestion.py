from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hf_agent.apply_metadata_suggestion import apply_suggestion


POST = """---
title: Old title
categories:
  - Translation
---
# Old title

Body text.
"""


def test_apply_suggestion_skips_when_not_approved(tmp_path: Path) -> None:
    post = tmp_path / "_posts" / "post.md"
    post.parent.mkdir()
    post.write_text(POST, encoding="utf-8")
    suggestion = tmp_path / "metadata-suggestion.json"
    suggestion.write_text(
        json.dumps(
            {
                "kind": "seo_metadata_suggestion",
                "status": "PARTIAL",
                "file_path": "_posts/post.md",
                "candidate": {"description": "New description"},
                "apply": {"allowed": False, "requires_human": True},
                "needs_policy_decision": ["canonical_policy"],
            }
        ),
        encoding="utf-8",
    )

    result = apply_suggestion(target_root=tmp_path, suggestion_path=suggestion)

    assert result["status"] == "SKIPPED"
    assert result["changed"] is False
    assert post.read_text(encoding="utf-8") == POST


def test_apply_suggestion_updates_frontmatter_when_approved(tmp_path: Path) -> None:
    post = tmp_path / "_posts" / "post.md"
    post.parent.mkdir()
    post.write_text(POST, encoding="utf-8")
    suggestion = tmp_path / "metadata-suggestion.json"
    suggestion.write_text(
        json.dumps(
            {
                "kind": "seo_metadata_suggestion",
                "status": "READY",
                "file_path": "_posts/post.md",
                "candidate": {
                    "title": "New title",
                    "description": "New description",
                    "categories": ["Translation", "HuggingFace"],
                    "image": "/blog/assets/example/thumbnail.png",
                    "canonical": "https://hugging-face-krew.github.io/example/",
                    "hreflang": {
                        "ko": "https://hugging-face-krew.github.io/example/",
                        "en": "https://huggingface.co/blog/example",
                    },
                    "json_ld": {},
                },
                "apply": {
                    "allowed": True,
                    "requires_human": False,
                    "mode": "frontmatter_only",
                },
                "needs_policy_decision": [],
            }
        ),
        encoding="utf-8",
    )

    result = apply_suggestion(target_root=tmp_path, suggestion_path=suggestion)

    updated = post.read_text(encoding="utf-8")
    assert result["status"] == "APPLIED"
    assert result["changed"] is True
    assert "description: New description" in updated
    assert "canonical: https://hugging-face-krew.github.io/example/" in updated
    assert "hreflang:" in updated
