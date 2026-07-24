# Quality Review Artifact Reuse Design

## Goal

Run the expensive translation-quality LLM judge once per candidate revision, then
reuse that exact result for verification, PR reporting, and repair input.

The workflow must continue to fail closed when an artifact is missing, malformed,
incomplete, or does not match the reviewed PR head.

## Current Problem

`reusable-pr-review.yml` currently invokes the quality harness independently in
three jobs:

1. `review / quality`
2. `Independent Verifier`
3. `Publish Report`

Each job starts on a separate runner with an empty temporary directory and metric
cache. A document with `N` aligned segments therefore causes approximately `3N`
Luna calls on the successful path. A failed review can cause additional complete
evaluations while preparing and verifying a repair.

The repeated evaluations also allow the gate result and the published report to
disagree because they were produced by separate LLM calls.

## Chosen Architecture

Use workflow-run artifacts as the handoff contract between jobs.

```text
review / quality ---- Luna once -----+
review / seo ------------------------+--> review artifacts
                                      |--> verifier
                                      |--> report publisher
                                      +--> repair input

repair changes candidate content --------> quality evaluation once for new content
```

The initial review result is authoritative for the reviewed head SHA. The
verifier checks the integrity and completeness of that result; it does not ask
Luna for a second semantic opinion.

## Artifact Contract

Each matrix review job uploads its outputs even when the gate rejects the
candidate. Artifact names include the immutable input head SHA:

- `quality-review-<head_sha>`
- `seo-review-<head_sha>`

The quality artifact contains:

- `quality.json` — wrapper conclusion
- `quality.md` — full human-readable report
- `quality-eval.json` — structured harness report
- `quality-pr-comment.md`
- `quality-source-segments.jsonl`
- `quality-target-segments.jsonl`
- `quality-mqm-judge.jsonl`

The SEO artifact contains:

- `seo.json` — wrapper conclusion
- `seo.md`
- `seo-eval.json`
- `metadata-suggestion.json`, when produced

Artifacts are retained for one day. Upload and download actions are pinned to
commit SHAs.

## Workflow Data Flow

### Review

The quality and SEO matrix jobs retain their existing gate exit codes. A gate
failure still marks the matrix job as failed.

An `if: always()` upload step runs after evaluation so a valid rejection report
is available to the report and repair jobs. Upload failure is itself a workflow
failure.

### Independent Verifier

The verifier checks out the exact candidate SHA, downloads the review artifacts,
and invokes a dedicated artifact-verification script.

For quality results, the verifier checks:

- all required files exist and contain parseable data;
- the checked-out commit equals the workflow input `head_sha`;
- the target file SHA-256 equals `quality-eval.json.metadata.target_hash`;
- the wrapper conclusion agrees with the harness status;
- the report provider and model match the workflow's expected
  `QUALITY_LLM_JUDGE_PROVIDER` and `LLM_JUDGE_MODEL` values (Luna by default);
- MQM evaluation covers every aligned target segment exactly once;
- skipped MQM segment count is zero;
- the prompt hash and configuration metadata are present;
- successful quality outcomes contain complete semantic evaluation.

The verifier validates a well-formed rejection artifact successfully. The
lifecycle still fails because the review gate failed, not because the rejection
report was malformed.

SEO verification checks its existing structured result contract and confirms
that its wrapper conclusion agrees with the SEO gate result.

### Report

The report job downloads the same artifacts and passes their Markdown and result
JSON files to the existing PR comment publisher. It does not execute either
review skill again.

This guarantees that the report shown to reviewers is the report that produced
the gate conclusion.

### Repair

The repair job downloads the failed review artifacts and uses them directly to
prepare feedback. It does not regenerate the failed reports.

If repair changes the target file, the repaired content is a new candidate and
both gates run once against that content before any push. A failed repaired
quality evaluation is not pushed.

## Failure Handling

The workflow fails closed in these cases:

- a required artifact is absent;
- an artifact download or upload fails;
- structured output is malformed;
- target path, target hash, or head SHA does not match;
- a successful quality result has incomplete MQM coverage;
- wrapper and structured gate conclusions disagree;
- the configured judge provider or model is not the expected value.

No fallback re-evaluation occurs in report or verifier jobs. Re-evaluation could
hide artifact corruption and reintroduce result disagreement.

## Security and Trust Boundary

Artifacts are created by the trusted reusable workflow after checking out the
candidate at the exact input SHA. Candidate Markdown is treated as data and is
not executed.

The report and verifier consume only artifacts from the same workflow run. They
also independently bind the result to the expected head SHA and target content
hash.

## Testing

Tests cover:

- successful quality artifact verification;
- valid reject artifact verification;
- missing required files;
- malformed JSON;
- target hash mismatch;
- wrapper/status mismatch;
- wrong provider or model;
- missing, duplicate, extra, and skipped MQM segments;
- workflow uploads artifacts with `if: always()`;
- verifier and report download artifacts;
- verifier and report do not invoke `run_skill_review.py`;
- repair consumes failed artifacts without regenerating reports;
- repaired content runs the quality judge exactly once;
- the full repository test suite.

## Expected Cost

For a successful candidate with `N` aligned segments:

- before: approximately `3N` Luna calls;
- after: `N` Luna calls.

For a repaired candidate:

- initial revision: `N` calls;
- changed repaired revision: `N` calls;
- total: `2N` calls.

The independent verifier performs no additional Luna calls.
