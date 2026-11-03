"""Prepare fixed-input translation experiments and publish supplied candidates.

No model calls. Generation and quality scoring stay in their existing tools.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")


def command(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True).stdout.strip()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def validate_plan(plan: dict[str, Any]) -> None:
    for field in ("run_id", "document_id"):
        if not ID.fullmatch(plan[field]):
            raise ValueError(f"Invalid {field}")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", plan["target_repo"]):
        raise ValueError("Invalid target_repo")
    for field in ("blog_base_sha", "workflow_sha"):
        if not SHA.fullmatch(plan[field]):
            raise ValueError(f"{field} must be a pinned full commit SHA")
    post = PurePosixPath(plan["post_path"])
    if (len(post.parts) != 2 or post.parts[0] != "_posts" or post.suffix != ".md"
            or "\\" in plan["post_path"]):
        raise ValueError("post_path must be one _posts/*.md file")
    if not plan["source_url"].startswith("https://") or not plan["title"].strip():
        raise ValueError("A source URL and title are required")
    if "REPLACE_" in json.dumps(plan):
        raise ValueError("Replace all example placeholders before preparing a run")
    budget = plan["budget_usd"]
    if isinstance(budget, bool) or not isinstance(budget, (float, int)) or not 0 < budget < float("inf"):
        raise ValueError("A finite positive budget_usd is required")
    arms = plan["arms"]
    if not arms or len({a["id"] for a in arms}) != len(arms):
        raise ValueError("Arms must be nonempty and unique")
    for arm in arms:
        if not ID.fullmatch(arm["id"]) or not isinstance(arm["settings"], dict) or not arm["settings"]:
            raise ValueError("Each arm requires an id and explicit settings")


def prepare(plan_path: Path, source: Path, output: Path) -> None:
    plan = read(plan_path)
    validate_plan(plan)
    data = source.read_bytes()
    if not data.strip():
        raise ValueError("Source snapshot is empty")
    # Never silently reuse a directory containing an earlier frozen run.
    output.mkdir(parents=True, exist_ok=False)
    (output / "source.md").write_bytes(data)
    write(output / "run.json", {
        "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
        "source_sha256": digest(data), "plan": plan,
    })


def load_run(run: Path) -> dict[str, Any]:
    data = read(run / "run.json")
    validate_plan(data["plan"])
    if digest((run / "source.md").read_bytes()) != data["source_sha256"]:
        raise ValueError("Frozen source snapshot has changed")
    return data


def arm_dir(run: Path, arm: str) -> Path:
    data = load_run(run)
    if arm not in {item["id"] for item in data["plan"]["arms"]}:
        raise ValueError("Unknown experiment arm")
    return run / "arms" / arm


def stage(run: Path, arm: str, checkout: Path, candidate: Path) -> dict[str, Any]:
    data = load_run(run)
    plan = data["plan"]
    directory = arm_dir(run, arm)
    if directory.exists():
        raise ValueError("Arm already staged; use a new arm/run rather than overwrite history")
    origin = command("git", "remote", "get-url", "origin", cwd=checkout)
    if not origin.removesuffix(".git").endswith(("/" + plan["target_repo"], ":" + plan["target_repo"])):
        raise ValueError("Checkout origin does not match target_repo")
    content = candidate.read_bytes()
    if not content.startswith(b"---\n") and not content.startswith(b"---\r\n"):
        raise ValueError("Supply a complete publishing Markdown file with frontmatter")
    branch = f"codex/experiment/{plan['run_id']}/{plan['document_id']}/{arm}"
    worktree = (directory / "worktree").resolve()
    directory.mkdir(parents=True)
    command("git", "worktree", "add", "-b", branch, str(worktree), plan["blog_base_sha"], cwd=checkout)
    target = worktree / plan["post_path"]
    if target.is_symlink() or target.parent.is_symlink():
        raise ValueError("Post path cannot be a symlink")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    command("git", "add", "--", plan["post_path"], cwd=worktree)
    command("git", "commit", "-m", f"[실험] {plan['run_id']} / {arm}: initial translation", cwd=worktree)
    state = {
        "branch": branch, "initial_sha": command("git", "rev-parse", "HEAD", cwd=worktree),
        "target_sha256": digest(content), "worktree": str(worktree),
        "pr_url": None,
    }
    (directory / "candidate.md").write_bytes(content)
    # Absolute source path survives run_local_review copying the manifest into
    # its own report directory. Regenerate this local manifest after relocation.
    manifest = (
        f"version: 1\nrun:\n  id: {plan['run_id']}-{arm}\n"
        f"source:\n  url: {json.dumps(plan['source_url'])}\n"
        f"  file_path: {json.dumps(str((run / 'source.md').resolve()))}\n"
        f"  hash: {data['source_sha256']}\n  extraction: markdown\n"
        f"translation:\n  target_repo: {plan['target_repo']}\n  branch: {branch}\n"
        f"  commit_sha: {state['initial_sha']}\n  file_path: {plan['post_path']}\n"
        "  pr_url: \n  locale: ko\n"
    )
    (directory / "manifest.yaml").write_text(manifest, encoding="utf-8")
    write(directory / "pr.json", state)
    return state


def body_for(data: dict[str, Any], arm: str, state: dict[str, Any]) -> str:
    plan = data["plan"]
    settings = next(a["settings"] for a in plan["arms"] if a["id"] == arm)
    return (
        f"<!-- hf-agent-experiment:{plan['run_id']}:{arm} -->\n"
        f"## 번역 실험: {plan['run_id']} / {arm}\n\n"
        f"- 원문: {plan['source_url']}\n"
        f"- 원문 SHA-256: `{data['source_sha256']}`\n"
        f"- 공통 blog base: `{plan['blog_base_sha']}`\n"
        f"- hf-workflow 기준 버전: `{plan['workflow_sha']}`\n"
        f"- 최초 번역 SHA: `{state['initial_sha']}`\n"
        f"- 전체 실행 예산: ${plan['budget_usd']} (외부 생성·수정 호출에도 별도 상한 적용 필요)\n\n"
        f"```json\n{json.dumps(settings, ensure_ascii=False, indent=2)}\n```\n\n"
        "이 PR에서 최초 번역과 자동 평가·수정 과정을 함께 관찰합니다. "
        "커밋별 평가·비용은 결과 댓글로 연결합니다. 비용 미확인은 0으로 계산하지 않습니다.\n"
    )


def publish(run: Path, arm: str, enable_loop: bool = False) -> str:
    data = load_run(run)
    plan = data["plan"]
    directory = arm_dir(run, arm)
    state = read(directory / "pr.json")
    repo = plan["target_repo"]
    if enable_loop:
        # Do not start an older production loop while waiting for deployment.
        for name in ("hf-agent-review.yml", "hf-agent-feedback.yml"):
            remote = json.loads(command("gh", "api", f"repos/{repo}/contents/.github/workflows/{name}"))
            workflow = base64.b64decode(remote["content"]).decode("utf-8")
            pins = re.findall(r"(?:ref:|workflow_ref:|\.yml@)\s*([a-zA-Z0-9_./-]+)", workflow)
            workflow_pins = [pin for pin in pins if SHA.fullmatch(pin)]
            if len(workflow_pins) != 3 or set(workflow_pins) != {plan["workflow_sha"]}:
                raise ValueError(f"{name} does not consistently reference the experiment workflow_sha")
    if not state["pr_url"]:
        worktree = Path(state["worktree"])
        if command("git", "rev-parse", "HEAD", cwd=worktree) != state["initial_sha"]:
            raise ValueError("Worktree HEAD differs from frozen initial candidate")
        if command("git", "status", "--porcelain", cwd=worktree):
            raise ValueError("Candidate worktree must be clean before push")
        command("git", "push", "-u", "origin", state["branch"], cwd=worktree)
        # Recover a PR created before an interrupted local state update.
        existing = json.loads(command("gh", "pr", "list", "--repo", repo, "--state", "all",
                                      "--head", state["branch"], "--json", "url,headRefOid"))
        if existing:
            if len(existing) != 1 or existing[0]["headRefOid"] != state["initial_sha"]:
                raise ValueError("Existing PR does not match the frozen initial candidate")
            state["pr_url"] = existing[0]["url"]
        else:
            body = directory / "pr-body.md"
            body.write_text(body_for(data, arm, state), encoding="utf-8")
            command("gh", "label", "create", "hf-agent:experiment", "--repo", repo,
                    "--color", "7057ff", "--description", "Translation experiment", "--force")
            state["pr_url"] = command(
                "gh", "pr", "create", "--repo", repo, "--base", "main", "--head", state["branch"],
                "--draft", "--label", "hf-agent:experiment", "--title",
                f"[실험][{plan['run_id']}][{arm}] {plan['title']}", "--body-file", str(body),
            )
        write(directory / "pr.json", state)
        manifest_path = directory / "manifest.yaml"
        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8").replace("  pr_url: \n", f"  pr_url: {state['pr_url']}\n"),
            encoding="utf-8",
        )
    if enable_loop:
        # Initial SHA is persisted BEFORE adding the label that triggers review.
        command("gh", "pr", "edit", state["pr_url"], "--repo", repo, "--add-label", "hf-agent:managed")
    return state["pr_url"]


def record(run: Path, arm: str, sha: str, checkout: Path, evaluation: Path, usage: Path) -> None:
    data = load_run(run)
    if not SHA.fullmatch(sha):
        raise ValueError("Full revision SHA required")
    directory = arm_dir(run, arm)
    state = read(directory / "pr.json")
    command("git", "merge-base", "--is-ancestor", state["initial_sha"], sha, cwd=checkout)
    # Preserve bytes; text-mode subprocess would normalize CRLF before hashing.
    content = subprocess.run(["git", "show", f"{sha}:{data['plan']['post_path']}"],
                             cwd=checkout, check=True, capture_output=True).stdout
    report = read(evaluation)
    for key, expected in {"head_sha": sha, "source_sha256": data["source_sha256"],
                          "target_sha256": digest(content)}.items():
        if report.get(key) != expected:
            raise ValueError(f"Evaluation {key} does not match this revision")
    if not isinstance(report.get("summary"), str) or not report["summary"].strip():
        raise ValueError("Evaluation summary required; raw reports can be attached separately")
    costs = read(usage)
    if costs.get("head_sha") != sha or not isinstance(costs.get("calls"), list):
        raise ValueError("Usage requires matching head_sha and calls list")
    for call in costs["calls"]:
        if call["phase"] not in {"generation", "evaluation", "repair", "routing", "guardrails"} or not call["model"]:
            raise ValueError("Each call requires phase and actual model")
        cost = call["cost_usd"]
        if cost is not None and (isinstance(cost, bool) or not isinstance(cost, (int, float))
                                 or not 0 <= cost < float("inf")):
            raise ValueError("Cost must be finite and nonnegative, or null for unknown")
        elapsed = call.get("elapsed_seconds")
        if elapsed is not None and (isinstance(elapsed, bool) or not isinstance(elapsed, (int, float))
                                   or not 0 <= elapsed < float("inf")):
            raise ValueError("Duration must be finite and nonnegative, or null for unknown")
    revision = directory / "revisions" / sha
    if revision.exists():
        raise ValueError("Revision already recorded; do not overwrite experiment evidence")
    revision.mkdir(parents=True)
    write(revision / "evaluation.json", report)
    write(revision / "usage.json", costs)
    (revision / "candidate.md").write_bytes(content)


def comment(run: Path, arm: str, sha: str, artifact_url: str | None) -> str:
    data = load_run(run)
    if not SHA.fullmatch(sha):
        raise ValueError("Full revision SHA required")
    directory = arm_dir(run, arm)
    state = read(directory / "pr.json")
    if not state["pr_url"]:
        raise ValueError("Publish the experiment PR before recording a result comment")
    revision = directory / "revisions" / sha
    report, usage = read(revision / "evaluation.json"), read(revision / "usage.json")
    known = sum(c["cost_usd"] for c in usage["calls"] if c["cost_usd"] is not None)
    unknown = sum(c["cost_usd"] is None for c in usage["calls"])
    elapsed = sum(c.get("elapsed_seconds") or 0 for c in usage["calls"])
    unknown_elapsed = sum(c.get("elapsed_seconds") is None for c in usage["calls"])
    marker = f"<!-- hf-agent-experiment-result:{data['plan']['run_id']}:{arm}:{sha} -->"
    body = (f"{marker}\n## 실험 결과: {arm}\n\n"
            f"- 대상 커밋: `{sha}`\n- 최초 번역: `{state['initial_sha']}`\n"
            f"- 이번 기록의 확인된 비용: ${known:.6f}\n"
            f"- 비용 미확인 호출: {unknown}개\n"
            f"- 확인된 호출 시간 합계: {elapsed:.3f}초 (문서 전체의 경과 시간과 다를 수 있음)\n"
            f"- 시간 미확인 호출: {unknown_elapsed}개\n"
            "- 비용 집계 범위: 이 revision의 calls 목록. 전체 실행 합계가 아닙니다.\n\n"
            f"{report['summary']}\n")
    if artifact_url:
        if not artifact_url.startswith("https://github.com/"):
            raise ValueError("Expected a GitHub Actions artifact/run URL")
        body += f"\n[상세 실행 자료]({artifact_url})\n"
    body_path = revision / "comment.md"
    body_path.write_text(body, encoding="utf-8")
    repo = data["plan"]["target_repo"]
    number = state["pr_url"].rstrip("/").split("/")[-1]
    pages = json.loads(command("gh", "api", "--paginate", "--slurp",
                               f"repos/{repo}/issues/{number}/comments?per_page=100"))
    # Only update this authenticated user's prior result, not a copied marker.
    login = command("gh", "api", "user", "--jq", ".login")
    existing = next((c for page in pages for c in page
                     if c["body"].startswith(marker) and c["user"]["login"] == login), None)
    payload = revision / "comment-payload.json"
    write(payload, {"body": body})
    path = (f"repos/{repo}/issues/comments/{existing['id']}" if existing
            else f"repos/{repo}/issues/{number}/comments")
    response = json.loads(command("gh", "api", "--method", "PATCH" if existing else "POST",
                                  path, "--input", str(payload)))
    return response["html_url"]


def bundle(run: Path, output: Path) -> None:
    """Export evidence only, excluding Git worktrees and arbitrary log files."""
    load_run(run)
    paths = [run / "run.json", run / "source.md"]
    for arm in load_run(run)["plan"]["arms"]:
        directory = arm_dir(run, arm["id"])
        paths.extend(directory / name for name in ("pr.json", "candidate.md", "manifest.yaml", "pr-body.md"))
        for revision in sorted((directory / "revisions").glob("*")):
            if SHA.fullmatch(revision.name):
                paths.extend(revision / name for name in ("evaluation.json", "usage.json", "candidate.md", "comment.md"))
    # Refuse overwriting prior evidence exports.
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            if path.is_file():
                archive.write(path, path.relative_to(run))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("bundle")
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    for action in ("stage", "publish", "record", "comment"):
        p = sub.add_parser(action)
        p.add_argument("--run", type=Path, required=True)
        p.add_argument("--arm", required=True)
        if action in {"stage", "record"}:
            p.add_argument("--checkout", type=Path, required=True)
        if action == "stage":
            p.add_argument("--candidate", type=Path, required=True)
        if action == "publish":
            p.add_argument("--enable-loop", action="store_true")
        if action in {"record", "comment"}:
            p.add_argument("--sha", required=True)
        if action == "record":
            p.add_argument("--evaluation", type=Path, required=True)
            p.add_argument("--usage", type=Path, required=True)
        if action == "comment":
            p.add_argument("--artifact-url")
    args = parser.parse_args()
    values = vars(args)
    action = values.pop("action")
    if "run" in values:
        values["run"] = values["run"].resolve()
    if action == "prepare":
        prepare(values.pop("plan"), values.pop("source"), values.pop("output"))
    else:
        print(globals()[action](**values) or "Saved.")


if __name__ == "__main__":
    main()
