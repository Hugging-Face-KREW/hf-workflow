from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Callable

from hf_agent.github_api import Requester, request_json


THREADS_QUERY = """
query ReviewThreads($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes { id isResolved path line }
      }
    }
  }
}
"""

REPLY_MUTATION = """
mutation Reply($threadId: ID!, $body: String!) {
  addPullRequestReviewThreadReply(
    input: {pullRequestReviewThreadId: $threadId, body: $body}
  ) { comment { id } }
}
"""

RESOLVE_MUTATION = """
mutation Resolve($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread { id isResolved }
  }
}
"""


def _graphql(
    query: str,
    variables: dict[str, Any],
    *,
    token: str,
    requester: Requester,
) -> dict[str, Any]:
    result = requester(
        "POST",
        "/graphql",
        token,
        {"query": query, "variables": variables},
    )
    if result.get("errors"):
        raise RuntimeError(f"GitHub GraphQL failed: {result['errors']}")
    return result


def list_unresolved_threads(
    *,
    repository: str,
    pr_number: int,
    token: str,
    requester: Requester = request_json,
) -> list[dict[str, Any]]:
    owner, name = repository.split("/", 1)
    result = _graphql(
        THREADS_QUERY,
        {"owner": owner, "name": name, "number": pr_number},
        token=token,
        requester=requester,
    )
    nodes = result["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    return [thread for thread in nodes if not thread["isResolved"]]


def reply_and_resolve(
    *,
    thread_id: str,
    body: str,
    token: str,
    requester: Requester = request_json,
) -> None:
    _graphql(
        REPLY_MUTATION,
        {"threadId": thread_id, "body": body},
        token=token,
        requester=requester,
    )
    _graphql(
        RESOLVE_MUTATION,
        {"threadId": thread_id},
        token=token,
        requester=requester,
    )


ThreadLoader = Callable[..., list[dict[str, Any]]]


def thread_gate(
    *,
    repository: str,
    pr_number: int,
    token: str,
    loader: ThreadLoader = list_unresolved_threads,
) -> int:
    return len(loader(repository=repository, pr_number=pr_number, token=token))


def main() -> int:
    parser = argparse.ArgumentParser(description="Count unresolved pull request threads")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr-number", required=True, type=int)
    parser.add_argument("--result-json", required=True, type=Path)
    args = parser.parse_args()
    count = thread_gate(
        repository=args.repository,
        pr_number=args.pr_number,
        token=os.environ["GITHUB_TOKEN"],
    )
    args.result_json.write_text(json.dumps({"unresolved_threads": count}) + "\n")
    print(f"Unresolved review threads: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
