#!/usr/bin/env python3
"""A period is what `--month`, `--week` and `--day` narrow the report to, named
outright or as `cur` / `prev`. What it protects is the edges: which days a
period spans, which month directories hold its rows, and which rows it keeps.

Run by path (`python3 .claude/costs/test_period.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `lib`.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date

from lib.period import PeriodError, iso_week, month_of, period
from lib.rows import SessionCost
from lib.tally import Tally

TODAY = date(2026, 10, 7)  # a Wednesday in 2026-W41

ROW = SessionCost(
    session_id="sess",
    branch=None,
    cwd=None,
    opening_prompt=None,
    prs=[],
    url=None,
    operator=None,
    first_response_at="2026-09-30T23:30:00.000Z",
    last_response_at=None,
    prices_as_of="2026-01-01",
    claude_code_total_usd=None,
    total=Tally(),
    own_turns=Tally(),
    subagents=Tally(),
    by_rate={},
    warnings=[],
)


def span(kind: str, value: str) -> tuple:
    found = period(kind, value, TODAY)
    return found.label, found.first.isoformat(), found.last.isoformat()


class NamedOutright(unittest.TestCase):
    def test_a_month_runs_to_its_last_day(self) -> None:
        self.assertEqual(span("month", "2026-02"), ("2026-02", "2026-02-01", "2026-02-28"))

    def test_a_week_runs_monday_to_sunday_by_the_iso_calendar(self) -> None:
        self.assertEqual(span("week", "2026-W01"), ("2026-W01", "2025-12-29", "2026-01-04"))

    def test_a_day_is_itself(self) -> None:
        self.assertEqual(span("day", "2026-10-07"), ("2026-10-07", "2026-10-07", "2026-10-07"))

    def test_case_is_ignored_and_the_label_keeps_iso_s(self) -> None:
        self.assertEqual(span("week", "2026-w41")[0], "2026-W41")
        self.assertEqual(span("week", "CUR")[0], "2026-W41")
        self.assertEqual(span("month", "Prev")[0], "2026-09")

    def test_a_malformed_or_impossible_one_raises(self) -> None:
        for kind, value in (("month", "2026-13"), ("week", "2026-41"), ("day", "2026-02-30")):
            with self.subTest(kind=kind, value=value), self.assertRaises(PeriodError):
                period(kind, value, TODAY)


class Relative(unittest.TestCase):
    def test_cur_holds_today_and_prev_is_the_one_before(self) -> None:
        self.assertEqual(span("month", "cur")[0], "2026-10")
        self.assertEqual(span("month", "prev")[0], "2026-09")
        self.assertEqual(span("week", "cur")[0], "2026-W41")
        self.assertEqual(span("week", "prev")[0], "2026-W40")
        self.assertEqual(span("day", "cur")[0], "2026-10-07")
        self.assertEqual(span("day", "prev")[0], "2026-10-06")

    def test_prev_month_crosses_a_year(self) -> None:
        self.assertEqual(period("month", "prev", date(2026, 1, 15)).label, "2025-12")


class WhichRowsItKeeps(unittest.TestCase):
    def test_a_week_spanning_two_months_reads_both(self) -> None:
        self.assertEqual(period("week", "2026-W40", TODAY).months(), ["2026-09", "2026-10"])

    def test_a_row_belongs_to_the_day_it_started(self) -> None:
        self.assertTrue(period("week", "2026-W40", TODAY).holds(ROW))
        self.assertTrue(period("month", "2026-09", TODAY).holds(ROW))
        self.assertFalse(period("day", "2026-10-01", TODAY).holds(ROW))

    def test_an_undated_row_counts_toward_its_month_alone(self) -> None:
        undated = replace(ROW, first_response_at=None)
        self.assertTrue(month_of(TODAY).holds(undated))
        self.assertFalse(period("week", "cur", TODAY).holds(undated))

    def test_the_label_matches_the_week_table_s(self) -> None:
        self.assertEqual(period("week", "cur", TODAY).label, iso_week(TODAY))


if __name__ == "__main__":
    unittest.main()
