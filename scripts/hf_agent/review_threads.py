from __future__ import annotations

import argparse
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from hf_agent.github_api import Requester, request_json


THREADS_QUERY = """
query ReviewThreads($owner: String!, $name: String!, $number: Int!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          path
          line
          comments(first: 100) {
            pageInfo { hasNextPage endCursor }
            nodes { databaseId }
          }
        }
      }
    }
  }
}
"""

THREAD_COMMENTS_QUERY = """
query ReviewThreadComments($threadId: ID!, $cursor: String) {
  node(id: $threadId) {
    ... on PullRequestReviewThread {
      comments(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { databaseId }
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
    threads: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        result = _graphql(
            THREADS_QUERY,
            {"owner": owner, "name": name, "number": pr_number, "cursor": cursor},
            token=token,
            requester=requester,
        )
        connection = result["data"]["repository"]["pullRequest"]["reviewThreads"]
        threads.extend(connection["nodes"])
        page_info = connection.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = str(page_info.get("endCursor") or "")
        if not cursor:
            raise RuntimeError("GitHub omitted the next review-thread cursor")

    unresolved = [thread for thread in threads if not thread["isResolved"]]
    for thread in unresolved:
        comments = thread.get("comments") or {}
        page_info = comments.get("pageInfo") or {}
        cursor = str(page_info.get("endCursor") or "")
        while page_info.get("hasNextPage"):
            if not cursor:
                raise RuntimeError("GitHub omitted the next review-comment cursor")
            result = _graphql(
                THREAD_COMMENTS_QUERY,
                {"threadId": thread["id"], "cursor": cursor},
                token=token,
                requester=requester,
            )
            next_comments = result["data"]["node"]["comments"]
            comments.setdefault("nodes", []).extend(next_comments["nodes"])
            page_info = next_comments.get("pageInfo") or {}
            cursor = str(page_info.get("endCursor") or "")
    return unresolved


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


def find_thread_id(threads: list[dict[str, Any]], *, comment_id: int) -> str:
    for thread in threads:
        comments = thread.get("comments", {}).get("nodes", [])
        if any(comment.get("databaseId") == comment_id for comment in comments):
            return str(thread["id"])
    raise ValueError(f"Review thread was not found for comment {comment_id}")


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
    parser.add_argument("--result-json", type=Path)
    parser.add_argument("--resolve-comment-id", type=int)
    parser.add_argument("--body")
    args = parser.parse_args()
    token = os.environ["GITHUB_TOKEN"]
    if args.resolve_comment_id is not None:
        if not args.body:
            parser.error("--body is required with --resolve-comment-id")
        threads = list_unresolved_threads(
            repository=args.repository,
            pr_number=args.pr_number,
            token=token,
        )
        reply_and_resolve(
            thread_id=find_thread_id(threads, comment_id=args.resolve_comment_id),
            body=args.body,
            token=token,
        )
        print(f"Resolved review comment: {args.resolve_comment_id}")
        return 0
    if args.result_json is None:
        parser.error("--result-json is required when checking threads")
    count = thread_gate(
        repository=args.repository,
        pr_number=args.pr_number,
        token=token,
    )
    args.result_json.write_text(json.dumps({"unresolved_threads": count}) + "\n")
    print(f"Unresolved review threads: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
