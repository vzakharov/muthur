#!/usr/bin/env python3
"""Drives the hook as the harness does — a payload on stdin, a transcript on
disk — for each rule that decides whether a prompt is stopped. The cost model
it prices with is pinned by `.claude/costs/test_restart.py`, whose record
builders these cases reuse.

Run by path (`python3 .claude/cold-cache/test_cold_cache.py`), as
`scripts/vet.sh` does.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, Optional

HERE = Path(__file__).resolve().parent
HOOK = HERE / "hooks" / "cold_cache.py"
# The ledger's directory, for its lib and its test's record builders.
sys.path.insert(0, str(HERE.parent / "costs"))

from test_restart import HOUR, opening, response, row


def latest(message_id: str = "last", ago: float = 2 * HOUR, context: int = 174_000, **kw: Any) -> Dict[str, Any]:
    return response(message_id, ago=ago, read=context - 1_000, write=1_000, **kw)


class HookCase(unittest.TestCase):
    """One session's transcript and state directory, and the hook run against them."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.transcript = self.root / "transcript.jsonl"
        self.transcript.write_text("")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def append(self, *records: Dict[str, Any]) -> None:
        with self.transcript.open("a") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

    def run_hook(self, event: str, env: Optional[Dict[str, str]] = None, **payload: Any) -> str:
        body = {
            "hook_event_name": event,
            "session_id": "sess",
            "transcript_path": str(self.transcript),
            **payload,
        }
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(body),
            capture_output=True,
            text=True,
            check=True,
            env={"PATH": "/usr/bin:/bin", "CLAUDE_PROJECT_DIR": str(self.root), **(env or {})},
        ).stdout

    def prompt(self, text: str = "carry on", env: Optional[Dict[str, str]] = None) -> Optional[str]:
        out = self.run_hook("UserPromptSubmit", env, prompt=text)
        if not out.strip():
            return None
        decision = json.loads(out)
        self.assertEqual(decision["decision"], "block")
        return decision["reason"]

    def fresh_sessions(self, context: int, cost: float) -> None:
        """A ledger whose fresh sessions oriented at `context` for `cost`."""
        month = self.root / ".claude" / "costs" / "sessions" / "2026-09"
        month.mkdir(parents=True)
        (month / "0.json").write_text(json.dumps(row("/go x", context, cost)))

    def resume(self, **fields: Any) -> None:
        self.run_hook("SessionStart", source="resume", **fields)


class WhenAPromptIsStopped(HookCase):
    def test_a_warm_cache_passes(self) -> None:
        self.append(opening(), latest(ago=600))
        self.assertIsNone(self.prompt())

    def test_a_cache_past_its_ttl_is_stopped_with_the_prices(self) -> None:
        self.append(opening(), latest())
        reason = self.prompt()
        assert reason is not None
        for figure in ("2.0 h", "174k", "Carry on: ~$1.07", "A new session, if everything", "~$1.17 to reorient", "from an estimate", "~142k instead of ~174k"):
            self.assertIn(figure, reason)

    def test_a_five_minute_ttl_expires_in_minutes(self) -> None:
        self.append(opening(ttl="5m"), latest(ago=600, ttl="5m"))
        reason = self.prompt()
        assert reason is not None
        self.assertIn("10 min", reason)

    def test_the_second_prompt_of_a_cold_spell_passes(self) -> None:
        self.append(opening(), latest())
        self.assertIsNotNone(self.prompt())
        self.assertIsNone(self.prompt())

    def test_a_new_response_and_a_new_gap_rearm_it(self) -> None:
        self.append(opening(), latest())
        self.prompt()
        self.append(latest("later", ago=1.5 * HOUR))
        self.assertIsNotNone(self.prompt())

    def test_the_ways_on_and_the_built_ins_that_prompt_nothing_pass(self) -> None:
        self.append(opening(), latest())
        for command in ("/compact", "  /clear", "/relay go", "/context", "/usage", "/model opus"):
            self.assertIsNone(self.prompt(command), command)
        self.assertIsNotNone(self.prompt())

    def test_skills_and_model_driven_built_ins_are_stopped(self) -> None:
        for command in ("/go", "/handle x", "/finalize", "/btw why", "/init", "/plan fix it", "/code-review"):
            with self.subTest(command=command):
                (self.root / "tmp" / "cold-cache" / "sess.blocked").unlink(missing_ok=True)
                self.transcript.write_text("")
                self.append(opening(), latest())
                self.assertIsNotNone(self.prompt(command))

    def test_a_bare_bang_resends_the_stopped_prompt(self) -> None:
        self.append(opening(), latest())
        self.assertIsNotNone(self.prompt("fix the flaky test"))
        out = json.loads(self.run_hook("UserPromptSubmit", prompt=" ! "))["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "UserPromptSubmit")
        self.assertTrue(out["additionalContext"].endswith("verbatim:\n\nfix the flaky test"))

    def test_a_bare_bang_with_nothing_stopped_passes_as_it_is(self) -> None:
        self.append(opening(), latest(ago=600))
        self.assertEqual(self.run_hook("UserPromptSubmit", prompt="!"), "")

    def test_a_bang_inside_a_prompt_is_just_a_prompt(self) -> None:
        self.append(opening(), latest())
        self.assertIsNotNone(self.prompt("go on !pass"))

    def test_a_cheap_recache_passes(self) -> None:
        self.fresh_sessions(20_000, 0.05)
        self.append(opening(), latest(context=45_000))
        self.assertIsNone(self.prompt())
        self.assertIsNotNone(self.prompt(env={"COLD_CACHE_MIN_USD": "0.01"}))

    def test_a_fresh_session_that_cannot_come_out_ahead_passes(self) -> None:
        self.fresh_sessions(132_000, 1.19)
        self.append(opening(), latest(context=94_000))
        self.assertIsNone(self.prompt())

    def test_a_fresh_session_ahead_by_less_than_the_margin_passes(self) -> None:
        # Against a $0.43 re-cache at 94k: under 10% better on both counts.
        self.fresh_sessions(90_000, 0.40)
        self.append(opening(), latest(context=94_000))
        self.assertIsNone(self.prompt())
        self.assertIsNotNone(self.prompt(env={"COLD_CACHE_MARGIN": "0"}))

    def test_a_fresh_session_that_carries_less_is_still_offered(self) -> None:
        self.fresh_sessions(60_000, 1.19)
        self.append(opening(), latest(context=94_000))
        self.assertIsNotNone(self.prompt())

    def test_an_unpriced_model_is_stopped_without_dollars(self) -> None:
        self.append(opening(model="claude-x"), latest(model="claude-x"))
        reason = self.prompt()
        assert reason is not None
        self.assertIn("no row in the price table", reason)
        self.assertNotIn("$", reason)

    def test_sidechains_and_synthetic_records_are_not_the_last_response(self) -> None:
        self.append(
            opening(),
            latest(),
            response("agent", ago=60, read=90_000, sidechain=True),
            response("none", ago=60, read=0, model="<synthetic>"),
        )
        self.assertIsNotNone(self.prompt())

    def test_off_disables_both_halves(self) -> None:
        self.append(opening(), latest())
        off = {"COLD_CACHE_GUARD": "off"}
        self.run_hook("SessionStart", off, source="resume", prompt_cache_likely_expired=True)
        self.assertFalse((self.root / "tmp" / "cold-cache" / "sess.json").exists())
        self.assertIsNone(self.prompt(env=off))


class TheResumeFlag(HookCase):
    def test_a_resume_the_client_calls_expired_is_stopped_on_its_figures(self) -> None:
        # Warm by the transcript; only the resume says otherwise.
        self.fresh_sessions(60_000, 0.30)
        self.append(opening(), latest(ago=600))
        self.resume(
            prompt_cache_likely_expired=True,
            seconds_since_last_response=23_161,
            context_tokens=149_773,
            estimated_cache_write_usd=1.1982,
        )
        reason = self.prompt()
        assert reason is not None
        self.assertIn("6.4 h", reason)
        self.assertIn("150k", reason)

    def test_the_flag_speaks_for_an_unpriced_model(self) -> None:
        self.append(opening(model="claude-x"), latest(ago=600, model="claude-x"))
        self.resume(
            prompt_cache_likely_expired=True,
            seconds_since_last_response=7_200,
            context_tokens=149_773,
            estimated_cache_write_usd=1.1982,
        )
        reason = self.prompt()
        assert reason is not None
        self.assertIn("Claude Code estimates re-caching at $1.20", reason)

    def test_any_other_start_clears_it(self) -> None:
        self.append(opening(), latest(ago=600))
        self.resume(prompt_cache_likely_expired=True, seconds_since_last_response=7_200, context_tokens=174_000)
        self.run_hook("SessionStart", source="startup")
        self.assertIsNone(self.prompt())

    def test_a_response_since_the_resume_retires_it(self) -> None:
        self.append(opening(), latest(ago=600))
        self.resume(prompt_cache_likely_expired=True, seconds_since_last_response=7_200, context_tokens=174_000)
        self.append(latest("after", ago=-5))
        self.assertIsNone(self.prompt())
        self.assertFalse((self.root / "tmp" / "cold-cache" / "sess.json").exists())


if __name__ == "__main__":
    unittest.main()
