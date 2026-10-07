"""GitHub REST and GraphQL access for `scripts/export-github-item.py`.

Every request goes through `lib.github.fetch`, so both the proxy and the direct
route are tried before anything is reported as failed.
"""

from __future__ import annotations

import json
import re
import urllib.request
from typing import Any

from lib.github import GITHUB_API_VERSION, fetch

# `lib.github` deliberately leaves this per-script: the two callers are told
# apart server-side by their user agents.
USER_AGENT = "export-github-item.py"


def request(
    url: str, token: str, accept: str, data: bytes | None = None
) -> tuple[bytes, dict[str, str]]:
    """Any `data` body is labeled JSON — the only kind this script posts."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "User-Agent": USER_AGENT,
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    return fetch(lambda: urllib.request.Request(url, data=data, headers=headers))


def api_json(path_or_url: str, token: str) -> tuple[Any, dict[str, str]]:
    url = (
        path_or_url
        if path_or_url.startswith("http")
        else f"https://api.github.com/{path_or_url.lstrip('/')}"
    )
    body, headers = request(url, token, "application/vnd.github+json")
    return json.loads(body), headers


def api_get(path: str, token: str) -> Any:
    data, _ = api_json(path, token)
    return data


def has_next_page(link_header: str | None) -> bool:
    if not link_header:
        return False
    return any(
        re.match(r'\s*<[^>]+>;\s*rel="next"', part) for part in link_header.split(",")
    )


def api_paginated(path: str, token: str) -> list[Any]:
    """Paginate with an explicit `page=` rather than the Link header's URL:
    GitHub phrases those as `repositories/{id}/…`, which the agent proxy in
    Claude Code web sessions rejects with 403.
    """
    items: list[Any] = []
    page = 1
    while True:
        sep = "&" if "?" in path else "?"
        url = f"{path}{sep}per_page=100&page={page}"
        data, headers = api_json(url, token)
        if not isinstance(data, list):
            raise RuntimeError(
                f"Expected JSON array from {url}, got {type(data).__name__}"
            )
        items.extend(data)
        if not has_next_page(headers.get("link")):
            return items
        page += 1


THREAD_RESOLUTION_QUERY = """
query($owner: String!, $repo: String!, $pr: Int!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          isResolved
          comments(first: 100) { nodes { databaseId } }
        }
      }
    }
  }
}
"""


class GraphqlError(Exception):
    """GitHub answers a bad GraphQL query with HTTP 200 and an `errors` array,
    so `fetch`'s ladder reads it as a success and the payload must be checked.
    """


def api_graphql(query: str, variables: dict[str, Any], token: str) -> Any:
    """Goes through `lib.github.fetch` rather than `gh api graphql`: a
    remote-session proxy can refuse `gh`'s GraphQL calls, depending on how the
    environment is set up, while the ladder's direct rung reaches
    `api.github.com` either way.
    """
    body, _ = request(
        "https://api.github.com/graphql",
        token,
        "application/vnd.github+json",
        data=json.dumps({"query": query, "variables": variables}).encode(),
    )
    parsed = json.loads(body)
    if parsed.get("errors"):
        raise GraphqlError(json.dumps(parsed["errors"]))
    return parsed["data"]


def fetch_thread_resolution(repo: str, number: int, token: str) -> dict[int, bool]:
    """Every comment id in a thread maps to that thread's `isResolved`.

    Resolution is the one fact no REST comment payload carries, hence GraphQL.
    Keying on every id rather than the root is what makes the two views line up:
    the export rebuilds threads from REST `in_reply_to_id` chains, which root on
    a different comment when the parent falls off the page.
    """
    owner, name = repo.split("/", 1)
    resolved_by_comment_id: dict[int, bool] = {}
    cursor: str | None = None
    while True:
        data = api_graphql(
            THREAD_RESOLUTION_QUERY,
            {"owner": owner, "repo": name, "pr": number, "cursor": cursor},
            token,
        )
        threads = data["repository"]["pullRequest"]["reviewThreads"]
        for thread in threads["nodes"]:
            for comment in thread["comments"]["nodes"]:
                comment_id = comment.get("databaseId")
                if comment_id is not None:
                    resolved_by_comment_id[comment_id] = thread["isResolved"]
        if not threads["pageInfo"]["hasNextPage"]:
            return resolved_by_comment_id
        cursor = threads["pageInfo"]["endCursor"]
