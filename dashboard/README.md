---
title: HF Workflow Dashboard
sdk: gradio
app_file: app.py
pinned: false
---

# HF Workflow Dashboard

Small Gradio dashboard for observing the HF blog translation workflow.

It shows, by target date:

- Hugging Face Blog RSS posts available for translation
- GitHub Actions run status
- `run-summary.json` status when an artifact is available
- Discord notification status inferred from job logs

## Hugging Face Space setup

Create a Gradio Space and upload the files in this directory.

Recommended Space secrets:

```text
GITHUB_TOKEN
```

`GITHUB_TOKEN` should be a fine-grained token with read access to
`Hugging-Face-KREW/hf-workflow`. Public API calls may work without it, but logs
and artifacts are more reliable with a token.

`GH_TOKEN` is also accepted as an alias.

Optional variables:

```text
GITHUB_REPO=Hugging-Face-KREW/hf-workflow
WORKFLOW_FILE=daily-translation.yml
HF_FEED_URL=https://huggingface.co/blog/feed.xml
```
