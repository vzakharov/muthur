#!/usr/bin/env python3
"""Drives the estimate notice as the harness does — a payload on stdin — over a
clone with a bare `origin`, whose `cost-ledger` carries the repository's own
roles. What it protects is the line such a role earns: a role merely listed
among the shared ones has its work booked under the nearest of them.

Run by path (`python3 .claude/costs/test_estimate_notice.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `test_stop_hook`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_stop_hook import Clone

SESSION = "sess"
WORK = "creative writing in a persona's voice, such as its reflections on songs"
LEDGER_REF = "refs/remotes/origin/cost-ledger"


class EstimateNoticeTest(unittest.TestCase):
    def setUp(self) -> None:
        base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, base)
        self.clone = Clone(base)
        self.costs = self.clone.root / ".claude" / "costs"

    def run_costs(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.costs / script), *args],
            env={**self.clone.env(), "CLAUDE_CODE_SESSION_ID": SESSION},
            capture_output=True,
            text=True,
            check=True,
        )

    def adds_artist(self) -> None:
        self.run_costs("estimate.py", "role", "set", "artist", "0.9", "senior", WORK)

    def notice(self) -> str:
        payload = {"session_id": SESSION, "cwd": str(self.clone.root), "hook_event_name": "UserPromptSubmit"}
        done = subprocess.run(
            [str(self.costs / "hooks" / "estimate-notice.sh")],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=self.clone.env(),
            check=True,
        )
        return json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]

    def test_a_repository_without_roles_of_its_own_gets_the_shared_ones_and_the_way_to_add_one(self) -> None:
        notice = self.notice()
        self.assertIn("roles: copywriter, editor", notice)
        self.assertNotIn("of its own:", notice)
        self.assertIn("`python3 .claude/costs/estimate.py role set <name> <multiplier> <grade>", notice)

    def test_a_fresh_container_fetches_the_ledger_and_names_its_role_with_grade_work_and_part(self) -> None:
        self.adds_artist()
        self.clone.git("update-ref", "-d", LEDGER_REF)
        notice = self.notice()
        self.assertIn(", artist; grades:", notice)
        self.assertIn(
            f"This repository adds a role of its own: `artist`, always `senior` — {WORK}. Book that work under it,"
            " `--part <hours> senior artist`",
            notice,
        )

    def test_a_ledger_that_cannot_be_fetched_is_said_rather_than_skipped(self) -> None:
        self.clone.git("remote", "set-url", "origin", str(self.clone.root.parent / "gone.git"))
        notice = self.notice()
        self.assertIn("roles: copywriter, editor", notice)
        self.assertIn("The `cost-ledger` branch could not be fetched", notice)

    def test_the_restated_estimate_keeps_the_role_in_view_and_says_a_misbooked_part_moves(self) -> None:
        self.adds_artist()
        self.run_costs("estimate.py", "set", "--part", "2", "senior", "copywriter", "the reflections need a voice")
        notice = self.notice()
        self.assertIn("This session's human-hour estimate: 2 h senior copywriter", notice)
        self.assertIn("`--part <hours> senior artist`", notice)
        self.assertIn("A part that booked such work under a shared role moves onto it.", notice)

    def test_a_role_the_shared_table_has_since_taken_up_gets_both_rates_named(self) -> None:
        self.adds_artist()
        shared = json.loads((self.costs / "rates.json").read_text(encoding="utf-8"))
        shared["roles"]["artist"] = 1.2
        (self.costs / "rates.json").write_text(json.dumps(shared), encoding="utf-8")
        notice = self.notice()
        self.assertIn(
            "Two rates for one role: This repository: `artist` is rated ×0.9 by its own table and ×1.2 by rates.json",
            notice,
        )
        self.assertIn("`estimate.py role drop artist` adopts the shared rate", notice)

    def test_a_table_that_does_not_parse_is_said_rather_than_skipped(self) -> None:
        parent = self.clone.seed_ledger()
        broken = self.clone.root.parent / "broken.json"
        broken.write_text(json.dumps({"roles": {}}))
        built = self.run_costs("ledger.py", "commit-row", parent, ".claude/costs/rates.repo.json", str(broken))
        self.clone.git("push", "-q", "origin", f"{built.stdout.strip()}:refs/heads/cost-ledger")
        notice = self.notice()
        self.assertIn("rate table does not parse", notice)
        self.assertIn("roles: not a non-empty object", notice)


if __name__ == "__main__":
    unittest.main()
