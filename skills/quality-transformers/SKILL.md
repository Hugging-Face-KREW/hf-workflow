# HF transformers Docs Translation Quality Skill

Use this skill when reviewing a Korean translation of a **Hugging Face
`transformers`** documentation page (`docs/source/ko/**/*.md` in
`github.com/huggingface/transformers`) for quality. Applies to both new
translations and stale-translation re-syncs.

- Blog posts → use `skills/quality`.
- diffusers / smolagents / lerobot / huggingface_hub docs → use
  `skills/quality-docs` (the repo-agnostic technical-docs profile). This skill
  is narrower and goes deeper on transformers-only conventions
  (`[[autodoc]]` API-path anchors, ` ```cli ` fences, `model_doc` boilerplate,
  the `[i18n-KO]` PR workflow).

## Inputs

Prefer a `translation-flow`-style manifest (see `examples/input-manifest.yaml`).
Otherwise ask for:

- source doc path in the transformers repo, e.g.
  `docs/source/en/tasks/translation.md` (pass it as `--source` — the harness
  does **not** auto-fetch transformers doc URLs, only `huggingface.co/blog/...`)
- translation file path, e.g. `docs/source/ko/tasks/translation.md`
- the `docs/source/ko/_toctree.yml` entry, if the toctree change is in scope
- whether this is a new translation or a re-sync of an outdated one

## Procedure

1. Read the manifest and the target translation file; locate the English
   source.
2. Run the scoring tool (see `README.md` for the full command). It reuses
   `skills/quality/tools/translation_quality_harness.py` with this skill's
   configs.
3. Check **fidelity**: Korean preserves source meaning, modal/certainty
   strength (may/can/should/must/only/up to), and the strength of
   experimental-API / deprecation / `> [!WARNING]` safety warnings.
4. Check **fluency**: natural Korean, informal-but-polite (해요체/합니다체 mix),
   gender-neutral. **No Korean sentence ends with a colon** — every
   sentence-final `:` becomes a period.
5. Check **terminology**: product/library/model/dataset/class/API names
   preserved; glossary + first-mention bilingual form
   (`미세 조정(fine-tuning)`) followed.
6. Check **doc-builder structure** (hard-fail if broken):
   - Heading anchors `[[slug]]` byte-identical to the English source anchor —
     kebab slug (`[[overview]]`) OR fully-qualified `[[autodoc]]` API path
     (`[[transformers.ProcessorMixin]]`). Never regenerate the slug from the
     heading text. Heading levels (`#` count) unchanged.
   - `[[open-in-colab]]` and `[[autodoc]] module.Class` directives + target
     paths unchanged.
   - Bracketed API refs `` [`Trainer`] `` / `` [`~mod.Class.method`] ``
     unchanged.
   - MDX components (`<Tip>`, `<Tip warning={true}>`, `<frameworkcontent>`,
     `<pt>`/`<tf>`, `<hfoptions>`, `<hfoption>`, `<Youtube id="..."/>`) and
     GitHub alert markers (`> [!WARNING]`, `> [!TIP]`, `> [!NOTE]`) keep tag
     names and props; only inner prose is translated.
7. Check **code**: execution tokens, identifiers, string literals with
   execution meaning (model IDs, env vars, paths), CLI, and fence language
   tags (` ```py `, ` ```cli `, ` ```bash `) untouched. Comment / docstring /
   `Args:` translation is a review item, not an automatic failure.
8. Check **formatting**: link/image targets preserved (link text may be
   translated); table shape preserved. transformers docs do **not** swap
   English links to `/ko/`.
9. Check **metadata**: Apache license header comment block kept verbatim with
   its `⚠️ Note ... doc-builder` line in English (synced to current source
   wording). `_toctree.yml`: `local` unchanged, `title` translated.
10. For a **re-sync**: obsolete content removed — `TODO`/`FIXME` comments,
    dropped section headings, removed env-var guidance, content that no longer
    matches current English.
11. `model_doc/*.md`: the `*이 모델은 <date>에 발표되었으며 <date>에 Hugging
    Face Transformers에 추가되었습니다.*` line translated with dates preserved.

## Manual checks (not automated)

`_toctree.yml` structural sync (order, no duplicate sections), license
`⚠️ Note` line freshness, `model_doc` date accuracy, and the KREW → maintainer
→ `build-doc` review-process completion.

## Output

Compact scorecard: fidelity / fluency / terminology / structure (anchors ·
levels · directives · API refs · MDX) / code / links / colons. Reference
`style/hf-transformers-ko-translation-guide.md` sections when explaining a
finding. When editing files, summarize fixes and remaining risks.
