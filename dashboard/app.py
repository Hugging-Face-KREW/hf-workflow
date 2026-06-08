from __future__ import annotations

import io
import json
import os
import re
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import gradio as gr
import requests


GITHUB_REPO = os.getenv("GITHUB_REPO", "Hugging-Face-KREW/hf-workflow")
WORKFLOW_FILE = os.getenv("WORKFLOW_FILE", "daily-translation.yml")
HF_FEED_URL = os.getenv("HF_FEED_URL", "https://huggingface.co/blog/feed.xml")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN", "")
KST = timezone(timedelta(hours=9))
_WORKFLOW_ID_CACHE: str | None = None


def headers() -> dict[str, str]:
    values = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "hf-workflow-dashboard",
    }
    if GITHUB_TOKEN:
        values["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return values


def github_get(path: str, *, raw: bool = False) -> Any:
    url = f"https://api.github.com/repos/{GITHUB_REPO}{path}"
    response = requests.get(url, headers=headers(), timeout=30)
    response.raise_for_status()
    return response.content if raw else response.json()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(node: ET.Element, names: set[str]) -> str:
    for child in list(node):
        if local_name(child.tag) in names and child.text:
            return child.text.strip()
    return ""


def atom_link(node: ET.Element) -> str:
    for child in list(node):
        if local_name(child.tag) != "link":
            continue
        href = child.attrib.get("href", "")
        rel = child.attrib.get("rel", "alternate")
        if href and rel == "alternate":
            return href.strip()
    return ""


def parse_datetime(raw: str) -> datetime:
    raw = raw.strip()
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def slug_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    return path.rsplit("/", 1)[-1] or "post"


def fetch_feed_posts() -> list[dict[str, str]]:
    response = requests.get(HF_FEED_URL, headers={"User-Agent": "hf-workflow-dashboard"}, timeout=30)
    response.raise_for_status()
    root = ET.fromstring(response.text)
    posts: list[dict[str, str]] = []

    for item in root.iter():
        if local_name(item.tag) not in {"item", "entry"}:
            continue
        title = child_text(item, {"title"})
        url = child_text(item, {"link"}) or atom_link(item)
        raw_date = child_text(item, {"pubDate", "published", "updated"})
        if not title or not url or not raw_date:
            continue
        published_at = parse_datetime(raw_date)
        posts.append(
            {
                "date": published_at.astimezone(KST).date().isoformat(),
                "title": title,
                "url": url,
                "slug": slug_from_url(url),
            }
        )
    return posts


def resolve_workflow_id() -> str:
    global _WORKFLOW_ID_CACHE
    if _WORKFLOW_ID_CACHE is not None:
        return _WORKFLOW_ID_CACHE

    if WORKFLOW_FILE.isdigit():
        _WORKFLOW_ID_CACHE = WORKFLOW_FILE
        return _WORKFLOW_ID_CACHE

    data = github_get("/actions/workflows?per_page=100")
    wanted = WORKFLOW_FILE.strip("/")
    for workflow in data.get("workflows", []):
        path = workflow.get("path", "")
        name = workflow.get("name", "")
        if path.endswith(wanted) or name == WORKFLOW_FILE:
            _WORKFLOW_ID_CACHE = str(workflow["id"])
            return _WORKFLOW_ID_CACHE
    raise RuntimeError(f"Could not find workflow matching {WORKFLOW_FILE!r}")


def list_workflow_runs(limit: int) -> list[dict[str, Any]]:
    workflow_id = resolve_workflow_id()
    data = github_get(f"/actions/workflows/{workflow_id}/runs?per_page={min(limit, 100)}")
    return data.get("workflow_runs", [])


def list_run_artifacts(run_id: int) -> list[dict[str, Any]]:
    try:
        data = github_get(f"/actions/runs/{run_id}/artifacts?per_page=50")
    except requests.HTTPError:
        return []
    return data.get("artifacts", [])


def download_artifact_zip(artifact: dict[str, Any]) -> bytes | None:
    url = artifact.get("archive_download_url")
    if not url:
        return None
    response = requests.get(url, headers=headers(), timeout=30)
    if response.status_code >= 400:
        return None
    return response.content


def artifact_summary(artifacts: list[dict[str, Any]]) -> tuple[str, list[str], list[str]]:
    statuses: list[str] = []
    pr_urls: list[str] = []
    target_dates: list[str] = []

    for artifact in artifacts:
        name = artifact.get("name", "")
        match = re.match(r"hf-workflow-(\d{4}-\d{2}-\d{2})$", name)
        if match:
            target_dates.append(match.group(1))

        payload = download_artifact_zip(artifact)
        if not payload:
            continue
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                for member in archive.namelist():
                    if not member.endswith("run-summary.json"):
                        continue
                    summary = json.loads(archive.read(member).decode("utf-8"))
                    for result in summary.get("results", []):
                        status = result.get("status", "")
                        slug = result.get("slug", "")
                        if status:
                            statuses.append(f"{slug}:{status}" if slug else status)
                        if result.get("pr_url"):
                            pr_urls.append(result["pr_url"])
        except (zipfile.BadZipFile, json.JSONDecodeError, UnicodeDecodeError):
            continue

    return ", ".join(statuses) or "-", pr_urls, target_dates


def run_logs(run_id: int) -> str:
    try:
        payload = github_get(f"/actions/runs/{run_id}/logs", raw=True)
    except requests.HTTPError:
        return ""
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            chunks = []
            for name in archive.namelist():
                if name.endswith(".txt"):
                    chunks.append(archive.read(name).decode("utf-8", errors="replace"))
            return "\n".join(chunks)
    except zipfile.BadZipFile:
        return ""


def infer_target_date(run: dict[str, Any], artifact_dates: list[str], logs: str) -> str:
    if artifact_dates:
        return artifact_dates[0]
    match = re.search(r'--date "(\d{4}-\d{2}-\d{2})"', logs)
    if match:
        return match.group(1)
    created_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
    return created_at.astimezone(KST).date().isoformat()


def notification_status(logs: str) -> str:
    output_lines = [
        line for line in logs.splitlines()
        if "\x1b[" not in line and "print(" not in line
    ]
    output = "\n".join(output_lines)
    if "Discord notification sent:" in output:
        return "sent"
    if "HTTP Error 403: Forbidden" in output:
        return "failed: discord 403"
    if "No created PR URL found; skipping Discord notification." in output:
        return "skipped: no created PR"
    if "No run summary found; skipping Discord notification." in output:
        return "skipped: no run summary"
    return "unknown"


def failure_reason(conclusion: str, logs: str) -> str:
    if conclusion != "failure":
        return "-"
    if "HTTP Error 403: Forbidden" in logs:
        return "Discord webhook returned 403"
    if "Command failed:" in logs:
        return "Command failed"
    if "error:" in logs:
        return "Script error"
    return "Unknown failure"


def render_dashboard(lookback_days: int, max_runs: int) -> tuple[str, list[list[Any]], list[list[Any]]]:
    posts = fetch_feed_posts()
    posts_by_date: dict[str, list[dict[str, str]]] = defaultdict(list)
    for post in posts:
        posts_by_date[post["date"]].append(post)

    api_error = ""
    try:
        runs = list_workflow_runs(max_runs)
    except Exception as exc:
        runs = []
        api_error = f"{type(exc).__name__}: {exc}"

    run_rows: list[list[Any]] = []
    seen_run_dates: set[str] = set()

    for run in runs:
        run_id = run["id"]
        artifacts = list_run_artifacts(run_id)
        summary_statuses, pr_urls, artifact_dates = artifact_summary(artifacts)
        logs = run_logs(run_id)
        target_date = infer_target_date(run, artifact_dates, logs)
        seen_run_dates.add(target_date)
        expected_posts = posts_by_date.get(target_date, [])
        conclusion = run.get("conclusion") or run.get("status") or "unknown"
        run_rows.append(
            [
                target_date,
                len(expected_posts),
                "\n".join(post["slug"] for post in expected_posts) or "-",
                conclusion,
                notification_status(logs),
                summary_statuses,
                "\n".join(pr_urls) or "-",
                failure_reason(conclusion, logs),
                run.get("html_url", ""),
            ]
        )

    today = datetime.now(KST).date()
    calendar_rows: list[list[Any]] = []
    for offset in range(lookback_days):
        day = today - timedelta(days=offset)
        day_key = day.isoformat()
        day_posts = posts_by_date.get(day_key, [])
        run_count = sum(1 for row in run_rows if row[0] == day_key)
        calendar_rows.append(
            [
                day_key,
                len(day_posts),
                "\n".join(post["slug"] for post in day_posts) or "-",
                run_count,
                "yes" if day_key in seen_run_dates else "no",
            ]
        )

    failures = [row for row in run_rows if row[3] == "failure"]
    notification_failures = [row for row in run_rows if str(row[4]).startswith("failed")]
    summary = "\n".join(
        [
            f"### HF Workflow Dashboard",
            f"- Repo: `{GITHUB_REPO}`",
            f"- Workflow: `{WORKFLOW_FILE}`",
            f"- Recent runs loaded: `{len(run_rows)}`",
            f"- Failed runs: `{len(failures)}`",
            f"- Notification failures: `{len(notification_failures)}`",
            f"- GitHub token configured: `{'yes' if GITHUB_TOKEN else 'no'}`",
            f"- GitHub API error: `{api_error or '-'}`",
        ]
    )
    return summary, calendar_rows, run_rows


with gr.Blocks(title="HF Workflow Dashboard") as demo:
    gr.Markdown("# HF Workflow Dashboard")
    gr.Markdown("Monitor HF blog translation targets, GitHub Actions runs, run summaries, and Discord notification status.")
    with gr.Row():
        lookback = gr.Slider(7, 60, value=21, step=1, label="Calendar lookback days")
        max_runs = gr.Slider(5, 50, value=20, step=1, label="Recent GitHub runs")
    refresh = gr.Button("Refresh")
    summary = gr.Markdown()
    calendar = gr.Dataframe(
        headers=["target_date", "rss_posts", "post_slugs", "runs", "has_run"],
        label="Translation Calendar",
        wrap=True,
    )
    runs = gr.Dataframe(
        headers=[
            "target_date",
            "rss_posts",
            "post_slugs",
            "run_conclusion",
            "discord_notification",
            "run_summary_statuses",
            "translation_pr_urls",
            "failure_reason",
            "run_url",
        ],
        label="Recent Workflow Runs",
        wrap=True,
    )

    refresh.click(render_dashboard, inputs=[lookback, max_runs], outputs=[summary, calendar, runs])
    demo.load(render_dashboard, inputs=[lookback, max_runs], outputs=[summary, calendar, runs])


if __name__ == "__main__":
    demo.launch()
