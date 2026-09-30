"""The session's telemetry events joined to its transcript: what they add to a
row, and what the row says when there are none."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

from lib.billed import parse_events
from lib.rows import parse_session_cost, row_text
from lib.shape import ShapeError
from test_pricing import boundary, response, step, summarise, t


def event(
    request: str,
    *,
    source: str = "sdk",
    second: int = 0,
    cost: float = 10.0,
    model: str = "test-model",
    speed: str = "normal",
    written: int = 0,
) -> str:
    """One `api_request` as the receiver writes it."""
    return json.dumps(
        {
            "request_id": request,
            "model": model,
            "speed": speed,
            "query_source": source,
            "timestamp": t(second),
            "input_tokens": 3,
            "output_tokens": 1_000_000,
            "cache_read_tokens": 0,
            "cache_creation_tokens": written,
            "cost_usd": cost,
            "duration_ms": 1000,
        }
    )


class WhatTheEventsAdd(unittest.TestCase):
    def test_adds_a_call_the_transcript_never_recorded_to_the_total_by_source(self) -> None:
        row = summarise(
            [step(1, request="req_1")],
            events=[event("req_1"), event("req_hidden", source="prompt_suggestion", cost=2.5)],
        )
        self.assertEqual(row.own_turns.cost_usd, 10.0)
        self.assertEqual(row.total.cost_usd, 12.5)
        self.assertEqual(row.total.responses, 2)
        assert row.telemetry is not None
        self.assertEqual(row.telemetry.events, 2)
        self.assertEqual(row.telemetry.matched, 1)
        self.assertEqual(list(row.telemetry.unseen), ["prompt_suggestion"])
        self.assertEqual(row.telemetry.unseen["prompt_suggestion"].cost_usd, 2.5)

    def test_files_an_unseen_call_under_the_table_s_name_for_its_speed(self) -> None:
        row = summarise([], events=[event("req_hidden", cost=1.0, written=7)])
        tally = row.by_rate["test-model/standard"]
        self.assertEqual((tally.cost_usd, tally.cache_write_5m_tokens), (1.0, 7))

    def test_keeps_the_table_s_price_on_a_matched_response(self) -> None:
        row = summarise([step(1, request="req_1")], events=[event("req_1", cost=10.0)])
        assert row.telemetry is not None
        self.assertEqual(row.total.cost_usd, 10.0)
        self.assertEqual(row.telemetry.matched_table_usd, row.telemetry.matched_event_usd)
        self.assertEqual(row.warnings, [])

    def test_warns_when_the_table_and_the_events_disagree(self) -> None:
        row = summarise([step(1, request="req_1")], events=[event("req_1", cost=12.0)])
        self.assertEqual(len(row.warnings), 1)
        self.assertIn("prices.json priced the 1 responses", row.warnings[0])

    def test_counts_an_event_the_exporter_sent_twice_once(self) -> None:
        row = summarise([], events=[event("req_hidden", cost=1.0), event("req_hidden", cost=1.0)])
        self.assertEqual(row.total.cost_usd, 1.0)

    def test_prices_each_compaction_from_the_compact_call_nearest_it(self) -> None:
        row = summarise(
            [step(1), boundary(100), step(101), boundary(200), step(201)],
            events=[
                event("req_c1", source="compact", second=98, cost=0.2),
                event("req_c2", source="compact", second=199, cost=0.3),
                event("req_s", source="prompt_suggestion", second=150, cost=1.0),
            ],
        )
        self.assertEqual([c.billed_usd for c in row.compactions], [0.2, 0.3])

    def test_leaves_a_compaction_unpriced_when_no_call_is_tagged_for_it(self) -> None:
        row = summarise([step(1), boundary(100), step(101)], events=[event("req_s", second=99)])
        self.assertIsNone(row.compactions[0].billed_usd)


class WithoutEvents(unittest.TestCase):
    def test_prices_from_the_transcript_alone_and_says_so(self) -> None:
        row = summarise([step(1, request="req_1")], events=None)
        self.assertIsNone(row.telemetry)
        self.assertEqual(row.total.cost_usd, 10.0)

    def test_round_trips_a_row_with_telemetry_and_parses_one_without(self) -> None:
        row = summarise([step(1, request="req_1")], events=[event("req_1"), event("req_2")])
        self.assertEqual(parse_session_cost(row_text(row)), row)
        before: Dict[str, Any] = json.loads(row_text(row))
        del before["telemetry"]
        self.assertIsNone(parse_session_cost(json.dumps(before)).telemetry)

    def test_names_the_line_of_an_event_that_does_not_parse(self) -> None:
        with self.assertRaisesRegex(ShapeError, "events line 2: `request_id` is missing"):
            parse_events(event("req_1") + "\n{}", "events")


class FromTheCommandLine(unittest.TestCase):
    def test_reads_the_events_it_is_pointed_at(self) -> None:
        with tempfile.TemporaryDirectory() as base:
            directory = Path(base)
            transcript = directory / "sess.jsonl"
            # The script prices with the real table, so the model is a real one.
            opus = response(model="claude-opus-5-5", output=1000, request="req_1", at=t(1))
            transcript.write_text(opus + "\n", encoding="utf-8")
            events = directory / "events.jsonl"
            events.write_text(event("req_1") + "\n" + event("req_2", cost=1.0) + "\n", encoding="utf-8")
            out = directory / "row.json"
            subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parent / "session_cost.py"),
                    "--transcript", str(transcript),
                    "--events", str(events),
                    "--out", str(out),
                ],
                check=True,
                capture_output=True,
            )
            row = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(row["telemetry"]["matched"], 1)
        self.assertEqual(row["total"]["costUsd"], row["ownTurns"]["costUsd"] + 1.0)


if __name__ == "__main__":
    unittest.main()
