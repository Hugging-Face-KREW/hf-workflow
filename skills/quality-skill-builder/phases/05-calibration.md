# Phase 5 — Threshold/formula calibration (last, evidence-based)

Start this **only after Phase 4 is functionally verified**.

1. **Gather several (ideally 3–5+) real, well-translated sample documents.**
   Ones that went through an actual PR review are ideal — seeing the review
   process (what was flagged, what got fixed), not just the merged result,
   reveals what translators/reviewers actually treated as important, and
   that becomes the basis for threshold adjustments.
2. **Run the harness against these samples with the original skill's default
   thresholds, unchanged.**
3. Check whether a known-good translation is unfairly flagged
   `review_required`/`reject` (false positive), or a bad translation comes
   out `auto_pass` (false negative).
4. Adjust **only** thresholds where a false positive/negative was actually
   observed. Don't touch a threshold just because "this document type is
   probably different" without evidence.
5. When adjusting, pick the **smallest change that explains the
   observation**. Record the rationale (which sample, what score) next to the
   adjusted value, in a config comment or a separate doc.
6. Re-verify with the same samples after adjusting, and re-run the original
   skill's test suite too.

**Deliverable**: calibration notes (what changed, why, on what evidence).
Template: `templates/calibration-notes.template.md`.

**Checkpoint**: before changing any threshold, show the user the observed
false positive/negative cases and the proposed change, and get approval.
This is the most sensitive point in the whole skill where nothing should
proceed without user confirmation — the score formula is the basis for every
other decision (auto-approve/reject).
