#!/usr/bin/env python3
"""Where `lib/filing.py` files a row, over a ledger held as a dict of path to
text. What it protects is that every row reaches one place — its branch's
first month, its ordinal by start time — from the month-only layout, a stale
copy, a race or a branch change alike, and that a ledger already in place is
left alone without a row of it being read.

Run by path (`python3 .claude/costs/test_filing.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `lib`.
"""

from __future__ import annotations

import unittest
from typing import Dict, Optional, Sequence

from lib.filing import PREFIX, Place, parse_path, refile
from lib.rows import SessionCost, row_text
from lib.tally import Tally

Ledger = Dict[str, str]


def row(session_id: str, branch: Optional[str], started: str, last: Optional[str] = None) -> str:
    return row_text(
        SessionCost(
            session_id=session_id,
            branch=branch,
            cwd=None,
            opening_prompt=None,
            prs=[],
            url=None,
            operator=None,
            first_response_at=started,
            last_response_at=last or started,
            prices_as_of="2026-01-01",
            claude_code_total_usd=None,
            total=Tally(),
            own_turns=Tally(),
            subagents=Tally(),
            by_rate={},
            warnings=[],
        )
    )


def at(relative: str) -> str:
    return f"{PREFIX}/{relative}"


def unread(path: str) -> str:
    raise AssertionError(f"{path} was read")


def applied(ledger: Ledger, incoming: Sequence[str] = ()) -> Ledger:
    changes = refile(list(ledger), ledger.__getitem__, incoming).changes
    after = {**ledger, **{path: text for path, text in changes.items() if text is not None}}
    return {path: text for path, text in sorted(after.items()) if changes.get(path, "") is not None}


SEP = "2026-09-10T10:00:00.000Z"
OCT = "2026-10-05T10:00:00.000Z"
LATER_OCT = "2026-10-20T10:00:00.000Z"


class Paths(unittest.TestCase):
    def test_a_branch_path_keeps_its_slashes_and_digits(self) -> None:
        self.assertEqual(parse_path(at("2026-10/release/2/3/s.json")), Place("2026-10", "release/2", 3))
        self.assertEqual(Place("2026-10", "claude/foo-a1", 1).path("s"), at("2026-10/claude/foo-a1/1/s.json"))

    def test_the_month_only_layout_and_a_padded_ordinal_are_not_places(self) -> None:
        self.assertIsNone(parse_path(at("2026-10/s.json")))
        self.assertIsNone(parse_path(at("2026-10/b/01/s.json")))
        self.assertIsNone(parse_path(at("b/1/s.json")))


class Migration(unittest.TestCase):
    def test_the_month_only_layout_is_filed_by_branch_month_and_start_order(self) -> None:
        ledger = {
            at("2026-10/c.json"): row("c", "b", LATER_OCT),
            at("2026-09/a.json"): row("a", "b", SEP),
            at("2026-10/b.json"): row("b", "b", OCT),
            at("2026-10/d.json"): row("d", "other", OCT),
        }
        self.assertEqual(
            list(applied(ledger)),
            [at("2026-09/b/1/a.json"), at("2026-09/b/2/b.json"), at("2026-09/b/3/c.json"), at("2026-10/other/1/d.json")],
        )

    def test_branchless_rows_go_under_their_own_month(self) -> None:
        ledger = {at("2026-09/a.json"): row("a", None, SEP), at("2026-10/b.json"): row("b", None, OCT)}
        self.assertEqual(list(applied(ledger)), [at("2026-09/.no-branch/1/a.json"), at("2026-10/.no-branch/1/b.json")])

    def test_a_second_pass_changes_nothing_and_reads_nothing(self) -> None:
        once = applied({at("2026-10/a.json"): row("a", "b", OCT), at("2026-10/b.json"): row("b", None, OCT)})
        self.assertEqual(refile(list(once), unread).changes, {})


class NewRows(unittest.TestCase):
    def test_a_later_session_joins_the_branch_s_first_month(self) -> None:
        ledger = {at("2026-09/b/1/a.json"): row("a", "b", SEP)}
        filing = refile(list(ledger), unread, [row("n", "b", OCT)])
        self.assertEqual(filing.placed, {"n": at("2026-09/b/2/n.json")})

    def test_the_ordinal_follows_the_highest_held_never_a_gap(self) -> None:
        ledger = {at("2026-10/b/1/a.json"): row("a", "b", OCT), at("2026-10/b/3/c.json"): row("c", "b", OCT)}
        self.assertEqual(refile(list(ledger), unread, [row("n", "b", OCT)]).placed["n"], at("2026-10/b/4/n.json"))

    def test_a_session_s_next_row_stays_where_it_is(self) -> None:
        ledger = {at("2026-10/b/1/a.json"): row("a", "b", OCT)}
        newer = row("a", "b", OCT, LATER_OCT)
        filing = refile(list(ledger), ledger.__getitem__, [newer])
        self.assertEqual(filing.changes, {at("2026-10/b/1/a.json"): newer})
        self.assertEqual(refile(list(ledger), ledger.__getitem__, [ledger[at("2026-10/b/1/a.json")]]).changes, {})

    def test_a_branch_change_moves_the_row_and_nothing_else(self) -> None:
        ledger = {at("2026-10/b/1/a.json"): row("a", "b", OCT), at("2026-10/b/2/x.json"): row("x", "b", OCT)}
        renamed = row("a", "c", OCT, LATER_OCT)
        self.assertEqual(
            applied(ledger, [renamed]),
            {at("2026-10/b/2/x.json"): ledger[at("2026-10/b/2/x.json")], at("2026-10/c/1/a.json"): renamed},
        )

    def test_a_row_keeps_its_place_ahead_of_a_new_one_taking_the_next(self) -> None:
        # `y` started first, so it is placed first; `a`'s own place is kept
        # for it all the same, and `y` takes the one after.
        ledger = {
            at("2026-10/b/1/z.json"): row("z", "b", OCT),
            at("2026-10/b/2/a.json"): row("a", "b", LATER_OCT),
            at("2026-10/y.json"): row("y", "b", OCT),
        }
        filing = refile(list(ledger), ledger.__getitem__, [row("a", "b", LATER_OCT, "2026-10-21T00:00:00.000Z")])
        self.assertEqual(filing.placed, {"a": at("2026-10/b/2/a.json"), "y": at("2026-10/b/3/y.json")})


class Healing(unittest.TestCase):
    def test_two_sessions_in_one_ordinal_leave_it_to_the_first_started(self) -> None:
        ledger = {at("2026-10/b/1/x.json"): row("x", "b", LATER_OCT), at("2026-10/b/1/y.json"): row("y", "b", OCT)}
        self.assertEqual(list(applied(ledger)), [at("2026-10/b/1/y.json"), at("2026-10/b/2/x.json")])

    def test_a_branch_under_two_months_keeps_the_earliest(self) -> None:
        ledger = {at("2026-10/b/1/x.json"): row("x", "b", OCT), at("2026-09/b/1/y.json"): row("y", "b", SEP)}
        self.assertEqual(list(applied(ledger)), [at("2026-09/b/1/y.json"), at("2026-09/b/2/x.json")])

    def test_a_stale_branch_s_month_only_copy_folds_into_the_filed_one(self) -> None:
        newer = row("a", "b", OCT, LATER_OCT)
        ledger = {at("2026-10/b/1/a.json"): row("a", "b", OCT), at("2026-10/a.json"): newer}
        self.assertEqual(applied(ledger), {at("2026-10/b/1/a.json"): newer})

    def test_an_older_stale_copy_is_dropped_for_the_filed_one(self) -> None:
        filed = row("a", "b", OCT, LATER_OCT)
        ledger = {at("2026-10/b/1/a.json"): filed, at("2026-10/a.json"): row("a", "b", OCT)}
        self.assertEqual(refile(list(ledger), ledger.__getitem__).changes, {at("2026-10/a.json"): None})


if __name__ == "__main__":
    unittest.main()
