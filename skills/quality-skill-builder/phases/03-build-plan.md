# Phase 3 — Build plan: keep/modify/new decisions + parsing requirements

Combine Phase 1 (what's different) and Phase 2 (exactly how the tool works)
to classify **every evaluation item** in the pipeline:

| Class | Meaning | Work needed |
|---|---|---|
| **Keep** | Still correct for the new document type | None |
| **Reconfigure assets only** | Logic is fine, values/wording aren't | Swap config values/guide text only (defer thresholds to Phase 5) |
| **Soften/harden** | Severity (hard↔review) needs to change | Change `status` in `gates.yml` only — a config change, not a logic change |
| **Disable** | Doesn't apply to the new document type at all | Turn off the option or set it empty. **Verify the parser actually supports empty/off syntax** — if not, a minimal parser fix is needed |
| **New parsing needed** | Comparing a new structural element requires info not currently extracted | See "Parsing requirements" below |
| **New gate/validator needed** | The comparison logic itself doesn't exist yet | Add a new comparison function to the tool (minimal scope) |
| **Structurally impossible** | Can't be handled by the current architecture (single source-file ↔ single target-file comparison) | Declare it out of automation scope, leave as a manual human/agent check |

## Spell out parsing requirements separately

For each new structural element to extract, specify:

- **What to extract**
- **Where from** — derivable from an existing segment/document field, or does
  the raw body need a new regex pass
- **Comparison method** — is a multiset (order-agnostic, count-only)
  comparison enough, or is a fixed-position pair comparison needed
- **Hard gate or review gate** — "does this breaking actually break the
  build/render" (hard) vs. "translation-quality issue but needs human
  judgment" (review)

**Deliverable**: the build plan doc. Each Phase 1 A/B/C item becomes a table
row with a "class" column and a "why" column (citing Phase 1/2 evidence).
Parsing requirements get their own table. Template:
`templates/build-plan.template.md`.

**Checkpoint**: show the plan to the user and get approval. "New
gate/validator needed" and "soften/harden" items change tool code or severity
policy, so they must be confirmed before moving to Phase 4. When ambiguous,
use `AskUserQuestion` with concrete options rather than a vague "how should I
proceed?"
