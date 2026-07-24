# SEO metadata module I/O guide

이 문서는 SEO 평가 모듈과 metadata 생성 모듈을 PR agent에 연결하기 위한 입출력 기준을 정리합니다.

## 목표

SEO는 두 단계로 분리합니다.

1. SEO 평가 / 루브릭 모듈
   - PR comment에 표시됩니다.
   - 실패하면 `HF Agent / Repair Failed Gates`가 실행됩니다.

2. Metadata 생성 모듈
   - frontmatter 후보를 JSON으로 제안합니다.
   - 직접 파일을 수정하거나 commit/push하지 않습니다.
   - PR agent가 별도 job에서 안전한 frontmatter 필드를 적용하고 commit합니다.

## SEO 평가 모듈 output

기존 wrapper 호환성을 위해 아래 파일은 유지해야 합니다.

```text
results/
  seo.md
  seo.json
  seo-eval.json
```

### `results/seo.md`

사람이 읽는 report입니다. PR comment의 접힘 영역에 표시됩니다.

권장 섹션:

```md
# SEO Eval Report

**Gate:** ✅ **PASS** — deterministic AND rubric

## Gate
## Blockers
## Required checks (gated)
## OpenAI rubric checks
## Advisory checks (not gated)
## Signals
## Frontmatter
```

`Gate`, `Blockers`, `Required checks (gated)`, `OpenAI rubric checks`만 blocking gate로 취급합니다.

`Advisory checks`, `Signals`, `Frontmatter`는 PR comment에 보여도 되지만, 실패를 만들어서는 안 됩니다.

### `results/seo.json`

PR agent wrapper가 읽는 기존 gate result입니다. shape을 바꾸지 않습니다.

```json
{
  "conclusion": "pass",
  "report_path": "/tmp/results/seo.md",
  "skill": "seo"
}
```

주의:

- `conclusion`은 SEO 평가 / 루브릭 gate 결과만 반영합니다.
- metadata suggestion의 `PARTIAL`, `ERROR`, `SKIPPED`가 `conclusion: fail`로 번지면 안 됩니다.
- 이 파일에 metadata suggestion 내용을 넣지 않습니다.

### `results/seo-eval.json`

metadata 생성 모듈의 입력입니다. 최소한 아래 필드는 있어야 합니다.

```json
{
  "gate": {
    "passed": true,
    "status": "PASS"
  },
  "input": {
    "file_path": "_posts/2026-01-01-sample.md",
    "source_url": "https://huggingface.co/blog/sample",
    "primary_keyword": "검색 임베딩 벤치마크"
  }
}
```

## Metadata 생성 모듈 input

metadata 생성 모듈은 아래 입력을 받습니다.

```bash
python skills/seo/tools/metadata_suggestion.py \
  --file "_posts/2026-01-01-sample.md" \
  --target-root "../target" \
  --eval-json "results/seo-eval.json" \
  --output "results/metadata-suggestion.json" \
  --report-path "results/seo.md"
```

선택 입력:

```bash
--manifest "manifest.yml"
--openai-required
--openai-model "gpt-5-nano"
```

manifest가 제공되면 metadata policy는 아래 위치에서 읽습니다.

```yaml
handoff:
  seo:
    metadata_policy:
      target_url: https://hugging-face-krew.github.io/sample/
      source_url: https://huggingface.co/blog/sample
      canonical_policy: self
      translation_indexing: independent
      target_locale: ko
      source_locale: en
```

## Metadata 생성 모듈 output

파일명은 고정입니다.

```text
results/metadata-suggestion.json
```

### 공통 shape

```json
{
  "schema_version": 1,
  "kind": "seo_metadata_suggestion",
  "status": "PARTIAL",
  "file_path": "_posts/2026-01-01-sample.md",
  "source_eval": {
    "status": "PASS",
    "passed": true,
    "report_path": "/tmp/results/seo.md",
    "eval_json_path": "/tmp/results/seo-eval.json"
  },
  "candidate": {
    "title": "...",
    "description": "...",
    "categories": ["Translation", "HuggingFace"],
    "image": "/blog/assets/sample/thumbnail.png",
    "canonical": "",
    "hreflang": {},
    "json_ld": {}
  },
  "apply": {
    "allowed": false,
    "mode": "frontmatter_only",
    "requires_human": true
  },
  "needs_policy_decision": [
    "target_url",
    "source_url",
    "canonical_policy",
    "translation_indexing",
    "target_locale",
    "source_locale"
  ],
  "warnings": [],
  "reason": "metadata candidate needs policy decisions or missing title/description"
}
```

주의:

- `metadata-suggestion.json`에는 `skill`을 넣지 않습니다.
- `metadata-suggestion.json`에는 `conclusion`을 넣지 않습니다.
- 그래야 PR agent가 이 파일을 blocking gate로 오인하지 않습니다.

## Status 기준

| status | 의미 | PR agent 동작 |
|---|---|---|
| `SKIPPED` | SEO gate가 fail이어서 metadata 생성을 건너뜀 | 적용 안 함 |
| `PARTIAL` | 후보는 있지만 정책 결정/필수 필드가 부족함 | safe frontmatter 필드만 적용 |
| `READY` | 자동 적용 가능한 후보 | `apply.allowed`가 true이면 적용 가능 |
| `ERROR` | metadata 생성 실패 | 적용 안 함, SEO gate fail로 바꾸지는 않음 |

## Frontmatter 자동 적용 정책

PR agent는 SEO gate와 verifier가 모두 green이면 metadata apply job을 실행합니다.

이 job은 deterministic/idempotent해야 하므로 OpenAI key를 주입하지 않습니다. 즉 자동 재발화 경로에서는 매 run마다 다른 title/description 후보가 나와 commit loop가 생기지 않아야 합니다.

`PARTIAL` 상태에서도 아래 safe field는 자동 적용할 수 있습니다.

```text
title
description
categories
image
```

아래 policy field는 정책값이 명확할 때만 적용합니다.

```text
canonical
hreflang
json_ld
```

`metadata-suggestion.json`이 생성되지 않은 경우 PR agent는 workflow를 실패시키지 않고 `SKIPPED`, `changed=false`로 처리합니다.

## 정책 field까지 자동 commit을 요청하는 output

metadata 생성 모듈이 PR agent에게 commit을 요청하려면 아래 조건을 모두 만족해야 합니다.

```json
{
  "status": "READY",
  "apply": {
    "allowed": true,
    "mode": "frontmatter_only",
    "requires_human": false,
    "target_files": [
      {
        "path": "_posts/2026-01-01-sample.md",
        "operation": "update_frontmatter",
        "fields": ["description", "image", "canonical", "hreflang"]
      }
    ],
    "commit_message": "🔧 Update SEO metadata"
  },
  "needs_policy_decision": []
}
```

PR agent는 정책 field까지 포함해서 적용할 때 아래 조건을 확인합니다.

- `kind == "seo_metadata_suggestion"`
- `status == "READY"`
- `apply.allowed == true`
- `apply.requires_human == false`
- `needs_policy_decision == []`
- `file_path`가 `_posts/*.md`

`PARTIAL`인 경우에는 위 조건을 모두 만족하지 않아도 safe frontmatter 필드만 적용할 수 있습니다. 이 경우 `canonical`, `hreflang`, `json_ld`는 적용하지 않습니다.

## 담당자에게 요청할 사항

SEO 모듈 담당자는 다음 기준을 맞춰주면 됩니다.

1. `seo.md`, `seo.json`, `seo-eval.json`은 계속 생성합니다.
2. `seo.json`은 기존 shape을 유지하고, metadata 결과를 gate 실패로 반영하지 않습니다.
3. `metadata-suggestion.json`은 `kind: seo_metadata_suggestion`으로 생성합니다.
4. `metadata-suggestion.json`에는 `skill`, `conclusion`을 넣지 않습니다.
5. `PARTIAL`이어도 `title`, `description`, `categories`, `image` 후보는 채워주세요. PR agent가 safe field만 자동 반영합니다.
6. 정책 field까지 자동 적용이 안전하면 `status: READY`, `apply.allowed: true`, `requires_human: false`, `target_files`를 채웁니다.
7. metadata 모듈은 직접 파일 수정, commit, push를 하지 않습니다.

## 담당자에게 보낼 짧은 요청문

SEO metadata 생성 모듈 output을 `results/metadata-suggestion.json`으로 맞춰주세요.

기존 `results/seo.md`, `results/seo.json`, `results/seo-eval.json`은 유지하고, `seo.json`은 SEO 평가/루브릭 gate 결과만 담아주세요. Metadata 생성 실패나 PARTIAL 상태가 `seo.json`의 fail로 번지면 안 됩니다.

`metadata-suggestion.json`에는 `skill`, `conclusion`을 넣지 말고, `PARTIAL`이어도 `title`, `description`, `categories`, `image` 후보는 가능하면 채워주세요. PR agent가 safe frontmatter 필드는 자동 반영합니다. `canonical`, `hreflang`, `json_ld`처럼 정책 판단이 필요한 필드까지 자동 적용 가능한 경우에만 `status: READY`, `apply.allowed: true`, `apply.requires_human: false`, `apply.target_files`를 채워주세요.

파일 수정/commit/push는 metadata 모듈이 하지 않고, PR agent가 `metadata-suggestion.json`을 읽어서 별도 job에서 처리합니다.
