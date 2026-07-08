"""Golden snapshot regression over a fixed fixture set.

Locks the orchestrator's structured output so any behavior change surfaces as a
diff. This verifies STABILITY, not output quality. Fixtures are drop-in: add or
remove a post and re-baseline with ``UPDATE_GOLDEN=1``. The golden mechanism is
intentionally decoupled from fixture realism — see the plan's harness note.
"""
import json
import os

import pytest

from seo_eval import evaluate_path

FIXTURES = [
    "generated/excellent-post",
    "generated/good-post",
    "generated/medium-post",
    "generated/poor-post",
    "generated/blocked-post",
    "real/2025-12-01-rteb",
    "real/2025-12-22-smolvla",
    "real/2025-12-15-ai-agents-are-here",
]


@pytest.mark.parametrize("rel", FIXTURES)
def test_golden(rel, fixtures_dir):
    golden_dir = fixtures_dir.parent / "golden"
    golden_dir.mkdir(exist_ok=True)
    post = fixtures_dir / f"{rel}.md"

    # No target_root, no keyword -> fully deterministic, repo-portable result.
    result = evaluate_path(post)
    serialized = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    golden = golden_dir / (rel.replace("/", "__") + ".json")
    if os.environ.get("UPDATE_GOLDEN") == "1":
        golden.write_text(serialized, encoding="utf-8")
        return
    if not golden.exists():
        golden.write_text(serialized, encoding="utf-8")
        pytest.skip(f"golden created: {golden.name} (re-run to compare)")
    assert serialized == golden.read_text(encoding="utf-8"), (
        f"output drifted from golden for {rel}; "
        f"if intended, re-run with UPDATE_GOLDEN=1"
    )


def test_determinism_same_input_same_output(fixtures_dir):
    post = fixtures_dir / "real" / "2025-12-01-rteb.md"
    a = json.dumps(evaluate_path(post), sort_keys=True)
    b = json.dumps(evaluate_path(post), sort_keys=True)
    assert a == b
