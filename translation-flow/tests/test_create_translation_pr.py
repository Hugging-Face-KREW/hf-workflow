from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

import scripts.create_translation_pr as create_translation_pr
from scripts.create_translation_pr import (
    FeedPost,
    SourceFrontmatter,
    build_translation_markdown,
    create_or_update_branch,
    create_pr,
    html_to_markdown,
    normalize_escaped_newlines,
    parse_feed,
    run_cmd,
    select_posts,
    split_source_frontmatter,
    slug_from_url,
    stabilize_manual_toc,
)
from scripts.translation_adapters import (
    PlaceholderTranslationAdapter,
    TranslationRequest,
    default_prompt_path,
    load_translation_prompt,
)


def test_parse_rss_feed_items() -> None:
    xml = """<?xml version="1.0"?>
    <rss>
      <channel>
        <item>
          <title>Test Post</title>
          <link>https://huggingface.co/blog/test-post</link>
          <pubDate>Mon, 11 May 2026 00:00:00 GMT</pubDate>
          <description>Summary</description>
        </item>
      </channel>
    </rss>
    """

    posts = parse_feed(xml)

    assert len(posts) == 1
    assert posts[0].title == "Test Post"
    assert posts[0].slug == "test-post"
    assert posts[0].published_date == date(2026, 5, 11)
    assert posts[0].published_at.tzinfo is not None


def test_parse_atom_feed_entries() -> None:
    xml = """<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Atom Post</title>
        <link href="https://huggingface.co/blog/atom-post" />
        <published>2026-05-11T12:00:00Z</published>
      </entry>
    </feed>
    """

    posts = parse_feed(xml)

    assert len(posts) == 1
    assert posts[0].url == "https://huggingface.co/blog/atom-post"
    assert posts[0].published_date == date(2026, 5, 11)


def test_select_posts_by_date() -> None:
    posts = [
        FeedPost("A", "https://huggingface.co/blog/a", datetime(2026, 5, 10, tzinfo=timezone.utc), "a"),
        FeedPost("B", "https://huggingface.co/blog/b", datetime(2026, 5, 11, tzinfo=timezone.utc), "b"),
    ]

    selected = select_posts(posts, date(2026, 5, 11), None, ZoneInfo("UTC"))

    assert [post.slug for post in selected] == ["b"]


def test_select_posts_by_local_timezone_date() -> None:
    posts = [
        FeedPost(
            "A",
            "https://huggingface.co/blog/a",
            datetime(2026, 5, 10, 18, 44, 11, tzinfo=timezone.utc),
            "a",
        ),
    ]

    selected = select_posts(posts, date(2026, 5, 11), None, ZoneInfo("Asia/Seoul"))

    assert [post.slug for post in selected] == ["a"]


def test_slug_from_url() -> None:
    assert slug_from_url("https://huggingface.co/blog/Transformers-to-MLX?x=1") == "transformers-to-mlx"


def test_discover_markdown_urls_prefers_org_slug_path() -> None:
    urls = create_translation_pr.discover_markdown_urls(
        "https://huggingface.co/blog/amazon/foundation-model-building-blocks",
        "",
    )

    assert urls[0] == (
        "https://raw.githubusercontent.com/huggingface/blog/main/amazon/"
        "foundation-model-building-blocks.md"
    )
    assert (
        "https://raw.githubusercontent.com/huggingface/blog/main/"
        "foundation-model-building-blocks.md"
    ) in urls


def test_extract_source_markdown_fails_fast_without_html_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        create_translation_pr,
        "discover_markdown_urls",
        lambda _post_url, _source_html: ["https://raw.example.com/post.md"],
    )
    monkeypatch.setattr(create_translation_pr, "fetch_text", lambda _url: "<html>not markdown</html>")

    with pytest.raises(RuntimeError, match="Could not fetch source markdown"):
        create_translation_pr.extract_source_markdown(
            "https://huggingface.co/blog/example/post",
            "<html></html>",
            allow_html_fallback=False,
        )


def test_extract_source_markdown_allows_html_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        create_translation_pr,
        "discover_markdown_urls",
        lambda _post_url, _source_html: [],
    )
    monkeypatch.setattr(create_translation_pr, "html_to_markdown", lambda _html: "# From HTML\n\nBody")

    result = create_translation_pr.extract_source_markdown(
        "https://huggingface.co/blog/example/post",
        "<html></html>",
        allow_html_fallback=True,
    )

    assert result == "# From HTML\n\nBody"


def test_enforce_structure_preservation_detects_missing_elements() -> None:
    source = """# Title

| A | B |
| --- | --- |
| 1 | 2 |

![img](https://example.com/image.png)

```python
print("hi")
```
"""
    translated = """# 제목

본문만 남김
"""

    with pytest.raises(RuntimeError, match="Translated markdown lost structural elements"):
        create_translation_pr.enforce_structure_preservation(source, translated)


def test_build_translation_markdown_preserves_source_metadata() -> None:
    post = FeedPost(
        title="Hello MLX",
        url="https://huggingface.co/blog/hello-mlx",
        published_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        slug="hello-mlx",
    )

    markdown = build_translation_markdown(
        post,
        "# 안녕하세요\n\n본문입니다.",
        "none",
        "https://huggingface.co/blog/hello-mlx",
    )

    assert "layout: post" in markdown
    assert 'source_url: "https://huggingface.co/blog/hello-mlx"' in markdown
    assert "translation_status: \"draft\"" in markdown
    assert 'translator: "none"' in markdown
    assert "# 안녕하세요" in markdown


def test_build_translation_markdown_includes_source_passthrough_frontmatter() -> None:
    post = FeedPost(
        title="Hello MLX",
        url="https://huggingface.co/blog/hello-mlx",
        published_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        slug="hello-mlx",
    )
    source_frontmatter = SourceFrontmatter(
        thumbnail="/blog/assets/hello-mlx/thumbnail.png",
        authors=("user: alice", "user: bob"),
    )

    markdown = build_translation_markdown(
        post,
        "# 안녕하세요\n\n본문입니다.",
        "none",
        "https://huggingface.co/blog/hello-mlx",
        source_frontmatter=source_frontmatter,
    )

    assert "thumbnail: /blog/assets/hello-mlx/thumbnail.png" in markdown
    assert "authors:" in markdown
    assert "  - user: alice" in markdown
    assert "  - user: bob" in markdown


def test_split_source_frontmatter_returns_body_and_selected_fields() -> None:
    source = """---
title: "Example"
date: "2026-05-11T23:18:26+00:00"
thumbnail: /blog/assets/example/thumb.png
authors:
  - user: meg
  - user: clem
---

# Heading

Body
"""
    parsed, body = split_source_frontmatter(source)

    assert parsed.title == "Example"
    assert parsed.published_at is not None
    assert parsed.published_at.date() == date(2026, 5, 11)
    assert parsed.thumbnail == "/blog/assets/example/thumb.png"
    assert parsed.authors == ("user: meg", "user: clem")
    assert body.startswith("# Heading")
    assert "---" not in body


def test_normalize_escaped_newlines_ignores_code_fence_content() -> None:
    source = """# 제목\\n
문장\\n\\n- 항목1\\n- 항목2\\n
```python
print("a\\\\n")
```
"""
    normalized = normalize_escaped_newlines(source)

    assert "# 제목\n" in normalized
    assert "- 항목1\n- 항목2\n" in normalized
    assert 'print("a\\\\n")' in normalized


def test_stabilize_manual_toc_merges_standalone_heading_id_line() -> None:
    source = """# Title

이 글에서: [A](#old)

## A
 {#section-3}

본문
"""
    stabilized = stabilize_manual_toc(source)

    assert "## A {#section-3}" in stabilized
    assert "{#section-3}" not in [line.strip() for line in stabilized.splitlines()]
    assert "이 글에서: [A](#section-3)" in stabilized


def test_stabilize_manual_toc_rewrites_table_of_contents_section_links() -> None:
    source = """# Title

## 목차

* [What are Multimodal Models?](#what-are-multimodal-models)
* [Installation](#installation)

## 다중모달 모델이란?

본문 A

## 설치

본문 B
"""
    stabilized = stabilize_manual_toc(source)

    assert "* [다중모달 모델이란?](#section-2)" in stabilized
    assert "* [설치](#section-3)" in stabilized
    assert "#what-are-multimodal-models" not in stabilized
    assert "#installation" not in stabilized


def test_html_to_markdown_extracts_article_shape() -> None:
    source = """
    <html><body><article><h1>Hello</h1><p>Use <code>mlx_lm</code>.</p>
    <pre><code>print("hi")</code></pre></article></body></html>
    """

    markdown = html_to_markdown(source)

    assert "# Hello" in markdown
    assert "Use `mlx_lm`." in markdown
    assert 'print("hi")' in markdown


def test_html_to_markdown_removes_blog_page_chrome() -> None:
    source = """
    <div class="blog-content">
      <div class="mb-4"><a href="/blog">Back to Articles</a></div>
      <h1>Title</h1>
      <div class="not-prose"><nav><li>Table of contents</li></nav></div>
      <p>Actual body with <a href="/models">models</a>.</p>
    </div>
    """

    markdown = html_to_markdown(source)

    assert "Back to Articles" not in markdown
    assert "Table of contents" not in markdown
    assert "# Title" in markdown
    assert "Actual body with [models](/models)." in markdown


def test_resolve_post_from_source_uses_frontmatter_metadata(monkeypatch) -> None:
    source_markdown = """---
title: "From Source"
published: "2026-05-11T23:18:26+00:00"
---

# From Source

Body
"""
    monkeypatch.setattr(create_translation_pr, "fetch_text", lambda _url: "<html></html>")
    monkeypatch.setattr(
        create_translation_pr,
        "extract_source_markdown",
        lambda _post_url, _source_html, allow_html_fallback=False, feed_url=create_translation_pr.DEFAULT_FEED_URL: source_markdown,
    )

    post = create_translation_pr.resolve_post_from_source(
        "https://huggingface.co/blog/amazon/foundation-model-building-blocks",
        allow_html_fallback=False,
    )

    assert post.title == "From Source"
    assert post.slug == "foundation-model-building-blocks"
    assert post.published_date == date(2026, 5, 11)


def test_resolve_post_from_source_requires_title_and_date(monkeypatch) -> None:
    source_markdown = """---
thumbnail: /blog/assets/example/thumb.png
---

# Missing metadata
"""
    monkeypatch.setattr(create_translation_pr, "fetch_text", lambda _url: "<html></html>")
    monkeypatch.setattr(
        create_translation_pr,
        "extract_source_markdown",
        lambda _post_url, _source_html, allow_html_fallback=False, feed_url=create_translation_pr.DEFAULT_FEED_URL: source_markdown,
    )

    with pytest.raises(RuntimeError, match="Missing `title`"):
        create_translation_pr.resolve_post_from_source(
            "https://huggingface.co/blog/example-post",
            allow_html_fallback=False,
        )


def test_resolve_post_from_source_falls_back_to_feed_date(monkeypatch) -> None:
    source_markdown = """---
title: "From Source"
thumbnail: /blog/assets/example/thumb.png
---

# Missing date metadata
"""
    monkeypatch.setattr(create_translation_pr, "fetch_text", lambda _url: "<html></html>")
    monkeypatch.setattr(
        create_translation_pr,
        "extract_source_markdown",
        lambda _post_url, _source_html, allow_html_fallback=False, feed_url=create_translation_pr.DEFAULT_FEED_URL: source_markdown,
    )
    fallback_dt = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(
        create_translation_pr,
        "resolve_published_at_from_feed",
        lambda _post_url, _feed_url: fallback_dt,
    )

    post = create_translation_pr.resolve_post_from_source(
        "https://huggingface.co/blog/open-asr-leaderboard-private-data",
        allow_html_fallback=False,
    )

    assert post.title == "From Source"
    assert post.published_at == fallback_dt


def test_resolve_post_from_source_raises_when_date_missing_after_feed_fallback(monkeypatch) -> None:
    source_markdown = """---
title: "From Source"
---

# Missing date metadata
"""
    monkeypatch.setattr(create_translation_pr, "fetch_text", lambda _url: "<html></html>")
    monkeypatch.setattr(
        create_translation_pr,
        "extract_source_markdown",
        lambda _post_url, _source_html, allow_html_fallback=False, feed_url=create_translation_pr.DEFAULT_FEED_URL: source_markdown,
    )
    monkeypatch.setattr(create_translation_pr, "resolve_published_at_from_feed", lambda *_: None)

    with pytest.raises(RuntimeError, match="Missing `date`/`published`"):
        create_translation_pr.resolve_post_from_source(
            "https://huggingface.co/blog/open-asr-leaderboard-private-data",
            allow_html_fallback=False,
        )


def test_extract_source_markdown_skips_for_feed_listed_post_without_raw_markdown(monkeypatch) -> None:
    post_url = "https://huggingface.co/blog/ibm-granite/granite-embedding-multilingual-r2"
    source_html = "<h1>Granite Title</h1><p>Body content</p>"
    monkeypatch.setattr(
        create_translation_pr,
        "discover_markdown_urls",
        lambda _post_url, _source_html: ["https://raw.githubusercontent.com/huggingface/blog/main/granite-embedding-multilingual-r2.md"],
    )

    def fail_fetch(_url: str) -> str:
        raise RuntimeError("404")

    monkeypatch.setattr(create_translation_pr, "fetch_text", fail_fetch)
    monkeypatch.setattr(
        create_translation_pr,
        "resolve_feed_post_by_url",
        lambda _post_url, _feed_url: FeedPost(
            "Granite",
            post_url,
            datetime(2026, 5, 14, tzinfo=timezone.utc),
            "granite-embedding-multilingual-r2",
        ),
    )

    with pytest.raises(create_translation_pr.SourceMarkdownSkipError) as excinfo:
        create_translation_pr.extract_source_markdown(post_url, source_html, allow_html_fallback=False)
    assert excinfo.value.reason == "enterprise_article"


def test_extract_source_markdown_skips_for_community_article(monkeypatch) -> None:
    post_url = "https://huggingface.co/blog/RikkaBotan/stable-static-embedding-v2-technical-report"
    source_html = "<h1>Community Article</h1><p>Body</p>"
    monkeypatch.setattr(create_translation_pr, "discover_markdown_urls", lambda _post_url, _source_html: [])

    with pytest.raises(create_translation_pr.SourceMarkdownSkipError) as excinfo:
        create_translation_pr.extract_source_markdown(post_url, source_html, allow_html_fallback=False)
    assert excinfo.value.reason == "community_article"


def test_main_post_url_skips_when_raw_markdown_missing_by_policy(
    monkeypatch, tmp_path: Path
) -> None:
    summary_path = tmp_path / "run-summary.json"
    post_url = "https://huggingface.co/blog/lablab-ai-amd-developer-hackathon/machinacheck"

    def fail_resolve(_post_url: str, allow_html_fallback: bool, feed_url: str):
        raise create_translation_pr.SourceMarkdownSkipError(
            "enterprise_article",
            [
                "https://raw.githubusercontent.com/huggingface/blog/main/lablab-ai-amd-developer-hackathon/machinacheck.md"
            ],
        )

    monkeypatch.setattr(create_translation_pr, "resolve_post_from_source", fail_resolve)

    result = create_translation_pr.main(
        [
            "--target-worktree",
            str(tmp_path),
            "--post-url",
            post_url,
            "--run-summary",
            str(summary_path),
        ]
    )

    assert result == 0
    summary = json.loads(summary_path.read_text())
    assert summary["results"][0]["status"] == "skipped_enterprise"
    assert summary["results"][0]["slug"] == "machinacheck"


def test_main_post_url_raises_when_frontmatter_metadata_missing(
    monkeypatch, tmp_path: Path
) -> None:
    summary_path = tmp_path / "run-summary.json"
    post_url = "https://huggingface.co/blog/community/example"

    def fail_resolve(_post_url: str, allow_html_fallback: bool, feed_url: str):
        raise RuntimeError(
            "Missing `title` in source markdown frontmatter for --post-url mode: "
            f"{post_url}"
        )

    monkeypatch.setattr(create_translation_pr, "resolve_post_from_source", fail_resolve)

    with pytest.raises(RuntimeError, match="Missing `title`"):
        create_translation_pr.main(
            [
                "--target-worktree",
                str(tmp_path),
                "--post-url",
                post_url,
                "--run-summary",
                str(summary_path),
            ]
        )
    assert not summary_path.exists()


def test_placeholder_adapter_keeps_source_markdown() -> None:
    adapter = PlaceholderTranslationAdapter()

    translated = adapter.translate(
        TranslationRequest(
            title="Hello",
            source_url="https://huggingface.co/blog/hello",
            source_markdown="# Hello",
        )
    )

    assert "TODO: Add Korean translation." in translated
    assert "# Hello" in translated


def test_default_translation_prompt_is_stored_in_docs() -> None:
    prompt = load_translation_prompt(default_prompt_path())

    assert "Hugging Face technical blog posts" in prompt
    assert "Output Korean Markdown only" in prompt
    assert "Chunking Rules" in prompt


def init_git_repo(path: Path) -> None:
    run_cmd(["git", "init"], cwd=path)
    run_cmd(["git", "config", "user.email", "test@example.com"], cwd=path)
    run_cmd(["git", "config", "user.name", "Test User"], cwd=path)


def test_create_or_update_branch_tracks_existing_remote_branch(tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    seed = tmp_path / "seed"
    worktree = tmp_path / "worktree"
    remote.mkdir()
    seed.mkdir()

    run_cmd(["git", "init", "--bare"], cwd=remote)
    init_git_repo(seed)
    (seed / "README.md").write_text("base\n")
    run_cmd(["git", "add", "README.md"], cwd=seed)
    run_cmd(["git", "commit", "-m", "base"], cwd=seed)
    run_cmd(["git", "branch", "-M", "main"], cwd=seed)
    run_cmd(["git", "remote", "add", "origin", str(remote)], cwd=seed)
    run_cmd(["git", "push", "-u", "origin", "main"], cwd=seed)
    run_cmd(["git", "switch", "-c", "translate/example"], cwd=seed)
    (seed / "_posts").mkdir()
    (seed / "_posts" / "example.md").write_text("remote translation\n")
    run_cmd(["git", "add", "_posts/example.md"], cwd=seed)
    run_cmd(["git", "commit", "-m", "remote branch"], cwd=seed)
    run_cmd(["git", "push", "-u", "origin", "translate/example"], cwd=seed)

    run_cmd(["git", "clone", str(remote), str(worktree)])
    run_cmd(["git", "switch", "main"], cwd=worktree)

    create_or_update_branch(worktree, "translate/example", "main")

    assert run_cmd(["git", "branch", "--show-current"], cwd=worktree).stdout.strip() == "translate/example"
    assert (worktree / "_posts" / "example.md").read_text() == "remote translation\n"


def test_create_pr_reuses_existing_pr_url(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run_cmd(args, cwd=None, check=True):
        calls.append(args)
        if args[:3] == ["gh", "pr", "view"]:
            return create_translation_pr.subprocess.CompletedProcess(args, 0, "https://github.com/o/r/pull/1\n", "")
        return create_translation_pr.subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(create_translation_pr, "run_cmd", fake_run_cmd)

    pr_url = create_pr(tmp_path, "translate/example", "Title", "Body", push=True, open_pr=True)

    assert pr_url == "https://github.com/o/r/pull/1"
    assert ["git", "push", "-u", "origin", "translate/example"] in calls
    assert not any(call[:3] == ["gh", "pr", "create"] for call in calls)


def test_create_pr_opts_into_the_managed_loop(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run_cmd(args, cwd=None, check=True):
        calls.append(args)
        if args[:3] == ["gh", "pr", "view"]:
            return create_translation_pr.subprocess.CompletedProcess(args, 1, "", "missing")
        if args[:3] == ["gh", "pr", "create"]:
            return create_translation_pr.subprocess.CompletedProcess(
                args, 0, "https://github.com/o/r/pull/2\n", ""
            )
        return create_translation_pr.subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(create_translation_pr, "run_cmd", fake_run_cmd)

    assert create_pr(
        tmp_path,
        "translate/example",
        "Title",
        "Body",
        push=False,
        open_pr=True,
    ) == "https://github.com/o/r/pull/2"
    assert [
        "gh",
        "pr",
        "create",
        "--title",
        "Title",
        "--body",
        "Body",
        "--label",
        "hf-agent:managed",
    ] in calls


def test_main_writes_empty_run_summary_when_no_posts(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    summary = tmp_path / "run-summary.json"

    monkeypatch.setattr(create_translation_pr, "fetch_text", lambda url: "<rss><channel></channel></rss>")

    result = create_translation_pr.main(
        [
            "--date",
            "2026-05-18",
            "--timezone",
            "Asia/Seoul",
            "--target-worktree",
            str(target),
            "--target-repo",
            "owner/repo",
            "--translator",
            "none",
            "--run-summary",
            str(summary),
        ]
    )

    assert result == 0
    assert summary.read_text() == '{\n  "results": []\n}'
