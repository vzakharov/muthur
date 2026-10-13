#!/usr/bin/env python3
"""Drives the estimate notice as the harness does — a payload on stdin — over a
copy of the ledger's code, so a `rates.repo.json` can be laid beside it. What it
protects is the line a repository's own role earns: a role merely listed among
the shared ones had its work booked under the nearest of them.

Run by path (`python3 .claude/costs/test_estimate_notice.py`), as `scripts/vet.sh`
does.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

COSTS = Path(__file__).resolve().parent
LIB = COSTS.parent / "hooks" / "lib.sh"
SESSION = "sess"
ARTIST = {
    "roles": {
        "artist": {
            "multiplier": 0.9,
            "grade": "senior",
            "work": "creative writing in a persona's voice, such as its reflections on songs",
        }
    }
}


class EstimateNoticeTest(unittest.TestCase):
    def setUp(self) -> None:
        base = tempfile.TemporaryDirectory()
        self.addCleanup(base.cleanup)
        self.root = Path(base.name)
        self.costs = self.root / ".claude" / "costs"
        shutil.copytree(
            COSTS,
            self.costs,
            ignore=shutil.ignore_patterns("sessions", "__pycache__", "test_*.py", "rates.repo.json"),
        )
        (self.root / ".claude" / "hooks").mkdir()
        shutil.copy(LIB, self.root / ".claude" / "hooks" / "lib.sh")

    def adds(self, text: str) -> None:
        (self.costs / "rates.repo.json").write_text(text, encoding="utf-8")

    def notice(self) -> str:
        payload = {"session_id": SESSION, "cwd": str(self.root), "hook_event_name": "UserPromptSubmit"}
        env = {key: value for key, value in os.environ.items() if key != "CLAUDE_PROJECT_DIR"}
        done = subprocess.run(
            [str(self.costs / "hooks" / "estimate-notice.sh")],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=True,
        )
        return json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]

    def estimate(self, *part: str) -> None:
        subprocess.run(
            [sys.executable, str(self.costs / "estimate.py"), "set", "--part", *part],
            env={**os.environ, "CLAUDE_CODE_SESSION_ID": SESSION},
            capture_output=True,
            check=True,
        )

    def test_a_repository_without_roles_of_its_own_gets_the_shared_ones_alone(self) -> None:
        notice = self.notice()
        self.assertIn("roles: copywriter, editor", notice)
        self.assertNotIn("of its own", notice)

    def test_a_repository_s_own_role_is_named_with_its_grade_its_work_and_the_part_that_books_it(self) -> None:
        self.adds(json.dumps(ARTIST))
        notice = self.notice()
        self.assertIn(", artist; grades:", notice)
        self.assertIn(
            "This repository adds a role of its own: `artist`, always `senior` — creative writing in a"
            " persona's voice, such as its reflections on songs. Book that work under it,"
            " `--part <hours> senior artist`",
            notice,
        )

    def test_the_restated_estimate_keeps_the_role_in_view_and_says_a_misbooked_part_moves(self) -> None:
        self.adds(json.dumps(ARTIST))
        self.estimate("2", "senior", "copywriter", "the reflections need a voice")
        notice = self.notice()
        self.assertIn("This session's human-hour estimate: 2 h senior copywriter", notice)
        self.assertIn("`--part <hours> senior artist`", notice)
        self.assertIn("A part that booked such work under a shared role moves onto it.", notice)

    def test_a_table_that_does_not_parse_is_said_rather_than_skipped(self) -> None:
        self.adds(json.dumps({"roles": {"editor": {"multiplier": 1, "grade": "senior", "work": "w"}}}))
        notice = self.notice()
        self.assertIn("rate table does not parse", notice)
        self.assertIn("rates.json rates this role already", notice)


if __name__ == "__main__":
    unittest.main()
