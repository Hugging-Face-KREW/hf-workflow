from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import scripts.create_translation_pr as create_translation_pr
from scripts.create_translation_pr import (
    FeedPost,
    build_translation_markdown,
    create_or_update_branch,
    create_pr,
    html_to_markdown,
    main,
    parse_feed,
    run_cmd,
    select_posts,
    slug_from_url,
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


def test_main_writes_empty_run_summary_when_no_posts(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    summary = tmp_path / "run-summary.json"

    monkeypatch.setattr(create_translation_pr, "fetch_text", lambda url: "<rss><channel></channel></rss>")

    result = main(
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
