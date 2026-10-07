#!/usr/bin/env python3
"""Drives the hook as the harness does — a payload on stdin, a transcript on
disk — for each rule that decides whether a wake fires. The period knob stands
in for the hour, so a case sleeps for at most a few seconds.

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
from typing import Any, Dict, Optional

HERE = Path(__file__).resolve().parent
HOOK = HERE / "hooks" / "keepalive.py"
# The ledger's directory, for its test's record builders.
sys.path.insert(0, str(HERE.parent / "costs"))

from test_restart import opening, response


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

    def wakes(self) -> int:
        return json.loads((self.state / "sess.json").read_text())["wakes"]

    def start(self, event: str, env: Optional[Dict[str, str]] = None, prompt: str = "carry on") -> "subprocess.Popen[str]":
        body: Dict[str, Any] = {
            "hook_event_name": event,
            "prompt": prompt,
            "session_id": "sess",
            "transcript_path": str(self.transcript),
        }
        proc = subprocess.Popen(
            [sys.executable, str(HOOK)],
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={"PATH": "/usr/bin:/bin", "CLAUDE_PROJECT_DIR": str(self.root), **(env or {})},
        )
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(body))
        proc.stdin.close()
        return proc

    def finish(self, proc: "subprocess.Popen[str]") -> "tuple[int, str]":
        _, err = proc.communicate(timeout=30)
        return proc.returncode, err

    def run_hook(self, event: str, env: Optional[Dict[str, str]] = None, prompt: str = "carry on") -> "tuple[int, str]":
        return self.finish(self.start(event, env, prompt))


class WhenTheSessionGoesIdle(HookCase):
    def test_a_stop_wakes_the_model_with_one_line_to_say(self) -> None:
        self.session(ago=1)
        self.knob(0)
        code, err = self.run_hook("Stop")
        self.assertEqual(code, 2)
        self.assertIn("wake 1 of 5", err)
        self.assertIn("at most seven words", err)
        self.assertEqual(self.wakes(), 1)

    def test_the_fifth_wake_relays_without_a_successor_and_nothing_follows_it(self) -> None:
        self.session(ago=1)
        self.knob(0)
        for wake in range(1, 5):
            self.assertIn(f"wake {wake} of 5", self.run_hook("Stop")[1])
        code, err = self.run_hook("Stop")
        self.assertEqual(code, 2)
        self.assertIn("last wake (5 of 5)", err)
        self.assertIn('"Without a successor"', err)
        self.assertEqual(self.run_hook("Stop"), (0, ""))

    def test_an_operator_prompt_starts_a_new_spell(self) -> None:
        self.session(ago=1)
        self.knob(0)
        for _ in range(5):
            self.run_hook("Stop")
        self.run_hook("UserPromptSubmit")
        self.assertIn("wake 1 of 5", self.run_hook("Stop")[1])

    def test_the_wake_reaching_user_prompt_submit_keeps_the_count(self) -> None:
        self.session(ago=1)
        self.knob(0)
        _, err = self.run_hook("Stop")
        self.run_hook("UserPromptSubmit", prompt=f"Stop hook blocking error from command \"Stop\": {err}")
        self.assertIn("wake 2 of 5", self.run_hook("Stop")[1])

    def test_the_wake_count_is_configurable(self) -> None:
        self.session(ago=1)
        self.knob(0)
        self.assertIn("last wake (1 of 1)", self.run_hook("Stop", {"CACHE_KEEPALIVE_WAKES": "1"})[1])


class WhenASleeperIsSuperseded(HookCase):
    def test_a_later_stop_stands_the_earlier_sleeper_down(self) -> None:
        self.session(ago=1)
        self.knob(1.5)
        first = self.start("Stop")
        time.sleep(0.5)
        second = self.start("Stop")
        self.assertEqual((self.finish(first)[0], self.finish(second)[0]), (0, 2))
        self.assertEqual(self.wakes(), 1)

    def test_an_operator_prompt_stands_the_sleeper_down(self) -> None:
        self.session(ago=1)
        self.knob(1.5)
        sleeper = self.start("Stop")
        time.sleep(0.5)
        self.run_hook("UserPromptSubmit")
        self.assertEqual(self.finish(sleeper), (0, ""))
        self.assertEqual(self.wakes(), 0)


class WhenThereIsNothingToKeepWarm(HookCase):
    def test_a_five_minute_cache_is_left_alone(self) -> None:
        self.session(ago=1, ttl="5m")
        self.assertEqual(self.run_hook("Stop"), (0, ""))
        self.assertFalse((self.state / "sess.json").exists())

    def test_a_session_with_no_transcript_yet_is_left_alone(self) -> None:
        self.assertEqual(self.run_hook("Stop"), (0, ""))

    def test_an_already_expired_cache_fires_at_once(self) -> None:
        self.session(ago=2 * 3600)
        self.assertEqual(self.run_hook("Stop")[0], 2)

    def test_the_off_switch_arms_nothing(self) -> None:
        self.session(ago=1)
        self.knob(0)
        self.assertEqual(self.run_hook("Stop", {"CACHE_KEEPALIVE": "off"}), (0, ""))

    def test_a_malformed_setting_arms_nothing_and_says_why(self) -> None:
        self.session(ago=1)
        self.knob(0)
        code, err = self.run_hook("Stop", {"CACHE_KEEPALIVE_LEAD": "five"})
        self.assertEqual(code, 0)
        self.assertIn("CACHE_KEEPALIVE_LEAD", err)


if __name__ == "__main__":
    unittest.main()
