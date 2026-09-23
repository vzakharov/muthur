#!/usr/bin/env python3
"""The rollup is a pure function of the rows, so each case is the rows written
out. What it protects is the bucketing rule — a session counted where it
started — and the branch label the report groups on.

Run by path (`python3 .claude/costs/test_totals.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `lib`.
"""

from __future__ import annotations

import json
import unittest
from dataclasses import replace
from datetime import date

from lib.pricing import SessionCost, Tally, parse_session_cost
from lib.shape import to_json
from lib.totals import branch_label, iso_week, totals_of


def tally(cost_usd: float) -> Tally:
    return Tally(responses=1, cost_usd=cost_usd)


ROW = SessionCost(
    session_id="sess",
    branch="a-branch",
    cwd=None,
    name=None,
    opening_prompt=None,
    prs=[],
    url=None,
    first_response_at="2026-03-04T05:06:07.000Z",
    last_response_at="2026-03-04T06:06:07.000Z",
    prices_as_of="2026-01-01",
    claude_code_total_usd=None,
    total=tally(1),
    own_turns=tally(1),
    subagents=tally(0),
    by_rate={},
    warnings=[],
)


class WhereASessionIsCounted(unittest.TestCase):
    def test_files_a_session_under_the_day_week_and_month_it_started_in(self) -> None:
        totals = totals_of([ROW])
        self.assertEqual(totals.by_day["2026-03-04"].cost_usd, 1)
        self.assertEqual(totals.by_month["2026-03"].cost_usd, 1)
        self.assertEqual(totals.by_week["2026-W10"].cost_usd, 1)

    def test_keeps_a_session_that_ran_past_midnight_whole_in_the_day_it_began(self) -> None:
        totals = totals_of(
            [
                replace(
                    ROW,
                    first_response_at="2026-03-04T23:50:00.000Z",
                    last_response_at="2026-03-05T00:30:00.000Z",
                )
            ]
        )
        self.assertEqual(totals.by_day["2026-03-04"].sessions, 1)
        self.assertNotIn("2026-03-05", totals.by_day)

    def test_counts_a_row_with_no_priced_response_in_the_total_and_branch_alone(self) -> None:
        totals = totals_of([replace(ROW, first_response_at=None, total=tally(0))])
        self.assertEqual(totals.sessions, 1)
        self.assertEqual(totals.by_branch["a-branch"].sessions, 1)
        self.assertEqual(totals.by_month, {})

    def test_sums_sessions_that_share_a_bucket(self) -> None:
        totals = totals_of([ROW, replace(ROW, total=tally(2.5))])
        self.assertEqual(totals.cost_usd, 3.5)
        self.assertEqual(totals.by_month["2026-03"].sessions, 2)


class HowABranchIsLabelled(unittest.TestCase):
    def test_names_the_prs_beside_the_branch_for_a_reader_to_click_through(self) -> None:
        self.assertEqual(branch_label(replace(ROW, prs=[70, 71])), "a-branch #70 #71")

    def test_counts_a_session_touching_two_prs_once_under_its_branch(self) -> None:
        totals = totals_of([replace(ROW, prs=[70, 71])])
        self.assertEqual(totals.by_branch["a-branch #70 #71"].sessions, 1)
        self.assertEqual(totals.cost_usd, 1)

    def test_says_so_rather_than_dropping_a_row_whose_branch_went_unrecorded(self) -> None:
        self.assertEqual(branch_label(replace(ROW, branch=None)), "(no branch)")


class IsoWeeks(unittest.TestCase):
    def test_gives_a_late_december_day_the_next_year_s_week_by_its_thursday(self) -> None:
        # 2025-12-29 is a Monday whose Thursday falls on 2026-01-01.
        self.assertEqual(iso_week(date(2025, 12, 29)), "2026-W01")

    def test_gives_an_early_january_day_the_previous_year_s_last_week(self) -> None:
        # 2027-01-01 is a Friday whose Thursday fell on 2026-12-31.
        self.assertEqual(iso_week(date(2027, 1, 1)), "2026-W53")


class RowsReadBack(unittest.TestCase):
    def test_a_written_row_parses_back_to_itself(self) -> None:
        self.assertEqual(parse_session_cost(json.dumps(to_json(ROW))), ROW)

    def test_a_row_from_before_the_naming_fields_still_parses(self) -> None:
        row = to_json(ROW)
        for key in ("name", "openingPrompt", "prs", "url", "claudeCodeTotalUsd"):
            del row[key]
        self.assertEqual(parse_session_cost(json.dumps(row)), ROW)


if __name__ == "__main__":
    unittest.main()
