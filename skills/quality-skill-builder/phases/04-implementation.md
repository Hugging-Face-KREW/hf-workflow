# Phase 4 — Implementation

Implement only what's in the Phase 3 plan (don't improvise items that aren't
there). Recommended order:

1. **Extend parsing** — add new fields to the document-parsing stage. Reuse
   existing fields/regexes as much as possible.
2. **Wire up comparison/validation logic** — add new gates/validators, or
   soften/harden existing gates via config.
3. **Write config assets** — `gates.yml`/`style_policy.yml`/`eval_config.yml`.
   **Leave thresholds (numbers) at the original skill's defaults** — don't
   touch them before Phase 5.
4. **Write the guide/prompt/glossary** — quote real cases gathered in Phase 1
   (source↔translation diffs, real review comments) as examples. Don't
   invent hypothetical examples.
5. **Write the skill entry points** — SKILL.md/README.md/AGENTS.md, etc.
6. **Verify scaffolding completeness + unchanged files** (below) — do this
   **before** running tests.

## How to build each file: copy vs. write from scratch

- **Files that are mostly the same as the original, with a few differences**
  (`pyproject.toml`, `schemas/*.json`, glossary, config with only a few
  changed values): `cp` the original, `diff` to confirm, then `Edit` only
  what needs to change. Don't retype from scratch. (`cp`+`diff` beats `Write`
  on both reliability and cost — see `RATIONALE.md`.)
- **Files that are entirely different from the original** (style guide body,
  SKILL.md, README, judge prompt): `diff` isn't meaningful, so just `Write`
  fresh.
- **Files meant to stay exactly the same** (e.g. glossary): don't even copy —
  reference the original's path from the new skill's README/CLI examples.
  Having the file exist in two places is itself a drift risk.

## Final check before build/test (mandatory, don't skip)

Even once Phase 4 implementation feels "done," check the following before
running tests.

1. **Compare file trees**:
   ```bash
   diff <(cd skills/<original> && find . -type f | sort) \
        <(cd skills/<new-skill> && find . -type f | sort)
   ```
   (ignore runtime caches like `.pytest_cache/`)
   - For **every file that exists only in the original**, decide: "is its
     absence in the new skill intentional, or just forgotten?" If
     intentional, **write down why in one sentence in the README or the
     build plan doc** — don't just leave it empty. "Checked and it's
     intentionally absent" and "never checked" look identical from the
     outside, so record the check itself.
   - For **files that exist only in the new skill**, confirm none of them
     are missing from the Phase 3 build plan.
2. **`diff` every file classified "keep" to confirm it's really unchanged**:
   ```bash
   diff skills/<original>/configs/eval_config.yml skills/<new-skill>/configs/eval_config.yml
   ```
   Confirm the diff shows **exactly** the changes recorded in the build plan
   (added comments, specific value changes) and nothing more. If there's any
   unplanned difference, decide whether it's intentional or a mistake, and
   fix the file or update the plan.
3. Schema/doc files (`schemas/*.json`, etc.) that are **structurally
   identical to the original with only a metadata line or two different**
   are also caught by step 1's "files that exist only in the original"
   check — don't skip step 1.

**Checkpoint**: report to the user, briefly, any "intentionally absent" calls
from step 1 and any unplanned differences found in step 2.

## Every time you change code

- **Minimal change** principle — don't expand a one-line fix into a
  refactor.
- **Run the original skill's existing test suite** before/after, to confirm
  no regression. Especially important when shared code is touched.
- Build a **minimal fixture pair** for the new document type and actually run
  the harness against it. **Verify by execution** that the intended gate
  fires at the intended severity, and that a previously-false gate no longer
  fires.
- If you added a new config key, re-confirm "does the parser actually read
  this" in code (ideally by loading it directly via `python -c`).

**Checkpoint**: the first moment shared tool code is touched (even if it was
in the plan), report the change's scope and impact (no effect on other
skills) to the user.
