# Translation Flow

`translation-flow` owns the operational workflow for creating Korean
translation work from Hugging Face Blog posts.

## Responsibility

This repo should:

- read `https://huggingface.co/blog/feed.xml` or an equivalent RSS source
- find posts published for the target date
- fetch source post metadata and content
- create a Korean translation file
- create a branch and PR in the target translation repository
- write a manifest that downstream skills can consume

This repo should not own SEO rewriting policy or translation quality scoring.
Those live in `seo-skills` and `quality-skills`.

## Manifest

The manifest is the handoff artifact. It tells downstream skills which source
post and translation file to operate on. New runs also store the raw source
Markdown under `source-snapshots/` and record `source.file_path` plus
`source.hash` in the manifest so quality checks can distinguish source drift
from translation errors. Created results also record `translation.commit_sha`
and the same `commit_sha` in `run-summary.json`, allowing downstream quality
checks to publish status only for the exact target revision they evaluated.

See:

- `manifests/example.yaml`

## Initial command shape

Install dev dependencies:

```bash
uv sync --extra dev
```

For actual translation generation, set an OpenAI API key:

```bash
cp .env.example .env
# Edit .env and fill OPENAI_API_KEY and GITHUB_TOKEN when pushing/dispatching.
set -a
source .env
set +a
```

Dry-run today's RSS selection:

```bash
uv run python scripts/create_translation_pr.py \
  --timezone Asia/Seoul \
  --target-worktree /path/to/hf-blog-translation-intern \
  --posts-dir output/posts \
  --no-pr \
  --no-push \
  --dry-run
```

Create a local draft branch, commit the generated translation file, and write a
manifest without pushing or opening a PR:

```bash
uv run python scripts/create_translation_pr.py \
  --date 2026-05-11 \
  --timezone Asia/Seoul \
  --target-worktree /path/to/hf-blog-translation-intern \
  --target-repo hyeonseo2/hf-blog-translation-intern \
  --posts-dir output/posts \
  --translator openai \
  --no-pr \
  --no-push \
  --output-manifest output/manifests/2026-05-11-example.yaml
```

Open a PR by omitting `--no-pr` and `--no-push`. This requires a configured
GitHub remote and the `gh` CLI.

To exercise the flow without calling a translation API, use:

```bash
uv run python scripts/create_translation_pr.py \
  --date 2026-05-11 \
  --timezone Asia/Seoul \
  --target-worktree /path/to/hf-blog-translation-intern \
  --target-repo hyeonseo2/hf-blog-translation-intern \
  --posts-dir output/posts \
  --translator none \
  --no-pr \
  --no-push
```

## Translation adapters

`scripts/translation_adapters.py` defines the adapter interface.

- `openai`: implemented with the OpenAI Responses API + ECL block translation pipeline
- `none` / `placeholder`: implemented for local workflow testing

The default translation prompt lives at:

- `docs/translation_prompt.md`

Override it with:

```bash
uv run python scripts/create_translation_pr.py \
  --translation-prompt docs/translation_prompt.md \
  ...
```

## Translation guidance

Broader reviewer guidance lives in `docs/hf_ko_translation_best_practice.md`.
The ECL runtime does not inject that full guide into each prompt; it keeps the
prompt context focused on source structure, glossary hits, and block labels.

Guide compression is enabled by default for the OpenAI adapter. It splits the
Markdown guidance docs into sections, selects source-relevant guide sections,
and compresses them into a short article-specific guide capsule before
translation:

```bash
ECL_GUIDE_COMPRESSION=llm
ECL_GUIDE_CONTEXT_MAX_CHARS=1200
ECL_GUIDE_SOURCE_EXCERPT_CHARS=2500
ECL_GUIDE_DOCS=docs/hf_translation_conventions.md,docs/hf_ko_translation_best_practice.md
```

Disable it with `ECL_GUIDE_COMPRESSION=off`.

The compressed guide is separate from the glossary. It should contain style,
preservation, and risk guidance, not concrete source-to-target term mappings.

## Local glossary

When present, TSV files under `skills/quality/glossary/` are merged into the ECL
glossary before translation:

```text
skills/quality/glossary/ko.tsv
skills/quality/glossary/ml_terms.tsv
skills/quality/glossary/product_terms.tsv
```

Each TSV file uses `source_term`, `ko_term`, and `policy` columns. The current
runtime uses `source_term -> ko_term` for prompt glossary mappings. Local TSV
entries override the built-in glossary and can be overridden by an explicit
runtime glossary. Override the directory with `ECL_LOCAL_GLOSSARY_DIR`.


## GitHub Actions

`Daily HF Blog Translation` runs from `.github/workflows/daily-translation.yml`.

Required repository secrets:

- `OPENAI_API_KEY`: OpenAI API key used by the OpenAI translation adapter
- `KREW_BOT_TOKEN`: fine-grained token owned by the
  [`huggingfacekrew`](https://github.com/huggingfacekrew) account and mapped to
  `GITHUB_TOKEN` at runtime. The token owner is shown as the author of
  translation PRs and automation comments. It can push branches, open PRs in
  `Hugging-Face-KREW/hugging-face-krew.github.io`, and dispatch workflows in
  `Hugging-Face-KREW/seo-skills` and `Hugging-Face-KREW/quality-skills`
- `DISCORD_WEBHOOK_URL`: optional Discord webhook URL. When present, the
  workflow posts a notification after it creates a translation PR.

The workflow:

1. resolves today's date in `Asia/Seoul`
2. clones the KREW GitHub Pages repo
3. generates a translation draft and PR
4. writes the manifest and source snapshot
5. generates local SEO and quality reports under `reports/`
6. posts or updates the quality PR comment on the translation PR
7. uploads the run summary, manifests, source snapshots, and reports as artifacts
