# Quality Skill Builder Agent Guide

Use this only when asked to build or rebuild a Korean-translation quality
skill for a document type not already covered by an existing quality skill
in this repo (e.g. `skills/quality`). This is a process skill, not a
translation review skill.

Expected workflow:

1. Read `SKILL.md` once for the overall picture (principles + phase index).
2. Start at Phase 0 (`phases/00-scope.md`) and confirm scope with the user.
3. Work through Phases 1–5 in order, re-reading each `phases/0N-*.md` at the
   point you start that phase rather than relying on memory.
4. Save each phase's deliverable to disk immediately; check whether it
   already exists before redoing a phase.
5. Stop at every checkpoint marked in a phase file and get user confirmation
   before continuing — especially before touching shared tool code or
   changing any threshold.
6. Finish with `phases/06-wrapup.md`.

Do not skip Phase 2 (tracing the existing harness from code) and jump
straight to writing config — the keep/modify decisions in Phase 3 depend on
it. Do not adjust thresholds or the composite score formula outside Phase 5.
`RATIONALE.md` explains why each rule exists but is not required reading to
do the work.
