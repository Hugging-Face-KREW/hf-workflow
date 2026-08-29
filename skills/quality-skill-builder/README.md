# Quality Skill Builder

A meta-skill documenting the process of rebuilding a translation-quality
review skill that targets one document type (like `skills/quality`, for HF
blog posts) into one that targets a **different document type**. The audience
is not an end user — it's **whichever agent is building a new quality skill
in this repo**.

## When to use

- You need a Korean-translation quality-review skill for a new document type
  (technical docs, course material, README, release notes, etc.).
- You want to keep and change things deliberately, with evidence recorded,
  instead of copying an existing quality skill wholesale and hand-editing it.

## File layout

```
SKILL.md                 entry point (router) — principles + phase index only, execution-essential
RATIONALE.md              "why" only — not needed to execute, read only when a rule seems arbitrary
phases/00~06-*.md         per-phase instructions — read at the moment you start that phase
templates/*.template.md   blank templates for the Phase 1/3/5 deliverables
```

`SKILL.md` is meant to be read once, just to get the overall picture. To
avoid Phase 1's content growing fuzzy by Phase 4, **each phase's detailed
instructions are designed to be re-read from `phases/0N-*.md` at the moment
that phase starts** — not relied on from memory. "Why this check exists"
(real incidents, background) is meta-information not needed for the work
itself, so it's split out into `RATIONALE.md`.

`SKILL.md`'s phase-index table lists each phase's goal, whether it has a
checkpoint, and its file path.

## Worked example

The actual work that built `skills/quality` → `skills/quality-docs` is this
skill's evidence base. Its results can be consulted directly:

- `skills/quality-docs/docs/blog-vs-technical-docs-differences.md` — Phase 1 deliverable example
- `skills/quality-docs/docs/blog-quality-harness-architecture.md` — Phase 2 deliverable example (documents the tool itself, so it's reused across document types)
- `skills/quality-docs/` as a whole — Phase 3–4 result

This skill's own structure (the `SKILL.md`/`RATIONALE.md`/`phases/*.md`
split) is itself a result of feedback gathered while doing that work (too
long; by Phase 4 the early content had gone fuzzy) — the background is at the
top of `RATIONALE.md`.

## Templates

`templates/` holds blank templates for the Phase 1/3/5 deliverables. Phase 2's
deliverable has no template, because it isn't remade per document type — it
documents the tool itself. Reuse it if it already exists; if not, model it
directly on
`skills/quality-docs/docs/blog-quality-harness-architecture.md`'s structure.
