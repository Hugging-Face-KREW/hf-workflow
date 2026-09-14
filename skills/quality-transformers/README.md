# Quality — transformers Docs profile

Korean translation quality review for **`github.com/huggingface/transformers`**
`docs/source/ko/**/*.md` pages. Scoped to the `transformers` repo only; see
`skills/quality` for Hugging Face blog posts.

This skill does **not** duplicate the scoring engine. It reuses
`skills/quality/tools/translation_quality_harness.py` and supplies its own
style guide, style policy, gates, evaluation config, glossary additions, and
judge prompt via CLI flags.

## Harness changes this profile depends on

The following **additive** changes were made to
`skills/quality/tools/translation_quality_harness.py` for this profile. The
blog test suite (`skills/quality/tests/`) still passes at the same
85 passed / 1 pre-existing-unrelated failure
(`test_openai_mqm_judge_runs_cache_misses_with_bounded_concurrency`,
`zip() takes no keyword arguments` on Python 3.9 — unrelated to this work).

1. `read_yaml_scalars`: an inline `key: []` now parses as an empty list.
   Previously it fell back to the hardcoded default, so
   `front_matter.required_target_keys: []` could not disable the frontmatter
   gate. The blog config uses the multi-line `- item` list form and is
   unaffected.
2. `strip_workflow_scaffold`: the doc-builder Apache license header comment
   block (`<!--Copyright <year> The HuggingFace Team ... -->`) is stripped
   before segmentation, so it is not compared as prose or style-checked. Blog
   posts do not carry this header.
3. `MarkdownDoc` gained `heading_anchors`, `heading_levels`, `directives`,
   `autodoc_refs`, `mdx_components` fields with matching `extract_*` functions.
4. Four **opt-in** hard gates in `validate_documents` (skipped unless the
   gates config sets `<gate>.enabled: true`):
   `anchor_preservation` (anchor multiset + heading-level sequence),
   `directive_preservation`, `autodoc_reference_preservation`,
   `mdx_component_preservation`. All compare source↔target as a multiset
   (Counter) difference, exactly like the `links`/`images` gates.
5. `validate_sentence_final_colon` (opt-in via
   `sentence_final_colon.enabled: true`): flags any Korean prose line that
   ends with `:`. Wired into `validate_documents` next to
   `validate_locale_punctuation`. `style_penalty` weight 8.
6. **Phase 5 fixes** — `anchor_preservation` now compares anchor **strings**
   only when the English source carries explicit `[[...]]` anchors (modern
   transformers sources omit them); the heading-**level** sequence check
   stays unconditional. `strip_bracket_heading_anchors` removes `[[slug]]`
   from heading lines before identifier/segment extraction so an
   `[[transformers.Foo]]` autodoc-path anchor no longer leaks into
   `protected_tokens`. `preserved_name_present` lets a Korean josa follow a
   preserved English name (`Transformers에서`) without a
   `preserve_product_name` false positive. All three are additive and
   blog-safe.

Every new gate is opt-in with `fallback=False`, so the `skills/quality` blog
profile does not run them unless its own gates config adds the keys. The
non-gate refinements (license-header strip, `[[slug]]` strip, glossary
particle tolerance) run for every profile but are no-ops on blog content —
`skills/quality/tests/` still passes at 85/86, unchanged from baseline.

## Tool command

```bash
python skills/quality/tools/translation_quality_harness.py \
  --manifest <manifest.yaml> \
  --target-root <transformers-checkout-root> \
  --source <transformers-checkout-root>/docs/source/en/<path>.md \
  --output-md reports/pr-N/quality-report.md \
  --output-json reports/pr-N/quality-report.json \
  --output-pr-comment reports/pr-N/pr-comment.md \
  --qe-metric off \
  --disable-embedding-similarity \
  --style-guide skills/quality-transformers/style/hf-transformers-ko-translation-guide.md \
  --style-policy skills/quality-transformers/configs/style_policy.yml \
  --evaluation-config skills/quality-transformers/configs/eval_config.yml \
  --gates-config skills/quality-transformers/configs/gates.yml \
  --glossary skills/quality-transformers/glossary/transformers_terms.tsv \
  --llm-judge-prompt skills/quality-transformers/judges/mqm_prompt.md \
  --fail-on-reject
```

**Why `--qe-metric off` and only the transformers glossary** (Phase 5
calibration — see `docs/calibration-notes.md`):

- The heuristic QE metric is length/token-overlap based and calibrated for
  blog-length prose; on reference-free Korean technical docs (0.56–0.87
  length ratio) it emitted up to 96 spurious `major` issues per page. Semantic
  adequacy is covered properly by the MQM judge.
- The shared blog glossaries (`product_terms.tsv` / `ml_terms.tsv` / `ko.tsv`)
  produced systematic `preserve_product_name` / `required`-term false
  positives on dense technical Korean (`Transformers에서`, `Spaces에`).
  Product / class / API name preservation is already covered by the
  `protected_tokens`, `inline_code`, and `autodoc_reference_preservation`
  hard gates plus the MQM judge.

Add `--llm-judge-provider openai` (with `OPENAI_API_KEY`) for the MQM judge;
without it the best attainable status is `review_required` (the harness marks
semantic adequacy incomplete without a judge).

All other CLI flags, phases, and behavior are documented in
`skills/quality/README.md` — this file only records what differs for the
transformers profile.

## What differs from the blog / generic-docs profile

- **`--gates-config`** (`configs/gates.yml`):
  - `front_matter.required_target_keys` / `preserved_source_keys` = `[]`
    (transformers docs have no YAML frontmatter).
  - `code_blocks.status` = `review_required` (comment/docstring translation is
    accepted in real merged PRs).
  - `anchor_preservation`, `directive_preservation`,
    `autodoc_reference_preservation`, `mdx_component_preservation` =
    `status: reject`, `enabled: true`.
  - `sentence_final_colon` = `status: review_required`, `enabled: true`.
- **`--style-guide`** (`style/hf-transformers-ko-translation-guide.md`): 23
  sections covering the license header, `_toctree.yml`, `[[...]]` anchors +
  heading levels, `[[autodoc]]`/`[[open-in-colab]]`, `` [`Class`] ``, MDX +
  `> [!WARNING]` alerts, ` ```cli `, the sentence-final-colon rule,
  re-sync/freshness, and the `model_doc` boilerplate line. Blog voice/title/
  emoji rules removed.
- **`--style-policy`** (`configs/style_policy.yml`): drops blog `title_quality`;
  keeps `modal_strength` (+ `experimental`/`deprecated`), `overstatement`,
  `translationese`, `list_consistency`, `alt_text`, `first_mention_terms`
  (transformers set). `hard_gate_rules` / `style_score` blocks are
  documentation only — the harness does not read them.
- **`--glossary`**: the three shared blog glossary files by original path,
  plus `glossary/transformers_terms.tsv` (PEFT, Accelerate, Trainer,
  TrainingArguments, doc-builder, autodoc, toctree, docstring, accelerator,
  experimental API).
- **`--llm-judge-prompt`** (`judges/mqm_prompt.md`): "transformers technical
  documentation" criteria — anchors, directives, API refs, MDX, license
  header, sentence-final colon, warning-strength, re-sync, `model_doc`
  boilerplate. Blog title/emoji/hook/CTA rules removed.
- **`--evaluation-config`** (`configs/eval_config.yml`): blog-profile
  thresholds except `language.min_korean_letter_ratio` 0.20 → 0.15 (Phase 5:
  `model_doc/*.md` pages are class-name / `[[autodoc]]` / code dominated).

## Files intentionally NOT copied from `skills/quality`

Checked file-tree diff against `skills/quality`; these are deliberate omissions,
not oversights:

- `tools/`, `pyproject.toml` — the harness is shared and called by path; this
  skill has no package of its own, so it needs no `pyproject.toml`.
- `schemas/*.json` — the shared harness reads
  `skills/quality/schemas/mqm_judge.schema.json` unconditionally (no CLI
  override) and the report-shape schema is documentation only, so a local
  copy would just be a drift risk.
- `glossary/{ko,ml_terms,product_terms}.tsv` — deliberately not passed on the
  command line (Phase 5: the shared blog glossaries caused false positives on
  dense technical Korean). Only `glossary/transformers_terms.tsv` is used.
- `style/hf-blog-ko-translation-guide.md` — replaced by
  `style/hf-transformers-ko-translation-guide.md`.
- `docs/*` blog artifacts (PRD, implementation plans, eval reports) — the
  harness was not redesigned here, so there was no PRD/impl-plan process. This
  skill's `docs/` holds its own Phase 1/2/3/5 build evidence instead.
- `tests/conftest.py`, `tests/*_set.yml`, `tests/test_*.py`,
  `tests/fixtures/translation_quality_harness/*` — see "Known gaps" below.

## Known gaps

- No `tests/test_*.py` / `golden_set.yml` / `challenge_set.yml` acceptance
  suite of its own — only the manual fixture pair under `tests/fixtures/`
  (`sample_source.md` / `sample_target.md` / `manifest.yaml`), run by hand.
  Building a real golden/challenge suite overlaps with Phase 5
  sample-gathering.
- `_toctree.yml` cross-file consistency, license `⚠️ Note` freshness, and
  `model_doc` date accuracy are out of automation scope — manual checks (see
  `SKILL.md`).
- Segment alignment is order-based `zip`; if the `model_doc` boilerplate line
  is present in the target but not the raw English source, expect a spurious
  "additional text segments" review flag. Verify against the raw source.

## Style Guide

`style/hf-transformers-ko-translation-guide.md` — built from official
`docs/TRANSLATING.md`, tracking issue transformers#20179,
`translation-flow/docs/hf_ko_translation_best_practice.md`, and merged PRs
#39519, #41340, #47157, #39913.

## Build evidence (`docs/`)

- `docs/blog-vs-transformers-docs-differences.md` — Phase 1 format/content/
  detail comparison.
- `docs/quality-harness-architecture.md` — Phase 2 trace of the shared harness
  from `main` (`tool_version` 0.6.0).
- `docs/build-plan.md` — Phase 3 keep/modify/new decisions and the approved
  harness changes.
