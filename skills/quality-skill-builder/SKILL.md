# Quality Skill Builder

This file is a **router**. Re-read the relevant `phases/0N-*.md` when you
start that phase — don't rely on memory of having read this file once. "Why"
(rationale, real incidents) lives separately in `RATIONALE.md` — not needed to
execute the work, only when a rule seems arbitrary.

## When to use

You already have a translation-quality-review skill for **one document
type** (e.g. `skills/quality` for HF blog posts), and need to rebuild it for
**another document type** (technical docs, course material, README, release
notes, etc.).

## Core principles (apply to every phase)

1. **Keep the whole pipeline.** Don't redesign the scoring tool's structure
   (parse → segment extraction/alignment → hard/review gates → glossary
   validation → style-guide validation → metric triage → MQM judge →
   score/status aggregation).
2. **Change skill, assets, and tool code only as much as needed.** Every code
   change must trace back to a concrete finding from Phase 1–3.
3. **Ask the user at judgment-call points** — especially before touching
   shared tool code, when a hard-vs-review classification is ambiguous, and
   before adjusting thresholds. Each phase file marks "ask here."
4. **Don't touch thresholds or the composite score formula before Phase 5.**
5. **Whenever shared code changes, re-run the original skill's test suite.**

## Execution principles

- **Stay one skill** — don't split into multiple skills or a dedicated Agent
  subtype. (Why: `RATIONALE.md#execution-shape`.)
- **Before starting a phase, check whether its output file already exists.**
  If so, continue from it instead of redoing the phase. Save each phase's
  output to disk as soon as it's ready.
- **Delegate token-heavy research (deep dives, code tracing) to the `Agent`
  tool** and keep only the distilled result (finished doc/table) on the main
  thread.
- Escalate to the `Workflow` tool only if the scope grows to multiple document
  types researched in parallel, or the user explicitly asks for
  orchestration — not the default.

## Phase index

| Phase | Goal | Checkpoint | File |
|---|---|---|---|
| 0 | Confirm scope | Yes | `phases/00-scope.md` |
| 1 | Analyze the new document type (format/content/detail) | Yes | `phases/01-document-analysis.md` |
| 2 | Trace the existing harness architecture from code | Yes | `phases/02-harness-architecture.md` |
| 3 | Build plan: keep/modify/new decisions + parsing requirements | Yes | `phases/03-build-plan.md` |
| 4 | Implementation + scaffolding-completeness check | Yes (first shared-code edit) | `phases/04-implementation.md` |
| 5 | Threshold/formula calibration (evidence-based, last) | Yes (before any value change) | `phases/05-calibration.md` |
| 6 | Wrap-up checklist | — | `phases/06-wrapup.md` |

## Deliverables at a glance

- Phase 1 → `docs/<original>-vs-<new>-differences.md` (template:
  `templates/format-content-detail-comparison.template.md`)
- Phase 2 → `docs/<tool>-architecture.md` (not remade per document type — it
  documents the tool itself, so it's reused)
- Phase 3 → build plan doc (template: `templates/build-plan.template.md`)
- Phase 4 → the actual skill folder
- Phase 5 → calibration notes (template: `templates/calibration-notes.template.md`)
