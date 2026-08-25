from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol


@dataclass(frozen=True)
class TranslationRequest:
    title: str
    source_url: str
    source_markdown: str
    target_locale: str = "ko"


class TranslationAdapter(Protocol):
    name: str

    def translate(self, request: TranslationRequest) -> str:
        """Return translated markdown body only."""


class PlaceholderTranslationAdapter:
    name = "none"

    def translate(self, request: TranslationRequest) -> str:
        return (
            "TODO: Add Korean translation.\n\n"
            "## Source text\n\n"
            "```markdown\n"
            f"{request.source_markdown.strip()}\n"
            "```\n"
        )


class OpenAITranslationAdapter:
    name = "openai"

    def __init__(self, model: Optional[str] = None, prompt_path: Optional[Path] = None) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
        self.prompt_path = prompt_path or default_prompt_path()

    def translate(self, request: TranslationRequest) -> str:
        try:
            from scripts.ecl_translation_pipeline import translate_markdown_with_ecl
            from scripts.context_compression import build_compressed_guide, parse_guide_paths
        except ModuleNotFoundError:
            try:
                from ecl_translation_pipeline import translate_markdown_with_ecl
                from context_compression import build_compressed_guide, parse_guide_paths
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "The ECL pipeline requires `markdown-it-py`. "
                    "Install dependencies with `uv sync` or `pip install markdown-it-py`."
                ) from exc

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "The OpenAI adapter requires the `openai` package. "
                "Install dependencies with `uv sync` or `pip install openai`."
            ) from exc

        client = OpenAI()
        core_rules = load_translation_prompt(self.prompt_path)
        target_language = locale_to_language(request.target_locale)
        print(
            f"[translation-openai] model={self.model} target_language={target_language} "
            f"source_chars={len(request.source_markdown)}",
            flush=True,
        )

        def call_openai(prompt: str, instructions: str, label: str, model: Optional[str] = None) -> str:
            print(
                f"[translation-openai] {label}_start model={model or self.model} prompt_chars={len(prompt)}",
                flush=True,
            )
            response = client.responses.create(
                model=model or self.model,
                instructions=instructions,
                input=prompt,
            )
            text = response.output_text.strip()
            if not text:
                raise RuntimeError(f"OpenAI returned an empty {label} response.")
            print(
                f"[translation-openai] {label}_done response_chars={len(text)}",
                flush=True,
            )
            return text

        def model_call(prompt: str) -> str:
            return call_openai(
                prompt,
                "You are a precise technical translation engine. Follow the user prompt strictly.",
                "translation",
            )

        compressed_guide = ""
        if guide_compression_enabled():
            flow_root = Path(__file__).resolve().parents[1]
            guide_paths = parse_guide_paths(os.getenv("ECL_GUIDE_DOCS"), base_dir=flow_root)
            max_chars = env_int("ECL_GUIDE_CONTEXT_MAX_CHARS", 1200)
            source_excerpt_chars = env_int("ECL_GUIDE_SOURCE_EXCERPT_CHARS", 2500)
            compression_model = os.getenv("ECL_GUIDE_COMPRESSION_MODEL", self.model)

            def compression_model_call(prompt: str) -> str:
                return call_openai(
                    prompt,
                    "You compress translation guidance for a downstream technical translation prompt.",
                    "guide_compression",
                    model=compression_model,
                )

            compressed_guide = build_compressed_guide(
                source_markdown=request.source_markdown,
                guide_paths=guide_paths,
                model_call=compression_model_call,
                max_chars=max_chars,
                source_excerpt_chars=source_excerpt_chars,
            )

        return translate_markdown_with_ecl(
            source_markdown=request.source_markdown,
            core_rules=core_rules,
            target_language=target_language,
            model_call=model_call,
            compressed_guide=compressed_guide,
        )


FALLBACK_TRANSLATION_PROMPT = """You are translating Hugging Face technical blog posts into Korean.

Output Korean Markdown only. Preserve source meaning, Markdown structure, links,
images, tables, and code blocks. Do not translate code, identifiers, model
names, API names, package names, commands, or URLs. Write natural Korean for
technical readers. Do not add commentary or a preface.
"""


def default_prompt_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "translation_prompt.md"


def load_translation_prompt(prompt_path: Path) -> str:
    if prompt_path.exists():
        return prompt_path.read_text().strip()
    return FALLBACK_TRANSLATION_PROMPT.strip()


def locale_to_language(locale: str) -> str:
    normalized = locale.strip().lower()
    if normalized in {"ko", "ko-kr"}:
        return "Korean"
    if normalized in {"en", "en-us"}:
        return "English"
    return locale


def env_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw.strip())
    except ValueError:
        return default
    return max(minimum, value)


def guide_compression_enabled() -> bool:
    value = os.getenv("ECL_GUIDE_COMPRESSION", "llm").strip().lower()
    if value in {"0", "false", "no", "off", "none", "disabled"}:
        return False
    return value in {"1", "true", "yes", "on", "llm"}


def get_translation_adapter(
    name: str,
    model: Optional[str] = None,
    prompt_path: Optional[Path] = None,
) -> TranslationAdapter:
    normalized = name.strip().lower()
    if normalized == "openai":
        return OpenAITranslationAdapter(model=model, prompt_path=prompt_path)
    if normalized in {"none", "placeholder"}:
        return PlaceholderTranslationAdapter()
    raise ValueError(f"Unknown translator adapter: {name}. Supported: openai, none")
