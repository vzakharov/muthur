#!/usr/bin/env python3
"""`delegation.weigh` against transcripts written out in the cases, at
`test_pricing.py`'s rate table: test-model reads its cache at 0.5, writes at 2
(5 minutes) and outputs at 10, USD per million tokens.

Run by path (`python3 .claude/costs/test_delegation.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `lib`.
"""

from __future__ import annotations

import unittest
from datetime import datetime
from typing import List, Optional

from delegation import weigh
from lib.delegations import PREFIX as DELEGATIONS_PREFIX
from lib.delegations import SEED_RUN_USD, Measured, Wave, describe, forecast, path_of, runs_of, text_of
from lib.pricing import UnpricedError
from lib.shape import ShapeError
from test_pricing import PRICES, response

AGENT = {"type": "tool_use", "id": "toolu_agent", "name": "Agent", "input": {}}


def main_transcript(later_context: Optional[int] = 1_500_000) -> str:
    """The delegator launches from a 1M-token context, its tool call in the
    response's second record; a later turn, when given, has grown to
    `later_context`."""
    lines = [
        response(id="own_1", read=1_000_000, output=1_000, stop="tool_use", at="2026-03-04T05:00:00.000Z"),
        response(
            id="own_1",
            read=1_000_000,
            output=1_000,
            stop="tool_use",
            at="2026-03-04T05:00:00.000Z",
            calls=[AGENT],
        ),
    ]
    if later_context is not None:
        lines.append(response(id="own_2", read=later_context, stop="end_turn", at="2026-03-04T06:00:00.000Z"))
    return "\n".join(lines)


def subagent_transcript() -> str:
    """Two turns whose context grows from 2M to 4M tokens, 1M output in all."""
    turns: List[str] = [
        response(id="sub_1", sidechain=True, read=2_000_000, output=400_000, at="2026-03-04T05:10:00.000Z"),
        response(id="sub_2", sidechain=True, read=4_000_000, output=600_000, at="2026-03-04T05:20:00.000Z"),
    ]
    return "\n".join(turns)


class WeighTest(unittest.TestCase):
    def test_both_sides_at_the_delegators_rates(self) -> None:
        w = weigh(main_transcript(), subagent_transcript(), "toolu_agent", PRICES)
        # 6M read at 0.5 and 1M output at 10.
        self.assertAlmostEqual(w.subagent_usd, 13.0)
        self.assertAlmostEqual(w.brief_usd, 0.01)
        self.assertAlmostEqual(w.delegated_usd, 13.01)
        # Reads (1M + 0) + (1M + 2M) at 0.5, output 1M at 10, growth 2M at 2.
        self.assertAlmostEqual(w.in_session_usd, 2.0 + 10.0 + 4.0)
        self.assertEqual((w.subagent_turns, w.in_session_turns, w.later_turns), (2, 2, 1))

    def test_what_each_later_turn_re_reads(self) -> None:
        w = weigh(main_transcript(), subagent_transcript(), "toolu_agent", PRICES)
        # Delegated, the context grew 0.5M; in-session it would have taken on
        # the subagent's 2M growth.
        self.assertAlmostEqual(w.carried_delegated_usd or 0, 0.25)
        self.assertAlmostEqual(w.carried_in_session_usd, 1.0)

    def test_fewer_turns_scale_the_reads_alone(self) -> None:
        w = weigh(main_transcript(), subagent_transcript(), "toolu_agent", PRICES, turns=1)
        self.assertAlmostEqual(w.in_session_usd, 1.0 + 10.0 + 4.0)
        self.assertEqual(w.in_session_turns, 1)

    def test_no_later_turn_leaves_the_delegated_carry_unmeasured(self) -> None:
        w = weigh(main_transcript(later_context=None), subagent_transcript(), "toolu_agent", PRICES)
        self.assertIsNone(w.carried_delegated_usd)
        self.assertEqual(w.later_turns, 0)

    def test_an_unknown_tool_use_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "toolu_other"):
            weigh(main_transcript(), subagent_transcript(), "toolu_other", PRICES)

    def test_an_unpriced_delegator_raises(self) -> None:
        main = response(id="own_1", model="unknown-model", read=10, calls=[AGENT], stop="tool_use")
        with self.assertRaises(UnpricedError):
            weigh(main, subagent_transcript(), "toolu_agent", PRICES)

    def test_the_launching_and_reviewing_re_reads(self) -> None:
        w = weigh(main_transcript(), subagent_transcript(), "toolu_agent", PRICES)
        self.assertEqual(w.launch_context, 1_000_000)
        self.assertAlmostEqual(w.launch_read_usd, 0.5)
        self.assertAlmostEqual(w.review_read_usd or 0, 0.75)
        self.assertEqual(w.subagent_model, "test-model")

    def test_no_later_turn_leaves_the_review_unmeasured(self) -> None:
        w = weigh(main_transcript(later_context=None), subagent_transcript(), "toolu_agent", PRICES)
        self.assertIsNone(w.review_read_usd)


class ForecastTest(unittest.TestCase):
    RATES = weigh(main_transcript(), subagent_transcript(), "toolu_agent", PRICES).launch_rates

    def test_direct_re_reads_once_a_turn_and_a_wave_twice_plus_the_run(self) -> None:
        f = forecast(turns=4, waves=2, context_tokens=1_000_000, rates=self.RATES, runs=[0.2, 0.4])
        self.assertAlmostEqual(f.turn_usd, 0.5)
        self.assertAlmostEqual(f.run_usd, 0.3)
        self.assertAlmostEqual(f.direct_usd, 2.0)
        self.assertAlmostEqual(f.steno_usd, 2 * (0.3 + 1.0))
        self.assertAlmostEqual(f.wave_usd, 1.3)

    def test_no_measured_run_falls_to_the_seed(self) -> None:
        f = forecast(turns=1, waves=1, context_tokens=0, rates=self.RATES, runs=[])
        self.assertEqual((f.run_usd, f.runs_measured), (SEED_RUN_USD, 0))
        self.assertIn("seed", describe(f))

    def test_a_zero_count_raises(self) -> None:
        with self.assertRaises(ValueError):
            forecast(turns=0, waves=1, context_tokens=1, rates=self.RATES, runs=[])


class WaveRowTest(unittest.TestCase):
    def wave(self, agent_id: str, run_usd: float) -> Wave:
        rates = ForecastTest.RATES
        return Wave(
            agent_id=agent_id,
            session_id="s",
            branch="b",
            model="test-model",
            recorded_at="2026-10-29T00:00:00+00:00",
            forecast=forecast(1, 1, 10, rates, []),
            measured=Measured(
                run_usd=run_usd, run_turns=1, dictate_usd=0, review_usd=None, brief_usd=0, in_session_usd=0
            ),
        )

    def test_a_row_reads_back_its_run_and_never_calibrates_itself(self) -> None:
        rows = [
            (path_of(self.wave(agent, usd), datetime(2026, 10, 29)), text_of(self.wave(agent, usd)))
            for agent, usd in (("a1", 0.1), ("a2", 0.3))
        ]
        self.assertEqual(rows[0][0], f"{DELEGATIONS_PREFIX}/2026-10/a1.json")
        self.assertEqual(runs_of(rows), [0.1, 0.3])
        self.assertEqual(runs_of(rows, leaving_out="a1"), [0.3])

    def test_a_row_without_its_run_raises(self) -> None:
        with self.assertRaisesRegex(ShapeError, "runUsd"):
            runs_of([("x/a.json", '{"measured": {}}')])


if __name__ == "__main__":
    unittest.main()
