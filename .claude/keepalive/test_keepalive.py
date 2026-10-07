#!/usr/bin/env python3
"""Drives the hook as the harness does — a payload on stdin, a transcript on
disk — and the watcher as the agent's background Bash call does. The period
knob stands in for the hour, so a watcher exits at once.

Run by path (`python3 .claude/keepalive/test_keepalive.py`), as
`scripts/vet.sh` does.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Dict, Optional

HERE = Path(__file__).resolve().parent
HOOK = HERE / "hooks" / "keepalive.py"
# The ledger's directory, for its test's record builders.
sys.path.insert(0, str(HERE.parent / "costs"))
sys.path.insert(0, str(HERE / "hooks"))

from test_restart import opening, response

import keepalive


class HookCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.transcript = self.root / "transcript.jsonl"
        self.state = self.root / "tmp" / "keepalive"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def session(self, ago: float, ttl: str = "1h") -> None:
        records = (opening(ttl=ttl), response("last", ago=ago, read=100_000, write=1_000, ttl=ttl))
        self.transcript.write_text("".join(json.dumps(r) + "\n" for r in records))

    def knob(self, seconds: float) -> None:
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "period").write_text(str(seconds))

    def data(self) -> Dict[str, object]:
        return json.loads((self.state / "sess.json").read_text())

    def env(self, extra: Optional[Dict[str, str]]) -> Dict[str, str]:
        return {"PATH": "/usr/bin:/bin", "CLAUDE_PROJECT_DIR": str(self.root), **(extra or {})}

    def start_watcher(self) -> "subprocess.Popen[str]":
        return subprocess.Popen(
            [sys.executable, str(HOOK), "watch", "sess", str(self.transcript)],
            stderr=subprocess.PIPE,
            text=True,
            env=self.env(None),
        )

    def wake(self) -> None:
        """One watcher run to its exit, as the knob at 0 makes it."""
        self.knob(0)
        proc = self.start_watcher()
        proc.communicate(timeout=30)
        self.assertEqual(proc.returncode, 0)

    def prompt(self, text: str = "carry on", env: Optional[Dict[str, str]] = None) -> "tuple[str, str]":
        """The hook's additional context, or "" when it adds none, and its stderr."""
        body = {
            "hook_event_name": "UserPromptSubmit",
            "prompt": text,
            "session_id": "sess",
            "transcript_path": str(self.transcript),
        }
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(body),
            capture_output=True,
            text=True,
            env=self.env(env),
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0)
        if not proc.stdout:
            return "", proc.stderr
        return json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"], proc.stderr

    def notice(self) -> str:
        """The prompt a wake reaches `UserPromptSubmit` with."""
        return f"Background command \"{keepalive.TASK}\" completed (exit code 0)"


class WhenAnOperatorPromptArrives(HookCase):
    def test_the_agent_is_told_to_start_the_watcher_unless_the_repo_suffices(self) -> None:
        out, _ = self.prompt()
        self.assertIn("As this turn's last action, start the cache keepalive's watcher", out)
        self.assertIn(f"{HOOK} watch sess {self.transcript}", out)
        self.assertIn("Skip it when", out)
        self.assertIn("loop boundary", out)

    def test_a_running_watcher_is_left_to_the_agent_to_stop(self) -> None:
        self.session(ago=1)
        self.knob(60)
        watcher = self.start_watcher()
        try:
            deadline = time.time() + 10
            while not (self.state / "sess.json").exists() or not self.data().get("pid"):
                self.assertLess(time.time(), deadline)
                time.sleep(0.05)
            out, _ = self.prompt()
            self.assertIn("watcher is running", out)
            self.assertIn("TaskStop", out)
        finally:
            watcher.kill()
            watcher.communicate()

    def test_it_starts_a_new_idle_spell(self) -> None:
        self.session(ago=1)
        for _ in range(3):
            self.wake()
            self.prompt(self.notice())
        self.prompt()
        self.wake()
        self.assertIn("wake 1 of 5", self.prompt(self.notice())[0])


class WhenTheWatcherWakesTheSession(HookCase):
    def test_the_wake_asks_for_one_short_line_and_a_new_watcher(self) -> None:
        self.session(ago=1)
        self.wake()
        self.assertEqual((self.data()["wakes"], self.data()["fired"], self.data()["pid"]), (1, True, None))
        out, _ = self.prompt(self.notice())
        self.assertIn("wake 1 of 5", out)
        self.assertIn("at most seven words", out)
        self.assertIn("start the cache keepalive's watcher", out)

    def test_the_fifth_wake_relays_without_a_successor_and_starts_nothing(self) -> None:
        self.session(ago=1)
        for wake in range(1, 5):
            self.wake()
            self.assertIn(f"wake {wake} of 5", self.prompt(self.notice())[0])
        self.wake()
        out, _ = self.prompt(self.notice())
        self.assertIn("last wake (5 of 5)", out)
        self.assertIn('"Without a successor"', out)
        self.assertIn("Do not start the watcher again", out)

    def test_the_wake_count_is_configurable(self) -> None:
        self.session(ago=1)
        self.wake()
        self.assertIn("last wake (1 of 1)", self.prompt(self.notice(), {"CACHE_KEEPALIVE_WAKES": "1"})[0])


class TheDeadline(HookCase):
    def test_a_one_hour_cache_is_woken_lead_seconds_before_expiry(self) -> None:
        self.session(ago=10)
        due = keepalive.deadline(self.transcript, 300)
        assert due is not None
        self.assertAlmostEqual(due, time.time() - 10 + 3600 - 300, delta=5)

    def test_a_five_minute_cache_is_left_alone(self) -> None:
        self.session(ago=1, ttl="5m")
        self.assertIsNone(keepalive.deadline(self.transcript, 300))

    def test_a_session_with_no_transcript_yet_is_left_alone(self) -> None:
        self.assertIsNone(keepalive.deadline(self.transcript, 300))


class TheSwitches(HookCase):
    def test_the_off_switch_says_nothing(self) -> None:
        self.assertEqual(self.prompt(env={"CACHE_KEEPALIVE": "off"}), ("", ""))

    def test_a_malformed_setting_says_why(self) -> None:
        out, err = self.prompt(env={"CACHE_KEEPALIVE_LEAD": "five"})
        self.assertEqual(out, "")
        self.assertIn("CACHE_KEEPALIVE_LEAD", err)


if __name__ == "__main__":
    unittest.main()
