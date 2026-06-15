# Humanize Korean Quick Rules

Adapted from `epoko77-ai/im-not-ai` under the MIT license.

## Protected Spans

Do not rewrite:

- code blocks and inline code
- URLs and markdown link targets
- direct quotes
- numbers, dates, and measurements
- model names, API names, library names, product names
- YAML frontmatter keys and technical metadata

## Categories

### A. Translationese

Patterns:

- `~를 통해`
- `~에 대해`
- `~에 있어서`
- `~에 의해`
- `가지고 있다`

Prefer direct Korean phrasing:

- `AI 기술을 통해 개선한다` -> `AI로 개선한다`
- `이 문제에 대해 설명한다` -> `이 문제를 설명한다`

### B. Excess English Glossing

Patterns:

- unnecessary English in parentheses
- repeated English terms where Korean is clear

Preserve standard technical terms such as `LLM`, `GPU`, `API`, model names, and
package names.

### C. Mechanical Structure

Patterns:

- repeated `첫째`, `둘째`, `셋째`
- excessive bullets for simple prose
- headings that restate every paragraph

Prefer natural paragraph flow when the list is not semantically necessary.

### D. Stock AI Expressions

Patterns:

- `결론적으로`
- `시사하는 바가 크다`
- `주목할 만하다`
- `혁신적인`

Delete or replace only when the phrase adds no meaning.

### E. Uniform Rhythm

Patterns:

- many adjacent sentences with the same ending
- consistently similar sentence length

Vary sentence length without changing facts.

### F. Inflated Modifiers

Patterns:

- `매우`
- `정말`
- `상당히`
- repeated `~적`, `~성`, `~화`

Remove weak intensifiers unless they carry factual meaning.

### G. Hedging

Patterns:

- `~할 수 있을 것으로 보인다`
- `~라고 할 수 있다`
- `~일 가능성이 있다`

Prefer direct phrasing when the source is direct. Preserve uncertainty when the
source is genuinely uncertain.

### H. Connector Overuse

Patterns:

- repeated sentence-initial `또한`
- repeated `따라서`, `즉`, `나아가`

Remove or vary connectors when paragraph relation is already clear.

### I. Formal Noun Bloat

Patterns:

- `~하는 것`
- `~할 필요가 있다`
- `~하는 점`

Prefer verbs:

- `확인할 필요가 있다` -> `확인해야 한다`

### J. Visual Ornament

Patterns:

- excessive bold
- unnecessary quote marks
- decorative separators or emoji in technical prose

Preserve markdown used for actual structure.

## Severity

- S1: highly recognizable AI tell; remove when safe.
- S2: strong signal when repeated; reduce.
- S3: weak signal; report only unless combined with other issues.

## Self-check

Before finalizing:

1. Meaning unchanged.
2. Protected spans unchanged.
3. Markdown structure intact.
4. Register preserved.
5. Change ratio stays narrow.
6. Suggestions map to a rule above.

