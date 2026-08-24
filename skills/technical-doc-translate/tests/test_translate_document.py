from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "translate_document.py"
SPEC = importlib.util.spec_from_file_location("technical_doc_translate", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


SOURCE = """---
title: Installation
---

<!--Copyright 2026 The HuggingFace Team. -->

# Installation

Read the [installation guide](https://example.com/install) and run `pip install transformers`.
See the [configuration reference][config-ref] and note [^cache].

[config-ref]: https://example.com/config

<Tip warning={true}>

> [!WARNING]
> Keep the configuration stable.

Set `HF_HOME` before running the command with `--cache-dir`.

</Tip>

```bash
python -m pip install transformers
```
"""


def fake_model_call(prompt: str) -> str:
    payload = json.loads(prompt.split("[Input blocks]\n", 1)[1])
    rows = []
    for item in payload:
        translated = (
            item["markdown"]
            .replace("Installation", "설치")
            .replace("Read the", "다음")
            .replace("and run", "를 읽고 실행하세요")
            .replace("Set", "설정하세요:")
            .replace("before running the command with", "명령 실행 전")
        )
        rows.append({"id": item["id"], "markdown": translated})
    return json.dumps(rows, ensure_ascii=False)


class ParseAndProtectionTests(unittest.TestCase):
    def test_transformers_components_and_comments_are_structural(self) -> None:
        blocks = MODULE.parse_blocks(SOURCE)
        kinds = [block.kind for block in blocks]
        self.assertIn("frontmatter", kinds)
        self.assertIn("comment", kinds)
        self.assertEqual(kinds.count("component"), 2)
        self.assertEqual(kinds.count("code"), 1)
        self.assertTrue(all(not block.translatable for block in blocks if block.kind in {"frontmatter", "comment", "component", "code"}))

    def test_link_label_remains_translatable_but_target_is_protected(self) -> None:
        text = "Read the [installation guide](https://example.com/install) and `pip install transformers`."
        protected, mapping = MODULE.protect_inline(text)
        self.assertIn("installation guide", protected)
        self.assertNotIn("https://example.com/install", protected)
        self.assertNotIn("pip install transformers", protected)
        self.assertTrue(all(token.startswith("⟦tdt0000-") for token in mapping))
        self.assertEqual(MODULE.restore_inline(protected, mapping), text)

    def test_reference_link_label_remains_translatable_but_identifier_is_protected(self) -> None:
        text = "Read the [configuration reference][config-ref] and note [^cache]."
        protected, mapping = MODULE.protect_inline(text)
        self.assertIn("configuration reference", protected)
        self.assertNotIn("[config-ref]", protected)
        self.assertNotIn("[^cache]", protected)
        self.assertEqual(MODULE.restore_inline(protected, mapping), text)

    def test_missing_placeholder_is_rejected(self) -> None:
        protected, mapping = MODULE.protect_inline("Use `Trainer`.")
        with self.assertRaisesRegex(ValueError, "Protected token mismatch"):
            MODULE.restore_inline(protected.replace(next(iter(mapping)), ""), mapping)

    def test_inline_html_comment_is_protected(self) -> None:
        text = "Keep <!-- do-not-translate --> stable."
        protected, mapping = MODULE.protect_inline(text)
        self.assertNotIn("do-not-translate", protected)
        self.assertEqual(MODULE.restore_inline(protected, mapping), text)

    def test_dirty_git_source_has_no_revision_claim(self) -> None:
        responses = [
            CompletedProcess(args=[], returncode=0, stdout="/repo\n", stderr=""),
            CompletedProcess(args=[], returncode=0, stdout=" M docs/source/en/example.md\n", stderr=""),
        ]
        with patch.object(MODULE.subprocess, "run", side_effect=responses):
            label, revision = MODULE.git_file_metadata(Path("/repo/docs/source/en/example.md"))
        self.assertEqual(label, "docs/source/en/example.md")
        self.assertEqual(revision, "")


class TranslationAndValidationTests(unittest.TestCase):
    def test_fake_translation_preserves_structure(self) -> None:
        blocks = MODULE.parse_blocks(SOURCE)
        translated = MODULE.translate_blocks(
            blocks,
            model_call=fake_model_call,
            rules="Translate to Korean and preserve protected tokens.",
            profile_rules="Preserve Transformers components.",
            batch_size=2,
        )
        self.assertIn("# 설치", translated)
        self.assertIn("<Tip warning={true}>", translated)
        self.assertIn("> [!WARNING]", translated)
        self.assertIn("`HF_HOME`", translated)
        self.assertIn("https://example.com/install", translated)
        self.assertIn("[config-ref]: https://example.com/config", translated)
        self.assertTrue(MODULE.validate_structure(SOURCE, translated).ok)

    def test_changed_code_and_link_fail_validation(self) -> None:
        changed = SOURCE.replace("python -m pip", "python -m uv").replace(
            "https://example.com/install", "https://example.com/other"
        )
        result = MODULE.validate_structure(SOURCE, changed)
        self.assertFalse(result.ok)
        self.assertTrue(any("fenced_code changed" in error for error in result.errors))
        self.assertTrue(any("link_targets changed" in error for error in result.errors))

    def test_manifest_records_source_hash_and_review_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.yaml"
            validation = MODULE.validate_structure(SOURCE, SOURCE)
            MODULE.write_manifest(
                path,
                source=Path("docs/source/en/example.md"),
                target=Path("docs/source/ko/example.md"),
                source_hash="abc123",
                source_revision="deadbeef",
                locale="ko",
                profile="transformers",
                model="test-model",
                validation=validation,
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn('hash: "abc123"', text)
            self.assertIn('revision: "deadbeef"', text)
            self.assertIn('generator: "technical-doc-translate"', text)
            self.assertIn("quality:\n    enabled: true", text)
            self.assertIn("      - hard_gates", text)


if __name__ == "__main__":
    unittest.main()
