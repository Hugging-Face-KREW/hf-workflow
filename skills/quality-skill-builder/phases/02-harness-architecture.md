# Phase 2 — Trace the existing harness architecture from code

Phase 1 established what's different. Now establish exactly how the existing
tool evaluates a translation, so Phase 3's keep/modify decisions are sound.
**Read the scoring script's code directly — don't guess from a README
summary or memory.** README and code can disagree (see `RATIONALE.md`).

## What to confirm

1. **Exactly what each pipeline stage compares, and with what algorithm.**
   Not "the hard gate checks code blocks" — trace it to "the whole code block
   is sha256-hashed, source/target hash lists are compared as a multiset
   (Counter) difference, and any mismatch becomes a missing/extra issue."
2. **Whether "hard gate" and "review gate" are actually two different
   mechanisms in code, or the same logic with only a config value (e.g.
   `status: reject` vs `review_required`) applied differently.**
3. **Whether each specific config key is actually read by the code.** A
   hand-rolled mini YAML parser commonly recognizes only a fixed set of paths
   and silently ignores everything else. → **Before adding a new config key,
   confirm code actually reads it** (read the parser function directly). If
   not, mark it explicitly in Phase 3/4 as "documentation only, no execution
   logic yet."
4. **Write the exact score/status aggregation formula.** Pull the real
   weight constants and the exact order of the conditional that decides the
   final status straight from the code.
5. **Understand the limits of the segment/alignment mechanism.** Is alignment
   order-based zip or meaning-based matching? Is some structural info (e.g.
   heading level) discarded during parsing? These limits directly determine
   Phase 3's "can't build this with the current structure" calls.

**Deliverable**: `docs/<tool>-architecture.md`. **Don't remake this per
document type** — it documents the tool itself, so reuse it once built. If it
already exists, just confirm it's current.

**Checkpoint**: after writing, re-check your own terminology for accuracy (a
figurative description can drift from the real mechanism — see
`RATIONALE.md`).
