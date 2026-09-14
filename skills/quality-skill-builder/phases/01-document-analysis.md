# Phase 1 — Analyze the new document type (structure · content · detail)

Goal: produce an **evidence-based** comparison document answering "what, and
why, is different between this document type and the original one."

## 1-A. Search the repo for existing knowledge first

Before starting new research, `grep`/`find` the repo for existing translation
convention/best-practice/PR-research docs for this document type. If one
exists, use it as the primary source instead of redoing research from
scratch.

## 1-B. Gather evidence

Actually read the following (verify the original text directly, don't
summarize from memory):

- The document type's **official contribution/translation guide**, if one
  exists, read verbatim.
- **At least one real, merged source↔translation file pair**, side by side.
  Guide documents can be stale or aspirational — real files show the actual
  convention.
- **Real review comments/PR discussion**, if available. What a reviewer
  flagged reveals implicit rules most accurately.

## 1-C. Organize into three buckets

- **A. File format/structure**: metadata location (frontmatter or not), TOC
  mechanism (manual vs. auto-generated, anchor syntax, whether heading level
  is meaningful), special directives, embedded components (MDX/JSX/HTML),
  code-block conventions, storage location/file lifespan.
- **B. Content/tone/structure**: tone baseline (varies by genre vs. uniform),
  title conventions, intro/closing conventions, scope and purpose of the
  no-added-information rule, warning/limitation strength rules, whether
  freshness sync is required, weight of the collaboration/review process.
- **C. Detail**: comment-translation policy, hyperlink-target policy (and
  exceptions), list/indentation structural risk, terminology priority
  (searchability vs. consistency), image/caption handling, any other quirk
  specific to this document type.

Organize each item as an **original document type vs. new document type**
table.

**Deliverable**: `docs/<original>-vs-<new>-differences.md`. Template:
`templates/format-content-detail-comparison.template.md`.

## 1-D. (Optional) Visual asset

If the user asks for an at-a-glance view, build a presentation-style HTML
artifact from the comparison doc (load the `artifact-design` skill first).
Don't build one unprompted.

**Checkpoint**: show the deliverable to the user and confirm nothing they
know is missing or wrong. Update the doc with their feedback before moving
on.
