#!/usr/bin/env python3
"""The rollup is a pure function of the rows, so each case is the rows written
out. What it protects is the bucketing rule — a session counted where it
started — and the branch label the report groups on.

Run by path (`python3 .claude/costs/test_totals.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `lib`.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

from lib.orientation import Compaction, Phase, Rereads
from lib.pricing import SessionCost, Tally, parse_session_cost
from lib.rows import ROOT, read_row, row_text
from lib.shape import to_json
from lib.totals import branch_label, iso_week, opening_command, operator_label, totals_of


def tally(cost_usd: float) -> Tally:
    return Tally(responses=1, cost_usd=cost_usd)


ROW = SessionCost(
    session_id="sess",
    branch="a-branch",
    cwd=None,
    opening_prompt=None,
    prs=[],
    url=None,
    operator=None,
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


class WhoseSessionItWas(unittest.TestCase):
    def test_files_a_session_under_its_operator_s_handle(self) -> None:
        totals = totals_of([replace(ROW, operator="vzakharov"), replace(ROW, total=tally(2))])
        self.assertEqual(totals.by_operator["@vzakharov"].cost_usd, 1)
        self.assertEqual(totals.by_operator["(unknown)"].cost_usd, 2)

    def test_says_so_rather_than_dropping_a_row_whose_operator_went_unresolved(self) -> None:
        self.assertEqual(operator_label(ROW), "(unknown)")


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

    def test_a_row_from_before_the_naming_and_orientation_fields_still_parses(self) -> None:
        row = to_json(ROW)
        for key in (
            "openingPrompt",
            "prs",
            "url",
            "operator",
            "claudeCodeTotalUsd",
            "orientation",
            "compactions",
        ):
            del row[key]
        self.assertEqual(parse_session_cost(json.dumps(row)), ROW)

    def test_a_measured_row_parses_back_to_itself(self) -> None:
        self.assertEqual(parse_session_cost(json.dumps(to_json(MEASURED))), MEASURED)


def phase(cost_usd: float, ended_by: str = "Edit", context: int = 50_000) -> Phase:
    return Phase(ended_by, "lib/a.py", "2026-03-04T05:10:00.000Z", context, tally(cost_usd))


MEASURED = replace(
    ROW,
    total=tally(4),
    opening_prompt="/handle claude/a-branch",
    orientation=phase(1),
    compactions=[
        Compaction(
            at="2026-03-04T05:30:00.000Z",
            trigger="manual",
            compacted_from=200_000,
            summary_chars=15_000,
            reorientation=phase(0.5, "end_turn", 30_000),
            rereads=Rereads(3, {"Read": 2, "Bash": 1}, 9_000, 0.2),
        )
    ],
)


class WhatOrientationAverages(unittest.TestCase):
    def test_skips_a_row_written_before_orientation_was_measured(self) -> None:
        summary = totals_of([ROW, MEASURED]).orientation
        assert summary is not None and summary.orientation is not None
        self.assertEqual((summary.measured, summary.rows), (1, 2))
        self.assertEqual(summary.orientation.phases, 1)
        self.assertEqual(summary.orientation.share_of_session.mean, 0.25)

    def test_has_nothing_to_average_over_unmeasured_rows(self) -> None:
        summary = totals_of([ROW]).orientation
        assert summary is not None
        self.assertIsNone(summary.orientation)
        self.assertIsNone(summary.compactions)

    def test_groups_by_what_ended_it_and_by_the_opening_command(self) -> None:
        other = replace(MEASURED, opening_prompt="fix the thing", orientation=phase(3, "end_turn"))
        summary = totals_of([MEASURED, other]).orientation
        assert summary is not None and summary.orientation is not None
        self.assertEqual(summary.orientation.usd.mean, 2)
        self.assertEqual(sorted(summary.by_ended_by), ["Edit", "end_turn"])
        self.assertEqual(summary.by_opening_command["/handle"].usd.mean, 1)
        self.assertEqual(summary.by_opening_command["(none)"].usd.mean, 3)

    def test_averages_the_compactions_and_sums_the_re_reads_by_tool(self) -> None:
        summary = totals_of([MEASURED, MEASURED]).orientation
        assert summary is not None and summary.compactions is not None
        self.assertEqual(summary.compactions.compactions, 2)
        self.assertEqual(summary.compactions.reorientation.usd.median, 0.5)
        self.assertEqual(summary.compactions.reread_calls.mean, 3)
        self.assertEqual(summary.compactions.rereads_by_tool, {"Bash": 2, "Read": 4})

    def test_reads_the_opening_command_off_the_opening_prompt(self) -> None:
        self.assertEqual(opening_command(MEASURED), "/handle")
        self.assertEqual(opening_command(ROW), "(none)")


class RetiredFields(unittest.TestCase):
    def setUp(self) -> None:
        # Under the repo's `tmp/`, where `write_atomic` stages: a rename out of
        # the system temp directory may cross filesystems.
        (ROOT / "tmp").mkdir(exist_ok=True)
        base = tempfile.TemporaryDirectory(dir=ROOT / "tmp")
        self.addCleanup(base.cleanup)
        self.path = Path(base.name) / "sess.json"

    def test_a_row_carrying_a_retired_key_is_rewritten_without_it(self) -> None:
        self.path.write_text(json.dumps({**to_json(ROW), "name": "a named session"}))
        self.assertEqual(read_row(self.path), (ROW, ["name"]))
        self.assertEqual(self.path.read_text(), row_text(ROW))

    def test_a_row_in_the_current_shape_is_left_untouched(self) -> None:
        self.path.write_text(row_text(ROW))
        before = self.path.stat().st_mtime_ns
        self.assertEqual(read_row(self.path), (ROW, []))
        self.assertEqual(self.path.stat().st_mtime_ns, before)


if __name__ == "__main__":
    unittest.main()
