#!/usr/bin/env python3
"""The human-hour estimate: what one may hold, which of a row's copy and a
running session's pending one wins, what `estimate.py` writes where, and the
ratio the report draws from them.

Run by path (`python3 .claude/costs/test_estimate.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `lib`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from lib.estimate_model import (
    AddedRole,
    Estimate,
    Part,
    Rates,
    checked,
    latest,
    parse_estimate,
    parse_rates,
    role_change,
    senior_hours,
    shadow_notes,
    split_comment,
    with_added_roles,
)
from lib.ledger_branch import BRANCH, RATES_ON_LEDGER, RATES_PATH
from lib.rows import ROOT, SessionCost, parse_session_cost, read_row, row_text
from lib.shape import ShapeError, to_json
from lib.tally import Tally
from lib.totals import effort_of, main_model
from hook_clone import Clone

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


def adding(**roles: object) -> str:
    return json.dumps({"roles": roles})


ARTIST = {"multiplier": 0.9, "grade": "senior", "work": "a persona's reflections on songs"}


def ledger_table(clone: Clone) -> object:
    return json.loads(clone.git("show", f"origin/{RATES_ON_LEDGER}"))


class RolesARepositoryAdds(unittest.TestCase):
    def test_join_the_shared_table_at_their_multiplier_and_their_one_grade(self) -> None:
        rates = with_added_roles(RATES, adding(artist=ARTIST))
        self.assertEqual(rates.roles, {**RATES.roles, "artist": 0.9})
        self.assertEqual(rates.grades, RATES.grades)
        self.assertEqual(rates.added, {"artist": AddedRole("senior", "a persona's reflections on songs")})

    def test_book_at_their_grade_alone_and_land_in_its_hours(self) -> None:
        rates = with_added_roles(RATES, adding(artist=ARTIST))
        booked = estimate_of("t", Part(2, "senior", "artist"))
        self.assertEqual(senior_hours(checked(booked, rates, "e"), rates), 2 * 0.9)
        with self.assertRaisesRegex(ShapeError, "part 1: role `artist` is booked at `senior` only"):
            checked(estimate_of("t", Part(2, "junior", "artist")), rates, "e")

    def test_keep_their_multiplier_once_the_shared_table_takes_them_up_and_say_so(self) -> None:
        rates = with_added_roles(RATES, adding(copywriter=ARTIST))
        self.assertEqual((rates.roles["copywriter"], rates.shadowed), (0.9, {"copywriter": 0.5}))
        (note,) = shadow_notes(rates, "a/repo")
        self.assertIn("a/repo: `copywriter` is rated ×0.9 by its own table and ×0.5 by rates.json", note)
        self.assertIn("`estimate.py role drop copywriter`", note)
        self.assertEqual(shadow_notes(with_added_roles(RATES, adding(artist=ARTIST)), "a/repo"), [])

    def test_refuse_a_grade_the_shared_table_lacks_and_anything_but_roles(self) -> None:
        for text, message in (
            (adding(artist={**ARTIST, "grade": "wizard"}), "grade `wizard`"),
            (json.dumps({"roles": {"artist": ARTIST}, "grades": {"wizard": 2}}), "only adds roles, not grades"),
            (adding(artist={k: v for k, v in ARTIST.items() if k != "grade"}), "exactly multiplier, grade, work"),
            (adding(artist={**ARTIST, "multiplier": 0}), "not positive"),
            (adding(artist={**ARTIST, "work": " "}), "`work` is 0 characters"),
            (adding(), "not a non-empty object"),
            ("{", "not JSON"),
        ):
            with self.subTest(message), self.assertRaisesRegex(ShapeError, message):
                with_added_roles(RATES, text)

    def test_rate_a_row_by_its_own_repository_s_table(self) -> None:
        artist = replace(ROW, session_id="art", estimate=estimate_of("a", Part(1, "senior", "artist")))
        rates = with_added_roles(RATES, adding(artist=ARTIST))
        summary = effort_of([artist, replace(ROW, estimate=estimate_of("a"))], RATES, {"art": rates})
        self.assertEqual(summary.overall.senior_hours, round(0.9 + 2 * 0.5, 2))
        with self.assertRaisesRegex(ShapeError, "role `artist`"):
            effort_of([artist], RATES)

    def test_rate_a_shadowed_role_by_its_own_table_in_its_repository_and_the_shared_one_elsewhere(self) -> None:
        shared = replace(RATES, roles={**RATES.roles, "artist": 1.2})
        own = replace(ROW, session_id="own", estimate=estimate_of("a", Part(1, "senior", "artist")))
        other = replace(ROW, session_id="other", estimate=estimate_of("a", Part(1, "senior", "artist")))
        summary = effort_of([own, other], shared, {"own": with_added_roles(shared, adding(artist=ARTIST))})
        self.assertEqual(summary.overall.senior_hours, round(0.9 + 1.2, 2))


class ChangingARepositorysTable(unittest.TestCase):
    def test_a_role_set_onto_no_table_starts_one_and_names_the_change(self) -> None:
        text, message = role_change(RATES, None, "artist", ARTIST, "t")
        assert text is not None
        self.assertEqual(json.loads(text), {"roles": {"artist": ARTIST}})
        self.assertEqual(message, "chore: estimate role artist ×0.9 at senior")

    def test_a_role_set_again_is_re_rated_and_the_others_kept(self) -> None:
        before = adding(artist=ARTIST, tutor={**ARTIST, "work": "lessons"})
        text, _ = role_change(RATES, before, "artist", {**ARTIST, "multiplier": 1.2}, "t")
        assert text is not None
        self.assertEqual(json.loads(text)["roles"], {"artist": {**ARTIST, "multiplier": 1.2}, "tutor": {**ARTIST, "work": "lessons"}})

    def test_dropping_the_last_role_leaves_no_table(self) -> None:
        self.assertEqual(role_change(RATES, adding(artist=ARTIST), "artist", None, "t"), (None, "chore: drop estimate role artist"))

    def test_refuses_a_shared_role_a_bad_entry_and_a_drop_of_nothing(self) -> None:
        for name, entry, message in (
            ("copywriter", ARTIST, "rates.json rates this role already"),
            ("artist", {**ARTIST, "grade": "wizard"}, "grade `wizard`"),
            ("tutor", None, "no role `tutor` to drop"),
        ):
            with self.subTest(message), self.assertRaisesRegex(ShapeError, message):
                role_change(RATES, adding(artist=ARTIST), name, entry, "t")


class WhichCopyWins(unittest.TestCase):
    def test_the_one_set_last(self) -> None:
        self.assertEqual(latest(estimate_of("b"), estimate_of("a")), estimate_of("b"))
        self.assertEqual(latest(None, estimate_of("a")), estimate_of("a"))
        self.assertIsNone(latest(None, None))


class RowsCarryTheirEstimate(unittest.TestCase):
    def test_a_row_with_an_estimate_parses_back_to_itself(self) -> None:
        row = replace(ROW, estimate=estimate_of("a", Part(1, "junior", "developer"), Part(2, "senior", "copywriter")))
        self.assertEqual(parse_session_cost(json.dumps(to_json(row))), row)

    def test_a_row_is_written_opening_on_its_total_then_its_estimate_and_orientation(self) -> None:
        row = replace(ROW, estimate=estimate_of("a"))
        written = row_text(row)
        self.assertEqual(list(json.loads(written))[:3], ["total", "estimate", "orientation"])
        self.assertEqual(parse_session_cost(written), row)

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


class TheCommand(unittest.TestCase):
    """`estimate.py` run in a clone with a bare `origin`, since editing another
    session's row pushes it to that origin's ledger."""

    running = "running-session"
    finished = "finished-session"
    path = ".claude/costs/sessions/2026-03/a-branch/1/finished-session.json"
    month_only = ".claude/costs/sessions/2026-03/finished-session.json"

    def setUp(self) -> None:
        self.base = Path(tempfile.mkdtemp())
        self.clone = Clone(self.base)

    def tearDown(self) -> None:
        shutil.rmtree(self.base)

    def estimate(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.clone.root / ".claude" / "costs" / "estimate.py"), *args],
            env={**self.clone.env(), "CLAUDE_CODE_SESSION_ID": self.running},
            capture_output=True,
            text=True,
        )

    def pending(self) -> Path:
        return self.clone.root / "tmp" / "estimates" / f"{self.running}.json"

    def ledger_row(self) -> SessionCost:
        text = self.clone.git("show", f"origin/{BRANCH}:{self.path}")
        return parse_session_cost(text)

    def test_a_running_session_s_estimate_waits_under_tmp_for_its_row(self) -> None:
        done = self.estimate(
            "set", "--part", "3", "senior", "developer", "a reason", "--part", "1", "junior", "editor", " another "
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        written = parse_estimate(json.loads(self.pending().read_text(encoding="utf-8")), "pending")
        assert written is not None
        self.assertEqual(
            written,
            Estimate(written.at, [Part(3, "senior", "developer", "a reason"), Part(1, "junior", "editor", "another")]),
        )

    def test_a_later_set_replaces_the_estimate_whole(self) -> None:
        for hours in ("3", "5"):
            self.estimate("set", "--part", hours, "senior", "developer", "why")
        written = parse_estimate(json.loads(self.pending().read_text(encoding="utf-8")), "p")
        assert written is not None
        self.assertEqual(written.parts, [Part(5, "senior", "developer", "why")])

    def test_another_session_s_estimate_lands_on_the_ledger_and_the_tree_copy_where_it_is_filed(self) -> None:
        stale = self.clone.root / self.month_only
        stale.parent.mkdir(parents=True)
        stale.write_text(row_text(replace(ROW, session_id=self.finished)), encoding="utf-8")
        done = self.estimate("set", "--part", "1", "junior", "developer", "after the fact", "--session", self.finished)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertFalse(stale.exists())
        tree = self.clone.root / self.path
        for row in (parse_session_cost(tree.read_text(encoding="utf-8")), self.ledger_row()):
            assert row.estimate is not None
            self.assertEqual(row.estimate.parts, [Part(1, "junior", "developer", "after the fact")])
        self.assertFalse(self.pending().exists())

    def test_a_row_only_the_ledger_holds_is_edited_there(self) -> None:
        staged = self.base / "row.json"
        staged.write_text(row_text(replace(ROW, session_id=self.finished)), encoding="utf-8")
        ledger = [sys.executable, str(self.clone.root / ".claude" / "costs" / "ledger.py")]
        subprocess.run([*ledger, "append-row", str(staged)], env=self.clone.env(), check=True)
        done = self.estimate("set", "--part", "2", "senior", "editor", "after the fact", "--session", self.finished)
        self.assertEqual(done.returncode, 0, done.stderr)
        estimate = self.ledger_row().estimate
        assert estimate is not None
        self.assertEqual(estimate.parts, [Part(2, "senior", "editor", "after the fact")])
        self.assertFalse((self.clone.root / self.path).exists())

    def test_a_refused_estimate_writes_nothing(self) -> None:
        done = self.estimate("set", "--part", "1", "wizard", "developer", "x")
        self.assertEqual(done.returncode, 1)
        self.assertIn("wizard", done.stderr)
        self.assertFalse(self.pending().exists())

    def test_a_part_without_its_reason_is_refused_whatever_else_is_given(self) -> None:
        done = self.estimate("set", "a reason for the whole", "--part", "1", "senior", "developer")
        self.assertEqual(done.returncode, 2)
        self.assertFalse(self.pending().exists())

    def test_rates_prints_the_table_estimates_are_checked_against(self) -> None:
        done = self.estimate("rates")
        self.assertEqual(done.returncode, 0, done.stderr)
        shared = parse_rates((COSTS / "rates.json").read_text(encoding="utf-8"))
        self.assertEqual(json.loads(done.stdout), {**to_json(shared), "notes": []})

    def test_role_set_pushes_the_role_to_the_ledger_where_an_estimate_can_book_it(self) -> None:
        done = self.estimate("role", "set", "artist", "0.9", "senior", ARTIST["work"])
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(ledger_table(self.clone), {"roles": {"artist": ARTIST}})
        self.assertEqual(
            self.clone.git("log", "-1", "--format=%s", f"origin/{BRANCH}"), "chore: estimate role artist ×0.9 at senior"
        )
        self.assertFalse((self.clone.root / RATES_PATH).exists())
        booked = self.estimate("set", "--part", "2", "senior", "artist", "why")
        self.assertEqual(booked.returncode, 0, booked.stderr)

    def test_a_role_another_clone_added_is_fetched_for_before_an_estimate_is_refused(self) -> None:
        self.estimate("role", "set", "artist", "0.9", "senior", ARTIST["work"])
        self.clone.git("update-ref", "-d", f"refs/remotes/origin/{BRANCH}")
        done = self.estimate("set", "--part", "2", "senior", "artist", "why")
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_role_set_refuses_a_role_the_shared_table_rates(self) -> None:
        done = self.estimate("role", "set", "copywriter", "0.9", "senior", "w")
        self.assertEqual(done.returncode, 1)
        self.assertIn("rates.json rates this role already", done.stderr)
        self.assertEqual(self.clone.origin_git("branch", "--list", BRANCH), "")

    def test_role_drop_removes_the_table_with_its_last_role(self) -> None:
        self.estimate("role", "set", "artist", "0.9", "senior", ARTIST["work"])
        done = self.estimate("role", "drop", "artist")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertNotIn(RATES_PATH, self.clone.ledger_files())

    def test_role_drop_is_refused_while_a_ledger_row_books_the_role(self) -> None:
        self.estimate("role", "set", "artist", "0.9", "senior", ARTIST["work"])
        staged = self.base / "row.json"
        booked = replace(ROW, session_id=self.finished, estimate=estimate_of("a", Part(1, "senior", "artist")))
        staged.write_text(row_text(booked), encoding="utf-8")
        ledger = [sys.executable, str(self.clone.root / ".claude" / "costs" / "ledger.py")]
        subprocess.run([*ledger, "append-row", str(staged)], env=self.clone.env(), check=True)
        done = self.estimate("role", "drop", "artist")
        self.assertEqual(done.returncode, 1)
        self.assertIn(f"`artist` is booked by 1 ledger row(s), {self.finished} first", done.stderr)
        self.assertEqual(ledger_table(self.clone), {"roles": {"artist": ARTIST}})

    def test_a_session_with_no_row_is_refused_rather_than_guessed_at(self) -> None:
        done = self.estimate("show", "--session", "no-such-session")
        self.assertEqual(done.returncode, 1)
        self.assertIn("no row", done.stderr)


class BackfillCarriesATreeTable(unittest.TestCase):
    """`ledger.py backfill` moving a repository's tree `rates.repo.json` onto the
    ledger, over a clone with a bare `origin`."""

    def setUp(self) -> None:
        self.base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.base)
        self.clone = Clone(self.base)
        self.tree = self.clone.root / RATES_PATH

    def run_costs(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.clone.root / ".claude" / "costs" / script), *args],
            env=self.clone.env(),
            capture_output=True,
            text=True,
        )

    def test_carries_the_tree_s_table_where_the_ledger_has_none_and_nothing_once_they_agree(self) -> None:
        self.tree.write_text(adding(artist=ARTIST), encoding="utf-8")
        done = self.run_costs("ledger.py", "backfill", "HEAD")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("carried in", done.stdout)
        self.assertEqual(ledger_table(self.clone), {"roles": {"artist": ARTIST}})
        again = self.run_costs("ledger.py", "backfill", "HEAD")
        self.assertIn("nothing to carry", again.stdout)

    def test_stops_naming_the_roles_where_the_tree_and_the_ledger_differ(self) -> None:
        self.run_costs("estimate.py", "role", "set", "artist", "0.9", "senior", ARTIST["work"])
        self.tree.write_text(adding(artist={**ARTIST, "multiplier": 1.2}), encoding="utf-8")
        done = self.run_costs("ledger.py", "backfill", "HEAD")
        self.assertEqual(done.returncode, 1)
        self.assertIn("they differ on `artist`", done.stderr)
        self.assertEqual(ledger_table(self.clone), {"roles": {"artist": ARTIST}})


if __name__ == "__main__":
    unittest.main()
