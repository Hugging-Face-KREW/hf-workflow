# HF PR Agent 구현 스펙

상태: 구현 제안  
기준 문서: `specs/agent-workflow-design.md`  
구현 원칙: GitHub native 기능 우선, 기존 코드 재사용, 안전 invariant 유지,
범용 프레임워크는 실제 필요가 생길 때까지 만들지 않는다.

두 문서가 MVP 구현 범위에서 충돌하면 이 문서가 우선한다. 기존 설계 문서는
장기 아키텍처와 판단 근거로 남긴다.

## 1. 결정 요약

이 구현은 별도의 `Task`, `Workspace`, `TaskStore`, `LockManager` 프레임워크를
만들지 않는다. 같은 효과를 GitHub 기능으로 구현한다.

| 필요한 개념 | MVP 구현 |
|---|---|
| Task | GitHub Actions job |
| Workspace | job별 fresh `actions/checkout` |
| 병렬 Task | Actions matrix |
| Task dependency | Actions `needs` |
| Branch mutation lock | Actions `concurrency` |
| Task 상태 | GitHub Checks와 artifact |
| PR lifecycle 상태 | required commit status |
| Event router | workflow `on:`과 job `if:` |
| Desired content contract | 기존 `manifest.yaml` |
| Runtime reconciliation | GitHub snapshot을 읽는 Python finalizer |

PR lifecycle은 durable state machine이지만 별도 state-machine engine으로
구현하지 않는다. GitHub 이벤트가 transition을 일으키고 GitHub의 현재 상태에서
다음 행동을 계산한다.

## 2. 목표

- 번역 PR 생성 또는 갱신 즉시 SEO, Quality 등 blocking review를 병렬 실행한다.
- 자동 review finding을 안전 범위에서 수정하고 새 SHA를 다시 검증한다.
- 신뢰된 사람이 PR comment나 review를 남기면 Ready 상태에서도 자동 loop를
  다시 실행한다.
- 각 gate는 PR Checks 화면에서 독립 job으로 보인다.
- 현재 head SHA와 최신 사람 피드백이 모두 검증된 경우에만 merge를 허용한다.
- inline review thread를 답변하고, 검증된 처리 결과만 resolve한다.
- 모호하거나 위험하거나 진전 없는 요청은 `needs-human`으로 종료한다.
- 모든 조건이 수렴하면 Discord로 merge 요청을 보내고 사람만 GitHub에서
  최종 merge한다.

## 3. 비목표

- Kelos 호환 API 또는 Kubernetes 실행기
- 범용 agent orchestration 제품
- 자체 Task database, queue, lock service
- GitHub Actions 외 실행기로 즉시 교체하기 위한 adapter 계층
- Discord 안에서 approve 또는 merge
- 자동 merge
- 초기 버전의 정기 reconciliation scheduler

이 항목은 실제 운영상 필요가 확인되면 별도 RFC로 추가한다.

## 4. 기존 코드 재사용

다음 코드는 교체하지 않고 확장한다.

| 기존 파일 | 재사용 방법 |
|---|---|
| `translation-flow/scripts/create_translation_pr.py` | 번역 PR 생성 유지 |
| `scripts/run_local_review.py` | gate runner의 진입점으로 확장 |
| `skills/seo/` | SEO check와 deterministic test 유지 |
| `skills/quality/` | Quality check와 report 생성 유지 |
| `scripts/notify_discord.py` | merge-ready와 needs-human payload 지원 |
| `reports/pr-*/manifest.yaml` | 콘텐츠와 활성 skill 계약으로 유지 |
| `.github/workflows/daily-translation.yml` | PR 생성 스케줄만 담당 |

`scripts/run_local_review.py`의 자체 YAML 파서는 제거하고 `yaml.safe_load()`를
사용한다. PyYAML은 이미 SEO skill에서 사용하는 의존성이므로 공통 실행 환경에
명시적으로 설치한다. 별도 YAML codec framework는 만들지 않는다.

## 5. 저장소별 배치

### 5.1 `hf-workflow`

```text
.github/workflows/
  daily-translation.yml
  reusable-pr-review.yml
  reusable-pr-mutate.yml

scripts/
  run_local_review.py
  handle_pr_feedback.py
  finalize_pr.py
  review_threads.py
  notify_discord.py

skills/
  seo/
  quality/

reports/pr-N/
  manifest.yaml
```

신규 Python 파일은 세 개로 제한한다.

- `handle_pr_feedback.py`: 사람 피드백 triage와 제한된 수정
- `finalize_pr.py`: snapshot 재검증과 Lifecycle Gate 게시
- `review_threads.py`: thread 조회, 답변, resolve

기존 `notify_discord.py`와 `run_local_review.py`는 확장한다.

### 5.2 `hugging-face-krew.github.io`

```text
.github/workflows/
  hf-agent-review.yml
  hf-agent-mutate.yml
```

대상 저장소 workflow는 검토된 `hf-workflow` commit SHA의 reusable workflow를
호출한다. tag나 moving branch를 호출하지 않는다.

두 workflow를 분리하는 이유는 권한 경계다.

- `hf-agent-review.yml`: 콘텐츠 read, checks/status/report와 검증된 mutation
  workflow dispatch만 허용
- `hf-agent-mutate.yml`: 신뢰된 이벤트에만 branch write 허용

## 6. GitHub 상태 모델

### 6.1 Canonical merge gate

Branch protection이 요구할 유일한 HF Agent context는 다음 commit status다.

```text
HF Agent / Lifecycle Gate
```

상태 의미:

| 상태 | 의미 |
|---|---|
| `pending` | review, feedback 처리 또는 재검증 중 |
| `success` | 현재 lifecycle key가 모든 조건을 충족 |
| `failure` | `needs-human` 또는 확정된 blocking failure |
| `error` | workflow 또는 외부 의존성 오류 |

개별 Actions job은 증거와 가시성을 제공하지만 최종 merge 허용 여부는 Lifecycle
Gate가 결정한다.

### 6.2 Lifecycle key

```text
lifecycle_key = repository + pr_number + head_sha + feedback_revision
```

`feedback_revision`은 신뢰된 사람이 작성한 입력만으로 계산한다.

```text
feedback_revision = sha256(sorted([
  kind + comment_id + updated_at + body_hash
]))
```

다음 입력은 revision에서 제외한다.

- agent와 GitHub Actions bot comment
- marker report comment
- agent가 thread에 남긴 답변
- 신뢰되지 않은 사용자의 comment

review thread의 resolved 상태는 revision에 섞지 않고 별도 readiness 조건으로
평가한다. agent가 thread를 resolve한 행위가 새 사람 피드백처럼 재귀 trigger되는
것을 막기 위해서다.

### 6.3 최소 runtime marker

별도 DB 대신 bot이 관리하는 PR report comment 하나에 최소 상태를 보존한다.

```html
<!-- hf-agent-state
{"head_sha":"abc123","repair_attempt":1,"finding_hash":"...","notified_sha":"..."}
-->
```

사람에게 보이는 Markdown report와 hidden JSON marker를 같은 comment에서 upsert
한다. marker는 source of truth가 아니라 repair budget과 알림 dedupe를 위한
보조 상태다. head, comments, threads, checks는 매번 GitHub에서 다시 읽는다.

## 7. Label

| Label | 의미 |
|---|---|
| `hf-agent:managed` | 자동 review와 안전한 mutation 허용 |
| `hf-agent:paused` | mutation 중지, read-only 진단만 허용 |
| `hf-agent:needs-human` | 사람의 방향 결정이 필요함 |

에이전트가 생성한 번역 PR에는 `hf-agent:managed`를 기본으로 붙인다.

MVP는 slash-command parser를 만들지 않는다. 운영 제어는 label, Actions rerun,
`workflow_dispatch`로 수행한다.

## 8. Trigger 계약

### 8.1 Review workflow

```yaml
on:
  pull_request:
    types: [opened, reopened, ready_for_review, synchronize]
  merge_group:
  workflow_dispatch:
```

동작:

1. PR이 열려 있고 draft가 아니며 `hf-agent:managed`인지 확인한다.
2. PR API에서 실제 `head.sha`를 조회한다.
3. Lifecycle Gate를 `pending`으로 게시한다.
4. exact SHA를 checkout하고 blocking gate를 병렬 실행한다.
5. gate 결과에 따라 verifier, repair 또는 finalizer로 진행한다.

### 8.2 사람 피드백 workflow

```yaml
on:
  issue_comment:
    types: [created, edited]
  pull_request_review:
    types: [submitted, edited]
  pull_request_review_comment:
    types: [created, edited]
  workflow_dispatch:
```

entrypoint 순서:

1. 이벤트가 PR에 속하는지 확인한다.
2. PR이 open, unmerged, managed, unpaused인지 확인한다.
3. actor가 repository `write` 이상 또는 trusted-reviewer allowlist인지 확인한다.
4. bot marker와 agent 답변을 제외한다.
5. API에서 현재 PR head SHA를 다시 조회한다.
6. 해당 SHA의 Lifecycle Gate를 즉시 `pending`으로 게시한다.
7. feedback handler를 실행한다.

리뷰 이벤트의 `GITHUB_SHA`는 PR head가 아닐 수 있으므로 mutation과 status
게시에 직접 사용하지 않는다.

### 8.3 자동 repair dispatch

review gate가 실패하면 review workflow가 같은 run 안에서 코드를 수정하지
않는다. write 권한을 가진 mutate workflow를 `workflow_dispatch`한다.

dispatch 입력:

```yaml
inputs:
  mode: repair
  pr_number: 143
  expected_head_sha: abc123
  failed_skills: [seo, quality]
  finding_hash: sha256-normalized-findings
```

mutation token으로 push한 새 commit이 `pull_request.synchronize`를 발생시켜 다음
review cycle을 시작한다. 기존 `KREW_BOT_TOKEN`을 사용할 수 있지만 장기적으로는
최소 권한 GitHub App installation token을 권장한다.

## 9. Review workflow 상세

### 9.1 Preflight

- target PR head SHA를 API로 조회한다.
- manifest의 repository, branch, PR URL, file path가 실제 PR과 일치하는지
  검증한다.
- marker에서 현재 repair attempt를 읽는다.
- 시작 snapshot을 JSON artifact로 저장한다.

```json
{
  "pr_number": 143,
  "head_sha": "abc123",
  "feedback_revision": "f01...",
  "started_at": "2026-07-04T00:00:00Z"
}
```

### 9.2 Blocking jobs

```text
HF Agent / SEO
HF Agent / Quality
HF Agent / Source Fidelity
HF Agent / Structure
HF Agent / Feedback Addressed
HF Agent / Independent Verifier
HF Agent / Review Threads Resolved
HF Agent / Publish Report
HF Agent / Finalize Lifecycle
```

초기 matrix에는 실제 구현이 존재하는 `seo`, `quality`만 활성화한다.
`source-fidelity`, `structure`, `feedback-addressed`는 해당 check가 구현되고
검증되기 전까지 이름만 미리 만들거나 항상 성공시키지 않는다.

```yaml
strategy:
  fail-fast: false
  matrix:
    skill: [seo, quality]
```

각 job은 다음 result JSON을 artifact로 남긴다.

```json
{
  "schema_version": 1,
  "skill": "seo",
  "head_sha": "abc123",
  "conclusion": "fail",
  "findings": [],
  "duration_ms": 42000
}
```

### 9.3 Independent verifier

Verifier는 review gate들이 pass한 뒤 별도 job에서 실행한다.

- exact candidate SHA fresh checkout
- `contents: read`
- write/push credential 없음
- implementer의 hidden reasoning 전달 금지
- deterministic check를 먼저 실행
- candidate 수정 금지

Verifier가 fail하면 finding만 반환한다. 수정은 새 repair cycle이 담당한다.

`Review Threads Resolved` job은 verifier 뒤에 실행한다. 검증을 통과한
disposition에 대해서만 답변·resolve를 수행한 뒤 unresolved thread가 남았는지
검사한다. 이 job의 실패는 content repair finding으로 취급하지 않는다.

### 9.4 Report

모든 gate가 종료되면 marker comment 하나를 upsert한다.

```markdown
## HF Agent 리뷰

| Gate | 결과 | 요약 |
|---|---|---|
| SEO | Fail | description 누락 |
| Quality | Pass | blocking finding 없음 |

Head SHA: `abc123`
Repair attempt: `1/3`
```

실패한 job도 `if: always()`로 artifact와 report를 남긴다.

## 10. 자동 repair loop

```text
review finding
→ finding normalize/hash
→ repair 가능 여부 확인
→ mutate workflow dispatch
→ expected SHA 재확인
→ 최소 수정
→ deterministic check
→ commit/push
→ synchronize
→ 전체 review 재실행
```

자동 repair 조건:

- `hf-agent:managed`이고 paused가 아님
- 현재 head SHA가 dispatch의 expected SHA와 같음
- 수정 대상이 manifest의 번역 파일 또는 명시적 allowlist 안에 있음
- changed lines 200 이하
- repair attempt 3회 미만
- 동일 finding hash가 연속 두 번 발생하지 않음
- 서로 충돌하는 사람 지시가 없음
- workflow, CI 설정, secret, dependency 변경이 필요하지 않음

하나라도 충족하지 않으면 수정하지 않고 `needs-human`으로 전환한다.

Mutation concurrency:

```yaml
concurrency:
  group: hf-agent-mutate-${{ repository }}-${{ pr_number }}
  cancel-in-progress: false
```

write 직전에 PR head SHA를 다시 조회한다. stale이면 파일을 쓰거나 commit하지
않고 최신 snapshot을 reconcile한다.

## 11. 사람 feedback loop

### 11.1 Triage 결과

MVP disposition은 네 개만 사용한다.

| Disposition | 동작 |
|---|---|
| `actionable` | 안전 정책 통과 시 수정 |
| `addressed` | 이미 반영됨을 근거와 함께 답변 |
| `no-change` | 질문 또는 객관적으로 수정 불필요, 이유 답변 |
| `needs-human` | 모호함, 충돌, 고위험 요청 |

### 11.2 코드 수정이 필요한 경우

```text
trusted feedback
→ Lifecycle Gate pending
→ exact SHA checkout
→ 최소 diff 생성
→ 관련 deterministic check
→ commit/push
→ 새 SHA 전체 review
→ verifier pass
→ thread에 commit 근거 답변
→ thread resolve
→ finalizer
```

### 11.3 코드 수정이 필요 없는 경우

- 질문에는 답변한다.
- 이미 반영됐으면 파일과 근거를 답변한다.
- duplicate, irrelevant, out-of-scope은 이유를 답변한다.
- 객관적인 disposition만 inline thread를 resolve할 수 있다.
- 모호하거나 합의가 필요한 thread는 unresolved로 유지한다.
- 같은 SHA에서 finalizer를 다시 실행한다.

코드가 바뀌지 않은 같은 SHA에는 merge-ready Discord 알림을 다시 보내지 않는다.

## 12. Review thread 처리

`scripts/review_threads.py`는 GitHub GraphQL API를 사용한다.

필요 연산:

- `PullRequest.reviewThreads` 조회
- unresolved thread와 comment 수집
- thread reply
- `resolveReviewThread` mutation

resolve 조건:

1. 적용한 commit이 현재 PR head에 존재한다.
2. 해당 SHA의 관련 deterministic gate와 verifier가 pass했다.
3. thread에 commit SHA와 처리 근거를 답변했다.
4. disposition이 `addressed`, `no-change` 또는 검증된 `actionable`이다.

`CHANGES_REQUESTED` review 상태는 thread resolved와 별개다. 에이전트는 사람
review를 dismiss하지 않는다.

Branch protection에서 GitHub native “Require conversation resolution before
merging”도 활성화한다.

## 13. Finalizer 알고리즘

`scripts/finalize_pr.py`가 최종 readiness를 한 곳에서 계산한다.

```python
before = load_start_snapshot_artifact()
after = fetch_current_github_snapshot()

if before.head_sha != after.head_sha:
    publish_status(after.head_sha, "pending", "New head requires review")
    exit_not_ready()

if before.feedback_revision != after.feedback_revision:
    publish_status(after.head_sha, "pending", "New feedback requires review")
    dispatch_reconcile(after)
    exit_not_ready()

if after.has_failed_repairable_gate:
    dispatch_repair_or_mark_needs_human(after)
    exit_not_ready()

if after.unresolved_review_threads:
    publish_status(after.head_sha, "failure", "Review threads unresolved")
    exit_not_ready()

if after.needs_human:
    publish_status(after.head_sha, "failure", "Human decision required")
    exit_not_ready()

publish_status(after.head_sha, "success", "Ready for human merge")
notify_merge_ready_once_per_head(after)
```

Lifecycle Gate `success` 조건:

- 현재 SHA의 모든 활성 blocking gate pass
- independent verifier pass
- pending actionable feedback 없음
- unresolved inline thread 0개
- `hf-agent:needs-human` 없음
- report 게시 성공
- 시작 이후 head SHA와 feedback revision 불변

## 14. Discord 알림

기존 `scripts/notify_discord.py`에 event별 payload builder를 추가한다.

```text
created       # 기존 PR 생성 알림
merge-ready   # 최종 사람 merge 요청
needs-human   # 사람 판단 요청
```

`merge-ready` payload:

- PR 제목과 URL
- 검증된 head SHA
- gate 요약
- unresolved thread 수 0
- “GitHub에서 최종 확인 후 merge” 문구

Dedupe:

```text
merge-ready = repository + PR + head_sha
needs-human = repository + PR + head_sha + feedback_revision + reason_hash
```

알림 실패는 merge readiness를 무효화하지 않는다. 실패는 job warning과 marker에
남기고 수동 재전송할 수 있게 한다.

## 15. 권한과 secret

### 15.1 Review workflow

```yaml
permissions:
  contents: read
  pull-requests: write  # marker report
  checks: read
  statuses: write       # Lifecycle Gate
  actions: write        # 검증된 repair workflow dispatch에만 사용
```

### 15.2 Mutation workflow

workflow 기본 권한은 read-only다. untrusted event는 authorization job까지만
실행한다. GitHub API로 actor를 검증한 job output이 `trusted=true`일 때만 별도
mutation job에 write 권한과 secret을 제공한다.

```yaml
permissions:
  contents: read
  pull-requests: read

jobs:
  authorize:
    permissions:
      contents: read
      pull-requests: read

  mutate:
    needs: authorize
    if: needs.authorize.outputs.trusted == 'true'
    permissions:
      contents: write
      pull-requests: write
      checks: read
      statuses: write
      actions: write
```

Secret:

```text
OPENAI_API_KEY
KREW_BOT_TOKEN 또는 GitHub App installation token
DISCORD_WEBHOOK_URL
```

보안 규칙:

- `pull_request_target`에서 PR 코드를 실행하지 않는다.
- comment body를 shell command로 보간하지 않는다.
- write token을 가진 job에서 PR 제공 스크립트를 실행하지 않는다.
- mutation path를 manifest file과 allowlist로 제한한다.
- reusable workflow와 third-party action을 commit SHA에 pin한다.
- actor permission을 이벤트 payload가 아니라 GitHub API로 확인한다.
- write secret은 trusted mutation job의 step env에만 주입한다.
- fork PR은 MVP managed mutation 대상에서 제외한다.

## 16. Branch protection

대상 repository의 기본 branch에 다음을 설정한다.

- Require pull request before merging
- Require status checks before merging
  - `HF Agent / Lifecycle Gate`
  - 기존 build/test required checks
- Require conversation resolution before merging
- Block force push
- 관리자 bypass는 긴급 운영 절차로만 사용

가능하면 Lifecycle Gate의 expected source를 해당 GitHub App 또는 GitHub Actions
app으로 제한한다.

## 17. 실패와 재시도

| 상황 | 처리 |
|---|---|
| 같은 SHA의 transient gate 오류 | 실패 job만 rerun |
| 같은 SHA의 evaluator 오류 | 해당 job과 finalizer rerun |
| 새 commit 생성 | 전체 blocking gate 재실행 |
| mutation 중 SHA 변경 | stale 종료 후 최신 snapshot reconcile |
| 동일 finding 두 번째 반복 | `needs-human` |
| repair 3회 초과 | `needs-human` |
| no-op repair | `needs-human` |
| Discord 실패 | warning, merge는 차단하지 않음 |
| GitHub/OpenAI 일시 오류 | 최대 2회 bounded retry |

초기 버전은 schedule reconciler를 두지 않는다. 누락 또는 stuck run은
`workflow_dispatch`로 복구한다. 실제 누락 사례가 반복되면 그때 최소 cron
reconciler를 추가한다.

## 18. 테스트 스펙

### 18.1 Unit

- feedback revision이 bot comment를 제외한다.
- trusted human comment 수정 시 revision이 바뀐다.
- stale SHA에서 mutation하지 않는다.
- path allowlist 밖의 diff를 거부한다.
- 동일 finding hash 반복을 감지한다.
- repair budget을 초과하면 `needs-human`이다.
- finalizer가 새 feedback revision에서 success를 게시하지 않는다.
- Discord merge-ready 알림은 head SHA당 한 번이다.
- 모호한 thread를 자동 resolve하지 않는다.

### 18.2 Integration

fixture PR snapshot을 사용해 다음 transition을 검증한다.

```text
opened → reviewing → ready
opened → reviewing → repairing → reviewing → ready
ready → human feedback → repairing → reviewing → ready
ready → informational comment → ready, no duplicate Discord
ready → ambiguous feedback → needs-human
repair → stale SHA → reconcile
```

### 18.3 Workflow smoke

- matrix job 하나가 실패해도 나머지 결과와 report가 생성된다.
- finalizer job은 dependency 실패 후에도 실행된다.
- comment event는 `GITHUB_SHA`가 아닌 실제 PR head에 pending status를 게시한다.
- mutation push가 target PR의 새 review run을 발생시킨다.
- read-only verifier에는 write token이 없다.

## 19. 구현 순서

### Phase 1: Review와 Lifecycle Gate

1. `run_local_review.py`를 JSON result 출력 가능하게 확장한다.
2. `reusable-pr-review.yml`과 target caller를 추가한다.
3. SEO/Quality matrix와 exact-SHA verifier를 연결한다.
4. `finalize_pr.py`로 Lifecycle Gate를 게시한다.
5. branch protection을 설정한다.

### Phase 2: 자동 repair

1. `handle_pr_feedback.py --mode repair`를 구현한다.
2. finding hash, repair budget, path/line 제한을 구현한다.
3. mutate workflow와 branch concurrency를 연결한다.
4. push 후 전체 gate 재실행을 검증한다.

### Phase 3: 사람 피드백과 thread

1. comment/review event routing과 actor permission 검사를 추가한다.
2. feedback event에서 Lifecycle Gate를 먼저 pending 처리한다.
3. 네 가지 disposition과 답변을 구현한다.
4. GraphQL thread query/reply/resolve를 구현한다.
5. feedback revision optimistic check를 추가한다.

### Phase 4: Discord와 운영 지표

1. merge-ready/needs-human payload를 추가한다.
2. marker comment에 dedupe 상태를 기록한다.
3. task duration, repair count, ready까지 걸린 시간을 job summary에 기록한다.

## 20. 완료 조건

- 번역 PR 생성 후 SEO와 Quality job이 자동으로 병렬 실행된다.
- 하나의 gate가 실패해도 모든 gate 결과와 report를 확인할 수 있다.
- 안전한 finding은 최대 3회 안에서 자동 수정·push·재검증된다.
- 새 commit은 이전 SHA 결과를 재사용하지 않고 전체 gate를 다시 실행한다.
- Ready 이후 신뢰된 사람 comment가 생기면 같은 SHA라도 Lifecycle Gate가
  `pending`이 되고 loop가 다시 실행된다.
- 실행 중 새 comment가 생기면 이전 snapshot으로 success를 게시하지 않는다.
- 적용한 inline feedback은 검증 후 근거를 답변하고 resolve한다.
- 모호하거나 위험한 thread는 unresolved와 `needs-human`으로 남는다.
- 현재 SHA의 모든 gate, verifier, feedback, thread 조건이 충족되어야 Lifecycle
  Gate가 `success`다.
- merge-ready Discord 알림은 head SHA당 한 번만 전송된다.
- 자동 merge는 없고 사람이 GitHub에서 최종 merge한다.
- 자체 Task framework, database, scheduler 없이 위 조건을 충족한다.

## 21. 운영 목표

GitHub-hosted runner 대기열이 정상이라는 전제에서 다음을 초기 목표로 둔다.

| 경로 | 목표 |
|---|---|
| 수정 없이 ready | p50 6분, p90 10분 |
| 자동 수정 1회 | p50 14분, p90 20분 |
| 전체 자동 loop | 30분 또는 mutation 3회 이내 |

실제 1~2주간 job duration을 수집한 뒤 목표를 조정한다.
