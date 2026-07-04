from __future__ import annotations

from typing import Any

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
