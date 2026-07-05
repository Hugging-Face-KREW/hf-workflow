from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hf_agent.handle_pr_feedback import (
    apply_feedback,
    apply_model_response,
    call_openai,
    parse_feedback_event,
    resolve_translation_path,
    route_feedback,
)


def test_parse_trusted_issue_comment() -> None:
    payload = {
        "action": "created",
        "comment": {
            "id": 42,
            "body": "Keep the API name in English.",
            "user": {"login": "reviewer", "type": "User"},
        },
        "issue": {
            "number": 161,
            "state": "open",
            "pull_request": {"url": "https://api.github.com/pulls/161"},
            "labels": [{"name": "hf-agent:managed"}],
        },
    }

    feedback = parse_feedback_event("issue_comment", payload, permission="write")

    assert feedback.pr_number == 161
    assert feedback.comment_id == "42"
    assert feedback.body == "Keep the API name in English."


@pytest.mark.parametrize("permission", ["read", "triage", "none"])
def test_parse_feedback_rejects_untrusted_permissions(permission: str) -> None:
    payload = {
        "action": "created",
        "comment": {"id": 1, "body": "Change it", "user": {"login": "reader", "type": "User"}},
        "issue": {
            "number": 1,
            "state": "open",
            "pull_request": {},
            "labels": [{"name": "hf-agent:managed"}],
        },
    }

    with pytest.raises(ValueError, match="trusted reviewer"):
        parse_feedback_event("issue_comment", payload, permission=permission)


def test_parse_feedback_rejects_paused_and_bot_events() -> None:
    payload = {
        "action": "created",
        "comment": {
            "id": 1,
            "body": "<!-- hf-agent-report -->",
            "user": {"login": "github-actions[bot]", "type": "Bot"},
        },
        "issue": {
            "number": 1,
            "state": "open",
            "pull_request": {},
            "labels": [
                {"name": "hf-agent:managed"},
                {"name": "hf-agent:paused"},
            ],
        },
    }

    with pytest.raises(ValueError):
        parse_feedback_event("issue_comment", payload, permission="write")


def test_resolve_translation_path_rejects_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="translation post"):
        resolve_translation_path(tmp_path, "../.github/workflows/pwn.yml")


def test_apply_model_response_accepts_a_small_actionable_change() -> None:
    original = "# Title\n\nUse Foo api.\n"
    response = json.dumps(
        {
            "disposition": "actionable",
            "reason": "Preserve the official API spelling.",
            "content": "# Title\n\nUse Foo API.\n",
        }
    )

    result = apply_model_response(original, response, max_changed_lines=10)

    assert result.disposition == "actionable"
    assert result.content.endswith("Foo API.\n")


def test_apply_model_response_rejects_large_changes() -> None:
    response = json.dumps(
        {
            "disposition": "actionable",
            "reason": "Rewrite everything.",
            "content": "\n".join(f"new {index}" for index in range(20)),
        }
    )

    with pytest.raises(ValueError, match="changed-line limit"):
        apply_model_response("one line\n", response, max_changed_lines=5)


def test_apply_feedback_writes_only_the_selected_post(tmp_path: Path) -> None:
    post = tmp_path / "_posts" / "post.md"
    post.parent.mkdir()
    post.write_text("# Title\n\nUse Foo api.\n")

    result = apply_feedback(
        target_root=tmp_path,
        file_path="_posts/post.md",
        feedback="Keep the official API spelling.",
        max_changed_lines=10,
        model_call=lambda prompt: json.dumps(
            {
                "disposition": "actionable",
                "reason": "Preserve the product spelling.",
                "content": "# Title\n\nUse Foo API.\n",
            }
        ),
    )

    assert result.disposition == "actionable"
    assert post.read_text().endswith("Foo API.\n")


def test_apply_feedback_does_not_write_for_a_question(tmp_path: Path) -> None:
    post = tmp_path / "_posts" / "post.md"
    post.parent.mkdir()
    post.write_text("Original\n")

    result = apply_feedback(
        target_root=tmp_path,
        file_path="_posts/post.md",
        feedback="Why was this term retained?",
        max_changed_lines=10,
        model_call=lambda prompt: json.dumps(
            {
                "disposition": "no-change",
                "reason": "The term is an official product name.",
            }
        ),
    )

    assert result.disposition == "no-change"
    assert post.read_text() == "Original\n"


def test_apply_feedback_removes_todo_comment_for_gate_repair(tmp_path: Path) -> None:
    post = tmp_path / "_posts" / "post.md"
    post.parent.mkdir()
    post.write_text("# Title\n\n본문입니다.\n<!-- TODO: temporary E2E failure sentinel. -->\n")

    result = apply_feedback(
        target_root=tmp_path,
        file_path="_posts/post.md",
        feedback=(
            "This is an automated PR gate repair.\n"
            "QUALITY gate failed:\n"
            "- WARN: no TODO marker remains\n"
            "- TODO markers: 1"
        ),
        max_changed_lines=10,
        model_call=lambda prompt: pytest.fail("deterministic gate repair should not call the model"),
    )

    assert result.disposition == "actionable"
    assert "TODO" not in post.read_text()


def test_call_openai_requests_one_json_response() -> None:
    calls = []

    class Responses:
        def create(self, **kwargs):
            calls.append(kwargs)
            return type("Response", (), {"output_text": '{"disposition":"no-change","reason":"ok"}'})()

    client = type("Client", (), {"responses": Responses()})()

    output = call_openai("prompt", model="gpt-test", client=client)

    assert json.loads(output)["disposition"] == "no-change"
    assert calls == [
        {
            "input": "prompt",
            "instructions": "Return valid JSON only.",
            "model": "gpt-test",
        }
    ]


def test_call_openai_strips_environment_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    class Responses:
        def create(self, **kwargs):
            return type("Response", (), {"output_text": '{"disposition":"no-change","reason":"ok"}'})()

    class OpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.responses = Responses()

    monkeypatch.setenv("OPENAI_API_KEY", " sk-test \n")
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=OpenAI))

    output = call_openai("prompt", model="gpt-test")

    assert json.loads(output)["disposition"] == "no-change"
    assert captured["api_key"] == "sk-test"


def test_route_feedback_marks_the_current_head_pending() -> None:
    payload = {
        "action": "created",
        "comment": {
            "id": 42,
            "body": "Keep the API name in English.",
            "user": {"login": "reviewer", "type": "User"},
        },
        "issue": {
            "number": 161,
            "state": "open",
            "pull_request": {},
            "labels": [{"name": "hf-agent:managed"}],
        },
    }
    statuses = []

    def requester(method, path, token, payload=None):
        if path.endswith("/collaborators/reviewer/permission"):
            return {"permission": "write"}
        if path.endswith("/pulls/161"):
            return {"head": {"sha": "current-sha"}}
        raise AssertionError(path)

    context = route_feedback(
        event_name="issue_comment",
        payload=payload,
        repository="owner/repo",
        token="token",
        requester=requester,
        status_publisher=lambda **status: statuses.append(status),
    )

    assert context["head_sha"] == "current-sha"
    assert context["pr_number"] == 161
    assert statuses[0]["state"] == "pending"
    assert statuses[0]["sha"] == "current-sha"
