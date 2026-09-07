# Quality — transformers Docs profile — Agent Guide

Use this profile only for `github.com/huggingface/transformers`
`docs/source/ko/**/*.md` translation quality review. Hugging Face blog posts →
`skills/quality`. Other Hugging Face library docs (diffusers, smolagents,
lerobot, huggingface_hub) are out of scope.

Expected workflow:

1. Read the `translation-flow` manifest (or gather source path, target path,
   `_toctree.yml` entry, and whether this is a new translation or a re-sync).
2. Locate the English source at `docs/source/en/<same-path>` and pass it as
   `--source` — the harness does not auto-fetch transformers doc URLs.
3. Run `skills/quality/tools/translation_quality_harness.py` with this
   profile's `--gates-config`, `--style-guide`, `--style-policy`,
   `--evaluation-config`, `--llm-judge-prompt`, `--qe-metric off`, and only
   `glossary/transformers_terms.tsv` (see `README.md` for the full command
   and why).
4. Review the report: fidelity, fluency (including the no-sentence-final-colon
   rule), terminology, and doc-builder structure — heading anchors `[[...]]`
   (kebab or `[[autodoc]]` API path) + heading levels, `[[open-in-colab]]`/
   `[[autodoc]]`, bracketed API refs, MDX components and `> [!WARNING]`
   alerts, code blocks, links, tables.
5. Confirm the manual checks: `_toctree.yml` `local` unchanged / `title`
   translated / structure synced, license `⚠️ Note` line current, `model_doc`
   dates correct, KREW → maintainer → `build-doc` process followed.
6. Apply focused fixes or write a review artifact.

Do not create new translation files here — that belongs to `translation-flow`.
This skill was built with the `quality-skill-builder` playbook (separate PR);
do not modify that skill.
