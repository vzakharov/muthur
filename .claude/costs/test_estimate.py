#!/usr/bin/env python3
"""The human-hour estimate: what one may hold, which of a row's copy and a
running session's pending one wins, what `estimate.py` writes where, and the
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

from lib.estimate import (
    Estimate,
    Part,
    Rates,
    checked,
    latest,
    parse_estimate,
    parse_rates,
    senior_hours,
    split_comment,
)
from lib.rows import ROOT, SessionCost, parse_session_cost, pending_estimate_path, read_row, row_text
from lib.shape import ShapeError, to_json
from lib.tally import Tally
from lib.totals import effort_of, main_model

RATES = Rates(roles={"copywriter": 0.5, "developer": 1}, grades={"junior": 0.4, "senior": 1})
COSTS = Path(__file__).resolve().parent


def estimate_of(at: str, *parts: Part) -> Estimate:
    """Each part given without a reason gets one."""
    given = [part if part.comment is not None else replace(part, comment="why") for part in parts]
    return Estimate(at, given or [Part(2, "senior", "copywriter", "why")])


def legacy(comment: str, *parts: Part) -> Estimate:
    """An estimate as rows were written before parts carried their reasons."""
    return Estimate("a", list(parts), comment)


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


class WhatAnEstimateMayHold(unittest.TestCase):
    def test_takes_roles_and_grades_the_table_names_and_a_tweet_sized_reason_on_each(self) -> None:
        self.assertEqual(checked(estimate_of("t"), RATES, "e"), estimate_of("t"))

    def test_refuses_a_role_or_grade_the_table_does_not_name(self) -> None:
        for part in (Part(1, "wizard", "developer"), Part(1, "senior", "wizard")):
            with self.assertRaisesRegex(ShapeError, "wizard"):
                checked(estimate_of("t", part), RATES, "e")

    def test_refuses_negative_hours_and_an_estimate_of_no_parts(self) -> None:
        for bad in (estimate_of("t", Part(-1, "senior", "developer")), Estimate("t", [])):
            with self.assertRaises(ShapeError):
                checked(bad, RATES, "e")

    def test_refuses_a_reason_past_280_characters_or_an_empty_one(self) -> None:
        checked(estimate_of("t", Part(1, "senior", "developer", "x" * 280)), RATES, "e")
        for comment in ("x" * 281, ""):
            with self.assertRaises(ShapeError):
                checked(estimate_of("t", Part(1, "senior", "developer", comment)), RATES, "e")

    def test_refuses_a_part_with_no_reason(self) -> None:
        with self.assertRaisesRegex(ShapeError, "part 2: no comment"):
            checked(Estimate("t", [Part(1, "senior", "developer", "why"), Part(1, "junior", "developer")]), RATES, "e")

    def test_takes_a_comment_for_the_whole_from_before_but_never_beside_reasons_on_parts(self) -> None:
        checked(legacy("why", Part(1, "senior", "developer")), RATES, "e")
        with self.assertRaisesRegex(ShapeError, "beside"):
            checked(legacy("why", Part(1, "senior", "developer", "why")), RATES, "e")
        with self.assertRaises(ShapeError):
            checked(legacy("x" * 281, Part(1, "senior", "developer")), RATES, "e")

    def test_adds_its_parts_up_in_senior_hours_by_role_and_grade(self) -> None:
        mixed = estimate_of("t", Part(2, "senior", "developer"), Part(3, "junior", "copywriter"))
        self.assertEqual(senior_hours(mixed, RATES), 2 + 3 * 0.5 * 0.4)

    def test_refuses_a_rate_table_with_a_non_positive_multiplier_or_a_missing_half(self) -> None:
        for text in ('{"roles": {"a": 1}, "grades": {"b": 0}}', '{"roles": {"a": 1}}'):
            with self.assertRaises(ShapeError):
                parse_rates(text)


class WhichCopyWins(unittest.TestCase):
    def test_the_one_set_last(self) -> None:
        self.assertEqual(latest(estimate_of("b"), estimate_of("a")), estimate_of("b"))
        self.assertEqual(latest(None, estimate_of("a")), estimate_of("a"))
        self.assertIsNone(latest(None, None))


class RowsCarryTheirEstimate(unittest.TestCase):
    def test_a_row_with_an_estimate_parses_back_to_itself(self) -> None:
        row = replace(ROW, estimate=estimate_of("a", Part(1, "junior", "developer"), Part(2, "senior", "copywriter")))
        self.assertEqual(parse_session_cost(json.dumps(to_json(row))), row)

    def test_a_row_from_before_estimates_reads_as_having_none(self) -> None:
        row = to_json(ROW)
        del row["estimate"]
        self.assertIsNone(parse_session_cost(json.dumps(row)).estimate)

    def test_a_part_missing_its_role_is_refused(self) -> None:
        with self.assertRaisesRegex(ShapeError, "role"):
            parse_estimate({"at": "a", "parts": [{"hours": 1, "grade": "junior", "comment": "c"}]}, "row")

    def test_a_row_from_before_reasons_on_parts_reads_with_its_comment_for_the_whole(self) -> None:
        old = {"at": "a", "parts": [{"hours": 1, "grade": "junior", "role": "qa"}], "comment": "why"}
        self.assertEqual(parse_estimate(old, "row"), legacy("why", Part(1, "junior", "qa")))


class SplittingACommentFromBefore(unittest.TestCase):
    QA = Part(0.5, "junior", "qa")
    PROMPTER = Part(1, "middle", "prompter")

    def test_moves_each_labelled_reason_onto_its_part_in_any_order(self) -> None:
        split = split_comment(
            legacy("middle prompter: two clauses; each a judgement; junior qa: routine re-runs.", self.QA, self.PROMPTER)
        )
        self.assertEqual(
            split,
            Estimate(
                "a",
                [replace(self.QA, comment="routine re-runs."), replace(self.PROMPTER, comment="two clauses; each a judgement")],
            ),
        )

    def test_leaves_a_comment_whose_placing_would_be_a_guess(self) -> None:
        for comment, parts in (
            ("Ledger reshaped into parts: rate table, CLI, docs.", (self.QA,)),
            ("junior qa: re-runs", (self.QA, self.PROMPTER)),
            ("junior qa: re-runs; senior qa: more re-runs", (self.QA,)),
            ("junior qa: one; junior qa: two", (self.QA, replace(self.QA, hours=2))),
            ("junior qa:", (self.QA,)),
        ):
            with self.subTest(comment):
                self.assertIsNone(split_comment(legacy(comment, *parts)))

    def test_has_nothing_to_split_where_the_parts_carry_their_reasons(self) -> None:
        self.assertIsNone(split_comment(estimate_of("a")))


class TheReportsRead(unittest.TestCase):
    def setUp(self) -> None:
        # Under the repo's `tmp/`, where `write_atomic` stages, as in test_totals.
        (ROOT / "tmp").mkdir(exist_ok=True)
        base = tempfile.TemporaryDirectory(dir=ROOT / "tmp")
        self.addCleanup(base.cleanup)
        self.row = Path(base.name) / "row.json"

    def written(self, estimate: Estimate) -> str:
        self.row.write_text(row_text(replace(ROW, estimate=estimate)), encoding="utf-8")
        return self.row.read_text(encoding="utf-8")

    def test_rewrites_a_row_whose_comment_splits_and_says_so(self) -> None:
        self.written(legacy("junior qa: routine", Part(1, "junior", "qa")))
        row, changes = read_row(self.row)
        self.assertEqual(changes, ["split the estimate's comment onto its parts"])
        on_disk = parse_session_cost(self.row.read_text(encoding="utf-8"))
        self.assertEqual(on_disk, row)
        self.assertEqual(on_disk.estimate, Estimate("a", [Part(1, "junior", "qa", "routine")]))

    def test_leaves_a_row_whose_comment_does_not_split_as_it_was(self) -> None:
        before = self.written(legacy("a summary of the work", Part(1, "junior", "qa")))
        _, changes = read_row(self.row)
        self.assertEqual(changes, [])
        self.assertEqual(self.row.read_text(encoding="utf-8"), before)


class TheReportsRatio(unittest.TestCase):
    def test_divides_summed_spend_by_summed_hours_rather_than_averaging_ratios(self) -> None:
        tiny = replace(
            ROW,
            total=Tally(responses=1, cost_usd=5),
            estimate=estimate_of("a", Part(0.1, "junior", "copywriter")),
        )
        big = replace(ROW, estimate=estimate_of("a", Part(4, "senior", "copywriter")))
        summary = effort_of([tiny, big], RATES)
        # $15 over 2.02 senior-hours; a mean of the two ratios would be $127.50.
        self.assertEqual(summary.overall.usd_per_senior_hour, round(15 / 2.02, 4))

    def test_counts_rows_with_no_estimate_without_rating_them(self) -> None:
        summary = effort_of([ROW, replace(ROW, estimate=estimate_of("a"))], RATES)
        self.assertEqual((summary.estimated, summary.rows, summary.overall.cost_usd), (1, 2, 10))

    def test_files_a_session_by_week_day_and_the_model_that_spent_most_of_it(self) -> None:
        self.assertEqual(main_model(ROW), "claude-opus-5-5")
        summary = effort_of([replace(ROW, estimate=estimate_of("a"))], RATES)
        self.assertEqual(list(summary.by_model_month), ["claude-opus-5-5 2026-03"])
        self.assertEqual(list(summary.by_week), ["2026-W10"])
        self.assertEqual(list(summary.by_day), ["2026-03-04"])

    def test_has_no_ratio_where_the_estimate_adds_up_to_no_hours(self) -> None:
        summary = effort_of([replace(ROW, estimate=estimate_of("a", Part(0, "senior", "developer")))], RATES)
        self.assertIsNone(summary.overall.usd_per_senior_hour)

    def test_raises_on_an_estimate_the_rate_table_refuses(self) -> None:
        with self.assertRaises(ShapeError):
            effort_of([replace(ROW, estimate=estimate_of("a", Part(1, "wizard", "developer")))], RATES)


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
        pending_estimate_path(self.running).unlink(missing_ok=True)

    def test_a_running_session_s_estimate_waits_under_tmp_for_its_row(self) -> None:
        done = estimate(
            "set", "--part", "3", "senior", "developer", "a reason", "--part", "1", "junior", "editor", " another ",
            session=self.running,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        pending = pending_estimate_path(self.running)
        self.assertTrue(pending.is_relative_to(ROOT / "tmp"))
        written = parse_estimate(json.loads(pending.read_text(encoding="utf-8")), "pending")
        assert written is not None
        self.assertEqual(
            written,
            Estimate(written.at, [Part(3, "senior", "developer", "a reason"), Part(1, "junior", "editor", "another")]),
        )

    def test_a_later_set_replaces_the_estimate_whole(self) -> None:
        for hours in ("3", "5"):
            estimate("set", "--part", hours, "senior", "developer", "why", session=self.running)
        written = parse_estimate(json.loads(pending_estimate_path(self.running).read_text(encoding="utf-8")), "p")
        assert written is not None
        self.assertEqual(written.parts, [Part(5, "senior", "developer", "why")])

    def test_another_session_s_estimate_lands_in_its_committed_row(self) -> None:
        done = estimate(
            "set", "--part", "1", "junior", "developer", "after the fact", "--session", self.finished,
            session=self.running,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        row = parse_session_cost(self.row.read_text(encoding="utf-8"))
        assert row.estimate is not None
        self.assertEqual(row.estimate.parts, [Part(1, "junior", "developer", "after the fact")])
        self.assertFalse(pending_estimate_path(self.running).exists())

    def test_a_refused_estimate_writes_nothing(self) -> None:
        done = estimate("set", "--part", "1", "wizard", "developer", "x", session=self.running)
        self.assertEqual(done.returncode, 1)
        self.assertIn("wizard", done.stderr)
        self.assertFalse(pending_estimate_path(self.running).exists())

    def test_a_part_without_its_reason_is_refused_whatever_else_is_given(self) -> None:
        done = estimate("set", "a reason for the whole", "--part", "1", "senior", "developer", session=self.running)
        self.assertEqual(done.returncode, 2)
        self.assertFalse(pending_estimate_path(self.running).exists())

    def test_a_session_with_no_row_is_refused_rather_than_guessed_at(self) -> None:
        done = estimate("show", "--session", "no-such-session", session=self.running)
        self.assertEqual(done.returncode, 1)


if __name__ == "__main__":
    unittest.main()
