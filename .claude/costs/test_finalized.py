#!/usr/bin/env python3
"""What `lib/finalized.py` reads off the attestation query's answer; the hook
tests in `test_stage_cost_row.py` cover what the branch does with it."""

from __future__ import annotations

import unittest
from typing import Any, Dict, List, Mapping

from lib.finalized import attested
from lib.github import Client

SHA = "a" * 40
LATER = "b" * 40


def client(pulls: List[List[str]]) -> Client:
    def transport(_query: str, _variables: Mapping[str, Any]) -> Dict[str, Any]:
        nodes = [{"comments": {"nodes": [{"body": body} for body in comments]}} for comments in pulls]
        return {"data": {"repository": {"pullRequests": {"nodes": nodes}}}}

    return Client(transport=transport)


def read(*pulls: List[str]) -> object:
    return attested(client(list(pulls)), "owner", "repo", "feature")


class AttestedTest(unittest.TestCase):
    def test_the_marker_s_sha_is_the_attestation(self) -> None:
        self.assertEqual(read([f"Ready.\n<!-- finalize-attestation {SHA} -->"]), SHA)

    def test_the_latest_marker_wins(self) -> None:
        self.assertEqual(
            read([f"<!-- finalize-attestation {SHA} -->", "chat", f"<!-- finalize-attestation {LATER} -->"]),
            LATER,
        )

    def test_a_marker_with_no_sha_is_no_attestation(self) -> None:
        self.assertIsNone(read(["<!-- finalize-attestation -->"]))

    def test_a_revoked_marker_withdraws_the_one_before_it(self) -> None:
        self.assertIsNone(read([f"<!-- finalize-attestation {SHA} -->", "<!-- finalize-attestation revoked -->"]))

    def test_a_branch_with_no_pr_is_not_attested(self) -> None:
        self.assertIsNone(read())

    def test_a_pr_with_no_marker_is_not_attested(self) -> None:
        self.assertIsNone(read(["looks good"]))


if __name__ == "__main__":
    unittest.main()
