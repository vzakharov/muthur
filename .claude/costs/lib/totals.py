"""Sums the session rows for `report.py` — the same spend by month, by ISO week,
by day, and by the branch that spent it.

Nothing here is written to disk: the totals are wholly derived from the rows,
and a derived file committed beside its own sources is a merge conflict every
branch pays for.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Iterable

from lib.pricing import SessionCost


@dataclass
class Bucket:
    sessions: int = 0
    responses: int = 0
    cost_usd: float = 0.0

    def count(self, row: SessionCost) -> None:
        self.sessions += 1
        self.responses += row.total.responses
        self.cost_usd += row.total.cost_usd


@dataclass
class Totals:
    sessions: int
    responses: int
    cost_usd: float
    by_month: Dict[str, Bucket] = field(default_factory=dict)
    by_week: Dict[str, Bucket] = field(default_factory=dict)
    by_day: Dict[str, Bucket] = field(default_factory=dict)
    by_branch: Dict[str, Bucket] = field(default_factory=dict)


def iso_week(day: date) -> str:
    """The ISO-8601 week a day falls in, `<year>-W<nn>`. The year is the one
    owning that week's Thursday, so the last days of December can read as week
    01 of the next year — the scheme working, not a rounding error."""
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def branch_label(row: SessionCost) -> str:
    """The branch a session's spend is filed under, with the pull requests it
    touched named beside it: the branch says roughly what the work was, the
    numbers are what a reader clicks through to. The spend is the branch's
    rather than each PR's, since a session that touched two would otherwise be
    counted twice."""
    return " ".join([row.branch or "(no branch)", *(f"#{pr}" for pr in row.prs)])


# Rounded where it is written rather than where it is read: a sum of floats
# carries digits no price has, and the output is read by people.
def _rounded(buckets: Dict[str, Bucket]) -> Dict[str, Bucket]:
    return {
        key: Bucket(bucket.sessions, bucket.responses, round(bucket.cost_usd, 4))
        for key, bucket in sorted(buckets.items())
    }


def totals_of(rows: Iterable[SessionCost]) -> Totals:
    """A session is filed under where it **started**, the rule that already picks
    its row's month, so one running past midnight stays whole. A row with no
    priced response has no day to file under and lands in the grand total and
    its branch alone."""
    grand = Bucket()
    by_month: Dict[str, Bucket] = {}
    by_week: Dict[str, Bucket] = {}
    by_day: Dict[str, Bucket] = {}
    by_branch: Dict[str, Bucket] = {}

    for row in rows:
        grand.count(row)
        by_branch.setdefault(branch_label(row), Bucket()).count(row)
        started_at = row.first_response_at
        if started_at is None:
            continue
        by_month.setdefault(started_at[:7], Bucket()).count(row)
        by_week.setdefault(iso_week(date.fromisoformat(started_at[:10])), Bucket()).count(row)
        by_day.setdefault(started_at[:10], Bucket()).count(row)

    return Totals(
        sessions=grand.sessions,
        responses=grand.responses,
        cost_usd=round(grand.cost_usd, 4),
        by_month=_rounded(by_month),
        by_week=_rounded(by_week),
        by_day=_rounded(by_day),
        by_branch=_rounded(by_branch),
    )
