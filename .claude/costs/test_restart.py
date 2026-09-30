#!/usr/bin/env python3
"""Pins the relay cost model to a worked example and its four
reorientation sources. The record builders here are also the cold-cache
guard's fixtures, which is why they take the fields its hook reads.

Run by path (`python3 .claude/costs/test_restart.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `lib`.
"""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

HERE = Path(__file__).resolve().parent

from lib.pricing import parse_prices
from lib.restart import (
    Reorientation,
    Session,
    line_for,
    rates_of,
    read_history,
    recache,
    reorientation_of,
    saving_over,
)

PRICES = parse_prices((HERE / "prices.json").read_text())
MODEL = "claude-opus-5-5"
OPUS = PRICES.rates[f"{MODEL}/standard"]
HOUR = 3600
# The context budget hook's `finish`, the slice a relay's saving is priced over.
FINISH = 100_000


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


def prompt_record(text: str) -> Dict[str, Any]:
    return {"type": "user", "message": {"role": "user", "content": text}}


def worked(context: int) -> Session:
    """A long session's figures: 37 requests per 100k of growth, a successor
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

    def test_a_relay_costs_the_summary_turn_and_the_reorientation(self) -> None:
        saving = saving_over(worked(126_000), FINISH)
        self.assertEqual(f"{saving.relay:.2f}", "0.76")
        self.assertLess(saving.usd, 0)

    def test_a_recache_reads_the_shared_prefix_and_writes_the_rest(self) -> None:
        self.assertEqual(f"{recache(worked(174_000)):.2f}", "1.07")

    def test_no_line_when_the_slice_is_too_short_to_pay_the_summary_turn(self) -> None:
        tiny = Session(0, 0, 0.5 / FINISH, Reorientation(97_000, 0.57, "test"), OPUS, OPUS.cache_write_1h)
        self.assertIsNone(line_for(tiny, FINISH, 0.0))

    def test_a_dated_model_id_is_priced_at_its_undated_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            transcript = Path(tmp) / "session.jsonl"
            transcript.write_text(json.dumps(opening(model=f"{MODEL}-20260901")) + "\n")
            history = read_history(transcript)
            assert history is not None
            self.assertEqual(rates_of(history, PRICES), OPUS)


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

    def source(self, opening: str, *records: Dict[str, Any], relay: bool = True) -> Reorientation:
        path = self.dir / "t.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in (prompt_record(opening), *records)) + "\n")
        history = read_history(path)
        assert history is not None
        return reorientation_of(path, history, PRICES, self.sessions, OPUS, relay)

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

    def test_a_fresh_successor_reads_the_ledgers_fresh_sessions(self) -> None:
        self.ledger(row("/relay take a", 90_000, 0.5), row("/go x", 50_000, 0.1), row("/handle y", 70_000, 0.3))
        found = self.source("/relay take b", opening(), self.acts(), relay=False)
        self.assertEqual((found.context, round(found.cost_usd, 2)), (60_000, 0.2))
        self.assertEqual(found.source, "the mean of 2 fresh sessions in the ledger")

    def test_a_fresh_successor_uses_a_fresh_sessions_own_orientation(self) -> None:
        self.ledger(row("/go y", 50_000, 0.1))
        found = self.source("/go x", opening(), self.acts(), relay=False)
        self.assertEqual(found.source, "this session's own orientation")

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


if __name__ == "__main__":
    unittest.main()
