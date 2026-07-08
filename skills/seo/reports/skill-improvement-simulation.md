# SEO Policy Variant Simulation

## Fixtures
- `current`: `{'PASS': 34, 'FAIL': 2, 'BLOCKED': 3, 'NEEDS_CHANGES': 3}`
- `demote_h1`: `{'PASS': 34, 'FAIL': 2, 'BLOCKED': 3, 'NEEDS_CHANGES': 3}`
- `demote_contextual`: `{'PASS': 34, 'FAIL': 2, 'BLOCKED': 3, 'NEEDS_CHANGES': 3}`
- `blockers_plus_structural`: `{'PASS': 34, 'FAIL': 2, 'BLOCKED': 3, 'NEEDS_CHANGES': 3}`
- `blockers_only`: `{'PASS': 39, 'BLOCKED': 3}`

## Posts
- `current`: `{'PASS': 19, 'NEEDS_CHANGES': 8, 'FAIL': 4}`
- `demote_h1`: `{'PASS': 19, 'NEEDS_CHANGES': 8, 'FAIL': 4}`
- `demote_contextual`: `{'PASS': 19, 'NEEDS_CHANGES': 8, 'FAIL': 4}`
- `blockers_plus_structural`: `{'PASS': 19, 'NEEDS_CHANGES': 8, 'FAIL': 4}`
- `blockers_only`: `{'PASS': 31}`

## Negative/blocker PASS risks
- `blockers_only` makes `generated_poor` (negative) PASS; failed `['alt_text_coverage', 'descriptive_alt_text']`
- `blockers_only` makes `mutated_missing_alt` (negative) PASS; failed `['alt_text_coverage', 'descriptive_alt_text']`
- `current` makes `mutated_broken_internal_link` (blocker) PASS; failed `[]`
- `demote_h1` makes `mutated_broken_internal_link` (blocker) PASS; failed `[]`
- `demote_contextual` makes `mutated_broken_internal_link` (blocker) PASS; failed `[]`
- `blockers_plus_structural` makes `mutated_broken_internal_link` (blocker) PASS; failed `[]`
- `blockers_only` makes `mutated_broken_internal_link` (blocker) PASS; failed `[]`
- `current` makes `mutated_missing_h1_no_title` (negative) PASS; failed `[]`
- `demote_h1` makes `mutated_missing_h1_no_title` (negative) PASS; failed `[]`
- `demote_contextual` makes `mutated_missing_h1_no_title` (negative) PASS; failed `[]`
- `blockers_plus_structural` makes `mutated_missing_h1_no_title` (negative) PASS; failed `[]`
- `blockers_only` makes `mutated_missing_h1_no_title` (negative) PASS; failed `[]`
- `current` makes `mutated_multiple_h1` (negative) PASS; failed `[]`
- `demote_h1` makes `mutated_multiple_h1` (negative) PASS; failed `[]`
- `demote_contextual` makes `mutated_multiple_h1` (negative) PASS; failed `[]`
- `blockers_plus_structural` makes `mutated_multiple_h1` (negative) PASS; failed `[]`
- `blockers_only` makes `mutated_multiple_h1` (negative) PASS; failed `[]`
- `blockers_only` makes `mutated_heading_skip` (negative) PASS; failed `['heading_hierarchy']`
- `current` makes `mutated_broken_image_path` (blocker) PASS; failed `[]`
- `demote_h1` makes `mutated_broken_image_path` (blocker) PASS; failed `[]`
- `demote_contextual` makes `mutated_broken_image_path` (blocker) PASS; failed `[]`
- `blockers_plus_structural` makes `mutated_broken_image_path` (blocker) PASS; failed `[]`
- `blockers_only` makes `mutated_broken_image_path` (blocker) PASS; failed `[]`
- `current` makes `mutated_description_body_mismatch` (negative) PASS; failed `[]`
- `demote_h1` makes `mutated_description_body_mismatch` (negative) PASS; failed `[]`
- `demote_contextual` makes `mutated_description_body_mismatch` (negative) PASS; failed `[]`
- `blockers_plus_structural` makes `mutated_description_body_mismatch` (negative) PASS; failed `[]`
- `blockers_only` makes `mutated_description_body_mismatch` (negative) PASS; failed `[]`
- `current` makes `mutated_meaningless_alt` (negative) PASS; failed `[]`
- `demote_h1` makes `mutated_meaningless_alt` (negative) PASS; failed `[]`
- `demote_contextual` makes `mutated_meaningless_alt` (negative) PASS; failed `[]`
- `blockers_plus_structural` makes `mutated_meaningless_alt` (negative) PASS; failed `[]`
- `blockers_only` makes `mutated_meaningless_alt` (negative) PASS; failed `[]`
- `current` makes `curated_semantic_negative_description` (negative) PASS; failed `[]`
- `demote_h1` makes `curated_semantic_negative_description` (negative) PASS; failed `[]`
- `demote_contextual` makes `curated_semantic_negative_description` (negative) PASS; failed `[]`
- `blockers_plus_structural` makes `curated_semantic_negative_description` (negative) PASS; failed `[]`
- `blockers_only` makes `curated_semantic_negative_description` (negative) PASS; failed `[]`
- `current` makes `curated_semantic_negative_title` (negative) PASS; failed `[]`
- `demote_h1` makes `curated_semantic_negative_title` (negative) PASS; failed `[]`
- `demote_contextual` makes `curated_semantic_negative_title` (negative) PASS; failed `[]`
- `blockers_plus_structural` makes `curated_semantic_negative_title` (negative) PASS; failed `[]`
- `blockers_only` makes `curated_semantic_negative_title` (negative) PASS; failed `[]`
