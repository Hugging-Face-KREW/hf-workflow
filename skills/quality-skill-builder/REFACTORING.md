# Pending refactoring — this skill will become profile-centric

**Status:** the instructions in `SKILL.md` and `phases/*.md` are valid **only
until the `skills/quality` profile refactoring lands.** Plan:
[`specs/quality-skill-refactoring-plan.md`](../../specs/quality-skill-refactoring-plan.md).

Until that refactoring ships, follow this skill exactly as written (build a
sibling `skills/quality-<name>/`). Do **not** pre-emptively restructure
against the plan below.

## This skill has two roles

1. **An executable playbook** — the tool an agent actually runs to build a
   Korean-translation quality-review skill for a new document type.
2. **A written record of how those skills get built** — the phase docs and
   `RATIONALE.md` double as process documentation (which decisions are made
   when, why each check exists, what went wrong before).

Both roles are affected by the refactoring: the steps change, and so does the
narrative of what "building one" means.

## Why the refactoring is coming

The refactoring's main goal is to **split out a `core` layer so shared assets
have a single maintenance point** — the engine, schemas, the gate mechanism,
the shared glossary, the MQM prompt skeleton. A common improvement, one that
applies regardless of document type or target repo, should then be made
**once** and be picked up everywhere.

The current skill pushes the opposite way. Phase 4 tells you to `cp` the
schemas, `pyproject.toml`, and the structural parts of the config into a new
sibling skill folder. Every new document type adds another full copy, so the
number of places to maintain **grows with the number of document types**.
That is the reverse of the goal above, which is why the refactoring is
treated as urgent rather than nice-to-have.

## What changes in this skill after the refactoring

The overall process stays broadly the same — six phases, keep the whole
pipeline, evidence before code changes, calibrate thresholds last. The
mechanics of Phases 0/2/3/4/5 change:

| Phase | Now | After refactoring |
|---|---|---|
| 0 | Output is a sibling `skills/quality-<name>/` folder | Output is a `skills/quality/profiles/<name>/` directory + a `profile.yml` (`extends: core`) |
| 2 | Re-derive the harness architecture doc per build | Point at the single `skills/quality/docs/quality-harness-architecture.md`; don't re-derive |
| 3 | keep/modify/new plan as whole-file forks | Plan expressed as **overlay deltas** against `*.base.*` files |
| 4 | `cp` schemas / `pyproject.toml` / engine / config structure, then diff the file tree | **No `cp` of shared assets.** Write `*.overlay.yml`, `mqm_prompt.overlay.md`, and the profile glossary only. The scaffolding-completeness check becomes: render the effective config with `profile_loader --render` and diff it against base — only the intended deltas should appear |
| 5 | Edit thresholds in the new skill's `eval_config.yml` | Edit `profiles/<name>/configs/eval_config.overlay.yml` only; base thresholds untouched |

Also:

- New engine capabilities (extra validators — anchors, directives, MDX
  components, sentence-final colon, etc.) are **registered through a
  profile-declared registry** (`extra_validators: [...]` in `profile.yml`)
  instead of being edited into shared engine code once per document type.
- `RATIONALE.md` lessons that are specifically about copy-completeness (the
  file-tree diff check, "looks done needs an actual diff") get rephrased
  around overlay-diffing against the rendered effective config.

## Sequencing

Per the plan, this skill is rewritten to the profile model in **Phase 4** of
the refactoring, after the `hf-blog` profile has been split out in place and
proven byte-equivalent. Do not merge a rewrite of this skill ahead of that.
