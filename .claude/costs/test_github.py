#!/usr/bin/env python3
"""The cross-repo ledger is read through one transport, so each case is a fake
GitHub answering in the shapes the real one returns: a repository listing
paged by cursor, and aliased month trees whose blobs carry the rows' text.
What it protects is which repositories count, that every row arrives or the
run stops, and that a row is counted once however many repositories carry it.

Run by path (`python3 .claude/costs/test_github.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `lib`.
"""

from __future__ import annotations

import json
import re
import unittest
from typing import Any, Dict, List, Mapping, Optional

from lib.github import Client, GitHubError, ServerError, discover, remote_ledger
from lib.rows import SessionCost, row_text
from lib.shape import ShapeError
from lib.tally import Tally

TRUNCATED = object()

Months = Dict[str, Dict[str, Any]]


def row(session_id: str, branch: str = "a-branch") -> str:
    return row_text(
        SessionCost(
            session_id=session_id,
            branch=branch,
            cwd=None,
            opening_prompt=None,
            prs=[],
            url=None,
            operator=None,
            first_response_at="2026-03-04T05:06:07.000Z",
            last_response_at="2026-03-04T06:06:07.000Z",
            prices_as_of="2026-01-01",
            claude_code_total_usd=None,
            total=Tally(responses=1, cost_usd=1),
            own_turns=Tally(responses=1, cost_usd=1),
            subagents=Tally(),
            by_rate={},
            warnings=[],
        )
    )


class FakeGitHub:
    """`ledgers` maps a repo to its months, each month's files to their text,
    or to None for a repo with no ledger. The listing pages `page` repos at a
    time; a 5xx is thrown on the first `failures` calls."""

    def __init__(
        self,
        ledgers: Mapping[str, Optional[Months]],
        watermarked: tuple = (),
        page: int = 2,
        failures: int = 0,
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.ledgers = dict(sorted(ledgers.items()))
        self.watermarked = set(watermarked)
        self.page = page
        self.failures = failures
        self.errors = errors
        self.queries: List[str] = []

    def node(self, repo: str) -> Dict[str, Any]:
        months = self.ledgers[repo]
        return {
            "nameWithOwner": repo,
            "ledger": None
            if months is None
            else {"entries": [{"name": m, "type": "tree"} for m in months] + [{"name": ".gitkeep", "type": "blob"}]},
            "watermark": {"__typename": "Blob"} if repo in self.watermarked else None,
        }

    def tree(self, repo: str, month: str) -> Dict[str, Any]:
        files = (self.ledgers[repo] or {})[month]
        return {
            "object": {
                "entries": [
                    {
                        "name": name,
                        "type": "blob",
                        "object": {"isTruncated": True, "isBinary": False, "text": "{"}
                        if text is TRUNCATED
                        else {"isTruncated": False, "isBinary": False, "text": text},
                    }
                    for name, text in files.items()
                ]
            }
        }

    def __call__(self, query: str, variables: Mapping[str, Any]) -> Dict[str, Any]:
        self.queries.append(query)
        if self.failures:
            self.failures -= 1
            raise ServerError("HTTP 502: Bad Gateway")
        if self.errors is not None:
            return {"data": None, "errors": self.errors}
        if "viewer" in query:
            start = int(variables.get("cursor") or 0)
            repos = list(self.ledgers)[start : start + self.page]
            more = start + self.page < len(self.ledgers)
            return {
                "data": {
                    "viewer": {
                        "repositories": {
                            "pageInfo": {"hasNextPage": more, "endCursor": str(start + self.page) if more else None},
                            "nodes": [self.node(repo) for repo in repos],
                        }
                    }
                }
            }
        data: Dict[str, Any] = {}
        alias = r'(\w+): repository\(owner: "([^"]+)", name: "([^"]+)"\) \{ '
        for found in re.finditer(alias + r'object\(expression: "HEAD:[^"]*/(\d{4}-\d{2})"\)', query):
            data[found[1]] = self.tree(f"{found[2]}/{found[3]}", found[4])
        for found in re.finditer(alias + r"\s*nameWithOwner", query):
            data[found[1]] = self.node(f"{found[2]}/{found[3]}")
        return {"data": data}


def no_sleep(_: float) -> None:
    pass


class WhichRepositoriesCount(unittest.TestCase):
    def test_keeps_ledger_repos_names_watermark_only_ones_and_follows_pages(self) -> None:
        github = FakeGitHub(
            {
                "a/ledger": {"2026-03": {}},
                "b/adopter": None,
                "c/stranger": None,
                "d/ledger": {"2026-04": {}, "2026-03": {}},
                "e/other": None,
            },
            watermarked=("a/ledger", "b/adopter"),
        )
        found = discover(Client(github, no_sleep))
        self.assertEqual([(c.repo, c.months) for c in found.ledgers], [("a/ledger", ["2026-03"]), ("d/ledger", ["2026-03", "2026-04"])])
        self.assertEqual(found.without_ledger, ["b/adopter"])
        self.assertEqual(found.seen, 5)
        self.assertEqual(sum("viewer" in query for query in github.queries), 3)

    def test_named_repos_are_queried_directly_and_one_without_a_ledger_raises(self) -> None:
        github = FakeGitHub({"a/ledger": {"2026-03": {}}, "b/plain": None})
        found = discover(Client(github, no_sleep), ["a/ledger"])
        self.assertEqual([c.repo for c in found.ledgers], ["a/ledger"])
        self.assertFalse(any("viewer" in query for query in github.queries))
        with self.assertRaisesRegex(GitHubError, "b/plain: no .claude/costs/sessions"):
            discover(Client(github, no_sleep), ["a/ledger", "b/plain"])


class FailuresAreLoud(unittest.TestCase):
    def test_a_5xx_is_retried_and_said_so(self) -> None:
        slept: List[float] = []
        said: List[str] = []
        github = FakeGitHub({"a/ledger": {"2026-03": {}}}, failures=2)
        self.assertEqual(len(discover(Client(github, slept.append, said.append)).ledgers), 1)
        self.assertEqual(slept, [2, 4])
        self.assertIn("HTTP 502: Bad Gateway; retrying in 4s", said)

    def test_a_5xx_that_persists_raises(self) -> None:
        with self.assertRaises(ServerError):
            discover(Client(FakeGitHub({"a/ledger": None}, failures=4), no_sleep))

    def test_a_graphql_error_raises_with_its_message(self) -> None:
        github = FakeGitHub({}, errors=[{"type": "NOT_FOUND", "message": "Could not resolve"}])
        with self.assertRaisesRegex(GitHubError, "Could not resolve"):
            discover(Client(github, no_sleep))

    def test_a_truncated_row_raises(self) -> None:
        github = FakeGitHub({"a/ledger": {"2026-03": {"s.json": TRUNCATED}}})
        with self.assertRaisesRegex(ShapeError, "a/ledger:.*s.json: GitHub did not return the row whole"):
            remote_ledger(Client(github, no_sleep))


class WhatIsRead(unittest.TestCase):
    def test_a_month_filter_requests_only_that_months_trees(self) -> None:
        github = FakeGitHub(
            {"a/ledger": {"2026-03": {"s.json": row("s")}, "2026-04": {"t.json": row("t")}}}
        )
        ledger = remote_ledger(Client(github, no_sleep), months={"2026-04"})
        self.assertEqual([r.session_id for r in ledger.rows], ["t"])
        self.assertEqual(ledger.repos[0].months, ["2026-04"])
        self.assertFalse(any("2026-03" in query for query in github.queries[1:]))

    def test_month_trees_are_fetched_in_batches_and_each_step_is_said(self) -> None:
        months = {f"2026-{n:02d}": {f"s{n}.json": row(f"s{n}")} for n in range(1, 8)}
        github = FakeGitHub({"a/ledger": months})
        said: List[str] = []
        ledger = remote_ledger(Client(github, no_sleep, said.append))
        self.assertEqual(len(ledger.rows), 7)
        self.assertEqual(len(github.queries), 1 + 2)
        self.assertEqual(
            said,
            [
                "listing your repositories: 0 so far",
                "1 ledger among 1 repository",
                "reading 1 ledger: 0 of 7 months, 0 rows so far",
                "reading 1 ledger: 5 of 7 months, 5 rows so far",
            ],
        )

    def test_a_session_in_two_repos_is_counted_once_and_named(self) -> None:
        github = FakeGitHub(
            {
                "a/source": {"2026-03": {"s.json": row("s")}},
                "b/fork": {"2026-03": {"s.json": row("s"), "t.json": row("t")}},
            }
        )
        ledger = remote_ledger(Client(github, no_sleep))
        self.assertEqual(sorted(r.session_id for r in ledger.rows), ["s", "t"])
        self.assertEqual(ledger.repo_of, {"s": "a/source", "t": "b/fork"})
        warnings = {repo.name: repo.warnings for repo in ledger.repos}
        self.assertEqual(warnings["a/source"], [])
        self.assertEqual(warnings["b/fork"], ["session s is also in a/source, counted there"])

    def test_a_row_in_another_shape_is_reshaped_and_reported(self) -> None:
        text = json.dumps({**json.loads(row("s")), "retiredKey": 1})
        ledger = remote_ledger(Client(FakeGitHub({"a/ledger": {"2026-03": {"s.json": text}}}), no_sleep))
        self.assertEqual([r.session_id for r in ledger.rows], ["s"])
        self.assertEqual(ledger.repos[0].warnings, ["1 row in an older or newer shape than this ledger's"])

    def test_a_repo_with_no_month_under_the_filter_is_left_out(self) -> None:
        github = FakeGitHub({"a/ledger": {"2026-03": {"s.json": row("s")}}, "b/ledger": {"2026-04": {}}})
        ledger = remote_ledger(Client(github, no_sleep), months={"2026-03"})
        self.assertEqual([repo.name for repo in ledger.repos], ["a/ledger"])


if __name__ == "__main__":
    unittest.main()
