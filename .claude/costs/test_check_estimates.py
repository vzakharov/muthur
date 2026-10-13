#!/usr/bin/env python3
"""The vet gate on human-hour estimates, run over a clone with a bare `origin`:
which sessions count as the branch's, how the running session's pending
estimate stands in for its row's, and the command a failure hands over.

Run by path (`python3 .claude/costs/test_check_estimates.py`), as
`scripts/vet.sh` does, which puts this directory on `sys.path` for the other
tests' fixtures.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Optional

from lib.rows import json_text, row_text
from test_estimate import ROW, estimate_of
from test_stop_hook import Clone

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

    def test_with_no_base_checks_the_running_session_alone_and_says_so(self) -> None:
        self.commit_row("added")
        self.clone.git("update-ref", "-d", "refs/remotes/origin/main")
        done = self.check()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("no base to read the branch against", done.stdout)


if __name__ == "__main__":
    unittest.main()
