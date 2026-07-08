"""Render an SEO eval result (from ``seo_eval.evaluate``) as markdown.

Kept separate from the orchestrator so the machine-readable result dict stays
the single source of truth and the human report is a pure view over it.
"""
from __future__ import annotations

from typing import Any


def _check_line(c: dict[str, Any]) -> str:
    sev = c.get("severity", "")
    if sev == "info":
        return f"ℹ️ {c['name']}: {c['message']}"
    icon = "✅" if c["passed"] else ("⛔" if sev == "blocker" else "❌" if sev == "required" else "🟠" if sev == "review" else "⚠️")
    return f"{icon} {c['name']}: {c['message']}"


def _rubric_summary(rub: dict[str, Any]) -> str:
    if not rub.get("available"):
        return f"skeleton — not run ({rub.get('reason', '')})"
    passed = rub.get("passed")
    return (f"{'✅ pass' if passed else '❌ fail'} "
            f"(mean {rub.get('mean')}, min {rub.get('min')})")


def render_markdown(result: dict[str, Any], *, post_display: str = "") -> str:
    gate = result["gate"]
    det = result["deterministic"]
    inp = result["input"]

    lines: list[str] = []
    status_label = gate.get("status", "PASS" if gate["passed"] else "FAIL")
    status_icons = {
        "PASS": "✅ PASS",
        "NEEDS_CHANGES": "🟡 NEEDS_CHANGES",
        "FAIL": "❌ FAIL",
        "BLOCKED": "⛔ BLOCKED",
    }
    status = status_icons.get(status_label, status_label)
    lines += [
        "# SEO Eval Report",
        "",
        f"**Gate: {status}** — {gate['reason']}",
        "",
        f"- File: `{post_display or inp['file_path']}`",
        f"- Source: {inp.get('source_url') or '—'}",
        f"- Primary keyword: {inp.get('primary_keyword') or '(none — D5 skipped)'}",
        f"- Mode: {inp['mode']}",
        "",
        "## Gate",
        "",
        f"- Status: `{status_label}`",
        f"- Blockers: {'✅ pass' if gate.get('blockers_passed', True) else '⛔ blocked'}",
        f"- Deterministic REQUIRED (D1–D7): "
        f"{'✅ pass' if det['required']['passed'] else '❌ fail'}",
        f"- Rubric (R1–R6): {_rubric_summary(result['rubric'])}",
        "",
        "## Blockers",
        "",
    ]
    blockers = result.get("blockers", {})
    lines += [_check_line(c) for c in blockers.get("checks", [])] or ["_(none)_"]

    lines += [
        "",
        "## Required checks (gated)",
        "",
    ]
    lines += [_check_line(c) for c in det["required"]["checks"]] or ["_(none)_"]

    lines += ["", "## Advisory checks (not gated)", ""]
    lines += [_check_line(c) for c in det["advisory"]["checks"]] or ["_(none)_"]

    sig = result.get("signals")
    if sig:
        lines += [
            "",
            "## Signals (evidence — not directly gated)",
            "",
            f"- Frontmatter: title `{sig['frontmatter']['title_chars']}` chars, "
            f"description `{sig['frontmatter']['description_chars']}` chars, "
            f"author present `{sig['frontmatter']['author_present']}`",
            f"- Title text: {sig['frontmatter'].get('title_text') or '—'}",
            f"- Description text: {sig['frontmatter'].get('description_text') or '—'}",
            f"- Opening text: {sig['opening'].get('first_real_paragraph') or '—'}",
            f"- Opening: first paragraph `{sig['opening']['first_real_paragraph_chars']}` chars, "
            f"first 3 paragraphs `{sig['opening']['first_three_paragraph_chars']}` chars",
            f"- Headings: markdown H1 `{sig['headings']['markdown_h1_count']}`, "
            f"rendered effective H1 `{sig['headings']['rendered_effective_h1_count']}`, "
            f"layout title H1 `{sig['headings']['layout_title_used_as_h1']}`",
            f"- Links: total `{sig['links']['total_count']}`, external `{sig['links']['external_count']}`, "
            f"internal `{sig['links']['internal_count']}`, citation signals `{sig['links']['citation_signal_count']}`",
            f"- Images: total `{sig['images']['total_count']}`, empty alt `{sig['images']['empty_alt_count']}`, "
            f"filename-like alt `{sig['images']['filename_like_alt_count']}`, "
            f"missing local files `{sig['images']['missing_local_file_count']}`",
        ]
        sem = sig.get("semantic_review")
        if sem:
            lines += [
                "",
                "### Semantic review packet",
                "",
                f"- Title: {sem.get('title_text') or '—'}",
                f"- Description: {sem.get('description_text') or '—'}",
                f"- Rendered H1 candidates: {', '.join(sem.get('rendered_h1_texts') or []) or '—'}",
                f"- Opening: {sem.get('opening_text') or '—'}",
                f"- Canonical/permalink: {sem.get('canonical') or '—'}",
                f"- Instruction: {sem.get('review_instruction')}",
            ]

    fm = result.get("frontmatter_advisory")
    if fm:
        lines += [
            "",
            "## Frontmatter (advisory — written by metadata step, not gated)",
            "",
        ]
        lines += [_check_line(c) for c in fm["checks"]]

    if not gate["passed"]:
        blocker_fails = [c for c in blockers.get("checks", []) if not c["passed"]]
        fails = [c for c in det["required"]["checks"] if not c["passed"]]
        if blocker_fails:
            lines += ["", "## Feedback — blockers to resolve first", ""]
            lines += [f"{i}. **{c['name']}** — {c['message']}"
                      for i, c in enumerate(blocker_fails, 1)]
        if fails:
            lines += ["", "## Feedback — fix these to pass", ""]
            lines += [f"{i}. **{c['name']}** — {c['message']}"
                      for i, c in enumerate(fails, 1)]

    bm = result.get("benchmark")
    if bm:
        lines += [
            "",
            "## Benchmark (Lighthouse SEO — informational, not gated)",
            "",
            f"**{bm.get('score', 0)}/100** (mode: {bm.get('mode', '?')}"
            + (f" — {bm['fallback_reason']}" if bm.get("fallback_reason") else "")
            + ")",
        ]
        for a in bm.get("audits", []):
            icon = {"pass": "✅", "fail": "❌", "na": "➖"}.get(a.get("status"), "·")
            lines.append(f"{icon} {a.get('label', a.get('name'))}: {a.get('message', '')}")

    return "\n".join(lines) + "\n"
