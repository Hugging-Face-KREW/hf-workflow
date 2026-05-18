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
post and translation file to operate on.

See:

- `docs/manifest.md`
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
  --target-worktree /path/to/hf-blog-ko \
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
  --target-worktree /path/to/hf-blog-ko \
  --target-repo your-org/hf-blog-ko \
  --translator openai \
  --no-pr \
  --no-push \
  --output-manifest manifests/2026-05-11-example.yaml
```

Open a PR by omitting `--no-pr` and `--no-push`. This requires a configured
GitHub remote and the `gh` CLI.

To exercise the flow without calling a translation API, use:

```bash
uv run python scripts/create_translation_pr.py \
  --date 2026-05-11 \
  --timezone Asia/Seoul \
  --target-worktree /path/to/hf-blog-ko \
  --target-repo your-org/hf-blog-ko \
  --translator none \
  --no-pr \
  --no-push
```

## Translation adapters

`scripts/translation_adapters.py` defines the adapter interface.

- `openai`: implemented with the OpenAI Responses API
- `none` / `placeholder`: implemented for local workflow testing
- `gemini`: reserved adapter slot
- `local`: reserved adapter slot

The default translation prompt lives at:

- `docs/translation_prompt.md`

Override it with:

```bash
uv run python scripts/create_translation_pr.py \
  --translation-prompt docs/translation_prompt.md \
  ...
```

## GitHub Actions

`Daily HF Blog Translation` runs from `.github/workflows/daily-translation.yml`.

Required repository secrets:

- `OPENAI_API_KEY`: OpenAI API key used by the OpenAI translation adapter
- `KREW_BOT_TOKEN`: fine-grained token mapped to `GITHUB_TOKEN` at runtime. It
  can push branches, open PRs in
  `Hugging-Face-KREW/hugging-face-krew.github.io`, and dispatch workflows in
  `Hugging-Face-KREW/seo-skills` and `Hugging-Face-KREW/quality-skills`
- `DISCORD_WEBHOOK_URL`: optional Discord webhook URL. When present, the
  workflow posts a notification after it creates a translation PR.

The workflow:

1. resolves today's date in `Asia/Seoul`
2. clones the KREW GitHub Pages repo
3. generates a translation draft and PR
4. uploads the manifest and run summary as artifacts
5. dispatches SEO and quality skill workflows with the manifest payload
