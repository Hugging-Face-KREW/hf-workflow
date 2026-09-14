# <original document type> vs <new document type>: Korean translation quality skill differences

<!--
This is the Phase 1 deliverable. Read SKILL.md's Phase 1 before writing.
- Don't fill in from guesswork: confirm at least one real source/translation
  file pair, the official guide, and a real review comment before filling in
  a row.
- Check the repo for existing related research first, and reuse it as the
  primary source if it exists (Phase 1-A).
- Each table cell should explain "why it differs" in one sentence, not just
  "it differs."
-->

## A. File format (structure/syntax)

| Item | <original document type> | <new document type> |
|---|---|---|
| Metadata location | | |
| TOC mechanism | | |
| Heading anchors/identifiers | | |
| Special directives/rendering syntax | | |
| Embedded components (MDX/JSX/HTML etc.) | | |
| Workflow scaffolding (if any) | | |
| Storage location/directory structure | | |
| File lifespan (snapshot vs. living document) | | |
<!-- Add rows for any format trait unique to this document type -->

## B. Content: flow, style, structure

| Item | <original document type> | <new document type> |
|---|---|---|
| Tone baseline (genre-adjusted vs. uniform) | | |
| Title conventions | | |
| Intro conventions | | |
| Closing conventions | | |
| Emoji/decorative elements | | |
| Structure (narrative vs. procedural) | | |
| Purpose of the no-added-information rule | | |
| Warning/limitation strength rules | | |
| Whether freshness sync is required | | |
| Weight of the collaboration/review process | | |

## C. Detail: comments, links, and other fine-grained rules

| Item | <original document type> | <new document type> |
|---|---|---|
| Code-comment translation policy | | |
| Hyperlink-target policy (and exceptions) | | |
| List/indentation structural risk | | |
| Terminology priority criteria | | |
| Image/caption handling | | |
| Whether source auto-fetch is supported | | |
<!-- Add rows for any detail unique to this document type -->

## D. Tool (harness) level differences — fill in alongside Phase 2

<!--
After confirming the harness architecture in Phase 2, record the concrete
config differences that will (or should) land in gates.yml/style_policy.yml
etc. here. This feeds the Phase 3 build plan doc.
-->

| Gate/validator | <original document type> default | Value needed for <new document type> | Rationale |
|---|---|---|---|

## E. Not yet resolved

<!-- Items that are structurally impossible to automate, or on hold pending user confirmation -->

-

## Self-check summary

<!-- Write 3–5 questions, based on this doc's A/B/C content, to quickly
check "have I left in an assumption from the original document type" during
the rest of this work. -->

1.
2.
3.
