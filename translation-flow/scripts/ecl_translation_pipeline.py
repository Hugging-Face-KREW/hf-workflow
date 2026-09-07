from __future__ import annotations

import ast
import csv
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional
import urllib.request

from markdown_it import MarkdownIt


PARSER = MarkdownIt("js-default", {"html": True})
TRANSLATABLE_KINDS = {"heading", "paragraph", "bullet_list", "ordered_list", "blockquote", "table"}
TOKEN_TO_KIND = {
    "heading_open": "heading",
    "paragraph_open": "paragraph",
    "bullet_list_open": "bullet_list",
    "ordered_list_open": "ordered_list",
    "blockquote_open": "blockquote",
    "table_open": "table",
    "fence": "code",
    "code_block": "code",
    "html_block": "html_block",
    "hr": "hr",
}

IMPERATIVE_VERBS = {
    "run",
    "install",
    "use",
    "call",
    "click",
    "open",
    "type",
    "enter",
    "navigate",
    "select",
    "create",
    "delete",
    "set",
    "configure",
    "deploy",
    "import",
    "load",
    "save",
    "execute",
    "launch",
    "start",
    "stop",
}

KEEP_RE = re.compile(r"(`[^`\n]+`|!?\[[^\]]*\]\([^)]+\)|https?://[^\s)>\]]+)")
TOKEN_NORMALIZE_RE = re.compile(r"[^0-9a-zA-Z.+/#_-]+")
PLURAL_SUFFIXES = ["s", "es"]
FENCE_START_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
CODE_BLOCK_PLACEHOLDER_RE = re.compile(r"^\{\{CODE_BLOCK_\d+\}\}$")
DEFAULT_TERMS_BASE_URL = "https://poc.terms.kr/data/"
DEFAULT_TERMS_CACHE_PATH = Path(".cache/ecl_translation/terms_kr_glossary.json")
DEFAULT_TERMS_TIMEOUT_SECONDS = 10.0
DEFAULT_LOCAL_GLOSSARY_DIR = Path(__file__).resolve().parents[2] / "skills" / "quality" / "glossary"
DEFAULT_LOCAL_GLOSSARY_FILES = ("ko.tsv", "ml_terms.tsv", "product_terms.tsv")
_EXTERNAL_GLOSSARY_CACHE: Optional[dict[str, str]] = None
_EXTERNAL_GLOSSARY_LOAD_FAILED = False

DEFAULT_GLOSSARY: dict[str, str] = {
    "Hugging Face": "허깅페이스",
    "OpenCLAW": "오픈클로",
    "Inference Providers": "추론 제공자",
    "open model": "오픈 모델",
    "dataset": "데이터셋",
    "benchmark": "벤치마크",
    "deployment": "배포",
}


def ecl_log(message: str) -> None:
    print(f"[translation-ecl] {message}", flush=True)


@dataclass
class Block:
    id: int
    kind: str
    raw: str
    start_line: int
    end_line: int
    translatable: bool


def normalize_term_key(text: str) -> str:
    text = text.lower().strip()
    text = TOKEN_NORMALIZE_RE.sub(" ", text)
    tokens = [
        token.strip(".,;:!?()[]{}\"'“”‘’")
        for token in text.split()
    ]
    return " ".join(token for token in tokens if token)


def parse_env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def terms_base_url() -> str:
    value = os.getenv("ECL_TERMS_BASE_URL", DEFAULT_TERMS_BASE_URL).strip()
    if not value:
        return DEFAULT_TERMS_BASE_URL
    return value if value.endswith("/") else value + "/"


def terms_cache_path() -> Path:
    raw = os.getenv("ECL_GLOSSARY_CACHE_PATH")
    if raw:
        return Path(raw).expanduser()
    return DEFAULT_TERMS_CACHE_PATH


def terms_timeout_seconds() -> float:
    raw = os.getenv("ECL_TERMS_TIMEOUT_SECONDS")
    if not raw:
        return DEFAULT_TERMS_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_TERMS_TIMEOUT_SECONDS
    return max(1.0, value)


def local_glossary_dir() -> Path:
    raw = os.getenv("ECL_LOCAL_GLOSSARY_DIR")
    if not raw:
        return DEFAULT_LOCAL_GLOSSARY_DIR
    path = Path(raw).expanduser()
    return path if path.is_absolute() else Path.cwd() / path


def fetch_json(url: str, timeout: float) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "translation-flow/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        text = response.read().decode(charset, errors="replace")
    return json.loads(text)


def load_cached_terms_glossary(cache_path: Path) -> dict[str, str]:
    if not cache_path.exists():
        return {}
    try:
        loaded = json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(loaded, dict):
        return {}
    glossary: dict[str, str] = {}
    for term, korean in loaded.items():
        if not isinstance(term, str) or not isinstance(korean, str):
            continue
        term = term.strip()
        korean = korean.strip()
        if term and korean:
            glossary[term] = korean
    return glossary


def save_terms_glossary_cache(cache_path: Path, glossary: dict[str, str]) -> None:
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(glossary, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        return


def download_terms_glossary(base_url: str, timeout: float) -> dict[str, str]:
    index_data = fetch_json(f"{base_url}index.json", timeout=timeout)
    if isinstance(index_data, list):
        filenames = index_data
    elif isinstance(index_data, dict):
        filenames = index_data.get("files", [])
    else:
        filenames = []
    if not isinstance(filenames, list):
        return {}

    glossary: dict[str, str] = {}
    for filename in filenames:
        if not isinstance(filename, str) or not filename.strip():
            continue
        try:
            rows_data = fetch_json(f"{base_url}{filename}", timeout=timeout)
        except Exception as exc:
            ecl_log(f"terms.kr chunk fetch failed: {filename} ({exc})")
            continue
        if isinstance(rows_data, list):
            rows = rows_data
        elif isinstance(rows_data, dict):
            rows = rows_data.get("rows", [])
        else:
            rows = []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            term = str(row.get("term", "")).strip()
            meanings = row.get("meanings")
            if not term or not isinstance(meanings, list) or not meanings:
                continue
            first = meanings[0] if isinstance(meanings[0], dict) else {}
            korean = str(first.get("korean", "")).strip()
            if korean:
                glossary[term] = korean
    return glossary


def load_termskr_glossary() -> dict[str, str]:
    global _EXTERNAL_GLOSSARY_CACHE
    global _EXTERNAL_GLOSSARY_LOAD_FAILED

    if _EXTERNAL_GLOSSARY_CACHE is not None:
        return _EXTERNAL_GLOSSARY_CACHE.copy()
    if _EXTERNAL_GLOSSARY_LOAD_FAILED:
        return {}

    cache_path = terms_cache_path()
    cached = load_cached_terms_glossary(cache_path)
    if cached:
        _EXTERNAL_GLOSSARY_CACHE = cached
        ecl_log(f"Loaded terms.kr glossary from cache entries={len(cached)} path={cache_path}")
        return cached.copy()

    try:
        downloaded = download_terms_glossary(terms_base_url(), terms_timeout_seconds())
    except Exception as exc:
        _EXTERNAL_GLOSSARY_LOAD_FAILED = True
        ecl_log(f"External glossary fetch failed ({exc}). Using built-in glossary only.")
        return {}

    if not downloaded:
        _EXTERNAL_GLOSSARY_LOAD_FAILED = True
        ecl_log("External glossary fetch returned no entries. Using built-in glossary only.")
        return {}

    save_terms_glossary_cache(cache_path, downloaded)
    _EXTERNAL_GLOSSARY_CACHE = downloaded
    ecl_log(f"Loaded terms.kr glossary from network entries={len(downloaded)}")
    return downloaded.copy()


def load_quality_glossary_tsv(path: Path) -> dict[str, str]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if not reader.fieldnames:
                return {}
            glossary: dict[str, str] = {}
            for row in reader:
                source_term = (row.get("source_term") or "").strip()
                ko_term = (row.get("ko_term") or "").strip()
                if source_term and ko_term:
                    glossary[source_term] = ko_term
            return glossary
    except OSError:
        return {}


def load_quality_glossaries(glossary_dir: Optional[Path] = None) -> dict[str, str]:
    root = glossary_dir or local_glossary_dir()
    if not root.exists():
        return {}

    glossary: dict[str, str] = {}
    for filename in DEFAULT_LOCAL_GLOSSARY_FILES:
        glossary.update(load_quality_glossary_tsv(root / filename))
    return glossary


def build_glossary_lookup(custom: dict[str, str]) -> tuple[dict[str, dict[str, str]], int]:
    merged: dict[str, dict[str, str]] = {}
    for term, korean in custom.items():
        key = normalize_term_key(term)
        if not key:
            continue
        merged[key] = {
            "term": term,
            "korean": korean,
            "definition": "",
            "source": "custom",
        }
    max_n = max((len(key.split()) for key in merged), default=1)
    return merged, min(max_n, 6)


def plural_variants(key: str) -> set[str]:
    parts = key.split()
    if not parts:
        return set()
    last, head = parts[-1], parts[:-1]
    out = {key}
    for suffix in PLURAL_SUFFIXES:
        out.add(" ".join(head + [last + suffix]))
    for suffix in PLURAL_SUFFIXES:
        if last.endswith(suffix) and len(last) > len(suffix) + 2:
            out.add(" ".join(head + [last[: -len(suffix)]]))
    return out


def build_plural_index(lookup: dict[str, dict[str, str]]) -> dict[str, str]:
    index: dict[str, str] = {}
    for key in lookup:
        for variant in plural_variants(key):
            if variant not in index or len(index[variant]) > len(key):
                index[variant] = key
    return index


def glossary_candidates(
    text: str,
    lookup: dict[str, dict[str, str]],
    plural_index: dict[str, str],
    max_n: int,
    max_hits: int,
) -> list[dict[str, str]]:
    tokens = normalize_term_key(text).split()
    hits: list[dict[str, str]] = []
    used: set[int] = set()
    for n in range(min(max_n, len(tokens)), 0, -1):
        for i in range(len(tokens) - n + 1):
            span = set(range(i, i + n))
            if span & used:
                continue
            key = " ".join(tokens[i : i + n])
            original_key = key if key in lookup else plural_index.get(key)
            if not original_key:
                continue
            meta = lookup.get(original_key)
            if not meta or not meta.get("korean"):
                continue
            hits.append({**meta, "key": original_key, "matched": key})
            used.update(span)
            if len(hits) >= max_hits:
                return hits
    return hits


def parse_markdown_blocks(body_text: str) -> list[Block]:
    lines = body_text.splitlines(keepends=True)
    tokens = PARSER.parse(body_text)
    blocks: list[Block] = []
    seen: set[tuple[int, int]] = set()
    block_id = 0
    for token in tokens:
        if token.level != 0 or token.map is None:
            continue
        kind = TOKEN_TO_KIND.get(token.type)
        if not kind:
            continue
        token_range = tuple(token.map)
        if token_range in seen:
            continue
        seen.add(token_range)
        start, end = token_range
        raw = "".join(lines[start:end])
        is_code_placeholder = bool(CODE_BLOCK_PLACEHOLDER_RE.fullmatch(raw.strip()))
        blocks.append(
            Block(
                id=block_id,
                kind=kind,
                raw=raw,
                start_line=start,
                end_line=end,
                translatable=(kind in TRANSLATABLE_KINDS and not is_code_placeholder),
            )
        )
        block_id += 1
    return blocks


def label_blocks(blocks: list[Block]) -> dict[int, str]:
    paragraph_ids = [block.id for block in blocks if block.kind == "paragraph"]
    paragraph_count = len(paragraph_ids)
    code_adjacent: set[int] = set()
    for i, block in enumerate(blocks):
        if block.kind != "code":
            continue
        for j in (i - 1, i + 1):
            if 0 <= j < len(blocks) and blocks[j].kind == "paragraph":
                code_adjacent.add(blocks[j].id)

    labels: dict[int, str] = {}
    for block in blocks:
        if not block.translatable or block.kind == "heading":
            continue
        if block.kind == "paragraph" and block.id in paragraph_ids[:2]:
            labels[block.id] = "intro"
            continue
        if block.kind == "paragraph" and paragraph_count >= 3 and block.id in paragraph_ids[-2:]:
            labels[block.id] = "conclusion"
            continue
        text = block.raw.strip()
        first_word = re.split(r"\s+", text.lower(), maxsplit=1)[0] if text else ""
        first_word = re.sub(r"^[-*\d.]+", "", first_word)
        if first_word in IMPERATIVE_VERBS:
            labels[block.id] = "instruction"
        elif block.id in code_adjacent:
            labels[block.id] = "code_context"
        else:
            labels[block.id] = "explanation"
    return labels


def protect_inline(markdown: str) -> tuple[str, dict[str, str]]:
    saved: dict[str, str] = {}

    def replacer(match: re.Match[str]) -> str:
        key = f"{{{{KEEP_{len(saved)}}}}}"
        saved[key] = match.group(0)
        return key

    return KEEP_RE.sub(replacer, markdown), saved


def restore_inline(markdown: str, saved: dict[str, str]) -> str:
    for key, value in saved.items():
        markdown = markdown.replace(key, value)
    return markdown


def protect_fenced_code_blocks(markdown: str) -> tuple[str, dict[str, str]]:
    lines = markdown.splitlines(keepends=True)
    protected: list[str] = []
    saved: dict[str, str] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        start_match = FENCE_START_RE.match(line)
        if not start_match:
            protected.append(line)
            i += 1
            continue

        fence = start_match.group("fence")
        fence_char = fence[0]
        fence_len = len(fence)
        block_lines = [line]
        i += 1
        while i < len(lines):
            current = lines[i]
            block_lines.append(current)
            stripped = current.lstrip(" \t")
            if stripped.startswith(fence_char * fence_len):
                tail = stripped[fence_len:].rstrip("\r\n")
                if not tail.strip() or set(tail.strip()) == {fence_char}:
                    i += 1
                    break
            i += 1

        key = f"{{{{CODE_BLOCK_{len(saved)}}}}}"
        saved[key] = "".join(block_lines)
        protected.append(key + "\n")
    return "".join(protected), saved


def restore_fenced_code_blocks(markdown: str, saved: dict[str, str]) -> str:
    for key, value in saved.items():
        markdown = markdown.replace(key, value)
    return markdown


def extract_doc_title(blocks: list[Block]) -> str:
    for block in blocks:
        if block.kind == "heading":
            return block.raw.strip().lstrip("#").strip()
    return "Untitled"


def parse_json_array(text: str) -> Optional[list[dict[str, Any]]]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    candidates = [cleaned]
    match = re.search(r"\[[\s\S]*\]", cleaned)
    if match:
        candidates.append(match.group(0))

    for candidate in candidates:
        for loader in (json.loads, ast.literal_eval):
            try:
                data = loader(candidate)
                if isinstance(data, list):
                    return data
            except Exception:
                continue
    return None


def restore_body(blocks: list[Block], translated: dict[int, str]) -> str:
    parts = [translated.get(block.id, block.raw).rstrip() for block in blocks]
    return "\n\n".join(part for part in parts if part).strip() + "\n"


def build_context(
    blocks: list[Block],
    doc_title: str,
    lookup: dict[str, dict[str, str]],
    plural_index: dict[str, str],
    max_n: int,
    max_glossary_terms: int,
    compressed_guide: Optional[str] = None,
) -> str:
    full_text = "\n".join(block.raw for block in blocks if block.translatable)
    headings = [block.raw.strip().lstrip("#").strip() for block in blocks if block.kind == "heading"]
    hits = glossary_candidates(full_text, lookup, plural_index, max_n, max_glossary_terms)

    lines = [
        f"Document title: {doc_title}",
        "Headings in document: " + (" > ".join(headings) if headings else "none"),
        "Style: technical blog translation in natural Korean. Do not over-explain terminology.",
    ]
    if hits:
        lines.append("Glossary:")
        for hit in hits:
            term = hit.get("term", "")
            korean = hit.get("korean", "")
            definition = hit.get("definition", "")
            if definition:
                lines.append(f"- {term} -> {korean} | {definition}")
            else:
                lines.append(f"- {term} -> {korean}")
    if compressed_guide:
        lines.append("Compressed translation guide:")
        lines.append(compressed_guide.strip())
    lines.append("Use block labels as role hints for tone and sentence style.")
    return "\n".join(lines)


def _translation_prompt(
    items: list[dict[str, Any]],
    doc_title: str,
    blocks: list[Block],
    core_rules: str,
    target_language: str,
    lookup: dict[str, dict[str, str]],
    plural_index: dict[str, str],
    max_n: int,
    max_glossary_terms: int,
    compressed_guide: Optional[str] = None,
) -> str:
    context_text = build_context(
        blocks=blocks,
        doc_title=doc_title,
        lookup=lookup,
        plural_index=plural_index,
        max_n=max_n,
        max_glossary_terms=max_glossary_terms,
        compressed_guide=compressed_guide,
    )
    return f"""
Translate the following Markdown blocks into {target_language}.

[Core Translation Rules]
{core_rules}

[Context]
{context_text}

[Output Rules]
- Context is guidance only. Do not translate Context.
- Output JSON array only.
- Preserve item count, ids, and order.
- Output schema for each item: {{"id": number, "markdown": "translated markdown"}}
- Preserve Markdown structure and placeholders like {{{{KEEP_0}}}} or {{{{CODE_BLOCK_0}}}} exactly.
- Do not alter URLs, link targets, inline code, fenced code, commands, model names, API names, parameter names, or file paths.
- Do not add explanations, notes, or summaries.

[Input JSON]
{json.dumps(items, ensure_ascii=False, indent=2)}
""".strip()


def translate_markdown_with_ecl(
    source_markdown: str,
    core_rules: str,
    target_language: str,
    model_call: Callable[[str], str],
    max_glossary_terms: int = 15,
    glossary: Optional[dict[str, str]] = None,
    use_external_glossary: Optional[bool] = None,
    compressed_guide: Optional[str] = None,
) -> str:
    protected_markdown, code_blocks = protect_fenced_code_blocks(source_markdown)
    if code_blocks:
        ecl_log(f"Protected fenced code blocks={len(code_blocks)}")

    blocks = parse_markdown_blocks(protected_markdown)
    if not blocks:
        ecl_log("No blocks parsed from source markdown. Returning source as-is.")
        restored = protected_markdown.strip() + ("\n" if protected_markdown else "")
        return restore_fenced_code_blocks(restored, code_blocks)

    labels = label_blocks(blocks)
    doc_title = extract_doc_title(blocks)
    translatable_count = sum(1 for block in blocks if block.translatable and block.raw.strip())
    ecl_log(
        f"Parsed blocks={len(blocks)}, translatable={translatable_count}, "
        f"source_chars={len(protected_markdown)}"
    )
    ecl_log(f"Document title: {doc_title}")

    merged_glossary: dict[str, str] = {}
    should_use_external = (
        use_external_glossary
        if use_external_glossary is not None
        else parse_env_bool("ECL_USE_EXTERNAL_GLOSSARY", True)
    )
    if should_use_external:
        external_glossary = load_termskr_glossary()
        if external_glossary:
            merged_glossary.update(external_glossary)
            ecl_log(f"Using external glossary entries={len(external_glossary)}")
    else:
        ecl_log("External glossary disabled via ECL_USE_EXTERNAL_GLOSSARY.")

    merged_glossary.update(DEFAULT_GLOSSARY)
    local_glossary = load_quality_glossaries()
    if local_glossary:
        merged_glossary.update(local_glossary)
        ecl_log(f"Using local TSV glossary entries={len(local_glossary)} path={local_glossary_dir()}")
    if glossary:
        merged_glossary.update(glossary)
    lookup, max_n = build_glossary_lookup(merged_glossary)
    plural_index = build_plural_index(lookup)
    ecl_log(
        f"Glossary entries={len(lookup)}, max_phrase_len={max_n}, max_glossary_terms={max_glossary_terms}"
    )

    items: list[dict[str, Any]] = []
    protections: dict[int, dict[str, str]] = {}
    for block in blocks:
        if not block.translatable or not block.raw.strip():
            continue
        protected, saved = protect_inline(block.raw)
        protections[block.id] = saved
        item: dict[str, Any] = {"id": block.id, "kind": block.kind, "markdown": protected}
        label = labels.get(block.id)
        if label:
            item["label"] = label
        items.append(item)

    if not items:
        ecl_log("No translatable items after filtering. Returning restored source.")
        restored = restore_body(blocks, {})
        return restore_fenced_code_blocks(restored, code_blocks)
    ecl_log(f"Prepared translation items={len(items)}")

    prompt = _translation_prompt(
        items=items,
        doc_title=doc_title,
        blocks=blocks,
        core_rules=core_rules,
        target_language=target_language,
        lookup=lookup,
        plural_index=plural_index,
        max_n=max_n,
        max_glossary_terms=max_glossary_terms,
        compressed_guide=compressed_guide,
    )
    ecl_log(f"Sending single model request. prompt_chars={len(prompt)}")

    raw_output = model_call(prompt)
    ecl_log(f"Received model response. response_chars={len(raw_output)}")
    parsed = parse_json_array(raw_output)
    if parsed is None:
        # Falling back to the source blocks here would silently publish the
        # untranslated English article, which downstream structure checks
        # cannot detect. Fail instead.
        raise RuntimeError(
            "Could not parse the translation model output as a JSON array "
            f"(response_chars={len(raw_output)}). Aborting instead of emitting untranslated text."
        )
    ecl_log(f"Parsed translated rows={len(parsed)}")

    translated_by_id: dict[int, str] = {}
    for row in parsed:
        if not isinstance(row, dict):
            continue
        block_id = row.get("id")
        markdown = row.get("markdown")
        if not isinstance(block_id, int) or not isinstance(markdown, str):
            continue
        translated_by_id[block_id] = restore_inline(markdown, protections.get(block_id, {}))
    ecl_log(f"Restored translated blocks={len(translated_by_id)}")

    missing_ids = [item["id"] for item in items if item["id"] not in translated_by_id]
    if missing_ids:
        # `restore_body` keeps the source text for any block the model dropped,
        # so a partial response would leak English paragraphs into the output.
        raise RuntimeError(
            f"Translation model returned no output for {len(missing_ids)} of {len(items)} blocks "
            f"(missing ids: {missing_ids[:10]}). Aborting instead of emitting untranslated text."
        )

    restored = restore_body(blocks, translated_by_id)
    restored = restore_fenced_code_blocks(restored, code_blocks)
    ecl_log(f"Final translated markdown chars={len(restored)}")
    return restored