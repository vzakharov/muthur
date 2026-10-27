#!/usr/bin/env python3
"""The cross-repo ledger is read through two transports, so each case is a fake
GitHub answering in the shapes the real one returns: a repository listing
paged by cursor, a recursive REST tree listing, and aliased blobs carrying the
rows' text. What it protects is which repositories count, that every row
arrives at any depth or the run stops, and that a row is counted once however
many repositories carry it.

Run by path (`python3 .claude/costs/test_github.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `lib`.
"""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from typing import Any, Dict, List, Mapping, Optional

from lib.github import Client, GitHubError, ServerError, discover, remote_ledger
from lib.ledger_branch import BRANCH
from lib.rows import SessionCost, row_text
from lib.shape import ShapeError
from lib.tally import Tally

TRUNCATED = object()

Months = Dict[str, Dict[str, Any]]


def row(session_id: str, branch: str = "a-branch", last: str = "2026-03-04T06:06:07.000Z") -> str:
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
            last_response_at=last,
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
    """`ledgers` maps a repo to the months its default branch holds, each
    month's files, by their path under it, to their text, or to None for a repo
    with none there; `branches` does the same for its `cost-ledger` branch. The
    listing pages `page` repos at a time; a 5xx is thrown on the first
    `failures` GraphQL calls."""

    def __init__(
        self,
        ledgers: Mapping[str, Optional[Months]],
        watermarked: tuple = (),
        page: int = 2,
        failures: int = 0,
        errors: Optional[List[Dict[str, Any]]] = None,
        branches: Optional[Mapping[str, Months]] = None,
        added_roles: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.ledgers = dict(sorted({**{repo: None for repo in branches or {}}, **ledgers}.items()))
        self.sides = {"HEAD": self.ledgers, f"refs/heads/{BRANCH}": dict(branches or {})}
        self.watermarked = set(watermarked)
        # A repo to its `rates.repo.json` text, or TRUNCATED.
        self.added_roles = dict(added_roles or {})
        self.page = page
        self.failures = failures
        self.errors = errors
        self.queries: List[str] = []
        self.listings: List[str] = []
        self.truncated_listing = False
        # Each blob a listing has named, by its oid.
        self.blobs: Dict[str, Any] = {}

    def node(self, repo: str) -> Dict[str, Any]:
        def side(rev: str) -> Optional[Dict[str, Any]]:
            months = self.sides[rev].get(repo)
            if months is None:
                return None
            return {
                "oid": f"{repo}@{rev}",
                "entries": [{"name": m, "type": "tree"} for m in months] + [{"name": ".gitkeep", "type": "blob"}],
            }

        return {
            "nameWithOwner": repo,
            "tree": side("HEAD"),
            "ledger": side(f"refs/heads/{BRANCH}"),
            "watermark": {"__typename": "Blob"} if repo in self.watermarked else None,
            "addedRoles": None if repo not in self.added_roles else self.blob(self.added_roles[repo]),
        }

    @staticmethod
    def blob(text: Any) -> Dict[str, Any]:
        if text is TRUNCATED:
            return {"isTruncated": True, "isBinary": False, "text": "{"}
        return {"isTruncated": False, "isBinary": False, "text": text}

    def rest(self, path: str) -> Dict[str, Any]:
        """`repos/<repo>/git/trees/<oid>?recursive=1`, the oid naming its side."""
        self.listings.append(path)
        found = re.fullmatch(r"repos/[^/]+/[^/]+/git/trees/([^@]+)@(.+)\?recursive=1", path)
        assert found, path
        tree: List[Dict[str, Any]] = [{"path": ".gitkeep", "type": "blob", "sha": "keep"}]
        for month, files in (self.sides[found[2]].get(found[1]) or {}).items():
            tree.append({"path": month, "type": "tree", "sha": f"tree-{month}"})
            for name, text in files.items():
                oid = "truncated" if text is TRUNCATED else hashlib.sha1(text.encode()).hexdigest()
                self.blobs[oid] = text
                tree.append({"path": f"{month}/{name}", "type": "blob", "sha": oid})
        return {"tree": tree, "truncated": self.truncated_listing}

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
                            "nodes": [self.node_answer(query, self.node(repo)) for repo in repos],
                        }
                    }
                }
            }
        data: Dict[str, Any] = {}
        alias = r'(\w+): repository\(owner: "([^"]+)", name: "([^"]+)"\) \{ '
        for found in re.finditer(alias + r'object\(oid: "([^"]+)"\)', query):
            data[found[1]] = {"object": self.blob(self.blobs[found[4]])}
        for found in re.finditer(alias + r"\s*nameWithOwner", query):
            data[found[1]] = self.node_answer(query, self.node(f"{found[2]}/{found[3]}"))
        return {"data": data}

    def node_answer(self, query: str, node: Dict[str, Any]) -> Dict[str, Any]:
        """A repository's table is on the ledger, so a query reading it anywhere
        else finds nothing."""
        ledger_side = f'addedRoles: object(expression: "refs/heads/{BRANCH}:.claude/costs/rates.repo.json")' in query
        return node if ledger_side else {**node, "addedRoles": None}


def no_sleep(_: float) -> None:
    pass


def client(github: FakeGitHub, said: Optional[List[str]] = None) -> Client:
    return Client(github, no_sleep, (said if said is not None else []).append, github.rest)


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
        with self.assertRaisesRegex(ShapeError, "a/ledger:.*s.json: GitHub did not return the file whole"):
            remote_ledger(client(github))

    def test_a_truncated_listing_raises(self) -> None:
        github = FakeGitHub({"a/ledger": {"2026-03": {"s.json": row("s")}}})
        github.truncated_listing = True
        with self.assertRaisesRegex(ShapeError, "a/ledger:HEAD:.claude/costs/sessions: GitHub truncated"):
            remote_ledger(client(github))

    def test_a_truncated_rates_repo_json_raises(self) -> None:
        github = FakeGitHub({"a/ledger": {"2026-03": {}}}, added_roles={"a/ledger": TRUNCATED})
        with self.assertRaisesRegex(
            ShapeError, f"a/ledger:refs/heads/{BRANCH}:.claude/costs/rates.repo.json: GitHub did not return"
        ):
            discover(Client(github, no_sleep))


class WhatIsRead(unittest.TestCase):
    def test_rows_at_any_depth_are_read_in_either_layout(self) -> None:
        github = FakeGitHub(
            {"a/ledger": {"2026-03": {"s.json": row("s"), "claude/b-x/2/t.json": row("t"), "a-branch/1/notes.txt": "x"}}}
        )
        ledger = remote_ledger(client(github))
        self.assertEqual(sorted(r.session_id for r in ledger.rows), ["s", "t"])
        self.assertEqual(github.listings, ["repos/a/ledger/git/trees/a/ledger@HEAD?recursive=1"])

    def test_rows_are_read_in_batches_and_each_step_is_said(self) -> None:
        months = {f"2026-{n:02d}": {f"b/{i}/s{n}-{i}.json": row(f"s{n}-{i}") for i in range(1, 11)} for n in range(1, 7)}
        github = FakeGitHub({"a/ledger": months})
        said: List[str] = []
        ledger = remote_ledger(client(github, said))
        self.assertEqual(len(ledger.rows), 60)
        self.assertEqual(len(github.queries), 1 + 2)
        self.assertEqual(
            said,
            [
                "listing your repositories: 0 so far",
                "1 ledger among 1 repository",
                "listing a/ledger's rows on HEAD",
                "reading 1 ledger: 0 of 60 rows",
                "reading 1 ledger: 50 of 60 rows",
            ],
        )

    def test_a_session_in_two_repos_is_counted_once_and_named(self) -> None:
        github = FakeGitHub(
            {
                "a/source": {"2026-03": {"s.json": row("s")}},
                "b/fork": {"2026-03": {"s.json": row("s"), "t.json": row("t")}},
            }
        )
        ledger = remote_ledger(client(github))
        self.assertEqual(sorted(r.session_id for r in ledger.rows), ["s", "t"])
        self.assertEqual(ledger.repo_of, {"s": "a/source", "t": "b/fork"})
        warnings = {repo.name: repo.warnings for repo in ledger.repos}
        self.assertEqual(warnings["a/source"], [])
        self.assertEqual(warnings["b/fork"], ["session s is also in a/source, counted there"])

    def test_a_row_in_another_shape_is_reshaped_and_reported(self) -> None:
        text = json.dumps({**json.loads(row("s")), "retiredKey": 1})
        ledger = remote_ledger(client(FakeGitHub({"a/ledger": {"2026-03": {"s.json": text}}})))
        self.assertEqual([r.session_id for r in ledger.rows], ["s"])
        self.assertEqual(ledger.repos[0].warnings, ["1 row in an older or newer shape than this ledger's"])

    def test_each_ledger_repo_s_own_roles_are_read_beside_its_rows(self) -> None:
        github = FakeGitHub(
            {"a/ledger": {"2026-03": {"s.json": row("s")}}, "b/ledger": {"2026-03": {}}, "c/plain": None},
            added_roles={"a/ledger": '{"roles": {}}', "c/plain": '{"roles": {}}'},
        )
        ledger = remote_ledger(client(github))
        self.assertEqual(ledger.added_roles, {"a/ledger": '{"roles": {}}'})


class TheTwoSides(unittest.TestCase):
    def test_a_repo_whose_rows_are_on_the_ledger_branch_alone_counts(self) -> None:
        github = FakeGitHub({}, branches={"a/moved": {"2026-03": {"s.json": row("s")}}})
        ledger = remote_ledger(client(github))
        self.assertEqual([r.session_id for r in ledger.rows], ["s"])
        self.assertEqual(discover(Client(github, no_sleep), ["a/moved"]).ledgers[0].months, ["2026-03"])

    def test_a_row_on_both_sides_is_one_session_and_the_later_copy_wins(self) -> None:
        later = "2026-03-04T09:00:00.000Z"
        github = FakeGitHub(
            {"a/ledger": {"2026-03": {"s.json": row("s"), "t.json": row("t")}}},
            branches={"a/ledger": {"2026-03": {"s.json": row("s", last=later), "a-branch/1/t.json": row("t")}}},
        )
        ledger = remote_ledger(client(github))
        self.assertEqual(sorted(r.session_id for r in ledger.rows), ["s", "t"])
        self.assertEqual(next(r for r in ledger.rows if r.session_id == "s").last_response_at, later)
        # `t` is the same blob on both sides, read once.
        self.assertEqual(sum(query.count("object(oid:") for query in github.queries), 3)
        self.assertEqual(ledger.repos[0].warnings, [])


if __name__ == "__main__":
    unittest.main()
