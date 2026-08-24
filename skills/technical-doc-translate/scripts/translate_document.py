#!/usr/bin/env python3
"""Translate Markdown/MDX technical documentation as protected prose blocks.

The command intentionally handles only translation generation and a structural
preflight. It does not create Git branches, commits, pull requests, or quality
scores.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Sequence


FENCE_START_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
COMMENT_START_RE = re.compile(r"^\s*<!--")
HTML_COMMENT_RE = re.compile(r"<!--[\s\S]*?-->")
STANDALONE_TAG_RE = re.compile(r"^\s*</?[A-Za-z][^>]*>\s*$")
FRONTMATTER_RE = re.compile(r"^---\s*(?:\r?\n)")
LINK_RE = re.compile(r"(?P<prefix>!?\[)(?P<label>[^\]]*)(?P<middle>\]\()(?P<target>[^)]+)(?P<suffix>\))")
REFERENCE_LINK_RE = re.compile(
    r"(?P<prefix>!?\[)(?P<label>[^\]\n]*)(?P<middle>\])(?P<reference>\[[^\]\n]*\])"
)
REFERENCE_DEFINITION_RE = re.compile(r"^[ \t]*\[(?!\^)[^\]\n]+\]:[^\n]*$", re.MULTILINE)
FOOTNOTE_ID_RE = re.compile(r"\[\^[^\]\n]+\]")
INLINE_CODE_RE = re.compile(r"(`+)([^`\n]+?)\1")
ANCHOR_RE = re.compile(r"\[\[[^\]\n]+\]\]|\{#[A-Za-z0-9_.:-]+\}")
ADMONITION_RE = re.compile(r"\[!(?:NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]")
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^>\n]*>")
URL_RE = re.compile(r"https?://[^\s)>\]]+")
ENV_RE = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")
CLI_FLAG_RE = re.compile(r"(?<!\w)--[A-Za-z0-9][A-Za-z0-9_-]*")
FILE_PATH_RE = re.compile(r"(?<![\w/])(?:[.~]?/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+)")
PLACEHOLDER_RE = re.compile(r"⟦tdt\d{4}-\d{4}⟧")
HEADING_RE = re.compile(r"^(#{1,6})\s+", re.MULTILINE)
LIST_MARKER_RE = re.compile(r"^(\s*)(?:[-+*]|\d+[.)])\s+", re.MULTILINE)
TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Block:
    id: int
    kind: str
    raw: str
    translatable: bool


@dataclass(frozen=True)
class ProtectedBlock:
    id: int
    kind: str
    markdown: str
    placeholders: dict[str, str]


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]
    invariant_counts: dict[str, int]


def _is_fence_start(line: str) -> bool:
    return FENCE_START_RE.match(line.rstrip("\r\n")) is not None


def _consume_fence(lines: Sequence[str], start: int) -> int:
    match = FENCE_START_RE.match(lines[start].rstrip("\r\n"))
    if not match:
        return start + 1
    fence = match.group("fence")
    marker = fence[0]
    minimum = len(fence)
    index = start + 1
    while index < len(lines):
        stripped = lines[index].lstrip(" \t").rstrip("\r\n")
        if stripped.startswith(marker * minimum):
            tail = stripped[minimum:]
            if not tail.strip() or set(tail.strip()) == {marker}:
                return index + 1
        index += 1
    raise ValueError(f"Unclosed fenced code block starting at line {start + 1}")


def _consume_comment(lines: Sequence[str], start: int) -> int:
    index = start
    while index < len(lines):
        if "-->" in lines[index]:
            return index + 1
        index += 1
    raise ValueError(f"Unclosed HTML comment starting at line {start + 1}")


def _consume_frontmatter(lines: Sequence[str]) -> int:
    if not lines or not FRONTMATTER_RE.match(lines[0]):
        return 0
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return index + 1
    raise ValueError("Unclosed YAML frontmatter")


def parse_blocks(markdown: str) -> list[Block]:
    """Split a document while keeping protected structural regions byte-stable."""

    lines = markdown.splitlines(keepends=True)
    blocks: list[Block] = []
    next_id = 0

    def append(kind: str, raw: str, translatable: bool) -> None:
        nonlocal next_id
        blocks.append(Block(next_id, kind, raw, translatable))
        next_id += 1

    index = 0
    frontmatter_end = _consume_frontmatter(lines)
    if frontmatter_end:
        append("frontmatter", "".join(lines[:frontmatter_end]), False)
        index = frontmatter_end

    while index < len(lines):
        line = lines[index]
        if not line.strip():
            start = index
            while index < len(lines) and not lines[index].strip():
                index += 1
            append("blank", "".join(lines[start:index]), False)
            continue
        if _is_fence_start(line):
            end = _consume_fence(lines, index)
            append("code", "".join(lines[index:end]), False)
            index = end
            continue
        if COMMENT_START_RE.match(line):
            end = _consume_comment(lines, index)
            append("comment", "".join(lines[index:end]), False)
            index = end
            continue
        if REFERENCE_DEFINITION_RE.match(line.rstrip("\r\n")):
            append("reference-definition", line, False)
            index += 1
            continue
        if STANDALONE_TAG_RE.match(line.rstrip("\r\n")):
            append("component", line, False)
            index += 1
            continue

        start = index
        index += 1
        while index < len(lines):
            candidate = lines[index]
            if (
                not candidate.strip()
                or _is_fence_start(candidate)
                or COMMENT_START_RE.match(candidate)
                or REFERENCE_DEFINITION_RE.match(candidate.rstrip("\r\n"))
                or STANDALONE_TAG_RE.match(candidate.rstrip("\r\n"))
            ):
                break
            index += 1
        append("prose", "".join(lines[start:index]), True)

    return blocks


def _placeholder(mapping: dict[str, str], value: str, namespace: int) -> str:
    token = f"⟦tdt{namespace:04d}-{len(mapping):04d}⟧"
    mapping[token] = value
    return token


def protect_inline(markdown: str, *, namespace: int = 0) -> tuple[str, dict[str, str]]:
    """Protect non-translatable inline syntax while leaving link labels prose."""

    mapping: dict[str, str] = {}

    def link_replacer(match: re.Match[str]) -> str:
        target = _placeholder(mapping, match.group("target"), namespace)
        return f"{match.group('prefix')}{match.group('label')}{match.group('middle')}{target}{match.group('suffix')}"

    protected = LINK_RE.sub(link_replacer, markdown)

    def reference_link_replacer(match: re.Match[str]) -> str:
        reference = _placeholder(mapping, match.group("reference"), namespace)
        return f"{match.group('prefix')}{match.group('label')}{match.group('middle')}{reference}"

    protected = REFERENCE_LINK_RE.sub(reference_link_replacer, protected)

    patterns = [
        INLINE_CODE_RE,
        FOOTNOTE_ID_RE,
        ANCHOR_RE,
        ADMONITION_RE,
        HTML_COMMENT_RE,
        HTML_TAG_RE,
        URL_RE,
        FILE_PATH_RE,
        CLI_FLAG_RE,
        ENV_RE,
    ]
    for pattern in patterns:
        protected = pattern.sub(lambda match: _placeholder(mapping, match.group(0), namespace), protected)
    return protected, mapping


def restore_inline(markdown: str, mapping: dict[str, str]) -> str:
    expected = Counter(mapping.keys())
    found = Counter(PLACEHOLDER_RE.findall(markdown))
    missing = sorted((expected - found).elements())
    extra = sorted((found - expected).elements())
    duplicated = sorted(token for token, count in found.items() if count != 1 and token in mapping)
    if missing or extra or duplicated:
        raise ValueError(
            "Protected token mismatch: "
            f"missing={missing or 'none'} extra={extra or 'none'} duplicated={duplicated or 'none'}"
        )
    restored = markdown
    for token, value in mapping.items():
        restored = restored.replace(token, value)
    return restored


def prepare_blocks(blocks: Iterable[Block]) -> list[ProtectedBlock]:
    prepared: list[ProtectedBlock] = []
    for block in blocks:
        if not block.translatable:
            continue
        markdown, placeholders = protect_inline(block.raw, namespace=block.id)
        prepared.append(ProtectedBlock(block.id, block.kind, markdown, placeholders))
    return prepared


def load_glossaries(paths: Sequence[Path]) -> dict[str, str]:
    glossary: dict[str, str] = {}
    for path in paths:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if not reader.fieldnames or "source_term" not in reader.fieldnames or "ko_term" not in reader.fieldnames:
                raise ValueError(f"Glossary must contain source_term and ko_term columns: {path}")
            for row in reader:
                source = (row.get("source_term") or "").strip()
                target = (row.get("ko_term") or "").strip()
                if source and target:
                    glossary[source] = target
    return glossary


def _json_array(text: str) -> list[dict[str, object]]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    candidates = [cleaned]
    match = re.search(r"\[[\s\S]*\]", cleaned)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
            return parsed
    raise ValueError("Translation response did not contain a JSON array")


def build_prompt(
    blocks: Sequence[ProtectedBlock],
    *,
    rules: str,
    profile_rules: str,
    glossary: dict[str, str],
    document_title: str,
) -> str:
    payload = [{"id": block.id, "kind": block.kind, "markdown": block.markdown} for block in blocks]
    glossary_lines = "\n".join(f"- {source} -> {target}" for source, target in glossary.items()) or "- none"
    return (
        f"{rules.strip()}\n\n"
        f"[Project profile]\n{profile_rules.strip() or 'No additional profile rules.'}\n\n"
        f"[Document context]\nTitle: {document_title or 'Untitled'}\n"
        f"Glossary:\n{glossary_lines}\n\n"
        "[Input blocks]\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def openai_model_call(model: str) -> Callable[[str], str]:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install the optional OpenAI dependency before running translation") from exc
    client = OpenAI()

    def call(prompt: str) -> str:
        response = client.responses.create(
            model=model,
            instructions="You are a precise technical-document translation engine. Follow the supplied contract exactly.",
            input=prompt,
        )
        output = response.output_text.strip()
        if not output:
            raise RuntimeError("OpenAI returned an empty translation response")
        return output

    return call


def _title_from_blocks(blocks: Sequence[Block]) -> str:
    for block in blocks:
        if not block.translatable:
            continue
        match = re.search(r"^#\s+(.+)$", block.raw, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()
    return ""


def _preserve_newline_shape(source: str, translated: str) -> str:
    trailing = source[len(source.rstrip("\r\n")) :]
    return translated.rstrip("\r\n") + trailing


def translate_blocks(
    blocks: Sequence[Block],
    *,
    model_call: Callable[[str], str],
    rules: str,
    profile_rules: str = "",
    glossary: dict[str, str] | None = None,
    batch_size: int = 24,
) -> str:
    prepared = prepare_blocks(blocks)
    translated_by_id: dict[int, str] = {}
    glossary = glossary or {}
    title = _title_from_blocks(blocks)

    for start in range(0, len(prepared), batch_size):
        batch = prepared[start : start + batch_size]
        prompt = build_prompt(
            batch,
            rules=rules,
            profile_rules=profile_rules,
            glossary=glossary,
            document_title=title,
        )
        rows = _json_array(model_call(prompt))
        expected_ids = [block.id for block in batch]
        actual_ids = [row.get("id") for row in rows]
        if actual_ids != expected_ids:
            raise ValueError(f"Translation block IDs changed: expected={expected_ids} actual={actual_ids}")
        for block, row in zip(batch, rows, strict=True):
            markdown = row.get("markdown")
            if not isinstance(markdown, str):
                raise ValueError(f"Translated block {block.id} has no markdown string")
            restored = restore_inline(markdown, block.placeholders)
            translated_by_id[block.id] = restored

    output: list[str] = []
    for block in blocks:
        value = translated_by_id.get(block.id, block.raw)
        if block.id in translated_by_id:
            value = _preserve_newline_shape(block.raw, value)
        output.append(value)
    return "".join(output)


def _extract_fences(markdown: str) -> list[str]:
    lines = markdown.splitlines(keepends=True)
    fences: list[str] = []
    index = 0
    while index < len(lines):
        if not _is_fence_start(lines[index]):
            index += 1
            continue
        end = _consume_fence(lines, index)
        fences.append("".join(lines[index:end]))
        index = end
    return fences


def _extract_comments(markdown: str) -> list[str]:
    return HTML_COMMENT_RE.findall(markdown)


def _table_shapes(markdown: str) -> list[int]:
    return [row.count("|") for row in TABLE_ROW_RE.findall(markdown)]


def _invariants(markdown: str) -> dict[str, list[str] | list[int]]:
    return {
        "fenced_code": _extract_fences(markdown),
        "html_comments": _extract_comments(markdown),
        "inline_code": [match.group(0) for match in INLINE_CODE_RE.finditer(markdown)],
        "link_targets": [match.group("target") for match in LINK_RE.finditer(markdown)],
        "reference_link_targets": [match.group("reference") for match in REFERENCE_LINK_RE.finditer(markdown)],
        "reference_definitions": REFERENCE_DEFINITION_RE.findall(markdown),
        "footnote_identifiers": FOOTNOTE_ID_RE.findall(markdown),
        "anchors": ANCHOR_RE.findall(markdown),
        "admonitions": ADMONITION_RE.findall(markdown),
        "html_tags": HTML_TAG_RE.findall(markdown),
        "heading_levels": [str(len(match.group(1))) for match in HEADING_RE.finditer(markdown)],
        "list_markers": [match.group(0) for match in LIST_MARKER_RE.finditer(markdown)],
        "table_shapes": _table_shapes(markdown),
        "environment_variables": ENV_RE.findall(markdown),
        "cli_flags": CLI_FLAG_RE.findall(markdown),
    }


def validate_structure(source: str, target: str) -> ValidationResult:
    source_values = _invariants(source)
    target_values = _invariants(target)
    errors: list[str] = []
    for name, expected in source_values.items():
        actual = target_values[name]
        if expected != actual:
            errors.append(f"{name} changed: source={expected!r} target={actual!r}")
    counts = {name: len(values) for name, values in source_values.items()}
    return ValidationResult(not errors, errors, counts)


def _yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def git_file_metadata(path: Path) -> tuple[str, str]:
    """Return a repository-relative path and exact clean file revision when available."""

    try:
        root_result = subprocess.run(
            ["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
        root = Path(root_result.stdout.strip()).resolve()
        relative = path.resolve().relative_to(root).as_posix()
        status_result = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain", "--", relative],
            check=True,
            capture_output=True,
            text=True,
        )
        if status_result.stdout.strip():
            return relative, ""
        revision_result = subprocess.run(
            ["git", "-C", str(root), "log", "-1", "--format=%H", "--", relative],
            check=True,
            capture_output=True,
            text=True,
        )
        return relative, revision_result.stdout.strip()
    except (OSError, subprocess.CalledProcessError, ValueError):
        return str(path), ""


def repository_relative_label(path: Path, source: Path) -> str:
    source_label, _ = git_file_metadata(source)
    if source_label == str(source):
        return str(path)
    try:
        root_result = subprocess.run(
            ["git", "-C", str(source.parent), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
        return path.resolve().relative_to(Path(root_result.stdout.strip()).resolve()).as_posix()
    except (OSError, subprocess.CalledProcessError, ValueError):
        return str(path)


def write_manifest(
    path: Path,
    *,
    source: Path,
    target: Path,
    source_hash: str,
    source_revision: str,
    locale: str,
    profile: str,
    model: str,
    validation: ValidationResult,
) -> None:
    lines = [
        "version: 1",
        "run:",
        f"  created_at: {_yaml_string(datetime.now(timezone.utc).isoformat())}",
        "source:",
        f"  file_path: {_yaml_string(str(source))}",
        f"  hash: {_yaml_string(source_hash)}",
    ]
    if source_revision:
        lines.append(f"  revision: {_yaml_string(source_revision)}")
    lines.extend(
        [
            "translation:",
            f"  file_path: {_yaml_string(str(target))}",
            f"  locale: {_yaml_string(locale)}",
            f"  profile: {_yaml_string(profile)}",
            '  generator: "technical-doc-translate"',
            f"  model: {_yaml_string(model)}",
            "validation:",
            f"  structural_status: {_yaml_string('pass' if validation.ok else 'fail')}",
            "handoff:",
            "  quality:",
            "    enabled: true",
            "    checks:",
            "      - fidelity",
            "      - fluency",
            "      - terminology",
            "      - formatting",
            "      - links",
            "      - hard_gates",
            "",
        ]
    )
    content = "\n".join(lines)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _default_rules_path() -> Path:
    return Path(__file__).resolve().parents[1] / "references" / "translation-prompt.md"


def _profile_rules_path(profile: str) -> Path | None:
    if profile == "transformers":
        return Path(__file__).resolve().parents[1] / "references" / "transformers-docs.md"
    return None


def _read_optional(path: Path | None) -> str:
    return path.read_text(encoding="utf-8") if path is not None else ""


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Translate a protected Markdown/MDX technical document into Korean.")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--target-locale", default="ko")
    parser.add_argument("--profile", choices=["generic", "transformers"], default="generic")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-5-nano"))
    parser.add_argument("--source-revision", default="", help="Optional authoritative Git revision for the source file.")
    parser.add_argument("--prompt", type=Path, default=_default_rules_path())
    parser.add_argument("--glossary", action="append", type=Path, default=[])
    parser.add_argument("--manifest-output", type=Path)
    parser.add_argument("--validation-output", type=Path)
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    source = args.source.resolve()
    target = args.target.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Source document not found: {source}")
    source_text = source.read_text(encoding="utf-8")
    if not source_text.strip():
        raise ValueError(f"Source document is empty: {source}")
    if target.exists() and not args.force and not args.dry_run:
        raise FileExistsError(f"Target already exists; pass --force only for an approved replacement: {target}")
    if args.batch_size < 1:
        raise ValueError("--batch-size must be at least 1")

    blocks = parse_blocks(source_text)
    prepared = prepare_blocks(blocks)
    source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    source_label, discovered_revision = git_file_metadata(source)
    source_revision = args.source_revision.strip() or discovered_revision
    if args.dry_run:
        summary = {
            "source": str(source),
            "target": str(target),
            "profile": args.profile,
            "source_sha256": source_hash,
            "source_revision": source_revision or None,
            "block_count": len(blocks),
            "translatable_block_count": len(prepared),
            "protected_token_count": sum(len(block.placeholders) for block in prepared),
            "kinds": dict(Counter(block.kind for block in blocks)),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    rules = args.prompt.read_text(encoding="utf-8")
    profile_rules = _read_optional(_profile_rules_path(args.profile))
    glossary = load_glossaries(args.glossary)
    translated = translate_blocks(
        blocks,
        model_call=openai_model_call(args.model),
        rules=rules,
        profile_rules=profile_rules,
        glossary=glossary,
        batch_size=args.batch_size,
    )
    validation = validate_structure(source_text, translated)
    if not validation.ok:
        detail = "\n".join(f"- {error}" for error in validation.errors)
        raise ValueError(f"Structural validation failed; target was not written:\n{detail}")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(translated, encoding="utf-8")

    if args.validation_output:
        args.validation_output.parent.mkdir(parents=True, exist_ok=True)
        args.validation_output.write_text(
            json.dumps(
                {"status": "pass", "errors": [], "invariant_counts": validation.invariant_counts},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    if args.manifest_output:
        write_manifest(
            args.manifest_output,
            source=Path(source_label),
            target=Path(repository_relative_label(target, source)),
            source_hash=source_hash,
            source_revision=source_revision,
            locale=args.target_locale,
            profile=args.profile,
            model=args.model,
            validation=validation,
        )

    print(f"Wrote translation: {target}")
    if args.manifest_output:
        print(f"Wrote manifest: {args.manifest_output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
