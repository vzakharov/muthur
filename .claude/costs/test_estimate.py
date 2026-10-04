#!/usr/bin/env python3
"""The human-hour estimate: what a revision may hold, how a row's revisions and
a running session's pending ones merge, what `estimate.py` writes where, and the
ratio the report draws from them.

Run by path (`python3 .claude/costs/test_estimate.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `lib`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from lib.estimate import Revision, checked, junior_hours, merged, parse_grades, parse_revisions
from lib.rows import ROOT, SessionCost, parse_session_cost, pending_estimates_path, row_text
from lib.shape import ShapeError, to_json
from lib.tally import Tally
from lib.totals import effort_of, main_model

GRADES = {"junior": 1, "senior": 2.5}
COSTS = Path(__file__).resolve().parent


def revision(at: str, hours: float = 2, grade: str = "senior", comment: str = "why") -> Revision:
    return Revision(at, hours, grade, comment)


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
    total=Tally(responses=1, cost_usd=10),
    own_turns=Tally(responses=1, cost_usd=10),
    subagents=Tally(),
    by_rate={
        "claude-opus-5-5/standard": Tally(responses=1, cost_usd=9),
        "claude-haiku-4-5/standard": Tally(responses=1, cost_usd=1),
    },
    warnings=[],
)


class WhatARevisionMayHold(unittest.TestCase):
    def test_takes_a_grade_the_table_names_and_a_tweet_sized_comment(self) -> None:
        self.assertEqual(checked(revision("t"), GRADES, "r"), revision("t"))

    def test_refuses_a_grade_the_table_does_not_name(self) -> None:
        with self.assertRaisesRegex(ShapeError, "wizard"):
            checked(revision("t", grade="wizard"), GRADES, "r")

    def test_refuses_negative_hours(self) -> None:
        with self.assertRaises(ShapeError):
            checked(revision("t", hours=-1), GRADES, "r")

    def test_refuses_a_comment_past_280_characters_or_an_empty_one(self) -> None:
        checked(revision("t", comment="x" * 280), GRADES, "r")
        for comment in ("x" * 281, ""):
            with self.assertRaises(ShapeError):
                checked(revision("t", comment=comment), GRADES, "r")

    def test_converts_to_junior_hours_by_the_grade_s_multiplier(self) -> None:
        self.assertEqual(junior_hours(revision("t", hours=2), GRADES), 5)

    def test_refuses_a_grade_table_with_a_non_positive_multiplier(self) -> None:
        with self.assertRaises(ShapeError):
            parse_grades('{"junior": 0}')


class HowHistoriesMerge(unittest.TestCase):
    def test_keeps_every_revision_oldest_first(self) -> None:
        self.assertEqual(
            merged([revision("b")], [revision("c"), revision("a")]),
            [revision("a"), revision("b"), revision("c")],
        )

    def test_the_row_wins_a_moment_both_carry_since_only_a_person_edits_it(self) -> None:
        edited = revision("a", hours=9)
        self.assertEqual(merged([edited], [revision("a")]), [edited])


class RowsCarryTheirEstimates(unittest.TestCase):
    def test_a_row_with_estimates_parses_back_to_itself(self) -> None:
        row = replace(ROW, estimates=[revision("a"), revision("b")])
        self.assertEqual(parse_session_cost(json.dumps(to_json(row))), row)

    def test_a_row_from_before_estimates_reads_as_having_none(self) -> None:
        row = to_json(ROW)
        del row["estimates"]
        self.assertEqual(parse_session_cost(json.dumps(row)).estimates, [])

    def test_a_revision_missing_its_comment_is_refused(self) -> None:
        with self.assertRaisesRegex(ShapeError, "comment"):
            parse_revisions([{"at": "a", "hours": 1, "grade": "junior"}], "row")


class TheReportsRatio(unittest.TestCase):
    def test_divides_summed_spend_by_summed_hours_rather_than_averaging_ratios(self) -> None:
        tiny = replace(
            ROW, total=Tally(responses=1, cost_usd=5), estimates=[revision("a", 0.1, "junior")]
        )
        big = replace(ROW, estimates=[revision("a", 4, "senior")])
        summary = effort_of([tiny, big], GRADES)
        # $15 over 10.1 junior-hours; a mean of the two ratios would be $26.
        self.assertEqual(summary.overall.usd_per_junior_hour, round(15 / 10.1, 4))

    def test_rates_a_session_by_its_current_estimate_alone(self) -> None:
        row = replace(ROW, estimates=[revision("a", 100), revision("b", 2, "junior")])
        self.assertEqual(effort_of([row], GRADES).overall.junior_hours, 2)

    def test_counts_rows_with_no_estimate_without_rating_them(self) -> None:
        summary = effort_of([ROW, replace(ROW, estimates=[revision("a")])], GRADES)
        self.assertEqual((summary.estimated, summary.rows, summary.overall.cost_usd), (1, 2, 10))

    def test_files_a_session_under_the_model_that_spent_most_of_it(self) -> None:
        self.assertEqual(main_model(ROW), "claude-opus-5-5")
        summary = effort_of([replace(ROW, estimates=[revision("a")])], GRADES)
        self.assertEqual(list(summary.by_model_month), ["claude-opus-5-5 2026-03"])
        self.assertEqual(list(summary.by_week), ["2026-W10"])

    def test_has_no_ratio_where_the_estimates_add_up_to_no_hours(self) -> None:
        summary = effort_of([replace(ROW, estimates=[revision("a", 0)])], GRADES)
        self.assertIsNone(summary.overall.usd_per_junior_hour)

    def test_raises_on_a_current_estimate_the_grade_table_refuses(self) -> None:
        with self.assertRaises(ShapeError):
            effort_of([replace(ROW, estimates=[revision("a", grade="wizard")])], GRADES)


def estimate(*args: str, session: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(COSTS / "estimate.py"), *args],
        env={**os.environ, "CLAUDE_CODE_SESSION_ID": session},
        capture_output=True,
        text=True,
    )


class TheCommand(unittest.TestCase):
    def setUp(self) -> None:
        # Session ids no real session has, so a run never touches a real row.
        self.running = f"test-running-{os.getpid()}"
        self.finished = f"test-finished-{os.getpid()}"
        self.month = Path(tempfile.mkdtemp(dir=COSTS / "sessions", prefix="test-"))
        self.row = self.month / f"{self.finished}.json"
        self.row.write_text(row_text(replace(ROW, session_id=self.finished)), encoding="utf-8")

    def tearDown(self) -> None:
        self.row.unlink(missing_ok=True)
        self.month.rmdir()
        pending_estimates_path(self.running).unlink(missing_ok=True)

    def test_a_running_session_s_revision_waits_under_tmp_for_its_row(self) -> None:
        done = estimate("set", "3", "senior", "a reason", session=self.running)
        self.assertEqual(done.returncode, 0, done.stderr)
        pending = pending_estimates_path(self.running)
        self.assertTrue(pending.is_relative_to(ROOT / "tmp"))
        written = parse_revisions(json.loads(pending.read_text(encoding="utf-8")), "pending")
        self.assertEqual([(r.hours, r.grade, r.comment) for r in written], [(3, "senior", "a reason")])

    def test_another_session_s_revision_lands_in_its_committed_row(self) -> None:
        done = estimate("set", "1", "junior", "after the fact", "--session", self.finished, session=self.running)
        self.assertEqual(done.returncode, 0, done.stderr)
        row = parse_session_cost(self.row.read_text(encoding="utf-8"))
        self.assertEqual([r.comment for r in row.estimates], ["after the fact"])
        self.assertFalse(pending_estimates_path(self.running).exists())

    def test_a_refused_revision_writes_nothing(self) -> None:
        done = estimate("set", "1", "wizard", "x", session=self.running)
        self.assertEqual(done.returncode, 1)
        self.assertIn("wizard", done.stderr)
        self.assertFalse(pending_estimates_path(self.running).exists())

    def test_a_session_with_no_row_is_refused_rather_than_guessed_at(self) -> None:
        done = estimate("show", "--session", "no-such-session", session=self.running)
        self.assertEqual(done.returncode, 1)


if __name__ == "__main__":
    unittest.main()
