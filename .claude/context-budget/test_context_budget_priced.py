#!/usr/bin/env python3
"""The priced lines: where the hook moves its warning and pause off the fixed
ones, from what the session's own transcript says a relay saves. Shares its
harness with `test_context_budget.py`.

Run by path (`python3 .claude/context-budget/test_context_budget_priced.py`), as
`scripts/vet.sh` does.
"""

from __future__ import annotations

import re
import unittest

from budget_harness import WARN, BudgetTestCase, priced


class ThePricedLines(BudgetTestCase):
    # Opening at 43k, acting at 90k, then growing 2k a request: a successor
    # reoriented at 90k for ~$0.04, and a relay that saves $0.20 over the next 100k
    # from ~160k and $0.80 from ~230k, both drifting in as the rate settles.
    def setUp(self) -> None:
        super().setUp()
        self.session.append(priced("open", 43_000, 0), priced("edit", 90_000, 1, edits="/repo/a.py"))
        self.top, self.at = 90_000, 1

    def reach(self, context: int) -> None:
        """Grow 2k a request, so each reading keeps the rate the lines were priced on."""
        while self.top < context:
            self.top, self.at = min(self.top + 2_000, context), self.at + 1
            self.session.append(priced(f"r{self.at}", self.top, self.at))

    def line(self, notice: str, kind: str) -> int:
        found = re.search(rf"past the (\d+)k {kind} line", notice)
        assert found is not None, notice
        return int(found.group(1)) * 1_000

    def test_warns_where_a_relay_saves_twenty_cents(self) -> None:
        self.reach(110_000)
        self.assertIsNone(self.session.notice())
        self.reach(170_000)
        notice = self.session.notice()
        assert notice is not None
        self.assertLess(self.line(notice, "warning"), 170_000)
        self.assertIn("where relaying saves $0.20", notice)
        self.assertIn("Relaying now costs ~$", notice)
        self.assertIn("over the next 100k tokens of work", notice)
        self.assertIn("reorientation priced from this session's own orientation", notice)

    def test_a_larger_warn_saving_moves_the_warning_out(self) -> None:
        later = {"MUTHUR_CONTEXT_BUDGET_WARN_SAVING_USD": "0.40", "MUTHUR_CONTEXT_BUDGET_PAUSE_SAVING_USD": "1.50"}
        self.reach(170_000)
        self.assertIsNone(self.session.notice(later))
        self.reach(200_000)
        notice = self.session.notice(later)
        assert notice is not None
        self.assertIn("where relaying saves $0.40", notice)

    def test_a_warn_saving_not_under_the_pause_saving_is_refused(self) -> None:
        self.reach(WARN + 1)
        result = self.session.tool_call({"MUTHUR_CONTEXT_BUDGET_WARN_SAVING_USD": "1"})
        self.assertEqual(result.stdout, "")
        self.assertIn("MUTHUR_CONTEXT_BUDGET_WARN_SAVING_USD", result.stderr)

    def test_a_saving_that_is_not_dollars_is_refused(self) -> None:
        self.reach(WARN + 1)
        result = self.session.tool_call({"MUTHUR_CONTEXT_BUDGET_PAUSE_SAVING_USD": "20%"})
        self.assertEqual(result.stdout, "")
        self.assertIn("MUTHUR_CONTEXT_BUDGET_PAUSE_SAVING_USD", result.stderr)

    def test_a_retired_percentage_knob_is_named_rather_than_ignored(self) -> None:
        self.reach(170_000)
        result = self.session.tool_call({"MUTHUR_CONTEXT_BUDGET_PAUSE_SAVING": "40"})
        self.assertIn("MUTHUR_CONTEXT_BUDGET_PAUSE_SAVING is no longer read", result.stderr)
        self.assertIn("warning line", result.stdout)

    def test_pauses_where_a_relay_saves_eighty_cents(self) -> None:
        self.reach(240_000)
        notice = self.session.notice()
        assert notice is not None
        self.assertLess(self.line(notice, "pause"), 240_000)
        self.assertIn("where relaying saves $0.80", notice)
        self.assertIn("saves ~$", notice)

    def test_a_larger_pause_saving_moves_the_pause_out(self) -> None:
        self.reach(240_000)
        notice = self.session.notice({"MUTHUR_CONTEXT_BUDGET_PAUSE_SAVING_USD": "3"})
        assert notice is not None
        self.assertIn("warning line", notice)

    def test_a_line_set_by_hand_stays_fixed(self) -> None:
        self.reach(150_000)
        self.assertIsNone(self.session.notice({"MUTHUR_CONTEXT_BUDGET_WARN": "200000"}))
        self.reach(200_000)
        notice = self.session.notice({"MUTHUR_CONTEXT_BUDGET_PAUSE": "300000"})
        assert notice is not None
        self.assertLess(self.line(notice, "warning"), 200_000)

    def test_fixed_lines_turn_the_pricing_off(self) -> None:
        fixed = {"MUTHUR_CONTEXT_BUDGET_LINES": "fixed"}
        self.reach(190_000)
        self.assertIsNone(self.session.notice(fixed))
        self.reach(WARN + 1)
        notice = self.session.notice(fixed)
        assert notice is not None
        self.assertIn(f"{WARN // 1_000}k warning line", notice)
        self.assertNotIn("Relaying now costs", notice)
        self.assertFalse((self.session.root / "tmp" / "context-budget" / "sess.line").exists())

    def test_the_fixed_lines_cap_the_priced_ones(self) -> None:
        # A single response gives no growth to measure and prices a line past its cap.
        self.session.transcript.write_text("")
        self.session.append(priced("open", 43_000, 0), priced("r1", WARN + 1, 1))
        # A relay saving $90 is priced past the pause cap, so the warning stands.
        notice = self.session.notice({"MUTHUR_CONTEXT_BUDGET_PAUSE_SAVING_USD": "90"})
        assert notice is not None
        self.assertIn(f"{WARN // 1_000}k warning line — its fixed cap", notice)
        self.assertIn("rather than for cost", notice)

    def test_a_hand_set_line_says_so(self) -> None:
        self.reach(150_000)
        notice = self.session.notice({"MUTHUR_CONTEXT_BUDGET_WARN": "140000", "MUTHUR_CONTEXT_BUDGET_LINES": "fixed"})
        assert notice is not None
        self.assertIn("140k warning line — set by MUTHUR_CONTEXT_BUDGET_WARN", notice)

    def test_an_unknown_mode_is_refused(self) -> None:
        self.reach(WARN + 1)
        result = self.session.tool_call({"MUTHUR_CONTEXT_BUDGET_LINES": "maybe"})
        self.assertEqual(result.stdout, "")
        self.assertIn("MUTHUR_CONTEXT_BUDGET_LINES", result.stderr)


if __name__ == "__main__":
    unittest.main()
