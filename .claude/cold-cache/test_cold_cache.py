#!/usr/bin/env python3
"""Pins the restart cost model to the calculator's figures, and drives the hook
as the harness does — a payload on stdin, a transcript on disk — for each rule
that decides whether a prompt is stopped.

Run by path (`python3 .claude/cold-cache/test_cold_cache.py`), as
`scripts/vet.sh` does.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

HERE = Path(__file__).resolve().parent
HOOK = HERE / "hooks" / "cold_cache.py"
# The ledger's lib is reached by path, as the hook reaches it.
sys.path.insert(0, str(HERE.parent / "costs"))

from lib.pricing import parse_prices
from lib.restart import (
    Session,
    after_expiry,
    estimated_warm_up,
    payback,
    read_history,
    while_warm,
)

PRICES = parse_prices((HERE.parent / "costs" / "prices.json").read_text())
MODEL = "claude-opus-5-5"
OPUS = PRICES.rates[f"{MODEL}/standard"]
HOUR = 3600


def iso(at: float) -> str:
    return datetime.fromtimestamp(at, timezone.utc).isoformat().replace("+00:00", "Z")


def response(
    message_id: str,
    *,
    ago: float,
    read: int,
    write: int = 0,
    model: str = MODEL,
    sidechain: bool = False,
    stop: str = "tool_use",
    tool: Optional[Dict[str, Any]] = None,
    ttl: str = "1h",
) -> Dict[str, Any]:
    split = {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 0}
    split[f"ephemeral_{ttl}_input_tokens"] = write
    return {
        "type": "assistant",
        "isSidechain": sidechain,
        "timestamp": iso(time.time() - ago),
        "message": {
            "id": message_id,
            "model": model,
            "stop_reason": stop,
            "content": [{"type": "tool_use", **tool}] if tool else [{"type": "text", "text": "…"}],
            "usage": {
                "input_tokens": 0,
                "cache_read_input_tokens": read,
                "cache_creation_input_tokens": write,
                "cache_creation": split,
                "output_tokens": 500,
            },
        },
    }


# The calculator's defaults: a session that opened at 82k, 41k of it the prefix
# every session shares, now carrying 174k.
def opening(ago: float = 3 * HOUR, **kw: Any) -> Dict[str, Any]:
    return response("first", ago=ago, read=41_000, write=41_000, **kw)


def latest(message_id: str = "last", ago: float = 2 * HOUR, context: int = 174_000, **kw: Any) -> Dict[str, Any]:
    return response(message_id, ago=ago, read=context - 1_000, write=1_000, **kw)


class TheCostModel(unittest.TestCase):
    def test_after_expiry_matches_the_calculator(self) -> None:
        write = OPUS.cache_write_1h
        s = Session(174_000, 41_000, 82_000, estimated_warm_up(82_000, 41_000, OPUS, write))
        priced = after_expiry(s, OPUS, write)
        self.assertEqual(f"{priced['carry on'].once:.2f}", "1.07")
        self.assertEqual(f"{priced['/compact'].once:.2f}", "1.15")
        self.assertEqual(f"{priced['new session'].once:.2f}", "1.17")
        back = payback(priced["/compact"], priced["carry on"])
        assert back is not None
        self.assertEqual(round(back), 5)

    def test_while_warm_carrying_on_is_free_up_front(self) -> None:
        write = OPUS.cache_write_1h
        s = Session(250_000, 41_000, 82_000, estimated_warm_up(82_000, 41_000, OPUS, write))
        priced = while_warm(s, OPUS, write)
        self.assertEqual(priced["carry on"].once, 0.0)
        back = payback(priced["new session"], priced["carry on"])
        saved = (250_000 - s.warm_up.context) * OPUS.cache_read / 1e6
        assert back is not None
        self.assertAlmostEqual(back, s.warm_up.cost_usd / saved)

    def test_payback_is_none_when_the_option_never_catches_up(self) -> None:
        write = OPUS.cache_write_1h
        # Below the warm-up's own context a new session saves nothing per request.
        s = Session(100_000, 41_000, 82_000, estimated_warm_up(82_000, 41_000, OPUS, write))
        priced = while_warm(s, OPUS, write)
        self.assertIsNone(payback(priced["new session"], priced["carry on"]))


class TheWarmUp(unittest.TestCase):
    def history(self, *records: Dict[str, Any]):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
            return read_history(path, PRICES)

    def test_ends_at_the_first_edit(self) -> None:
        h = self.history(
            opening(),
            response("look", ago=100, read=82_000, write=20_000),
            response("edit", ago=90, read=102_000, write=3_000, tool={"name": "Edit", "input": {}}),
            response("more", ago=80, read=105_000, write=40_000, tool={"name": "Write", "input": {}}),
        )
        assert h is not None and h.warm_up is not None
        self.assertEqual(h.warm_up.context, 105_000)
        # Three responses priced, the fourth after the warm-up is not.
        self.assertAlmostEqual(
            h.warm_up.cost_usd,
            (41_000 * 0.2 + 41_000 * 8 + 82_000 * 0.2 + 20_000 * 8 + 102_000 * 0.2 + 3_000 * 8 + 3 * 500 * 20) / 1e6,
        )

    def test_ends_at_a_bash_commit_or_a_finished_answer(self) -> None:
        commit = self.history(
            opening(),
            response("ls", ago=90, read=82_000, write=5_000, tool={"name": "Bash", "input": {"command": "ls"}}),
            response("c", ago=80, read=87_000, write=1_000, tool={"name": "Bash", "input": {"command": "git commit -m x"}}),
        )
        answer = self.history(opening(), response("a", ago=80, read=82_000, write=9_000, stop="end_turn"))
        assert commit is not None and commit.warm_up is not None
        assert answer is not None and answer.warm_up is not None
        self.assertEqual(commit.warm_up.context, 88_000)
        self.assertEqual(answer.warm_up.context, 91_000)

    def test_is_unknown_before_it_ends_or_when_unpriced(self) -> None:
        looking = self.history(opening(), response("ls", ago=90, read=82_000, write=5_000))
        unpriced = self.history(opening(model="claude-x"), response("a", ago=80, read=82_000, stop="end_turn"))
        assert looking is not None and unpriced is not None
        self.assertIsNone(looking.warm_up)
        self.assertIsNone(unpriced.warm_up)


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
        for figure in ("2.0 h", "174k", "$1.07", "$1.15", "$1.17", "~5 requests"):
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

    def test_commands_and_the_stop_word_pass(self) -> None:
        self.append(opening(), latest())
        self.assertIsNone(self.prompt("/compact"))
        self.assertIsNone(self.prompt("  /clear"))
        self.assertIsNone(self.prompt("go on !pass"))
        self.assertIsNotNone(self.prompt())

    def test_a_cheap_recache_passes(self) -> None:
        self.append(opening(), latest(context=45_000))
        self.assertIsNone(self.prompt())
        self.assertIsNotNone(self.prompt(env={"COLD_CACHE_MIN_USD": "0.01"}))

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
