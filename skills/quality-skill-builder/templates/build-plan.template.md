# <new document type> translation quality skill build plan

<!--
Phase 3 deliverable. Write this after reading Phase 1
(format-content-detail-comparison) and Phase 2 (harness architecture doc) in
full. This doc must be the sole input to Phase 4 implementation — don't
improvise changes in Phase 4 that aren't recorded here.
-->

## Keep/modify/new decisions per evaluation item

<!--
Use the classification from SKILL.md Phase 3 as-is:
Keep / Reconfigure assets only / Soften-harden / Disable / New parsing needed /
New gate-validator needed / Structurally impossible
-->

| Evaluation item | Class | What changes | Rationale (cite Phase 1/2) |
|---|---|---|---|
| front_matter hard gate | | | |
| code_blocks hard gate | | | |
| inline_code / links / images / latex / tables / todo_markers | | | |
| glossary validation | | | |
| 11 style-guide validators | | | |
| Metric triage (QE/embedding/chrF) | | | |
| MQM judge prompt | | | |
| <new item unique to this document type> | | | |

## Parsing requirements

| New info to extract | Extraction location/method | Comparison method (multiset vs. order/pair-based) | Hard or review gate |
|---|---|---|---|

## Items judged structurally impossible

<!-- Items that can't be automated with the current architecture (single
source-file ↔ single target-file comparison), to be left as "requires manual
check" in the skill docs -->

-

## Assets to change

<!-- List the actual file paths to be touched. Separate new files from
existing files where only a value changes. -->

### New files

-

### Existing files where only a value/wording changes

-

### Tool code (harness) changes

<!-- State "none" explicitly if there are none. If there are, specify exactly
which function/logic, and why config alone isn't enough. -->

-

## Items requiring user approval

<!-- Collect every item classified "new gate/validator needed" or
"soften/harden," plus any tool-code change, here so none are missed when
requesting approval. -->

-
