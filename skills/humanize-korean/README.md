# Humanize Korean Skill

This folder contains a Codex-compatible skill adapted for reviewing Korean text
that sounds machine-written.

The initial reference is:

- `epoko77-ai/im-not-ai`
- Source skill path: `codex/skills/humanize-korean`
- License: MIT

This repo keeps a local adapted copy instead of a submodule because the upstream
Codex skill uses a references symlink into its Claude skill tree. A local copy is
more stable for CI and for manifest-based translation PR workflows.

## Local report

```bash
python skills/humanize-korean/tools/simple_humanize_report.py \
  --input path/to/korean.md \
  --output reports/humanize-report.md
```

The deterministic tool is a smoke-test helper. The actual skill remains an
agent instruction: preserve meaning and only adjust Korean style when asked.

