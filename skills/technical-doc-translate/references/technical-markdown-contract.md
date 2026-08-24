# Technical Markdown Translation Contract

Use this contract for a new translation or full-document refresh.

## Inputs

- `source.file_path`: current source Markdown or MDX file
- `translation.file_path`: intended translated file
- `translation.locale`: target locale, normally `ko`
- `translation.profile`: project-specific preservation profile
- optional glossary TSV files with `source_term` and `ko_term` columns

The source file is authoritative. An existing target is useful context for an
incremental update, but it must not override newly changed source facts.

## Translatable content

- headings and reader-facing prose
- list items and blockquotes
- prose cells in Markdown tables
- link labels and meaningful Markdown image alt text
- user-facing warning, note, and component body text

## Protected content

- fenced code
- inline code and executable examples
- URLs, link targets, image paths, anchors, and footnote identifiers
- CLI flags, environment variables, file paths, model IDs, dataset IDs, and API
  identifiers
- Markdown/MDX/HTML component tags and attributes
- HTML comments and copyright/license text

The v1 helper also keeps YAML frontmatter byte-stable. Translate frontmatter
fields separately only when the project has an explicit metadata policy.
HTML/MDX tag attributes are also byte-stable in v1, including `alt` props.
Localize a user-facing attribute only through a project-specific reviewed edit.
The v1 helper does not reliably classify legacy indented code blocks. Handle
such a document manually or add explicit protection before batch translation;
do not assume the helper will preserve those blocks.

Structural protection is necessary but not sufficient. A translation can pass
structure checks and still be semantically wrong, incomplete, or unnatural.

## Manifest

The translation command writes a small YAML handoff artifact when
`--manifest-output` is supplied. It records:

- source path and SHA-256
- source Git revision when it is supplied or discoverable
- target path and locale
- project profile
- generator and model
- creation time
- structural validation status
- downstream quality-review intent

The manifest does not mean the translation passed human or semantic review.
For an incremental update, use `source.revision` to retrieve the exact prior
English file. `source.hash` alone can reveal that content changed, but cannot
identify which source revision should be diffed.

## Failure behavior

Do not write the target when:

- the source is missing or empty;
- the model output omits, duplicates, or invents block IDs;
- a protected placeholder changes;
- structural validation finds changed code, links, anchors, component tags, or
  comments;
- the target exists and `--force` was not explicitly supplied.

Write generated artifacts only after all batches and structural checks succeed.
