from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import textwrap
import urllib.request
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
DEFAULT_LOCALE = "ko"


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
) -> str:
    translated_markdown = translated_markdown.strip()
    title = first_markdown_heading(translated_markdown) or post.title

    body = f"""---
layout: post
title: "{escape_yaml_string(title)}"
author: dailybot
categories: [Translation, HuggingFace]
slug: "{post.slug}"
source_url: "{post.url}"
source_published_date: "{post.published_date.isoformat()}"
source_published_at: "{post.published_at.isoformat()}"
locale: "ko"
translation_status: "draft"
translator: "{translator_name}"
---

> Source: {post.url}

* TOC
{{:toc}}
<!--toc-->

_이 글은 Hugging Face 블로그의 [{post.title}]({source_url})를 한국어로 번역한 글입니다._

---

<!--
Review instructions:
- Verify the Korean translation against the source post.
- Preserve technical meaning, code blocks, links, headings, model names, API names, and product names.
-->

{translated_markdown}
"""
    return body


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
            code = node.get_text("\n").strip("\n")
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


def commit_file(worktree: Path, file_path: str, message: str) -> None:
    run_cmd(["git", "add", file_path], cwd=worktree)
    diff = run_cmd(["git", "diff", "--cached", "--quiet"], cwd=worktree, check=False)
    if diff.returncode == 0:
        log("No staged changes to commit.")
        return
    run_cmd(["git", "commit", "-m", message], cwd=worktree)


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
        ["gh", "pr", "create", "--title", title, "--body", body],
        cwd=worktree,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create PR with gh:\n{result.stderr}")
    return result.stdout.strip()


def default_manifest_path(post: FeedPost, target_date: date) -> Path:
    return Path("manifests") / f"{target_date.isoformat()}-{post.slug}.yaml"


def write_run_summary(summary_path: Path, run_results: list[dict[str, str]]) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps({"results": run_results}, indent=2))
    log(f"Wrote run summary: {summary_path}")


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
        choices=["openai", "none", "placeholder", "gemini", "local"],
        help="Translation adapter to use. `openai` is implemented now.",
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
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    local_tz = ZoneInfo(args.timezone)
    target_date = date.fromisoformat(args.date)
    target_worktree = Path(args.target_worktree).expanduser().resolve()
    if not target_worktree.exists():
        parser.error(f"--target-worktree does not exist: {target_worktree}")

    log(f"Fetching feed: {args.feed_url}")
    posts = parse_feed(fetch_text(args.feed_url))
    selected = select_posts(posts, target_date, args.post_url, local_tz)
    if not selected:
        log(f"No posts found for {target_date.isoformat()}.")
        if args.run_summary:
            write_run_summary(Path(args.run_summary), [])
        return 0
    if len(selected) > 1 and args.output_manifest:
        parser.error("--output-manifest can only be used when one post is selected")

    target_repo = args.target_repo or infer_github_repo(target_worktree)
    base_branch = current_branch(target_worktree)
    if not base_branch:
        raise RuntimeError(f"Could not determine current branch in {target_worktree}")
    prompt_path = Path(args.translation_prompt) if args.translation_prompt else None
    translator = get_translation_adapter(args.translator, model=args.openai_model, prompt_path=prompt_path)
    run_results: list[dict[str, str]] = []

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

        source_html = fetch_text(post.url)
        source_markdown = html_to_markdown(source_html)
        if not source_markdown:
            raise RuntimeError(f"Could not extract source markdown from {post.url}")
        log(f"Translating with adapter: {translator.name}")
        translated_markdown = translator.translate(
            TranslationRequest(
                title=post.title,
                source_url=post.url,
                source_markdown=source_markdown,
                target_locale=DEFAULT_LOCALE,
            )
        )

        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(build_translation_markdown(post, translated_markdown, translator.name, post.url))

        commit_file(
            target_worktree,
            file_path,
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
        write_run_summary(Path(args.run_summary), run_results)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
