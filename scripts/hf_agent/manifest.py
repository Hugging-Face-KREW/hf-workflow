from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_FEED_URL = "https://huggingface.co/blog/feed.xml"
DEFAULT_LOCALE = "ko"


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def read_simple_manifest(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    parents_by_level: dict[int, str] = {}
    for raw_line in path.read_text().splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("- "):
            continue
        match = re.match(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)$", raw_line)
        if not match:
            continue
        indent = len(match.group("indent"))
        key = match.group("key")
        value = match.group("value").strip()
        level = indent // 2
        for stored_level in list(parents_by_level):
            if stored_level >= level:
                del parents_by_level[stored_level]

        parents = [parents_by_level[index] for index in range(level) if index in parents_by_level]
        dotted = ".".join([*parents, key])
        data[dotted] = value.strip('"')
        if value == "":
            parents_by_level[level] = key
    return data


def parse_frontmatter(markdown: str) -> dict[str, str]:
    if not markdown.startswith("---"):
        return {}
    end = markdown.find("\n---", 3)
    if end == -1:
        return {}
    frontmatter: dict[str, str] = {}
    for line in markdown[3:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"')
    return frontmatter


def slug_from_file_path(file_path: str) -> str:
    name = Path(file_path).stem
    match = re.match(r"^\d{4}-\d{2}-\d{2}-(.+)$", name)
    return match.group(1) if match else name


def date_from_file_path(file_path: str) -> str:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", Path(file_path).name)
    return match.group(1) if match else datetime.now(timezone.utc).date().isoformat()


def source_title_from_markdown(markdown: str, fallback: str) -> str:
    match = re.search(r"Hugging Face [^\[]*\[([^\]]+)\]\(", markdown)
    if match:
        return match.group(1).strip()
    return fallback.strip()


def choose_translation_file(pr_json: dict[str, Any], requested_file_path: str = "") -> str:
    if requested_file_path:
        return requested_file_path

    files = pr_json.get("files") or []
    paths: list[str] = []
    for item in files:
        path = item.get("path") if isinstance(item, dict) else str(item)
        if path.startswith("_posts/") and path.endswith(".md"):
            paths.append(path)

    if len(paths) == 1:
        return paths[0]
    if not paths:
        raise ValueError("No translated markdown file found in PR files.")
    raise ValueError(f"Multiple translated markdown files found: {', '.join(paths)}")


def build_manifest_text(
    *,
    pr_json: dict[str, Any],
    target_repo: str,
    file_path: str,
    markdown: str,
    feed_url: str = DEFAULT_FEED_URL,
) -> str:
    frontmatter = parse_frontmatter(markdown)
    pr_number = str(pr_json.get("number") or "")
    pr_url = str(pr_json.get("url") or "")
    branch = str(pr_json.get("headRefName") or "")
    pr_title = str(pr_json.get("title") or "")
    slug = frontmatter.get("slug") or slug_from_file_path(file_path)
    target_date = date_from_file_path(file_path)
    source_url = frontmatter.get("source_url", "")
    source_title = source_title_from_markdown(markdown, pr_title)
    source_published_date = frontmatter.get("source_published_date") or target_date
    source_published_at = frontmatter.get("source_published_at") or f"{source_published_date}T00:00:00+00:00"
    locale = frontmatter.get("locale") or DEFAULT_LOCALE
    run_id = f"pr-{pr_number}-{slug}" if pr_number else f"{target_date}-{slug}"
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")

    return f"""version: 1

run:
  id: {run_id}
  created_at: {created_at}
  target_date: {target_date}

source:
  feed_url: {feed_url}
  url: {source_url}
  slug: {slug}
  title: {yaml_quote(source_title)}
  published_date: {source_published_date}
  published_at: {source_published_at}
  language: en

translation:
  target_repo: {target_repo}
  branch: {branch}
  file_path: {file_path}
  pr_url: {pr_url}
  locale: {locale}

skills:
  seo:
    enabled: true
    config:
      primary_keyword: ""
      secondary_keywords: []
  quality:
    enabled: true
    config:
      checks:
        - fidelity
        - fluency
        - terminology
        - formatting
        - links
"""
