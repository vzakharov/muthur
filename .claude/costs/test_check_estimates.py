#!/usr/bin/env python3
"""The vet gate on human-hour estimates, run over a clone with a bare `origin`:
which sessions count as the branch's, how the running session's pending
estimate stands in for its row's, and the command a failure hands over.

Run by path (`python3 .claude/costs/test_check_estimates.py`), as
`scripts/vet.sh` does, which puts this directory on `sys.path` for the other
tests' fixtures.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Optional

from lib.estimate_model import Part
from lib.rows import json_text, row_text
from test_estimate import ROW, estimate_of
from hook_clone import Clone

CHECK = ".claude/costs/check_estimates.py"
ESTIMATED = estimate_of("2026-03-04T07:00:00.000Z")


class TheGate(unittest.TestCase):
    def setUp(self) -> None:
        base = tempfile.TemporaryDirectory()
        self.addCleanup(base.cleanup)
        self.clone = Clone(Path(base.name))

    def write_row(self, session_id: str, **fields: object) -> Path:
        path = self.clone.root / ".claude" / "costs" / "sessions" / "2026-03" / f"{session_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(row_text(replace(ROW, session_id=session_id, **fields)), encoding="utf-8")
        return path

    def commit_row(self, session_id: str, **fields: object) -> None:
        self.write_row(session_id, **fields)
        self.clone.git("add", "-A")
        self.clone.git("commit", "-q", "-m", f"row {session_id}")

    def land_on_trunk(self) -> None:
        self.clone.git("push", "-q", "origin", "HEAD:main")
        self.clone.git("fetch", "-q", "origin")

    def check(self, running: Optional[str] = None) -> subprocess.CompletedProcess:
        env = self.clone.env()
        if running is not None:
            env["CLAUDE_CODE_SESSION_ID"] = running
        return subprocess.run(
            ["python3", str(self.clone.root / CHECK)], capture_output=True, text=True, env=env
        )

    def run_costs(self, script: str, *args: str) -> None:
        subprocess.run(
            ["python3", str(self.clone.root / ".claude" / "costs" / script), *args],
            env=self.clone.env(),
            capture_output=True,
            check=True,
        )

    def test_passes_a_branch_with_no_sessions(self) -> None:
        done = self.check()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("ok — 0 session(s)", done.stdout)

    def test_fails_a_row_the_branch_adds_without_an_estimate_naming_the_command(self) -> None:
        self.commit_row("added")
        done = self.check()
        self.assertEqual(done.returncode, 1)
        self.assertIn("added", done.stderr)
        self.assertIn('estimate.py set --part <hours> <grade> <role> "<why>" [--part ...] --session added', done.stderr)
        self.assertIn("origin/main", done.stderr)

    def test_passes_a_row_the_branch_adds_with_an_estimate(self) -> None:
        self.commit_row("added", estimate=ESTIMATED)
        self.assertEqual(self.check().returncode, 0)

    def test_leaves_a_row_the_trunk_already_carries_alone(self) -> None:
        self.commit_row("old")
        self.land_on_trunk()
        self.assertEqual(self.check().returncode, 0)

    def test_leaves_a_trunk_row_the_branch_only_reshapes_but_not_one_that_spent_again(self) -> None:
        self.commit_row("old")
        self.land_on_trunk()
        self.commit_row("old", warnings=["reshaped"])
        self.assertEqual(self.check().returncode, 0)
        self.commit_row("old", last_response_at="2026-03-05T00:00:00.000Z")
        done = self.check()
        self.assertEqual(done.returncode, 1)
        self.assertIn("--session old", done.stderr)

    def test_fails_the_running_session_with_no_row_and_no_pending_estimate(self) -> None:
        done = self.check(running="live")
        self.assertEqual(done.returncode, 1)
        self.assertIn("live ('this session')", done.stderr)
        self.assertNotIn("--session", done.stderr)

    def test_passes_the_running_session_on_its_pending_estimate_whatever_its_row_says(self) -> None:
        self.commit_row("live")
        pending = self.clone.root / "tmp" / "estimates" / "live.json"
        pending.parent.mkdir(parents=True)
        pending.write_text(json_text(ESTIMATED), encoding="utf-8")
        done = self.check(running="live")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("ok — 1 session(s)", done.stdout)

    def test_fails_a_tree_copy_of_the_table_naming_the_way_onto_the_ledger(self) -> None:
        (self.clone.root / ".claude" / "costs" / "rates.repo.json").write_text('{"roles": {}}', encoding="utf-8")
        done = self.check()
        self.assertEqual(done.returncode, 1)
        self.assertIn("rates.repo.json is in the tree", done.stderr)
        self.assertIn("ledger.py backfill`, then `git rm .claude/costs/rates.repo.json`", done.stderr)

    def test_warns_of_a_role_both_tables_rate_without_failing(self) -> None:
        self.run_costs("estimate.py", "role", "set", "artist", "0.9", "senior", "songs")
        shared_path = self.clone.root / ".claude" / "costs" / "rates.json"
        shared = json.loads(shared_path.read_text(encoding="utf-8"))
        shared["roles"]["artist"] = 1.2
        shared_path.write_text(json.dumps(shared), encoding="utf-8")
        done = self.check()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("this repository: `artist` is rated ×0.9 by its own table and ×1.2 by rates.json", done.stderr)

    def test_reads_the_table_off_the_ledger_tip_another_clone_pushed(self) -> None:
        self.run_costs("estimate.py", "role", "set", "artist", "0.9", "senior", "songs")
        self.clone.git("update-ref", "-d", "refs/remotes/origin/cost-ledger")
        self.commit_row("added", estimate=estimate_of("a", Part(1, "senior", "artist")))
        done = self.check()
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_with_no_base_checks_the_running_session_alone_and_says_so(self) -> None:
        self.commit_row("added")
        self.clone.git("update-ref", "-d", "refs/remotes/origin/main")
        done = self.check()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("no base to read the branch against", done.stdout)


if __name__ == "__main__":
    unittest.main()
