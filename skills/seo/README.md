# SEO Skill

Reusable SEO/GEO review for a single Korean Hugging Face Blog translation in
`Hugging-Face-KREW/hugging-face-krew.github.io`. See `SKILL.md` for the full
spec; this is the quick reference.

## Modules

- **Module 1 — Eval:** body-only deterministic gate + optional semantic judge
  seam. Produces `PASS`, `NEEDS_CHANGES`, `FAIL`, or `BLOCKED`, plus markdown
  and JSON output.
- **Module 2 — Metadata writer:** policy-aware metadata candidate generation and
  deterministic write-back for an approved `MetadataPlan` are implemented and
  tested (`tools/metadata.py`).

Translation quality is **out of scope** (separate quality skill).

## Usage

```bash
# PR / pre-publish flow (from a translation-flow manifest)
python tools/seo_eval.py --manifest <manifest.yaml> \
  --target-root <cloned target repo> --output <report.md>

# Published flow (direct file)
python tools/seo_eval.py --file _posts/2025-12-01-rteb.md \
  --target-root ../hugging-face-krew.github.io --output /tmp/seo.md
```

Outputs `<report.md>` and `<report>.json`. Exit code: `0` only for `PASS`, `1`
for `NEEDS_CHANGES`, `FAIL`, or `BLOCKED`. Add `--primary-keyword` to enable the
keyword checks (D5/D10); the manifest's `handoff.seo.primary_keyword` is empty
in practice. `--benchmark heuristic` adds an informational Lighthouse-SEO score
(never affects the gate).

## PR agent outputs

The existing HF Agent review bot depends on stable SEO output names:

- `results/seo.md`: human-readable SEO Eval Report / rubric feedback.
- `results/seo.json`: PR-agent wrapper, e.g.
  `{"skill":"seo","conclusion":"pass","report_path":"results/seo.md"}`.
- `results/seo-eval.json`: full machine-readable `seo_eval.py` result.
- `results/metadata-suggestion.json`: metadata candidate JSON for later
  review/apply. It deliberately omits `skill` and `conclusion` so existing PR
  report and repair loaders do not treat it as a gate result.

For local/daily reports the same split is written under `reports/<report_id>/`
as `seo-report.md`, `seo-eval.json`, and `metadata-suggestion.json`.

## Quality-status fixtures

The test harness is not meant to make every existing blog post pass. It checks
whether the skill consistently separates representative quality levels:

- `excellent-post.md` → `PASS`
- `good-post.md` → `PASS` with possible advisory feedback
- `medium-post.md` → `NEEDS_CHANGES`
- `poor-post.md` → `FAIL`
- `blocked-post.md` → `BLOCKED`

Existing HFKREW posts are kept as regression samples only; they prove the tool
does not crash on realistic content and document current behavior.

Additional internal samples live under `tests/fixtures/real/` and
`tests/fixtures/mutated/`. See `tests/fixtures/README.md` for the sample
catalog and intended failure modes.

## Internal batch sample audit

For practical resilience checks across many existing posts, run:

```bash
python tools/sample_audit.py \
  --posts-dir ../hugging-face-krew.github.io/_posts \
  --target-root ../hugging-face-krew.github.io \
  --json reports/internal-hfkrew-31-sample-audit.json \
  --markdown reports/internal-hfkrew-31-sample-audit.md
```

This collects each post's status, frontmatter metadata, content shape, required
failures, and blockers. It is an internal material audit, not a merge gate.

## Tests

```bash
pip install -e .[dev]          # pyyaml + pytest + markdown + beautifulsoup4
python -m pytest tests          # functional unit tests + golden regression, offline
UPDATE_GOLDEN=1 python -m pytest tests/test_golden_regression.py   # re-baseline golden
```

## Layout

```
tools/
  seo_eval.py        # orchestrator: body-only AND gate, manifest|--file input
  report.py          # markdown renderer over the result dict
  rubric.py          # R1–R6 compatibility + semantic/alt judge seams
  metadata.py        # policy-aware metadata candidate + deterministic write-back
  metadata_suggestion.py  # read-only metadata candidate JSON output
  checkers/          # content / keywords / images / frontmatter / seo_audits
  utils.py           # frontmatter parse + text metrics
  heuristic.py       # Lighthouse Tier-B heuristic
  benchmark.py       # Lighthouse Tier-A/B orchestrator (informational)
tests/               # pytest harness + fixtures/ + golden/
```

> `tools/simple_seo_report.py` is the legacy minimal checker, kept only for the
> old `tests/test_simple_seo_report.py`. `seo_eval.py` supersedes it.
