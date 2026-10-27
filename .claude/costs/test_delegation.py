#!/usr/bin/env python3
"""`delegation.weigh` against transcripts written out in the cases, at
`test_pricing.py`'s rate table: test-model reads its cache at 0.5, writes at 2
(5 minutes) and outputs at 10, USD per million tokens.

Run by path (`python3 .claude/costs/test_delegation.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `lib`.
"""

from __future__ import annotations

import unittest
from typing import List, Optional

from delegation import weigh
from lib.pricing import UnpricedError
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


if __name__ == "__main__":
    unittest.main()
