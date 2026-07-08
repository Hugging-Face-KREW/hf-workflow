"""Schema-bound qualitative SEO judges.

Deterministic checks own objective failures such as noindex, missing alt, broken
local links, and heading structure. This module owns only judgments that require
semantic comparison:

* metadata meaning consistency: title/description/H1/opening should not promise
  different topics.
* non-empty alt usefulness: alt text that exists but is generic (``image-1``) or
  file-like should be surfaced without hard-coding every bad string.

The default path remains offline-safe. If a caller does not provide a judge
function, ``evaluate()`` returns ``available=False`` as before. CI tests inject a
stub judge, and production can wire this seam to a schema-bound LLM call.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

JudgeFn = Callable[[str, dict[str, Any]], dict[str, Any]]
PASS_STATUSES = {"PASS"}
RUBRIC_ITEMS: dict[str, str] = {
    "R1": "첫 문단 답변성(GEO): 맥락 없이 핵심 질문에 직답/정의",
    "R2": "heading 검색의도 정합성",
    "R3": "alt 의미 정확성",
    "R4": "citation 권위·적합성",
    "R5": "인용가능성(자기완결 문장)",
    "R6": "키워드 검색-무결성 (검색어 용어 보존)",
}

PASS_MEAN = 4.0
PASS_MIN = 3


@dataclass
class RubricResult:
    """Outcome of the rubric pass.

    ``available=False`` means the rubric did not run; ``passed`` is then ``None``
    and the orchestrator falls back to the deterministic gate alone.
    """

    available: bool = False
    checks: list[dict[str, Any]] = field(default_factory=list)
    scores: dict[str, int] = field(default_factory=dict)  # retained for legacy reports
    notes: dict[str, str] = field(default_factory=dict)  # retained for legacy reports
    required: bool = False
    reason: str = "rubric not run (stage-1 skeleton)"

    @property
    def mean(self) -> Optional[float]:
        if not self.scores:
            return None
        return round(sum(self.scores.values()) / len(self.scores), 2)

    @property
    def min(self) -> Optional[int]:
        return min(self.scores.values()) if self.scores else None

    @property
    def passed(self) -> Optional[bool]:
        if not self.available:
            return None
        if self.scores:
            return self.mean >= PASS_MEAN and self.min >= PASS_MIN
        required = [c for c in self.checks if c.get("severity") == "required"]
        if not required:
            return True
        return all(c.get("status") in PASS_STATUSES for c in required)

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "checks": self.checks,
            "scores": self.scores,
            "mean": self.mean,
            "min": self.min,
            "notes": self.notes,
            "required": self.required,
            "passed": self.passed,
            "reason": self.reason,
        }


def _seo_policy(manifest: dict[str, Any]) -> dict[str, Any]:
    seo = (manifest.get("handoff", {}) or {}).get("seo", {}) or {}
    return seo.get("policy", {}) or {}


def _llm_judge_config(manifest: dict[str, Any]) -> dict[str, Any]:
    policy = _seo_policy(manifest)
    return policy.get("llm_judges", {}) or {}


def _judge_enabled(config: dict[str, Any], name: str) -> bool:
    value = config.get(name, {})
    if value is False:
        return False
    if isinstance(value, dict):
        return bool(value.get("enabled", False))
    return bool(value)


def _judge_severity(config: dict[str, Any], name: str, default: str) -> str:
    value = config.get(name, {})
    if isinstance(value, dict):
        return str(value.get("severity") or default)
    return default


def semantic_metadata_payload(signals: dict[str, Any]) -> dict[str, Any]:
    sem = signals.get("semantic_review", {}) or {}
    headings = signals.get("headings", {}) or {}
    return {
        "frontmatter": {
            "title": sem.get("title_text", ""),
            "description": sem.get("description_text", ""),
        },
        "opening": sem.get("opening_text", ""),
        "rendered_h1": sem.get("rendered_h1_texts", []) or [],
        "headings": headings.get("markdown_headings", [])[:12],
        "instruction": (
            "Compare only meaning among present title, description, rendered H1, "
            "headings, and opening. Ignore missing fields, length, noindex, "
            "canonical/hreflang, links, images, and alt text."
        ),
    }


def alt_semantics_payload(signals: dict[str, Any]) -> dict[str, Any]:
    images = signals.get("images", {}) or {}
    return {
        "image_count": images.get("total_count", 0),
        "non_empty_alt_count": sum(
            1 for img in images.get("image_details", []) if str(img.get("alt", "")).strip()
        ),
        "images": images.get("image_details", [])[:30],
        "instruction": (
            "Evaluate only non-empty alt text usefulness. Ignore empty alt text; "
            "coverage is handled by deterministic validators."
        ),
    }


def _normalize_semantic_metadata(raw: dict[str, Any], *, severity: str) -> dict[str, Any]:
    status = str(raw.get("status") or "PASS").upper()
    if status not in {"PASS", "NEEDS_CHANGES", "FAIL"}:
        status = "FAIL"
    issues = raw.get("issues") or raw.get("findings") or []
    if not isinstance(issues, list):
        issues = [str(issues)]
    return {
        "name": "semantic_metadata",
        "severity": severity,
        "status": status,
        "passed": status == "PASS",
        "issues": [str(issue) for issue in issues],
        "evidence": raw.get("evidence", []) if isinstance(raw.get("evidence", []), list) else [],
        "reason": str(raw.get("reason") or raw.get("rationale") or ""),
    }


def _normalize_alt_semantics(raw: dict[str, Any], *, severity: str) -> dict[str, Any]:
    status = str(raw.get("status") or "PASS").upper()
    if status not in {"PASS", "NEEDS_CHANGES", "FAIL"}:
        status = "FAIL"
    problems = raw.get("problem_images") or []
    if not isinstance(problems, list):
        problems = []
    return {
        "name": "alt_semantics",
        "severity": severity,
        "status": status,
        "passed": status == "PASS",
        "problem_images": problems,
        "reason": str(raw.get("reason") or ""),
    }


def evaluate_from_signals(
    signals: dict[str, Any],
    manifest: dict[str, Any],
    *,
    judge: JudgeFn | None = None,
) -> RubricResult:
    """Evaluate configured semantic judges from deterministic evidence.

    ``judge`` receives ``(judge_name, payload)`` and must return a dict matching
    that judge's schema. Keeping the call injectable makes tests deterministic
    and avoids hard-coding a model provider into the harness.
    """
    config = _llm_judge_config(manifest)
    enabled = [
        name for name in ("semantic_metadata", "alt_semantics")
        if _judge_enabled(config, name)
    ]
    required_legacy = bool(_seo_policy(manifest).get("rubric_required", False))
    if not enabled:
        return RubricResult(
            available=False,
            required=required_legacy,
            reason=(
                "rubric required by policy but no llm_judges are enabled"
                if required_legacy else
                "rubric not run (schema-bound judges not configured)"
            ),
        )
    if judge is None:
        return RubricResult(
            available=False,
            required=required_legacy or any(
                _judge_severity(config, name, "required" if name == "semantic_metadata" else "review")
                == "required"
                for name in enabled
            ),
            reason="rubric configured but no schema-bound judge function was provided",
        )

    checks: list[dict[str, Any]] = []
    if "semantic_metadata" in enabled:
        severity = _judge_severity(config, "semantic_metadata", "required")
        checks.append(_normalize_semantic_metadata(
            judge("semantic_metadata", semantic_metadata_payload(signals)),
            severity=severity,
        ))
    if "alt_semantics" in enabled:
        severity = _judge_severity(config, "alt_semantics", "review")
        checks.append(_normalize_alt_semantics(
            judge("alt_semantics", alt_semantics_payload(signals)),
            severity=severity,
        ))

    return RubricResult(
        available=True,
        checks=checks,
        required=any(c.get("severity") == "required" for c in checks),
        reason="schema-bound semantic judges",
    )


def evaluate(
    body: str,
    frontmatter: dict[str, Any],
    manifest: dict[str, Any],
    *,
    source_url: str = "",
    primary_keyword: str = "",
) -> RubricResult:
    """Backward-compatible seam used by the current orchestrator.

    The real semantic judges need the deterministic ``signals`` packet. Call
    ``evaluate_from_signals`` from new integrations; this legacy function stays
    offline-safe for existing tests and CLI behavior.
    """
    policy = _seo_policy(manifest)
    required = bool(policy.get("rubric_required", False))
    reason = (
        "rubric required by policy but not run"
        if required else
        "rubric not run (schema-bound policy judge not configured)"
    )
    return RubricResult(
        available=False,
        required=required,
        reason=reason,
    )
