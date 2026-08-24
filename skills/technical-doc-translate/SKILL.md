---
name: technical-doc-translate
description: Translate or refresh Markdown and MDX technical documentation into Korean while preserving executable code, identifiers, links, anchors, tables, and framework-specific document syntax. Use for documentation translation work, not translation-quality review or general prose translation.
---

# Technical Document Translation

Create a faithful Korean technical document whose executable and structural
parts remain usable. Treat translation generation, quality review, and Git/PR
operations as separate responsibilities.

## Establish the task

Confirm the source file, target file, target locale, and project profile. Read
the repository instructions and nearby translated files before choosing
terminology or style.

- For Hugging Face Transformers documentation, read
  [references/transformers-docs.md](references/transformers-docs.md).
- For the preservation rules and manifest contract, read
  [references/technical-markdown-contract.md](references/technical-markdown-contract.md).

Do not translate a document that has no available source. Do not infer that a
mentioned path authorizes overwriting an existing translation.

## Choose the translation mode

- **New translation or full refresh:** use
  `scripts/translate_document.py` to translate the current source as structured
  blocks. Write to a new target or an explicitly approved replacement path.
- **Incremental update:** require a trustworthy base English Git revision from
  a prior manifest, the document backlog's verified EN SHA, or the last merged
  translation PR. Compare that revision with the current source, map changed
  headings or blocks to the Korean file, and edit only those sections. Preserve
  accepted Korean wording outside the changed source. A content hash detects
  drift but cannot reconstruct the base file. If no retrievable base revision
  exists, use a full-refresh draft or request human scoping instead of guessing.
  The batch script is not a three-way merge tool.
- **Planning or inventory:** report the proposed work without creating or
  editing translation files.

For a new translation or full refresh, first preview the parse without an API
call:

```bash
python skills/technical-doc-translate/scripts/translate_document.py \
  --source docs/source/en/example.md \
  --target docs/source/ko/example.md \
  --profile transformers \
  --dry-run
```

Then run the translation only when the request authorizes the file write and
the required API credentials are available. The runtime expects
`OPENAI_API_KEY`; if the `openai` package is absent, install this skill package
in the active project environment with
`python -m pip install -e skills/technical-doc-translate`.

```bash
python skills/technical-doc-translate/scripts/translate_document.py \
  --source docs/source/en/example.md \
  --target docs/source/ko/example.md \
  --profile transformers \
  --manifest-output reports/example/translation-manifest.yaml
```

Use `--force` only when replacing an existing target is explicitly intended.
The script must complete structural validation before it writes the target.

## Translation requirements

Translate reader-facing prose, headings, list text, table prose, link labels,
and useful Markdown image alt text. Preserve source meaning, conditions,
confidence, limitations, and information order. The v1 helper keeps HTML/MDX
tag attributes byte-stable; review user-facing attributes separately when a
project explicitly permits localizing them.

Never translate or silently modify:

- fenced code, inline code, commands, flags, environment variables, paths, or
  configuration keys;
- API names, class and function names, arguments, model and dataset IDs, or
  product names that must remain searchable;
- link targets, image paths, explicit anchors, Markdown/MDX component names,
  component props, HTML comments, or copyright/license blocks;
- table shape, heading level, list nesting, or source section coverage.

The v1 helper automatically isolates fenced code, but it does not reliably
classify legacy indented code blocks. If the source contains them, handle the
document manually or add explicit protection before using the batch helper.

Prefer natural Korean technical prose over English-shaped sentences. Do not add
explanations, examples, claims, or conclusions that are absent from the source.
Treat a glossary as an input policy, not as proof that every term has one fixed
translation in every context.

## Verify and hand off

After translation:

1. Read the generated Korean file in full.
2. Inspect the source/target diff and the structural validation report.
3. Check headings, warnings, tables, links, code examples, and component
   boundaries in context.
4. Record the source SHA and generated manifest.
5. Hand the result to a separate quality-review workflow when available.

Do not create a branch, commit, push, PR, issue, or spreadsheet update unless
that external action is separately requested. Report unresolved terminology or
structure questions instead of guessing.
