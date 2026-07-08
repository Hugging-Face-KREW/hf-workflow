#!/usr/bin/env python3
"""Body-only SEO evaluation orchestrator (Module 1).

Evaluates a post's BODY (structure / keywords / images) against a deterministic
REQUIRED gate (D1–D7) AND an LLM rubric (R1–R6). Frontmatter is intentionally
excluded from the gate — the metadata writer (Module 2) generates it *after* a
pass, so gating on it would deadlock (design `seo-eval-decisions.md` §2–§3).

The deterministic gate always runs offline. Optional schema-bound rubric checks
can be injected by the caller; without them the gate runs on deterministic
results alone.

Inputs (mutually exclusive):
  --manifest <yaml>                  translation-flow manifest (PR / pre-publish flow)
  --file <path> [--target-root <dir>]  a post in the target repo (published flow)

Outputs: a markdown report (--output, else stdout) and a machine-readable JSON
sibling. Exit code: 0 if the gate passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).parent))

import yaml  # noqa: E402

from checkers import (  # noqa: E402
    check_blockers,
    check_content_structure,
    check_frontmatter,
    check_images,
    check_keywords,
)
import report as report_mod  # noqa: E402
import rubric as rubric_mod  # noqa: E402
from policy import apply_policy, load_policy  # noqa: E402
from signals import collect_signals  # noqa: E402

# Severities that gate the result vs. those shown for information only.
_GATED = "required"
_ADVISORY = ("review", "recommended", "optional", "info")


def classify_status(
    blockers_passed: bool,
    gate_passed: bool,
    required_checks: list[dict[str, Any]],
    rubric_checks: list[dict[str, Any]] | None = None,
) -> str:
    """Map checker results onto the review states used by PR feedback.

    PASS means the post can proceed to metadata generation. NEEDS_CHANGES is a
    small, fixable quality gap. FAIL is broader body-quality failure. BLOCKED is
    reserved for explicit publish-safety issues such as noindex or broken local
    internal links.
    """
    if not blockers_passed:
        return "BLOCKED"
    if gate_passed:
        return "PASS"
    failed_required = [c for c in required_checks if not c.get("passed")]
    failed_required += [
        c for c in (rubric_checks or [])
        if c.get("severity") == _GATED and not c.get("passed")
    ]
    return "NEEDS_CHANGES" if len(failed_required) == 1 else "FAIL"


def _load_manifest(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_inputs(args: argparse.Namespace) -> dict[str, Any]:
    """Normalize either --manifest or --file into one input bundle."""
    if args.manifest:
        manifest = _load_manifest(Path(args.manifest))
        translation = manifest.get("translation", {}) or {}
        seo = (manifest.get("handoff", {}) or {}).get("seo", {}) or {}
        file_path = translation.get("file_path", "")
        source_url = (manifest.get("source", {}) or {}).get("url", "")
        primary = args.primary_keyword or seo.get("primary_keyword", "") or ""
        secondary = seo.get("secondary_keywords", []) or []
        mode = "manifest"
    else:
        file_path = args.file
        source_url = args.source_url or ""
        primary = args.primary_keyword or ""
        secondary = []
        manifest = {
            "source": {"url": source_url},
            "translation": {"file_path": file_path, "locale": args.locale or ""},
        }
        mode = "file"

    target_root = Path(args.target_root) if args.target_root else None
    post_path = (target_root / file_path) if target_root else Path(file_path)
    content = post_path.read_text(encoding="utf-8")
    frontmatter, body = parse_inputs(content)

    return {
        "manifest": manifest,
        "file_path": file_path,
        "source_url": source_url,
        "primary_keyword": primary,
        "secondary_keywords": secondary,
        "mode": mode,
        "target_root": target_root,
        "post_path": post_path,
        "content": content,
        "frontmatter": frontmatter,
        "body": body,
    }


def parse_inputs(content: str):
    # Local indirection so utils stays the single frontmatter parser.
    from utils import parse_frontmatter
    return parse_frontmatter(content)


def _slim(checker_result: dict[str, Any]) -> dict[str, Any]:
    return {k: checker_result[k] for k in ("passed", "score", "summary")
            if k in checker_result}


def evaluate(
    inp: dict[str, Any],
    *,
    benchmark_mode: str = "off",
    benchmark_url: Optional[str] = None,
    rubric_judge=None,
) -> dict[str, Any]:
    """Run the body-only deterministic gate + rubric seam. Returns a fully
    deterministic, path-relative result dict (safe to snapshot as golden)."""
    body = inp["body"]
    frontmatter = inp["frontmatter"]
    primary = inp["primary_keyword"]
    secondary = inp["secondary_keywords"]
    target_root = inp["target_root"]
    rel_post = inp["file_path"]

    blockers_res = check_blockers(frontmatter, body, target_root, rel_post if target_root else None)
    content_res = check_content_structure(inp["content"], body, primary)
    keyword_res = check_keywords(body, primary, secondary)
    images_res = check_images(body, target_root, rel_post if target_root else None)
    signals = collect_signals(
        inp["content"],
        body,
        frontmatter,
        target_root=target_root,
        post_path=rel_post if target_root else None,
    )

    review_policy = load_policy(inp["manifest"])
    all_checks = apply_policy(
        content_res["checks"] + keyword_res["checks"] + images_res["checks"],
        review_policy,
    )
    required = [c for c in all_checks if c.get("severity") == _GATED]
    advisory = [c for c in all_checks if c.get("severity") in _ADVISORY]
    det_passed = all(c["passed"] for c in required)

    if rubric_judge is None:
        rub = rubric_mod.evaluate(
            body, frontmatter, inp["manifest"],
            source_url=inp["source_url"], primary_keyword=primary,
        )
    else:
        rubric_manifest = deepcopy(inp["manifest"])
        handoff = rubric_manifest.setdefault("handoff", {})
        seo = handoff.setdefault("seo", {})
        seo["policy"] = review_policy
        rub = rubric_mod.evaluate_from_signals(
            signals,
            rubric_manifest,
            judge=rubric_judge,
        )
    rubric_passed = rub.passed  # None when the rubric did not run

    if rubric_passed is None:
        gate_passed = det_passed
        reason = ("deterministic gate only (rubric judge not configured)"
                  if det_passed else "deterministic REQUIRED checks failed")
    else:
        gate_passed = det_passed and rubric_passed
        reason = "deterministic AND rubric"

    status = classify_status(blockers_res["passed"], gate_passed, required, rub.checks)
    final_passed = status == "PASS"

    result: dict[str, Any] = {
        "input": {
            "file_path": rel_post,
            "source_url": inp["source_url"],
            "primary_keyword": primary,
            "mode": inp["mode"],
        },
        "deterministic": {
            "required": {"passed": det_passed, "checks": required},
            "advisory": {"checks": advisory},
            "checkers": {
                "content": _slim(content_res),
                "keywords": _slim(keyword_res),
                "images": _slim(images_res),
            },
        },
        "blockers": blockers_res,
        "policy": {
            "name": review_policy.get("name", "default"),
            "severities": review_policy.get("severities", {}),
            "rubric_required": bool(review_policy.get("rubric_required", False)),
        },
        "signals": signals,
        "rubric": rub.to_dict(),
        "frontmatter_advisory": check_frontmatter(frontmatter),  # NOT gated
        "gate": {
            "passed": final_passed,
            "status": status,
            "deterministic_passed": det_passed,
            "blockers_passed": blockers_res["passed"],
            "rubric_passed": rubric_passed,
            "reason": reason,
        },
    }

    if benchmark_mode != "off":
        result["benchmark"] = _run_benchmark_safe(
            inp, body, frontmatter, benchmark_mode, benchmark_url)

    return result


def evaluate_path(
    post_path,
    *,
    target_root=None,
    source_url: str = "",
    primary_keyword: str = "",
    secondary_keywords: Optional[list[str]] = None,
    locale: str = "",
    benchmark_mode: str = "off",
    benchmark_url: Optional[str] = None,
    rubric_judge=None,
) -> dict[str, Any]:
    """Evaluate a single post file directly (used by the published flow and
    tests). ``file_path`` in the result is repo-relative (or the basename when
    no ``target_root`` is given), so the result stays portable/snapshot-stable.
    """
    post_path = Path(post_path)
    troot = Path(target_root) if target_root else None
    if troot is not None:
        full = post_path if post_path.is_absolute() else troot / post_path
        file_path = str(full.relative_to(troot))
    else:
        full = post_path
        file_path = post_path.name

    content = full.read_text(encoding="utf-8")
    frontmatter, body = parse_inputs(content)
    inp = {
        "manifest": {"source": {"url": source_url},
                     "translation": {"file_path": file_path, "locale": locale}},
        "file_path": file_path,
        "source_url": source_url,
        "primary_keyword": primary_keyword,
        "secondary_keywords": secondary_keywords or [],
        "mode": "file",
        "target_root": troot,
        "post_path": full,
        "content": content,
        "frontmatter": frontmatter,
        "body": body,
    }
    return evaluate(
        inp,
        benchmark_mode=benchmark_mode,
        benchmark_url=benchmark_url,
        rubric_judge=rubric_judge,
    )


def _run_benchmark_safe(inp, body, frontmatter, mode, url) -> dict[str, Any]:
    """Benchmark is informational and must never block; swallow any failure
    (incl. missing markdown/bs4) into a reported error row."""
    try:
        from benchmark import run_benchmark
        return run_benchmark(
            inp["manifest"], inp["target_root"] or Path("."),
            body, frontmatter, mode=mode, benchmark_url=url,
        )
    except Exception as exc:  # noqa: BLE001
        return {"mode": "error", "score": 0, "fallback_reason": str(exc),
                "audits": [], "passed": False}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Body-only SEO evaluation (Module 1).")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--manifest", help="translation-flow manifest YAML (PR flow)")
    src.add_argument("--file", help="post path within --target-root (published flow)")
    p.add_argument("--target-root", help="cloned target repo root (enables D7 file check)")
    p.add_argument("--source-url", help="source post URL (published flow)")
    p.add_argument("--primary-keyword", default="", help="override primary keyword")
    p.add_argument("--locale", default="", help="post locale (published flow)")
    p.add_argument("--output", help="markdown report path (default: stdout)")
    p.add_argument("--json", dest="json_out",
                   help="JSON result path (default: <output>.json when --output set)")
    p.add_argument("--benchmark", choices=["auto", "lighthouse", "heuristic", "off"],
                   default="off", help="Lighthouse SEO benchmark (informational)")
    p.add_argument("--benchmark-url", default=None,
                   help="audit a published URL directly (post-publish re-check)")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    inp = resolve_inputs(args)
    result = evaluate(inp, benchmark_mode=args.benchmark,
                      benchmark_url=args.benchmark_url)
    md = report_mod.render_markdown(result, post_display=str(inp["post_path"]))

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        json_path = Path(args.json_out) if args.json_out else out.with_suffix(".json")
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        print(f"Wrote SEO report: {out}")
        print(f"Wrote SEO eval JSON: {json_path}")
    else:
        sys.stdout.write(md)
        if args.json_out:
            Path(args.json_out).write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    return 0 if result["gate"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
