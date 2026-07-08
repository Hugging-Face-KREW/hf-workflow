"""Configurable SEO review policy.

Checkers should collect deterministic evidence. This module owns the mapping
from check names to gating severity so projects can tune policy without editing
checker code.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

POLICY_ROOT = Path(__file__).resolve().parents[1] / "config"
DEFAULT_POLICY = POLICY_ROOT / "default-policy.yml"

VALID_SEVERITIES = {"blocker", "required", "review", "recommended", "optional", "info"}


def load_policy(manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    base = yaml.safe_load(DEFAULT_POLICY.read_text(encoding="utf-8")) or {}
    manifest = manifest or {}
    seo = (manifest.get("handoff", {}) or {}).get("seo", {}) or {}
    override = seo.get("policy", {}) or {}

    merged = deepcopy(base)
    if override.get("severities"):
        severities = merged.setdefault("severities", {})
        severities.update(override["severities"])
    if override.get("llm_judges"):
        judges = merged.setdefault("llm_judges", {})
        for name, config in override["llm_judges"].items():
            if isinstance(config, dict) and isinstance(judges.get(name), dict):
                judges[name].update(config)
            else:
                judges[name] = config
    if "rubric_required" in override:
        merged["rubric_required"] = bool(override["rubric_required"])
    return merged


def apply_policy(checks: list[dict[str, Any]], policy: dict[str, Any]) -> list[dict[str, Any]]:
    severities = policy.get("severities", {}) or {}
    applied = []
    for check in checks:
        item = dict(check)
        configured = severities.get(item.get("name"))
        # An explicitly skipped info check should remain informational. Example:
        # no primary_keyword supplied means keyword policy is not applicable.
        if configured and item.get("severity") != "info":
            if configured not in VALID_SEVERITIES:
                raise ValueError(f"invalid severity for {item.get('name')}: {configured}")
            item["default_severity"] = item.get("severity")
            item["severity"] = configured
        applied.append(item)
    return applied
