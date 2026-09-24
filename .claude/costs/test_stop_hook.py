#!/usr/bin/env python3
"""Drives the `Stop` hook as the harness does — a payload on stdin, over a clone
with a bare `origin` — and reads the repository it leaves behind. What it
protects is the tree the harness's own `Stop` check reads: the row committed and
pushed without leaving anything dirty or ahead, the agent's own work left where
it was, and a line to the agent only where the check had something to count.

Run by path (`python3 .claude/costs/test_stop_hook.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `test_pricing`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import List

from test_pricing import PRICE_TABLE, response

COSTS = Path(__file__).resolve().parent
LIB = COSTS.parent / "hooks" / "lib.sh"
HOOK = ".claude/costs/hooks/stop-session-cost.sh"
SESSION = "sess"

class Clone:
    """A branch pushed to a bare `origin`, carrying the ledger's code and nothing
    of its rows, with a `HOME` of its own so no global git config or launcher
    settings reach it."""

    def __init__(self, base: Path) -> None:
        self.origin = base / "origin.git"
        self.root = base / "repo"
        self.home = base / "home"
        self.transcript = base / "transcript.jsonl"
        self.home.mkdir()
        self.responses = 0

        subprocess.run(["git", "init", "-q", "--bare", str(self.origin)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.root)], check=True)
        for key, value in {
            "user.name": "Test",
            "user.email": "test@example.com",
            "commit.gpgsign": "false",
        }.items():
            self.git("config", key, value)
        self.git("remote", "add", "origin", str(self.origin))

        costs = self.root / ".claude" / "costs"
        shutil.copytree(
            COSTS,
            costs,
            ignore=shutil.ignore_patterns("sessions", "__pycache__", "test_*.py"),
        )
        (costs / "prices.json").write_text(json.dumps(PRICE_TABLE))
        (self.root / ".claude" / "hooks").mkdir()
        shutil.copy(LIB, self.root / ".claude" / "hooks" / "lib.sh")
        (self.root / ".gitignore").write_text("tmp/\n__pycache__/\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "init")
        self.git("push", "-q", "origin", "main")
        self.git("checkout", "-q", "-b", "feature")
        self.git("push", "-q", "-u", "origin", "feature")
        self.respond()

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True,
            text=True,
            check=True,
            env=self.env(),
        ).stdout.strip()

    def env(self) -> dict:
        return {"PATH": "/usr/bin:/bin", "HOME": str(self.home), "GIT_CONFIG_NOSYSTEM": "1"}

    def respond(self) -> None:
        """One more priced turn in the transcript, so the next row differs."""
        self.responses += 1
        with self.transcript.open("a") as f:
            record = response(id=f"msg_{self.responses}", output=1_000, stop="end_turn")
            f.write(record + "\n")

    def register_check(self) -> None:
        settings = {"hooks": {"Stop": [{"hooks": [{"command": "~/.claude/stop-hook-git-check.sh"}]}]}}
        (self.home / ".claude").mkdir(exist_ok=True)
        (self.home / ".claude" / "launcher-settings.json").write_text(json.dumps(settings))

    def stop(self, *, active: bool = False) -> subprocess.CompletedProcess:
        payload = {
            "hook_event_name": "Stop",
            "session_id": SESSION,
            "transcript_path": str(self.transcript),
            "cwd": str(self.root),
            "stop_hook_active": active,
        }
        return subprocess.run(
            [str(self.root / HOOK)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env={**self.env(), "CLAUDE_PROJECT_DIR": str(self.root)},
        )

    def cost(self, *args: str) -> None:
        """`session_cost.py` run by hand, the way an agent or a person runs it."""
        subprocess.run(
            ["python3", str(self.root / ".claude" / "costs" / "session_cost.py"),
             "--transcript", str(self.transcript), "--session-id", SESSION, *args],
            capture_output=True,
            check=True,
            env=self.env(),
        )

    def row(self) -> Path:
        [row] = (self.root / ".claude" / "costs" / "sessions").glob(f"*/{SESSION}.json")
        return row

    def status(self) -> str:
        return self.git("status", "--porcelain")

    def commits(self) -> int:
        return int(self.git("rev-list", "--count", "HEAD"))

    def files_in(self, rev: str) -> List[str]:
        return self.git("show", "--name-only", "--format=", rev).splitlines()


class StopHookTest(unittest.TestCase):
    def setUp(self) -> None:
        base = tempfile.TemporaryDirectory()
        self.addCleanup(base.cleanup)
        self.clone = Clone(Path(base.name))

    def assertLevelWithOrigin(self) -> None:
        self.assertEqual(self.clone.status(), "")
        self.assertEqual(self.clone.git("rev-parse", "HEAD"), self.clone.git("rev-parse", "origin/feature"))
        remote = subprocess.run(
            ["git", "-C", str(self.clone.origin), "rev-parse", "feature"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.assertEqual(remote, self.clone.git("rev-parse", "HEAD"))

    def test_a_row_is_committed_and_pushed_leaving_the_tree_clean(self) -> None:
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertLevelWithOrigin()
        self.assertTrue(self.clone.git("log", "-1", "--format=%s").startswith("chore: session cost +"))
        self.assertEqual(self.clone.files_in("HEAD"), [".claude/costs/sessions/2026-03/sess.json"])

    def test_the_tree_is_clean_and_level_while_the_push_is_in_flight(self) -> None:
        # `origin` runs this before it takes the push, which is the stretch the
        # harness's check could land in. A repository hook runs with `origin`'s
        # own git environment set, which would point the clone's commands at it.
        seen = self.clone.root.parent / "seen"
        probe = self.clone.origin / "hooks" / "pre-receive"
        probe.write_text(
            "#!/bin/sh\n"
            "unset GIT_DIR GIT_QUARANTINE_PATH GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES\n"
            f"cd '{self.clone.root}' && {{ git status --porcelain; "
            f"git rev-list --count origin/feature..HEAD; }} > '{seen}'\n"
        )
        probe.chmod(0o755)
        self.assertEqual(self.clone.stop().returncode, 0)
        self.assertEqual(seen.read_text(), "0\n")

    def test_the_row_is_signed_where_commits_are(self) -> None:
        # A stand-in for gpg: git asks only for the status line and an armoured
        # block, so no key is needed to see whether it was asked at all.
        signer = self.clone.home / "sign"
        signer.write_text(
            "#!/bin/sh\ncat >/dev/null\necho '[GNUPG:] SIG_CREATED ' >&2\n"
            "printf -- '-----BEGIN PGP SIGNATURE-----\\n\\nstub\\n-----END PGP SIGNATURE-----\\n'\n"
        )
        signer.chmod(0o755)
        for setting, value in {"gpg.program": str(signer), "commit.gpgsign": "true"}.items():
            self.clone.git("config", setting, value)
        self.assertEqual(self.clone.stop().returncode, 0)
        self.assertIn("gpgsig", self.clone.git("cat-file", "commit", "HEAD"))

    def test_a_row_that_has_not_changed_is_not_committed_again(self) -> None:
        self.clone.stop()
        before = self.clone.commits()
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.clone.commits(), before)
        self.assertLevelWithOrigin()

    def test_work_the_agent_has_staged_stays_staged_and_out_of_the_commit(self) -> None:
        (self.clone.root / "work.txt").write_text("in flight\n")
        self.clone.git("add", "work.txt")
        result = self.clone.stop()
        self.assertEqual(result.returncode, 2)
        self.assertIn("committed and pushed", result.stderr)
        self.assertEqual(self.clone.git("diff", "--cached", "--name-only"), "work.txt")
        self.assertEqual(self.clone.files_in("HEAD"), [".claude/costs/sessions/2026-03/sess.json"])

    def test_a_row_left_dirty_is_named_to_the_agent_where_a_check_read_it(self) -> None:
        self.clone.register_check()
        self.clone.stop()
        self.clone.respond()
        self.clone.cost()
        self.assertNotEqual(self.clone.status(), "")
        result = self.clone.stop()
        self.assertEqual(result.returncode, 2)
        self.assertIn("was counting it", result.stderr)
        self.assertLevelWithOrigin()

    def test_a_row_left_dirty_is_committed_silently_where_no_check_ran(self) -> None:
        self.clone.stop()
        self.clone.respond()
        self.clone.cost()
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertLevelWithOrigin()

    def test_a_refired_stop_never_blocks(self) -> None:
        self.clone.register_check()
        self.clone.stop()
        self.clone.respond()
        self.clone.cost()
        result = self.clone.stop(active=True)
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertLevelWithOrigin()

    def test_a_failed_push_is_reported_as_committed_but_not_pushed(self) -> None:
        self.clone.git("remote", "set-url", "origin", str(self.clone.root.parent / "missing.git"))
        result = self.clone.stop()
        self.assertEqual(result.returncode, 2)
        self.assertIn("committed but not pushed", result.stderr)
        self.assertEqual(self.clone.status(), "")
        self.assertEqual(self.clone.git("rev-list", "--count", "origin/feature..HEAD"), "1")


if __name__ == "__main__":
    unittest.main()
