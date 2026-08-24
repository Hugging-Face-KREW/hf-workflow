# Hugging Face Transformers Documentation Profile

Use this profile for files under `docs/source/en` and `docs/source/ko` in the
`huggingface/transformers` repository.

## Read before translating

Read the repository's current `docs/TRANSLATING.md`, the relevant source file,
the existing Korean file when present, and nearby Korean documents in the same
section. Current repository instructions override examples in this profile.

## Path and navigation rules

- Keep the English and Korean document path aligned unless the current
  `_toctree.yml` or an explicit migration says otherwise.
- Translate navigation titles in `docs/source/ko/_toctree.yml`, but preserve
  each `local` path exactly.
- Treat `_toctree.yml` as YAML, not Markdown. The Markdown translation helper
  does not edit it.
- Do not add a document to the Korean table of contents until its target file
  exists and the requested scope includes that navigation edit.

## Transformers syntax to preserve

Preserve component names, attributes, nesting, and closing tags, including
constructs such as:

```text
<Tip>
<Tip warning={true}>
<hfoptions id="...">
<hfoption id="...">
<PipelineTag pipeline="...">
```

Also preserve:

- fenced code and fence language;
- inline code, API symbols, AutoDoc references, and bracketed cross-references;
- `[[anchor-id]]` and `{#anchor-id}` syntax;
- relative link targets, image URLs, and query fragments;
- environment variables, CLI flags, model IDs, dataset IDs, and file paths;
- the copyright/license comment block.

Translate prose inside components while leaving their wrapper lines intact.

## Korean style

- Use clear `합니다`-style technical prose unless nearby maintained documents
  establish a different local convention.
- Prefer the terminology already used by maintained Korean Transformers docs.
- Preserve Hugging Face product and library names unless a current project
  glossary explicitly requires a different form.
- Keep modal strength and operational conditions exact. A recommendation must
  not become a requirement, and a possibility must not become a guarantee.
- Do not add tutorial explanations that are absent from the source.

## Required verification

- Run the translation helper's structural validation.
- Review the source/target diff around every code block and component boundary.
- Confirm links and anchors resolve under the Korean documentation route.
- Validate `_toctree.yml` separately when navigation changes are part of the
  request.
- Run the repository's available documentation checks before describing the
  translation as ready to merge.
