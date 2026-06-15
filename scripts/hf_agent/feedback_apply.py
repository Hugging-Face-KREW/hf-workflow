from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import replace

from hf_agent.feedback_state import FeedbackState, PendingFeedback, stable_body_hash


def build_feedback_prompt(
    *,
    manifest: dict[str, str],
    markdown: str,
    pending: list[PendingFeedback],
) -> str:
    file_path = manifest.get("translation.file_path", "")
    source_url = manifest.get("source.url", "")
    feedback_lines: list[str] = []
    for item in pending:
        location = ""
        if item.path:
            location = f" ({item.path}"
            if item.line:
                location += f", line {item.line}"
            location += ")"
        feedback_lines.append(
            "\n".join(
                [
                    f"- key: {item.key}",
                    f"  status: {item.status}{location}",
                    f"  author: {item.comment.author}",
                    f"  updated_at: {item.comment.updated_at}",
                    f"  body: {item.body}",
                ]
            )
        )

    return "\n".join(
        [
            "You are editing a Korean Hugging Face blog translation based on PR feedback.",
            "",
            "Rules:",
            "- Preserve facts, source meaning, numbers, names, URLs, code, links, images, tables, and frontmatter structure.",
            "- Apply only the feedback listed below.",
            "- If feedback is ambiguous, leave the text unchanged and add an HTML comment near the relevant paragraph: <!-- hf-agent-needs-human: reason -->.",
            "- Do not add new sections.",
            "- Return only the full updated markdown.",
            "",
            f"Translation file: {file_path}",
            f"Source URL: {source_url}",
            "",
            "Pending feedback:",
            "\n".join(feedback_lines),
            "",
            "Current markdown:",
            markdown,
        ]
    )


def mark_feedback_applied(
    state: FeedbackState,
    pending: list[PendingFeedback],
    *,
    applied_sha: str,
    run_at: str,
) -> FeedbackState:
    processed = dict(state.processed_comments)
    for item in pending:
        processed[item.key] = {
            "body_hash": stable_body_hash(item.body),
            "updated_at": item.comment.updated_at,
            "applied_sha": applied_sha,
            "status": "applied",
        }
    return replace(
        state,
        last_run_at=run_at,
        last_applied_sha=applied_sha,
        processed_comments=processed,
    )


def rewrite_with_openai(prompt: str, model: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for feedback application.")

    payload = {
        "model": model,
        "input": prompt,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))

    chunks: list[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                chunks.append(content.get("text", ""))
    text = "".join(chunks).strip()
    if not text:
        raise RuntimeError("OpenAI returned an empty feedback application.")
    return text

