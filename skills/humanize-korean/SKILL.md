# Humanize Korean Skill

Use this skill when reviewing Korean prose for "AI-like" tone, especially
translationese, rigid structure, repeated sentence rhythm, filler connectors,
passive phrasing, and inflated stock expressions.

This skill is adapted from `epoko77-ai/im-not-ai` for this workflow repository.
The upstream project describes a Codex-compatible `humanize-korean` skill for
removing Korean AI-writing tells while preserving meaning.

## Inputs

Prefer one of:

- Korean markdown file path
- Korean text pasted by the user
- translation-flow manifest plus target repo root

When a manifest is provided, read `translation.file_path` and operate on that
file in the target repo.

## Invariants

1. Preserve facts, claims, dates, numbers, names, URLs, code, and direct quotes.
2. Do not add content.
3. Do not remove technical nuance.
4. Preserve the original register: formal text should remain formal.
5. Avoid over-editing. If a change would alter more than a narrow phrase or
   sentence rhythm, report it instead of applying it.
6. Keep frontmatter, markdown structure, links, images, tables, and code blocks
   intact.

## Procedure

1. Read `references/quick-rules.md`.
2. Identify protected spans: code blocks, inline code, URLs, markdown links,
   frontmatter values, direct quotes, numbers, model names, API names, and
   product names.
3. Scan only normal prose for AI-tone patterns.
4. Group findings by category and severity.
5. If reviewing only, produce findings with before/after suggestions.
6. If editing, make surgical changes only where a finding maps to the rulebook.
7. Re-read the changed text and verify the invariants.

## Output

When reviewing:

- concise findings list
- category and severity
- suggested replacement
- remaining risks

When editing:

- summarize changed categories
- report estimated change ratio
- note anything intentionally left unchanged

## Notes

This is not a translation skill, SEO skill, or factual quality skill. Use it
after translation quality is acceptable and the remaining issue is Korean style.

