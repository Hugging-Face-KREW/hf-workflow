# SEO Test Fixtures

These fixtures verify quality classification and dataset coverage, not whether
every existing blog post already passes SEO review. The independent dataset
labels and limitations are tracked in `evaluation_manifest.yml`; the pytest
status expectations are current-behavior regression checks.

## Generated fixtures

- `generated/excellent-post.md` -> `PASS`
- `generated/good-post.md` -> `PASS`
- `generated/medium-post.md` -> `NEEDS_CHANGES`
- `generated/poor-post.md` -> `FAIL`
- `generated/blocked-post.md` -> `BLOCKED`

## Real HFKREW samples

`real/` contains copied posts from `Hugging-Face-KREW/hugging-face-krew.github.io`.
They cover short guide posts, long technical translations, image-heavy posts,
and posts with different heading styles. These are regression samples for
realistic content shape, not a requirement that all current posts pass.

## Mutated samples

`mutated/` contains deliberate variants for specific failure modes:

- `missing-description.md`: frontmatter metadata advisory, body still passes.
- `missing-alt.md`: image alt failure.
- `broken-internal-link.md`: blocks only when evaluated with `target_root`.
- `noindex.md`: explicit publish blocker.
- `short-opening.md`: short introduction shape sample.
- additional mutations cover empty body, missing title/H1, multiple H1,
  heading-level skips, missing citations, broken local image paths, missing
  author, long title, and TOC-before-opening behavior.

## Dataset manifest

`evaluation_manifest.yml` is the source of truth for why each sample exists.
It records:

- source type: synthetic, mutation, or real HFKREW
- independent human label: positive, borderline, negative, blocker, or real regression
- phenomena covered by the sample
- rationale and limitation for using the sample

Use the manifest when judging whether the dataset supports a product claim.
Use golden snapshots only for current-behavior regression.
