# Why this skill looks the way it does

**Not needed to execute the skill.** Read this only when a rule in
`SKILL.md`/`phases/*.md` seems arbitrary and you want the backstory. Every
case here comes from the session that built `skills/quality-docs` from
`skills/quality`.

## Execution shape: why one skill

Not split into multiple skills or a dedicated Agent subtype:

- Every phase ends in a checkpoint that needs user confirmation. An
  autonomously-run Agent would still stop at the same points, so nothing is
  gained — and the human would have to remember what order to invoke several
  skills in.
- Phases are sequentially dependent (Phase 3 needs Phase 1+2 output, Phase 4
  needs the Phase 3 plan). Splitting into separate skills makes it easy to
  lose information while handing outputs from one to the next.
- The context-accumulation problem (Phase 1's research, Phase 2's multi-
  thousand-line code trace) is handled by "save each phase's output to disk
  immediately + delegate heavy research to the `Agent` tool" instead of
  splitting the skill. Because output lives in files, a new session can pick
  up mid-way — that's the "many sessions stitched together by files" design,
  as opposed to one long session.

## Phase 2: README and the actual code disagreed

The blog style guide (`hf-blog-ko-translation-guide.md`) said code comments
could be translated freely. But the actual hard gate (`code_blocks`) required
an exact hash match on the whole code block, so it always blocked a comment
translation — the guide and the tool contradicted each other. Trusting the
README/style-guide summary alone would have carried a wrong assumption into
Phase 3. That's why Phase 2 requires reading the code directly.

## Phase 2: called multiset comparison "majority-vote comparison"

While documenting the harness's hard/review-gate comparison mechanism
(`compare_counter`/`counter_diff`), the architecture doc used the Korean term
for "majority vote" to describe it — but the actual mechanism (count each
list's values with `Counter` and subtract — a multiset/bag difference) has
nothing to do with voting. The user caught it. Whether the mechanism was
understood correctly shows up even in small wording mistakes like this — why
the Phase 2 checkpoint includes "re-check your own terminology after writing."

## Phase 2/3: the config parser silently ignores things — hit twice

The harness uses a hand-rolled mini YAML parser that only recognizes a fixed
set of key paths and silently ignores anything else (no error).

1. Writing `required_target_keys: []` in `gates.yml` to disable the
   frontmatter-required-key check didn't work — the parser doesn't support
   inline empty-list syntax, so it silently fell back to the hardcoded
   default (`["title"]`). Result: every frontmatter-less technical doc was
   *always* falsely rejected. This needed a one-line fix to the harness
   itself (make `key: []` parse as an actual empty list); confirmed the
   existing blog config never uses that syntax, so blog behavior didn't
   change, before proceeding.
2. New style rule keys added to `style_policy.yml` (`anchor_preservation`,
   `directive_preservation`, etc.) aren't in the parser's fixed path list
   (`load_style_policy()`'s `if path == [...]` conditions), so those rules are
   **documented but never actually executed**. Still unresolved — only noted
   in the style guide.

Lesson: before adding a new config key, check whether code actually reads it.
Otherwise "rules you think you configured but that are actually inert" keep
piling up.

## Phase 4: a concrete case for `cp`+`diff` over `Write`

`eval_config.yml`, described as "reuse the blog values as-is," was actually
retyped by hand while adding comments. Only later, running
`diff skills/quality/configs/eval_config.yml
skills/quality-docs/configs/eval_config.yml`, was it confirmed that nothing
but the intended 4 comment lines had changed. It worked out, but "checked and
it happened to be fine" is less reliable than "built with `cp`+`Edit` so it
couldn't have been wrong in the first place." `cp` also doesn't need the
model to regenerate file content — for "mostly the same file," `cp`+`diff`
wins on both reliability and cost.

## Phase 4: thought it was "done," but files were missing

After judging `skills/quality-docs` finished, the user asked to verify the
basic scaffolding was in place. Comparing file trees with `find` showed
`schemas/mqm_judge.schema.json` and `schemas/quality_report.schema.json` were
missing entirely — files that describe the harness's JSON output shape,
almost identical regardless of document type, simply forgotten. "Feels done"
is a subjective judgment; an actual file-tree diff is objective evidence.

## Phase 1: reused research already in the repo

Before starting web research for `skills/quality-docs`, a file already
existed in the repo:
`translation-flow/docs/hf_ko_translation_best_practice.md` — real Korean
translation PR/issue/review comments from transformers, smolagents, lerobot,
diffusers, and huggingface_hub, with source links. It became the primary
source, supplemented with the official guide (`docs/TRANSLATING.md`) and a
direct comparison of a real merged source↔translation file pair. Skipping the
repo search would have meant redoing research that already existed.

## Phase 1: a correction research alone couldn't have caught

After finishing the anchor/TOC research, the user corrected it directly:
`_toctree.yml` only manages the sidebar; the in-page TOC is auto-generated
from the heading structure. Neither the official guide nor the file
comparison had made this explicit. Domain knowledge from a person can't be
substituted by document research alone — why the Phase 1 checkpoint ends with
"show the deliverable to the user and get confirmation."
