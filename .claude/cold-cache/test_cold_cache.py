#!/usr/bin/env python3
"""Pins the relay cost model to the plan's worked example and its four
reorientation sources, and drives the hook
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
    FINISH,
    Reorientation,
    Session,
    line_for,
    read_history,
    reorientation_of,
    saving_over,
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
    cwd: str = "/repo",
) -> Dict[str, Any]:
    split = {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 0}
    split[f"ephemeral_{ttl}_input_tokens"] = write
    return {
        "type": "assistant",
        "isSidechain": sidechain,
        "cwd": cwd,
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


def prompt_record(text: str) -> Dict[str, Any]:
    return {"type": "user", "message": {"role": "user", "content": text}}


def worked(context: int) -> Session:
    """The plan's worked example: 37 requests per 100k of growth, a successor
    reoriented at 97k for $0.57."""
    return Session(context, 41_000, 37 / 100_000, Reorientation(97_000, 0.57, "test"), OPUS, OPUS.cache_write_1h)


class TheCostModel(unittest.TestCase):
    def test_the_warn_line_is_where_a_relay_starts_saving(self) -> None:
        line = line_for(worked(0), FINISH, 0.0)
        assert line is not None
        self.assertAlmostEqual(line, 200_000, delta=5_000)
        self.assertAlmostEqual(saving_over(worked(line), FINISH).usd, 0.0, places=4)

    def test_the_pause_line_is_where_it_saves_a_fifth(self) -> None:
        line = line_for(worked(0), FINISH, 0.2)
        assert line is not None
        self.assertAlmostEqual(line, 300_000, delta=10_000)
        self.assertAlmostEqual(saving_over(worked(line), FINISH).share, 0.2, places=4)

    def test_a_warm_relay_costs_the_summary_turn_and_the_reorientation(self) -> None:
        saving = saving_over(worked(126_000), FINISH)
        self.assertEqual(saving.carry_on, 0.0)
        self.assertEqual(f"{saving.relay:.2f}", "0.76")
        self.assertLess(saving.usd, 0)

    def test_a_cold_relay_pays_the_recache_too(self) -> None:
        warm, cold = saving_over(worked(174_000), FINISH), saving_over(worked(174_000), FINISH, cold=True)
        self.assertEqual(f"{cold.carry_on:.2f}", "1.07")
        self.assertGreater(cold.relay, cold.carry_on)
        # Both options re-cache, so the cold saving is the warm one plus the read
        # a warm summary turn pays and a cold one folds into its re-cache.
        self.assertAlmostEqual(cold.usd - warm.usd, 174_000 * OPUS.cache_read / 1e6)

    def test_no_line_when_the_slice_is_too_short_to_pay_the_summary_turn(self) -> None:
        tiny = Session(0, 0, 0.5 / FINISH, Reorientation(97_000, 0.57, "test"), OPUS, OPUS.cache_write_1h)
        self.assertIsNone(line_for(tiny, FINISH, 0.0))


def row(opening_prompt: str, context: Optional[int], cost: float) -> Dict[str, Any]:
    """A ledger row as far as the reorientation reads it; the rest zeroed."""
    tally = {
        k: 0
        for k in (
            "inputTokens", "cacheWrite5mTokens", "cacheWrite1hTokens", "cacheReadTokens",
            "outputTokens", "thinkingTokens", "responses",
        )
    }
    ended = context is not None
    return {
        "sessionId": opening_prompt, "branch": None, "cwd": None, "openingPrompt": opening_prompt,
        "prs": [], "url": None, "operator": None, "firstResponseAt": None, "lastResponseAt": None,
        "pricesAsOf": "2026-09-01", "claudeCodeTotalUsd": None,
        "total": {**tally, "costUsd": 0.0}, "ownTurns": {**tally, "costUsd": 0.0},
        "subagents": {**tally, "costUsd": 0.0}, "byRate": {}, "warnings": [],
        "orientation": {
            "endedBy": "Edit" if ended else None, "endedOn": "a.py" if ended else None,
            "endedAt": iso(0) if ended else None, "contextTokens": context,
            "spend": {**tally, "costUsd": cost},
        },
        "compactions": [], "telemetry": None,
    }


class TheReorientation(unittest.TestCase):
    """The four sources, each tried only when those before it have nothing."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.sessions = self.dir / "sessions"
        (self.sessions / "2026-09").mkdir(parents=True)

    def source(self, opening: str, *records: Dict[str, Any]) -> Reorientation:
        path = self.dir / "t.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in (prompt_record(opening), *records)) + "\n")
        history = read_history(path)
        assert history is not None
        return reorientation_of(path, history, PRICES, self.sessions, OPUS)

    def ledger(self, *rows: Dict[str, Any]) -> None:
        for i, r in enumerate(rows):
            (self.sessions / "2026-09" / f"{i}.json").write_text(json.dumps(r))

    def acts(self) -> Dict[str, Any]:
        return response("edit", ago=90, read=102_000, write=3_000, tool={"name": "Edit", "input": {"file_path": "/repo/a.py"}})

    def test_a_relayed_session_uses_its_own_reorientation(self) -> None:
        self.ledger(row("/relay take b", 90_000, 0.5))
        found = self.source("/relay take b", opening(), self.acts())
        self.assertEqual(found.context, 105_000)
        self.assertEqual(found.source, "this session's own reorientation")

    def test_then_the_mean_of_the_ledgers_relayed_sessions(self) -> None:
        self.ledger(row("/relay take a", 90_000, 0.5), row("/relay take b", 110_000, 0.7), row("/go x", 50_000, 0.1), row("/relay take c", None, 0.9))
        found = self.source("/relay take b", opening())
        self.assertEqual((found.context, round(found.cost_usd, 2)), (100_000, 0.6))
        self.assertEqual(found.source, "the mean of 2 relayed sessions in the ledger")

    def test_then_this_sessions_own_orientation(self) -> None:
        self.ledger(row("/go x", 50_000, 0.1))
        found = self.source("/go x", opening(), self.acts())
        self.assertEqual(found.source, "this session's own orientation")
        self.assertEqual(found.context, 105_000)

    def test_a_scratch_write_is_not_acting(self) -> None:
        scratch = response("tmp", ago=90, read=102_000, write=3_000, tool={"name": "Write", "input": {"file_path": "/repo/tmp/x"}})
        found = self.source("/go x", opening(), scratch)
        self.assertTrue(found.source.startswith("an estimate"))

    def test_then_the_estimate(self) -> None:
        found = self.source("/go x", opening())
        self.assertEqual(found.context, 82_000 + 60_000)
        self.assertTrue(found.source.startswith("an estimate"))


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
        for figure in ("2.0 h", "174k", "Carry on: ≈$1.07", "/relay: ≈$2.40", "costs ≈$1.33 more", "from an estimate"):
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
        for command in ("/compact", "  /clear", "/relay /go", "/context", "/usage", "/model opus"):
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
