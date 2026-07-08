---
name: blog-seo
description: >-
  Evaluate and improve a Hugging Face KREW blog post (Korean translation or
  already-published post) for SEO/GEO. Use when asked to run an SEO
  review/audit, give SEO feedback on a post body, check a PR's translated post
  before publishing, or write SEO metadata. Runs from a translation-flow
  manifest (PR flow) or a direct file path (published flow). Out of scope:
  translation quality (fidelity/fluency/terminology).
---

# HF Blog SEO Skill

SEO/GEO review for `Hugging-Face-KREW/hugging-face-krew.github.io` posts. The
skill is two modules: Module 1 runs the deterministic gate and optional semantic
judge seam; Module 2 creates policy-aware metadata candidates and can write back
an approved metadata plan.

## When to use
- "SEO 평가/감사", "이 포스트 SEO 봐줘", "발행 전 PR SEO 체크", "메타데이터 작성".
- Applies to both **published** posts and **unpublished** (PR) posts.

## Out of scope
- Translation quality (fidelity / fluency / terminology) → separate quality skill.
  The rubric's R6 only checks keyword/term **search integrity**, not fluency.

## Workflow
```
SEO eval (body only) ──fail──> return feedback (failing REQUIRED checks)
                     └─pass──> build/apply approved metadata plan (Module 2)
```
- Eval gates the **body** only (structure / keyword / images). Frontmatter is
  **not** gated — the metadata writer generates it after a pass (avoids deadlock).
- Gate = deterministic required checks plus optional rubric checks when a
  schema-bound judge is injected. Without a judge function, the skill remains
  fully offline and gates on deterministic checks alone.
- In the PR agent, metadata generation is read-only: it writes
  `metadata-suggestion.json` for a later apply/repair step, but does not edit or
  commit the post.

## Inputs
- PR / pre-publish: `--manifest <translation-flow manifest.yaml>`
- Published: `--file <_posts/...md> --target-root <repo>` (+ `--source-url`, `--primary-keyword`)
- The manifest's `handoff.seo.primary_keyword` is empty in practice; pass
  `--primary-keyword` to enable D5/D10, otherwise they are skipped (non-blocking).

## Run
```bash
# PR flow — writes <output> and <output>.json; exit 0 only for PASS
python skills/seo/tools/seo_eval.py --manifest reports/pr-130/manifest.yaml \
  --target-root ../hugging-face-krew.github.io --output reports/pr-130/seo-report.md

# Published flow
python skills/seo/tools/seo_eval.py --file _posts/2025-12-01-rteb.md \
  --target-root ../hugging-face-krew.github.io --output /tmp/seo.md

# Optional informational Lighthouse SEO benchmark (Tier A real / Tier B heuristic)
python skills/seo/tools/seo_eval.py ... --benchmark heuristic
```

## PR agent output contract
- `results/seo.md`: existing Markdown SEO Eval Report used in PR comments and
  failed-gate repair feedback.
- `results/seo.json`: existing wrapper JSON with `skill`, `conclusion`, and
  `report_path`; kept for backwards compatibility.
- `results/seo-eval.json`: full SEO evaluation JSON.
- `results/metadata-suggestion.json`: metadata candidate JSON. It must not
  include `skill` or `conclusion`, so existing PR agent loaders ignore it as a
  non-gate artifact.

## Deterministic items (body only)
- **REQUIRED (hard gate):** D1 H1 count == 1 · D2 heading hierarchy (no skips) ·
  D3 opening length (KO ≥150 chars / EN ≥50 words) · D4 ≥1 citation ·
  D5 primary keyword in H1 + opening (skipped if no keyword) ·
  D6 alt coverage 100% + descriptive · D7 image files exist (with `--target-root`).
- **RECOMMENDED:** D8 question-or-keyword subheading · D9 internal links 2–3 ·
  D10 secondary keyword coverage. **OPTIONAL:** D11 body length · D12 WebP · D13 lazy.

## Statuses
- `PASS`: deterministic gate passes; metadata writer may run next.
- `NEEDS_CHANGES`: exactly one required quality check failed; return focused feedback.
- `FAIL`: multiple required quality checks failed; return body improvement feedback.
- `BLOCKED`: explicit publish-safety blocker such as `robots: noindex` or a broken local internal link.

The fixtures intentionally cover these quality levels. They are not a benchmark
that all existing blog posts must pass.

## Rubric / semantic judge
The legacy R1–R6 score contract is preserved for compatibility. New semantic
review uses two narrow seams: `semantic_metadata` for title/description/H1/body
meaning mismatch, and `alt_semantics` for non-empty but unhelpful alt text.
`semantic_metadata` is required when enabled; `alt_semantics` defaults to review.

## Tests (repeatable, offline)
```bash
python -m pytest skills/seo/tests        # functional unit tests + golden regression
UPDATE_GOLDEN=1 python -m pytest skills/seo/tests/test_golden_regression.py  # re-baseline
```
Verifies tool behavior and stability (not output quality). Golden fixtures are
drop-in and provisional. `tools/` holds the checkers; `tools/rubric.py` exposes
provider-free judge seams, and `tools/metadata.py` returns `PARTIAL` until
canonical/hreflang policy is supplied.
