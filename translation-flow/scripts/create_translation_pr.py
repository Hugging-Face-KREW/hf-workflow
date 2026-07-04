from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import textwrap
import urllib.request
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable, Optional
from zoneinfo import ZoneInfo

try:
    from scripts.translation_adapters import TranslationRequest, get_translation_adapter
except ModuleNotFoundError:
    from translation_adapters import TranslationRequest, get_translation_adapter


DEFAULT_FEED_URL = "https://huggingface.co/blog/feed.xml"
DEFAULT_BLOG_ORIGIN = "https://huggingface.co"
DEFAULT_LOCALE = "ko"
HEADING_RE = re.compile(r"^(?P<marks>#{1,6})\s+(?P<text>.+?)\s*$")
EXPLICIT_HEADING_ID_RE = re.compile(
    r"^(?P<title>.*?)(?:\s+\{:\s*#(?P<id1>[A-Za-z0-9_-]+)\s*\}|\s+\{#(?P<id2>[A-Za-z0-9_-]+)\})\s*$"
)
FENCE_START_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
STANDALONE_HEADING_ID_RE = re.compile(r"^\s*\{(?::\s*)?#(?P<id>[A-Za-z0-9_-]+)\s*\}\s*$")
AUTHOR_ITEM_RE = re.compile(r"^\s*-\s*(?P<value>.+?)\s*$")
ATX_HEADING_RE = re.compile(r"^#{1,6}\s+\S")
SETEXT_HEADING_RE = re.compile(r"^(?:=+|-+)\s*$")
TABLE_SEPARATOR_RE = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$"
)
TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")


@dataclass(frozen=True)
class FeedPost:
    title: str
    url: str
    published_at: datetime
    slug: str
    summary: str = ""

    @property
    def published_date(self) -> date:
        return self.published_at.date()


@dataclass(frozen=True)
class SourceFrontmatter:
    title: str = ""
    published_at: Optional[datetime] = None
    thumbnail: str = ""
    image: str = ""
    authors: tuple[str, ...] = ()


class SourceMarkdownUnavailableError(RuntimeError):
    pass


class SourceMarkdownSkipError(SourceMarkdownUnavailableError):
    def __init__(self, reason: str, attempted_urls: list[str]):
        self.reason = reason
        attempted = ", ".join(attempted_urls) if attempted_urls else "(no markdown candidates discovered)"
        if reason == "community_article":
            message = (
                "Could not fetch source markdown from raw URLs for a Community Article. "
                "Skipping this post by policy. "
                f"Attempted: {attempted}"
            )
        elif reason == "enterprise_article":
            message = (
                "Could not fetch source markdown from raw URLs for an Enterprise Article. "
                "Skipping this post by policy. "
                f"Attempted: {attempted}"
            )
        else:
            message = (
                "Could not fetch source markdown from raw URLs. "
                "Skipping this post by policy. "
                f"Attempted: {attempted}"
            )
        super().__init__(message)


def log(message: str) -> None:
    print(f"[translation-flow] {message}", flush=True)


def run_cmd(
    args: list[str],
    cwd: Optional[Path] = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        command = " ".join(args)
        raise RuntimeError(
            f"Command failed: {command}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "translation-flow/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def fetch_binary(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "translation-flow/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(node: ET.Element, names: Iterable[str]) -> str:
    wanted = set(names)
    for child in list(node):
        if local_name(child.tag) in wanted and child.text:
            return html.unescape(child.text.strip())
    return ""


def atom_link(node: ET.Element) -> str:
    for child in list(node):
        if local_name(child.tag) != "link":
            continue
        href = child.attrib.get("href")
        rel = child.attrib.get("rel", "alternate")
        if href and rel == "alternate":
            return href.strip()
    return ""


def parse_datetime(raw: str) -> datetime:
    raw = raw.strip()
    if not raw:
        raise ValueError("missing published date")
    try:
        parsed = parsedate_to_datetime(raw)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (TypeError, ValueError):
        pass
    normalized = raw.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def slug_from_url(url: str) -> str:
    clean = url.split("?", 1)[0].rstrip("/")
    slug = clean.rsplit("/", 1)[-1]
    return slugify(slug)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9가-힣]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "post"


def parse_feed(xml_text: str) -> list[FeedPost]:
    root = ET.fromstring(xml_text)
    posts: list[FeedPost] = []

    for item in root.iter():
        name = local_name(item.tag)
        if name not in {"item", "entry"}:
            continue

        title = child_text(item, ["title"])
        url = child_text(item, ["link"]) or atom_link(item)
        raw_date = child_text(item, ["pubDate", "published", "updated"])
        summary = child_text(item, ["description", "summary"])

        if not title or not url or not raw_date:
            continue

        posts.append(
            FeedPost(
                title=title,
                url=url,
                published_at=parse_datetime(raw_date),
                slug=slug_from_url(url),
                summary=summary,
            )
        )

    return posts


def select_posts(
    posts: list[FeedPost],
    target_date: date,
    post_url: Optional[str],
    local_tz: ZoneInfo,
) -> list[FeedPost]:
    if post_url:
        selected = [post for post in posts if post.url.rstrip("/") == post_url.rstrip("/")]
        if not selected:
            raise RuntimeError(f"No RSS post matched --post-url {post_url}")
        return selected
    return [post for post in posts if post.published_at.astimezone(local_tz).date() == target_date]


def build_translation_markdown(
    post: FeedPost,
    translated_markdown: str,
    translator_name: str,
    source_url: str,
    source_frontmatter: Optional[SourceFrontmatter] = None,
) -> str:
    translated_markdown = translated_markdown.strip()
    title = first_markdown_heading(translated_markdown) or post.title
    passthrough_lines = render_source_frontmatter_lines(source_frontmatter)
    passthrough_block = ""
    if passthrough_lines:
        passthrough_block = "\n".join(passthrough_lines) + "\n"

    body = f"""---
layout: post
title: "{escape_yaml_string(title)}"
author: dailybot
categories: [Translation, HuggingFace]
{passthrough_block}slug: "{post.slug}"
source_url: "{post.url}"
source_published_date: "{post.published_date.isoformat()}"
source_published_at: "{post.published_at.isoformat()}"
locale: "ko"
translation_status: "draft"
translator: "{translator_name}"
---

* TOC
{{:toc}}
<!--toc-->
_이 글은 Hugging Face 블로그의 [{post.title}]({source_url})를 한국어로 번역한 글입니다._

<!-- Source: {post.url} -->

---

<!--
Review instructions:
- Verify the Korean translation against the source post.
- Preserve technical meaning, code blocks, links, headings, model names, API names, and product names.
-->

{translated_markdown}
"""
    return body


def render_source_frontmatter_lines(source_frontmatter: Optional[SourceFrontmatter]) -> list[str]:
    if source_frontmatter is None:
        return []
    lines: list[str] = []
    if source_frontmatter.image:
        lines.append(f"image: {source_frontmatter.image}")
    if source_frontmatter.authors:
        lines.append("authors:")
        lines.extend(f"  - {author}" for author in source_frontmatter.authors)
    return lines


def normalize_thumbnail_url(thumbnail: str) -> str:
    value = unquote_yaml_scalar(thumbnail.strip())
    if not value:
        return value
    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        return value
    if value.startswith("/"):
        return f"{DEFAULT_BLOG_ORIGIN}{value}"
    return value


def thumbnail_asset_extension(thumbnail_url: str) -> str:
    path = urlparse(thumbnail_url).path
    suffix = Path(path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return suffix
    return ".png"


def thumbnail_asset_repo_path(post: FeedPost, thumbnail_url: str) -> str:
    asset_dir = f"{post.published_date.isoformat()}-{post.slug}"
    return str(
        Path("assets")
        / "images"
        / "blog"
        / "posts"
        / asset_dir
        / f"thumbnail{thumbnail_asset_extension(thumbnail_url)}"
    )


def prepare_thumbnail_asset(
    target_worktree: Path,
    post: FeedPost,
    source_frontmatter: SourceFrontmatter,
) -> tuple[SourceFrontmatter, str]:
    if not source_frontmatter.thumbnail:
        return source_frontmatter, ""

    source_url = normalize_thumbnail_url(source_frontmatter.thumbnail)
    repo_path = thumbnail_asset_repo_path(post, source_url)
    output_path = target_worktree / repo_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(fetch_binary(source_url))
    log(f"Wrote thumbnail asset: {output_path}")

    return (
        SourceFrontmatter(
            title=source_frontmatter.title,
            published_at=source_frontmatter.published_at,
            thumbnail=source_frontmatter.thumbnail,
            image=repo_path,
            authors=source_frontmatter.authors,
        ),
        repo_path,
    )


def unquote_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
        return value[1:-1]
    return value


def split_source_frontmatter(markdown: str) -> tuple[SourceFrontmatter, str]:
    normalized = markdown.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith("---\n"):
        return SourceFrontmatter(), normalized.strip()
    end = normalized.find("\n---\n", 4)
    if end == -1:
        return SourceFrontmatter(), normalized.strip()

    block = normalized[4:end]
    body = normalized[end + 5 :].strip()

    title = ""
    published_at: Optional[datetime] = None
    thumbnail = ""
    authors: list[str] = []
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if line.startswith("title:"):
            title = unquote_yaml_scalar(line.split(":", 1)[1].strip())
            i += 1
            continue
        if line.startswith("date:") or line.startswith("published:") or line.startswith("published_at:"):
            published_raw = unquote_yaml_scalar(line.split(":", 1)[1].strip())
            if published_raw and published_at is None:
                try:
                    published_at = parse_datetime(published_raw)
                except ValueError:
                    pass
            i += 1
            continue
        if line.startswith("thumbnail:"):
            thumbnail = line.split(":", 1)[1].strip()
            i += 1
            continue
        if stripped == "authors:":
            i += 1
            while i < len(lines):
                item_line = lines[i]
                item_match = AUTHOR_ITEM_RE.match(item_line)
                if item_match:
                    authors.append(item_match.group("value").strip())
                    i += 1
                    continue
                if not item_line.strip():
                    i += 1
                    continue
                break
            continue
        i += 1

    return SourceFrontmatter(
        title=title,
        published_at=published_at,
        thumbnail=thumbnail,
        authors=tuple(authors),
    ), body


def resolve_published_at_from_feed(post_url: str, feed_url: str) -> Optional[datetime]:
    post = resolve_feed_post_by_url(post_url, feed_url)
    if post is None:
        return None
    return post.published_at


def resolve_feed_post_by_url(post_url: str, feed_url: str) -> Optional[FeedPost]:
    try:
        posts = parse_feed(fetch_text(feed_url))
    except Exception as exc:
        log(f"Feed fallback lookup failed for --post-url metadata: {exc}")
        return None
    normalized_url = post_url.rstrip("/")
    for post in posts:
        if post.url.rstrip("/") == normalized_url:
            return post
    return None


def classify_source_unavailable_reason(post_url: str, source_html: str, feed_url: str) -> Optional[str]:
    if "Community Article" in source_html:
        return "community_article"
    if resolve_feed_post_by_url(post_url, feed_url) is not None:
        return "enterprise_article"
    return None


def resolve_post_from_source(post_url: str, allow_html_fallback: bool, feed_url: str = DEFAULT_FEED_URL) -> FeedPost:
    source_html = fetch_text(post_url)
    source_markdown_raw = extract_source_markdown(
        post_url,
        source_html,
        allow_html_fallback=allow_html_fallback,
        feed_url=feed_url,
    )
    source_frontmatter, _ = split_source_frontmatter(source_markdown_raw)
    if not source_frontmatter.title:
        raise RuntimeError(
            "Missing `title` in source markdown frontmatter for --post-url mode: "
            f"{post_url}"
        )
    published_at = source_frontmatter.published_at
    if published_at is None:
        published_at = resolve_published_at_from_feed(post_url, feed_url)
        if published_at is not None:
            log("Recovered `published_at` from RSS feed for --post-url mode.")
    if published_at is None:
        raise RuntimeError(
            "Missing `date`/`published` in source markdown frontmatter for --post-url mode: "
            f"{post_url}"
        )
    return FeedPost(
        title=source_frontmatter.title,
        url=post_url,
        published_at=published_at,
        slug=slug_from_url(post_url),
        summary="",
    )

def normalize_escaped_newlines(markdown: str) -> str:
    escaped_count = markdown.count("\\n")
    if escaped_count < 3 and "\\r\\n" not in markdown:
        return markdown

    lines = markdown.splitlines(keepends=True)
    out: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0

    for line in lines:
        fence_match = FENCE_START_RE.match(line)
        if fence_match:
            candidate = fence_match.group("fence")
            candidate_char = candidate[0]
            candidate_len = len(candidate)
            if in_fence:
                stripped = line.lstrip(" \t")
                if stripped.startswith(fence_char * fence_len):
                    tail = stripped[fence_len:].strip()
                    if not tail or set(tail) == {fence_char}:
                        in_fence = False
                        fence_char = ""
                        fence_len = 0
                out.append(line)
                continue
            in_fence = True
            fence_char = candidate_char
            fence_len = candidate_len
            out.append(line)
            continue

        if in_fence:
            out.append(line)
            continue

        out.append(line.replace("\\r\\n", "\n").replace("\\n", "\n"))

    normalized = "".join(out)
    if normalized != markdown:
        log(f"Normalized escaped newlines in translated markdown (count={escaped_count}).")
    return normalized


def split_heading_text_and_id(text: str) -> tuple[str, Optional[str]]:
    match = EXPLICIT_HEADING_ID_RE.match(text.strip())
    if not match:
        return text.strip(), None
    heading_id = match.group("id1") or match.group("id2")
    return match.group("title").strip(), heading_id


def is_toc_heading(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return normalized == "목차" or "table of contents" in normalized


def stabilize_manual_toc(markdown: str) -> str:
    lines = markdown.splitlines()
    if not lines:
        return markdown

    rebuilt_lines: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0
    heading_rows: list[tuple[int, str, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        fence_match = FENCE_START_RE.match(line)
        if fence_match:
            candidate_fence = fence_match.group("fence")
            candidate_char = candidate_fence[0]
            candidate_len = len(candidate_fence)
            if in_fence:
                stripped = line.lstrip(" \t")
                if stripped.startswith(fence_char * fence_len):
                    tail = stripped[fence_len:].strip()
                    if not tail or set(tail) == {fence_char}:
                        in_fence = False
                        fence_char = ""
                        fence_len = 0
                rebuilt_lines.append(line)
                i += 1
                continue
            in_fence = True
            fence_char = candidate_char
            fence_len = candidate_len
            rebuilt_lines.append(line)
            i += 1
            continue

        if in_fence:
            rebuilt_lines.append(line)
            i += 1
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match and heading_match.group("marks") == "##":
            heading_text, heading_id = split_heading_text_and_id(heading_match.group("text"))
            heading_text = heading_text.replace("\\n", " ").strip()
            if not heading_id and i + 1 < len(lines):
                standalone_match = STANDALONE_HEADING_ID_RE.match(lines[i + 1])
                if standalone_match:
                    heading_id = standalone_match.group("id")
                    i += 1
            if not heading_id:
                heading_id = f"section-{len(heading_rows) + 1}"
            rebuilt_line = f"## {heading_text} {{#{heading_id}}}"
            rebuilt_lines.append(rebuilt_line)
            heading_rows.append((len(rebuilt_lines) - 1, heading_text, heading_id))
            i += 1
            continue

        rebuilt_lines.append(line)
        i += 1

    if not heading_rows:
        return "\n".join(rebuilt_lines).strip() + "\n"

    toc_heading_rows = [row for row in heading_rows if is_toc_heading(row[1])]
    toc_entries = [
        f"[{text}](#{heading_id})"
        for line_idx, text, heading_id in heading_rows
        if (line_idx, text, heading_id) not in toc_heading_rows
    ]
    rebuilt_toc = "이 글에서: " + " · ".join(toc_entries)

    # If the translated body has an explicit "Table of Contents" section,
    # rewrite its list links to stable section IDs generated above.
    if toc_heading_rows:
        toc_line_idx = toc_heading_rows[0][0]
        toc_section_targets = [
            (text, heading_id) for line_idx, text, heading_id in heading_rows if line_idx > toc_line_idx
        ]
        if toc_section_targets:
            next_h2_idx = next(
                (line_idx for line_idx, _, _ in heading_rows if line_idx > toc_line_idx),
                len(rebuilt_lines),
            )
            toc_block = [""] + [f"* [{text}](#{heading_id})" for text, heading_id in toc_section_targets] + [""]
            rebuilt_lines = rebuilt_lines[: toc_line_idx + 1] + toc_block + rebuilt_lines[next_h2_idx:]

    in_fence = False
    fence_char = ""
    fence_len = 0
    for idx, line in enumerate(rebuilt_lines):
        fence_match = FENCE_START_RE.match(line)
        if fence_match:
            candidate_fence = fence_match.group("fence")
            candidate_char = candidate_fence[0]
            candidate_len = len(candidate_fence)
            if in_fence:
                stripped = line.lstrip(" \t")
                if stripped.startswith(fence_char * fence_len):
                    tail = stripped[fence_len:].strip()
                    if not tail or set(tail) == {fence_char}:
                        in_fence = False
                        fence_char = ""
                        fence_len = 0
                continue
            in_fence = True
            fence_char = candidate_char
            fence_len = candidate_len
            continue
        if in_fence:
            continue

        stripped = line.strip()
        if stripped.startswith("이 글에서:") or stripped.startswith("In this post:"):
            rebuilt_lines[idx] = rebuilt_toc
            break

    return "\n".join(rebuilt_lines).strip() + "\n"


def first_markdown_heading(markdown: str) -> str:
    for line in markdown.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1)
    return ""


def escape_yaml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def html_to_markdown(source_html: str) -> str:
    try:
        return html_to_markdown_with_bs4(source_html)
    except ImportError:
        pass

    source_html = re.sub(r"(?is)<script.*?</script>", " ", source_html)
    source_html = re.sub(r"(?is)<style.*?</style>", " ", source_html)
    source_html = select_article_html(source_html)
    source_html = re.sub(r"(?is)<pre[^>]*><code[^>]*>(.*?)</code></pre>", code_block, source_html)
    source_html = re.sub(r"(?is)<pre[^>]*>(.*?)</pre>", code_block, source_html)
    source_html = re.sub(r"(?is)<h1[^>]*>(.*?)</h1>", lambda m: "\n# " + clean_inline(m.group(1)) + "\n\n", source_html)
    source_html = re.sub(r"(?is)<h2[^>]*>(.*?)</h2>", lambda m: "\n## " + clean_inline(m.group(1)) + "\n\n", source_html)
    source_html = re.sub(r"(?is)<h3[^>]*>(.*?)</h3>", lambda m: "\n### " + clean_inline(m.group(1)) + "\n\n", source_html)
    source_html = re.sub(r"(?is)<h4[^>]*>(.*?)</h4>", lambda m: "\n#### " + clean_inline(m.group(1)) + "\n\n", source_html)
    source_html = re.sub(r"(?is)<li[^>]*>(.*?)</li>", lambda m: "\n- " + clean_inline(m.group(1)), source_html)
    source_html = re.sub(r"(?is)<p[^>]*>(.*?)</p>", lambda m: "\n" + clean_inline(m.group(1)) + "\n", source_html)
    source_html = re.sub(r"(?is)<br\s*/?>", "\n", source_html)
    text = re.sub(r"(?s)<[^>]+>", " ", source_html)
    text = html.unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text


def html_to_markdown_with_bs4(source_html: str) -> str:
    from bs4 import BeautifulSoup
    from bs4.element import NavigableString, Tag

    soup = BeautifulSoup(source_html, "html.parser")
    container = soup.select_one(".blog-content") or soup.find("article") or soup.find("main") or soup

    for node in container.select("script, style, svg, .not-prose, .SVELTE_HYDRATER"):
        node.decompose()

    blocks: list[str] = []
    for node in container.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre"]):
        if not isinstance(node, Tag):
            continue
        if any(parent.name in {"p", "li", "pre"} for parent in node.parents if parent is not container):
            continue
        if node.name == "pre":
            code_node = node.find("code")
            code = code_node.get_text() if isinstance(code_node, Tag) else node.get_text()
            code = code.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
            if code:
                blocks.append(f"```\n{code}\n```")
            continue
        text = inline_markdown(node).strip()
        if not text or text == "Back to Articles":
            continue
        if node.name and re.fullmatch(r"h[1-4]", node.name):
            level = int(node.name[1])
            blocks.append(f"{'#' * level} {text}")
        elif node.name == "li":
            blocks.append(f"- {text}")
        else:
            blocks.append(text)

    return "\n\n".join(blocks).strip()


def inline_markdown(node: object) -> str:
    from bs4.element import NavigableString, Tag

    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag):
        return ""
    if node.name == "code":
        return "`" + node.get_text().strip() + "`"
    if node.name == "a":
        href = node.get("href")
        text = "".join(inline_markdown(child) for child in node.children).strip()
        if href and text:
            return f"[{text}]({href})"
        return text
    if node.name in {"script", "style", "svg"}:
        return ""
    text = "".join(inline_markdown(child) for child in node.children)
    text = re.sub(r"\[\[\d+\]\]", "", text)
    return re.sub(r"[ \t\r\f\v]+", " ", html.unescape(text))


def select_article_html(source_html: str) -> str:
    patterns = [
        r"(?is)<article[^>]*>(.*?)</article>",
        r"(?is)<main[^>]*>(.*?)</main>",
    ]
    for pattern in patterns:
        match = re.search(pattern, source_html)
        if match:
            return match.group(1)
    return source_html


def clean_inline(value: str) -> str:
    value = re.sub(r"(?is)<code[^>]*>(.*?)</code>", lambda m: "`" + html.unescape(m.group(1).strip()) + "`", value)
    value = re.sub(
        r"(?is)<a[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        lambda m: f"[{clean_inline(m.group(2))}]({html.unescape(m.group(1))})",
        value,
    )
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def code_block(match: re.Match[str]) -> str:
    code = html.unescape(re.sub(r"(?s)<[^>]+>", "", match.group(1))).strip("\n")
    return f"\n\n```\n{code}\n```\n\n"


def github_blob_to_raw(url: str) -> Optional[str]:
    match = re.match(r"^https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$", url.strip())
    if not match:
        return None
    owner, repo, ref, path = match.groups()
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"


def discover_markdown_urls(post_url: str, source_html: str) -> list[str]:
    candidates: list[str] = []
    parsed = urlparse(post_url)
    path_parts = [part for part in parsed.path.split("/") if part]
    if path_parts[:1] == ["blog"] and len(path_parts) >= 2:
        slug = path_parts[-1]
        if len(path_parts) >= 3:
            org = path_parts[-2]
            candidates.append(f"https://raw.githubusercontent.com/huggingface/blog/main/{org}/{slug}.md")
        candidates.append(f"https://raw.githubusercontent.com/huggingface/blog/main/{slug}.md")

    for match in re.finditer(r'https://github\.com/huggingface/blog/blob/main/[^"\'<> ]+\.md', source_html):
        raw_url = github_blob_to_raw(match.group(0))
        if raw_url:
            candidates.append(raw_url)

    seen: set[str] = set()
    unique: list[str] = []
    for url in candidates:
        if url in seen:
            continue
        seen.add(url)
        unique.append(url)
    return unique


def looks_like_markdown(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if stripped.startswith("---\n") and "\n---\n" in stripped:
        return True
    if any(ATX_HEADING_RE.match(line.strip()) for line in stripped.splitlines()):
        return True
    if any(SETEXT_HEADING_RE.match(line.strip()) for line in stripped.splitlines()):
        return True
    if any(TABLE_ROW_RE.match(line) for line in stripped.splitlines()):
        return True
    if any(line.lstrip().startswith(("- ", "* ", "+ ")) for line in stripped.splitlines()):
        return True
    return "```" in stripped and "\n" in stripped


def extract_source_markdown(
    post_url: str,
    source_html: str,
    allow_html_fallback: bool = False,
    feed_url: str = DEFAULT_FEED_URL,
) -> str:
    attempted_urls: list[str] = []
    for url in discover_markdown_urls(post_url, source_html):
        attempted_urls.append(url)
        try:
            fetched = fetch_text(url)
        except Exception as exc:
            log(f"Source markdown fetch failed: {url} ({exc})")
            continue
        if looks_like_markdown(fetched):
            log(f"Using source markdown: {url}")
            return fetched.strip()
        log(f"Ignoring markdown candidate with unexpected shape: {url}")

    if allow_html_fallback:
        log("Source markdown not found. Falling back to HTML extraction due to --allow-html-fallback.")
        return html_to_markdown(source_html)

    skip_reason = classify_source_unavailable_reason(post_url, source_html, feed_url)
    if skip_reason is not None:
        raise SourceMarkdownSkipError(skip_reason, attempted_urls)

    attempted = ", ".join(attempted_urls) if attempted_urls else "(no markdown candidates discovered)"
    raise SourceMarkdownUnavailableError(
        "Could not fetch source markdown from raw URLs. "
        "Run again with --allow-html-fallback if you want HTML extraction. "
        f"Attempted: {attempted}"
    )


def _iter_non_fence_lines(markdown: str) -> list[str]:
    lines = markdown.splitlines()
    kept: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0

    for line in lines:
        fence_match = FENCE_START_RE.match(line)
        if fence_match:
            candidate_fence = fence_match.group("fence")
            candidate_char = candidate_fence[0]
            candidate_len = len(candidate_fence)
            if in_fence:
                stripped = line.lstrip(" \t")
                if stripped.startswith(fence_char * fence_len):
                    tail = stripped[fence_len:].strip()
                    if not tail or set(tail) == {fence_char}:
                        in_fence = False
                        fence_char = ""
                        fence_len = 0
                continue
            in_fence = True
            fence_char = candidate_char
            fence_len = candidate_len
            continue

        if in_fence:
            continue
        kept.append(line)
    return kept


def count_fenced_code_blocks(markdown: str) -> int:
    lines = markdown.splitlines()
    count = 0
    in_fence = False
    fence_char = ""
    fence_len = 0

    for line in lines:
        fence_match = FENCE_START_RE.match(line)
        if not fence_match:
            continue

        candidate_fence = fence_match.group("fence")
        candidate_char = candidate_fence[0]
        candidate_len = len(candidate_fence)
        if in_fence:
            stripped = line.lstrip(" \t")
            if stripped.startswith(fence_char * fence_len):
                tail = stripped[fence_len:].strip()
                if not tail or set(tail) == {fence_char}:
                    in_fence = False
                    fence_char = ""
                    fence_len = 0
            continue

        in_fence = True
        fence_char = candidate_char
        fence_len = candidate_len
        count += 1

    return count


def count_markdown_tables(markdown: str) -> int:
    lines = _iter_non_fence_lines(markdown)
    table_count = 0
    for i, line in enumerate(lines):
        if not TABLE_SEPARATOR_RE.match(line):
            continue
        prev_line = lines[i - 1] if i > 0 else ""
        if TABLE_ROW_RE.match(prev_line):
            table_count += 1
    return table_count


def count_markdown_images(markdown: str) -> int:
    content = "\n".join(_iter_non_fence_lines(markdown))
    return len(IMAGE_RE.findall(content))


def enforce_structure_preservation(source_markdown: str, translated_markdown: str) -> None:
    metrics = {
        "tables": (count_markdown_tables(source_markdown), count_markdown_tables(translated_markdown)),
        "images": (count_markdown_images(source_markdown), count_markdown_images(translated_markdown)),
        "code_blocks": (
            count_fenced_code_blocks(source_markdown),
            count_fenced_code_blocks(translated_markdown),
        ),
    }
    regressions = [
        f"{name}:{translated_count}<{source_count}"
        for name, (source_count, translated_count) in metrics.items()
        if translated_count < source_count
    ]
    if regressions:
        raise RuntimeError(
            "Translated markdown lost structural elements: "
            + ", ".join(regressions)
        )


def infer_github_repo(worktree: Path) -> str:
    result = run_cmd(["git", "remote", "get-url", "origin"], cwd=worktree)
    remote = result.stdout.strip()
    match = re.search(r"github\.com[:/](?P<repo>[^/]+/[^/.]+)(?:\.git)?$", remote)
    if not match:
        raise RuntimeError(f"Could not infer GitHub repo from origin remote: {remote}")
    return match.group("repo")


def create_manifest(
    post: FeedPost,
    feed_url: str,
    target_repo: str,
    branch: str,
    file_path: str,
    pr_url: str,
    target_date: date,
    manifest_path: Path,
) -> None:
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    content = f"""version: 1

run:
  id: {target_date.isoformat()}-{post.slug}
  created_at: {created_at}
  target_date: {target_date.isoformat()}

source:
  feed_url: {feed_url}
  url: {post.url}
  slug: {post.slug}
  title: "{escape_yaml_string(post.title)}"
  published_date: {post.published_date.isoformat()}
  published_at: {post.published_at.isoformat()}
  language: en

translation:
  target_repo: {target_repo}
  branch: {branch}
  file_path: {file_path}
  pr_url: {pr_url}
  locale: {DEFAULT_LOCALE}

handoff:
  seo:
    enabled: true
    primary_keyword: ""
    secondary_keywords: []
  quality:
    enabled: true
    checks:
      - fidelity
      - fluency
      - terminology
      - formatting
      - links
"""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(content)


def ensure_clean_worktree(worktree: Path) -> None:
    result = run_cmd(["git", "status", "--porcelain"], cwd=worktree)
    if result.stdout.strip():
        raise RuntimeError(
            f"Target worktree has uncommitted changes. Commit or stash them first: {worktree}"
        )


def ensure_no_tracked_changes(worktree: Path) -> None:
    result = run_cmd(["git", "status", "--porcelain"], cwd=worktree)
    tracked_changes = [
        line for line in result.stdout.splitlines()
        if line and not line.startswith("?? ")
    ]
    if tracked_changes:
        raise RuntimeError(
            f"Target worktree has tracked uncommitted changes. Commit or stash them first: {worktree}"
        )


def create_branch(worktree: Path, branch: str) -> None:
    existing = run_cmd(["git", "rev-parse", "--verify", branch], cwd=worktree, check=False)
    if existing.returncode == 0:
        run_cmd(["git", "switch", branch], cwd=worktree)
    else:
        run_cmd(["git", "switch", "-c", branch], cwd=worktree)


def create_or_update_branch(worktree: Path, branch: str, base_branch: str) -> None:
    remote_ref = f"origin/{branch}"
    fetch = run_cmd(
        ["git", "fetch", "origin", f"{branch}:refs/remotes/{remote_ref}"],
        cwd=worktree,
        check=False,
    )
    if fetch.returncode == 0:
        existing = run_cmd(["git", "rev-parse", "--verify", branch], cwd=worktree, check=False)
        if existing.returncode == 0:
            run_cmd(["git", "switch", branch], cwd=worktree)
            run_cmd(["git", "merge", "--ff-only", remote_ref], cwd=worktree)
        else:
            run_cmd(["git", "switch", "-c", branch, "--track", remote_ref], cwd=worktree)
        return

    run_cmd(["git", "switch", base_branch], cwd=worktree)
    create_branch(worktree, branch)


def current_branch(worktree: Path) -> str:
    return run_cmd(["git", "branch", "--show-current"], cwd=worktree).stdout.strip()


def commit_paths(worktree: Path, file_paths: list[str], message: str) -> None:
    if not file_paths:
        return
    run_cmd(["git", "add", *file_paths], cwd=worktree)
    diff = run_cmd(["git", "diff", "--cached", "--quiet"], cwd=worktree, check=False)
    if diff.returncode == 0:
        log("No staged changes to commit.")
        return
    run_cmd(["git", "commit", "-m", message], cwd=worktree)


def commit_file(worktree: Path, file_path: str, message: str) -> None:
    commit_paths(worktree, [file_path], message)


def create_pr(
    worktree: Path,
    branch: str,
    title: str,
    body: str,
    push: bool,
    open_pr: bool,
) -> str:
    if push:
        run_cmd(["git", "push", "-u", "origin", branch], cwd=worktree)
    if not open_pr:
        return ""

    existing = run_cmd(
        ["gh", "pr", "view", branch, "--json", "url", "-q", ".url"],
        cwd=worktree,
        check=False,
    )
    if existing.returncode == 0 and existing.stdout.strip():
        return existing.stdout.strip()

    result = run_cmd(
        [
            "gh",
            "pr",
            "create",
            "--title",
            title,
            "--body",
            body,
            "--label",
            "hf-agent:managed",
        ],
        cwd=worktree,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create PR with gh:\n{result.stderr}")
    return result.stdout.strip()


def default_manifest_path(post: FeedPost, target_date: date) -> Path:
    return Path("manifests") / f"{target_date.isoformat()}-{post.slug}.yaml"


def default_translation_file_path(posts_dir: str, post: FeedPost, target_date: date) -> str:
    return str(Path(posts_dir) / f"{target_date.isoformat()}-{post.slug}.md")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create Korean translation work from Hugging Face Blog RSS posts."
    )
    parser.add_argument("--date", default=date.today().isoformat(), help="Target publish date.")
    parser.add_argument("--timezone", default="Asia/Seoul", help="Timezone used for --date matching.")
    parser.add_argument("--feed-url", default=DEFAULT_FEED_URL)
    parser.add_argument("--post-url", default=None, help="Select one post by URL instead of date.")
    parser.add_argument("--target-worktree", required=True, help="Local clone of the translation repo.")
    parser.add_argument("--target-repo", default=None, help="GitHub repo, e.g. owner/repo.")
    parser.add_argument("--posts-dir", default="_posts")
    parser.add_argument("--branch-prefix", default="translate")
    parser.add_argument("--output-manifest", default=None)
    parser.add_argument("--run-summary", default=None, help="Write JSON summary for GitHub Actions.")
    parser.add_argument(
        "--translator",
        default="openai",
        choices=["openai", "none", "placeholder"],
        help="Translation adapter to use. `openai` is the production path.",
    )
    parser.add_argument("--openai-model", default=None, help="Override OPENAI_MODEL for the OpenAI adapter.")
    parser.add_argument(
        "--translation-prompt",
        default=None,
        help="Path to the translation prompt used by adapter implementations.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print selected posts without writing files.")
    parser.add_argument("--skip-existing", action="store_true", help="Skip before API calls when target file exists.")
    parser.add_argument("--force", action="store_true", help="Overwrite target file if it already exists.")
    parser.add_argument(
        "--allow-untracked",
        action="store_true",
        help="Allow unrelated untracked files in the target worktree.",
    )
    parser.add_argument("--no-push", action="store_true", help="Do not push the branch.")
    parser.add_argument("--no-pr", action="store_true", help="Do not create a GitHub PR.")
    parser.add_argument(
        "--allow-html-fallback",
        action="store_true",
        help="Allow HTML extraction only when raw markdown fetch fails.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    local_tz = ZoneInfo(args.timezone)
    target_date = date.fromisoformat(args.date)
    target_worktree = Path(args.target_worktree).expanduser().resolve()
    if not target_worktree.exists():
        parser.error(f"--target-worktree does not exist: {target_worktree}")

    run_results: list[dict[str, str]] = []

    if args.post_url:
        log(f"Resolving source metadata for --post-url: {args.post_url}")
        try:
            selected = [
                resolve_post_from_source(
                    args.post_url,
                    allow_html_fallback=args.allow_html_fallback,
                    feed_url=args.feed_url,
                )
            ]
        except SourceMarkdownSkipError as exc:
            slug = slug_from_url(args.post_url)
            pseudo_post = FeedPost(
                title=slug,
                url=args.post_url,
                published_at=datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc),
                slug=slug,
            )
            file_path = default_translation_file_path(args.posts_dir, pseudo_post, target_date)
            manifest_path = (
                Path(args.output_manifest)
                if args.output_manifest
                else default_manifest_path(pseudo_post, target_date)
            )
            status = "skipped_community" if exc.reason == "community_article" else "skipped_enterprise"
            if exc.reason == "enterprise_article":
                log(f"Skipping Enterprise Article due to missing raw markdown: {args.post_url}")
            else:
                log(f"Skipping post-url target due to source policy: {exc}")
            run_results.append(
                {
                    "status": status,
                    "slug": slug,
                    "source_url": args.post_url,
                    "file_path": file_path,
                    "manifest_path": str(manifest_path),
                    "pr_url": "",
                }
            )
            if args.run_summary:
                summary_path = Path(args.run_summary)
                summary_path.parent.mkdir(parents=True, exist_ok=True)
                summary_path.write_text(json.dumps({"results": run_results}, indent=2))
                log(f"Wrote run summary: {summary_path}")
            return 0
    else:
        log(f"Fetching feed: {args.feed_url}")
        posts = parse_feed(fetch_text(args.feed_url))
        selected = select_posts(posts, target_date, None, local_tz)
    if not selected:
        log(f"No posts found for {target_date.isoformat()}.")
        if args.run_summary:
            summary_path = Path(args.run_summary)
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(json.dumps({"results": run_results}, indent=2))
            log(f"Wrote run summary: {summary_path}")
        return 0
    if len(selected) > 1 and args.output_manifest:
        parser.error("--output-manifest can only be used when one post is selected")

    target_repo = args.target_repo or infer_github_repo(target_worktree)
    base_branch = current_branch(target_worktree)
    if not base_branch:
        raise RuntimeError(f"Could not determine current branch in {target_worktree}")
    prompt_path = Path(args.translation_prompt) if args.translation_prompt else None
    translator = get_translation_adapter(args.translator, model=args.openai_model, prompt_path=prompt_path)

    for post in selected:
        branch = f"{args.branch_prefix}/{post.slug}"
        file_path = default_translation_file_path(args.posts_dir, post, target_date)
        manifest_path = Path(args.output_manifest) if args.output_manifest else default_manifest_path(post, target_date)

        log(f"Selected post: {post.title} ({post.url})")
        log(f"Target file: {target_worktree / file_path}")
        log(f"Manifest: {manifest_path}")
        if args.dry_run:
            run_results.append(
                {
                    "status": "dry_run",
                    "slug": post.slug,
                    "source_url": post.url,
                    "file_path": file_path,
                    "manifest_path": str(manifest_path),
                    "pr_url": "",
                }
            )
            continue

        if args.allow_untracked:
            ensure_no_tracked_changes(target_worktree)
        else:
            ensure_clean_worktree(target_worktree)
        full_path = target_worktree / file_path
        if full_path.exists() and not args.force:
            if args.skip_existing:
                log(f"Skipping existing translation before API call: {full_path}")
                run_results.append(
                    {
                        "status": "skipped_existing",
                        "slug": post.slug,
                        "source_url": post.url,
                        "file_path": file_path,
                        "manifest_path": str(manifest_path),
                        "pr_url": "",
                    }
                )
                continue
            raise RuntimeError(
                f"Translation file already exists: {full_path}. "
                "Use --skip-existing to skip or --force to overwrite."
            )

        source_html = fetch_text(post.url)
        try:
            source_markdown_raw = extract_source_markdown(
                post.url,
                source_html,
                allow_html_fallback=args.allow_html_fallback,
                feed_url=args.feed_url,
            )
        except SourceMarkdownSkipError as exc:
            status = "skipped_community" if exc.reason == "community_article" else "skipped_enterprise"
            if exc.reason == "enterprise_article":
                log(f"Skipping Enterprise Article due to missing raw markdown: {post.url}")
            else:
                log(f"Skipping post due to source policy: {post.url} ({exc.reason})")
            run_results.append(
                {
                    "status": status,
                    "slug": post.slug,
                    "source_url": post.url,
                    "file_path": file_path,
                    "manifest_path": str(manifest_path),
                    "pr_url": "",
                }
            )
            continue
        if not source_markdown_raw:
            raise RuntimeError(f"Could not extract source markdown from {post.url}")
        source_frontmatter, source_markdown = split_source_frontmatter(source_markdown_raw)
        if source_frontmatter.thumbnail or source_frontmatter.authors:
            log(
                "Captured source frontmatter for passthrough: "
                f"thumbnail={'yes' if source_frontmatter.thumbnail else 'no'}, "
                f"authors={len(source_frontmatter.authors)}"
            )
        log(f"Source markdown chars: {len(source_markdown)}")
        log(f"Translating with adapter: {translator.name}")

        run_cmd(["git", "switch", base_branch], cwd=target_worktree)
        create_or_update_branch(target_worktree, branch, base_branch)

        if full_path.exists() and not args.force:
            if args.skip_existing:
                log(f"Skipping existing translation on branch before API call: {full_path}")
                run_results.append(
                    {
                        "status": "skipped_existing",
                        "slug": post.slug,
                        "source_url": post.url,
                        "file_path": file_path,
                        "manifest_path": str(manifest_path),
                        "pr_url": "",
                    }
                )
                continue
            raise RuntimeError(
                f"Translation file already exists on branch {branch}: {full_path}. "
                "Use --skip-existing to skip or --force to overwrite."
            )

        translated_markdown = translator.translate(
            TranslationRequest(
                title=post.title,
                source_url=post.url,
                source_markdown=source_markdown,
                target_locale=DEFAULT_LOCALE,
            )
        )
        translated_markdown = normalize_escaped_newlines(translated_markdown)
        translated_markdown = stabilize_manual_toc(translated_markdown)
        enforce_structure_preservation(source_markdown, translated_markdown)
        log(f"Translated markdown chars: {len(translated_markdown)}")

        output_frontmatter = source_frontmatter
        thumbnail_file_path = ""
        if source_frontmatter.thumbnail:
            output_frontmatter, thumbnail_file_path = prepare_thumbnail_asset(
                target_worktree,
                post,
                source_frontmatter,
            )

        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(
            build_translation_markdown(
                post,
                translated_markdown,
                translator.name,
                post.url,
                source_frontmatter=output_frontmatter,
            )
        )
        log(f"Wrote translated file: {full_path}")

        commit_paths(
            target_worktree,
            [path for path in [file_path, thumbnail_file_path] if path],
            f"Add Korean translation draft for {post.slug}",
        )

        pr_title = f"Translate Hugging Face blog post: {post.title}"
        pr_body = textwrap.dedent(
            f"""\
            Source: {post.url}

            This PR adds a Korean translation draft for `{post.slug}`.

            Downstream handoff:
            - SEO review should use the translation-flow manifest.
            - Quality review should use the translation-flow manifest.
            """
        )
        pr_url = create_pr(
            target_worktree,
            branch,
            pr_title,
            pr_body,
            push=not args.no_push,
            open_pr=not args.no_pr,
        )
        create_manifest(
            post,
            args.feed_url,
            target_repo,
            branch,
            file_path,
            pr_url,
            target_date,
            manifest_path,
        )
        log(f"Wrote manifest: {manifest_path}")
        run_results.append(
            {
                "status": "created",
                "slug": post.slug,
                "source_url": post.url,
                "file_path": file_path,
                "manifest_path": str(manifest_path),
                "pr_url": pr_url,
            }
        )

    if args.run_summary:
        summary_path = Path(args.run_summary)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps({"results": run_results}, indent=2))
        log(f"Wrote run summary: {summary_path}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
