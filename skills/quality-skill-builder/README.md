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
REFACTORING.md            pending change notice — these instructions are valid only until the
                          skills/quality profile refactoring lands; read before starting
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

This skill's own structure (the `SKILL.md`/`RATIONALE.md`/`phases/*.md`
split) is itself a result of feedback gathered while using an earlier,
monolithic version of this playbook (too long; by Phase 4 the early content
had gone fuzzy) — the background is at the top of `RATIONALE.md`.

## Relationship to the `skills/quality` refactoring

This skill is both an executable playbook and a written record of how
document-type quality skills get built. Its current shape — `cp` shared
assets into a new sibling skill per document type — runs against the
direction of the planned `skills/quality` refactoring, whose goal is to pull
a `core` layer out so shared assets have one maintenance point. The plan is
[`specs/quality-skill-refactoring-plan.md`](../../specs/quality-skill-refactoring-plan.md);
what changes in this skill once it lands is in `REFACTORING.md`.

## Templates

`templates/` holds blank templates for the Phase 1/3/5 deliverables. Phase 2's
deliverable has no template, because it isn't remade per document type — it
documents the tool itself. Reuse it if a prior run of this skill already
produced one for the harness in question; otherwise write it from scratch
following the section structure in `SKILL.md`'s Phase 2 description.
