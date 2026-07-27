from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hf_agent.handle_pr_feedback import (
    MAX_REPAIR_OUTPUT_TOKENS,
    REPAIR_RESPONSE_FORMAT,
    apply_feedback,
    apply_model_response,
    build_feedback_prompt,
    call_openai,
    is_metadata_apply_request,
    parse_metadata_policy_overrides,
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


def test_apply_model_response_rejects_broad_sentence_punctuation_loss() -> None:
    original = "\n".join(
        [
            "첫 번째 문장입니다.",
            "두 번째 문장입니다。",
            "세 번째 문장입니다!",
            "**네 번째 문장입니다.**",
        ]
    )
    response = json.dumps(
        {
            "disposition": "actionable",
            "reason": "Apply feedback.",
            "content": "\n".join(
                [
                    "첫 번째 문장입니다",
                    "두 번째 문장입니다",
                    "세 번째 문장입니다",
                    "**네 번째 문장입니다**",
                ]
            ),
        }
    )

    with pytest.raises(ValueError, match="sentence-final punctuation"):
        apply_model_response(original, response, max_changed_lines=20)


def test_apply_model_response_allows_japanese_period_normalization() -> None:
    original = "문장입니다。\n"
    response = json.dumps(
        {
            "disposition": "actionable",
            "reason": "Normalize Korean sentence punctuation.",
            "content": "문장입니다.\n",
        }
    )

    result = apply_model_response(original, response, max_changed_lines=4)

    assert result.content == "문장입니다.\n"


def test_feedback_prompt_requires_preserving_sentence_punctuation() -> None:
    prompt = build_feedback_prompt("문장입니다。\n", "Make the punctuation Korean.")

    assert "Preserve Korean sentence-final punctuation" in prompt
    assert 'replace it with "." instead of removing punctuation' in prompt
    assert "Do not make broad style rewrites" in prompt


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


def test_metadata_apply_request_detection() -> None:
    assert is_metadata_apply_request("metadata apply")
    assert is_metadata_apply_request("SEO metadata apply please")
    assert is_metadata_apply_request("메타데이터 적용해줘")
    assert not is_metadata_apply_request("Why is metadata partial?")


def test_parse_metadata_policy_overrides() -> None:
    policy = parse_metadata_policy_overrides(
        """
metadata apply
target_url: https://hugging-face-krew.github.io/sample/
source_url: https://huggingface.co/blog/sample
canonical-policy: self
translation_indexing: independent
target_locale: ko
source_locale: en
ignored: value
"""
    )

    assert policy == {
        "target_url": "https://hugging-face-krew.github.io/sample/",
        "source_url": "https://huggingface.co/blog/sample",
        "canonical_policy": "self",
        "translation_indexing": "independent",
        "target_locale": "ko",
        "source_locale": "en",
    }


def test_apply_feedback_applies_partial_metadata_safe_fields(tmp_path: Path) -> None:
    post = tmp_path / "_posts" / "post.md"
    post.parent.mkdir()
    post.write_text(
        "---\ntitle: Old title\ncategories:\n  - Translation\n---\n# Old title\n\nBody.\n",
        encoding="utf-8",
    )
    suggestion = tmp_path / "metadata-suggestion.json"
    suggestion.write_text(
        json.dumps(
            {
                "kind": "seo_metadata_suggestion",
                "status": "PARTIAL",
                "file_path": "_posts/post.md",
                "candidate": {
                    "title": "New title",
                    "description": "New description",
                    "categories": ["Translation", "HuggingFace"],
                    "image": "/assets/thumb.png",
                    "canonical": "https://should-not-apply.example/",
                },
                "apply": {"allowed": False, "requires_human": True},
                "needs_policy_decision": ["canonical_policy"],
            }
        ),
        encoding="utf-8",
    )

    result = apply_feedback(
        target_root=tmp_path,
        file_path="_posts/post.md",
        feedback="metadata apply",
        max_changed_lines=20,
        model_call=lambda prompt: pytest.fail("metadata apply should not call the model"),
        metadata_suggestion_path=suggestion,
    )

    updated = post.read_text(encoding="utf-8")
    assert result.disposition == "actionable"
    assert "Applied fields: title, description, categories, image." in result.reason
    assert "description: New description" in updated
    assert "canonical:" not in updated


def test_apply_feedback_requires_metadata_suggestion_for_metadata_apply(tmp_path: Path) -> None:
    post = tmp_path / "_posts" / "post.md"
    post.parent.mkdir()
    post.write_text("Original\n", encoding="utf-8")

    result = apply_feedback(
        target_root=tmp_path,
        file_path="_posts/post.md",
        feedback="metadata apply",
        max_changed_lines=20,
        model_call=lambda prompt: pytest.fail("metadata apply should not call the model"),
    )

    assert result.disposition == "needs-human"
    assert "no metadata suggestion" in result.reason
    assert post.read_text(encoding="utf-8") == "Original\n"


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
            "instructions": "Return the repair decision as structured JSON.",
            "max_output_tokens": MAX_REPAIR_OUTPUT_TOKENS,
            "model": "gpt-test",
            "text": {"format": REPAIR_RESPONSE_FORMAT},
        }
    ]


def test_feedback_cli_writes_metadata_intent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    post = tmp_path / "_posts" / "post.md"
    post.parent.mkdir()
    post.write_text(
        "---\ntitle: Old title\ncategories:\n  - Translation\n---\n# Old title\n\nBody.\n",
        encoding="utf-8",
    )
    suggestion = tmp_path / "metadata-suggestion.json"
    suggestion.write_text(
        json.dumps(
            {
                "kind": "seo_metadata_suggestion",
                "status": "PARTIAL",
                "file_path": "_posts/post.md",
                "candidate": {"description": "New description"},
                "apply": {"allowed": False, "requires_human": True},
                "needs_policy_decision": ["canonical_policy"],
            }
        ),
        encoding="utf-8",
    )
    result_json = tmp_path / "result.json"

    from hf_agent import handle_pr_feedback

    assert handle_pr_feedback.main.__module__ == "hf_agent.handle_pr_feedback"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "handle_pr_feedback",
            "--target-root",
            str(tmp_path),
            "--file",
            "_posts/post.md",
            "--feedback",
            "metadata apply",
            "--metadata-suggestion",
            str(suggestion),
            "--result-json",
            str(result_json),
        ],
    )

    assert handle_pr_feedback.main() == 0
    payload = json.loads(result_json.read_text())
    assert payload["changed"] is True
    assert payload["intent"] == "metadata"


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
