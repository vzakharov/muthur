"""The stretch of time a report covers — a month, an ISO week or a day, named
outright or as `cur` / `prev` from today — and which rows fall inside it.

A row belongs to the period its session **started** in, the rule every bucket
of the report already follows. Rows are stored by month, so a period is also
the months whose directories hold its rows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List

from lib.rows import SessionCost

KINDS = ("month", "week", "day")
RELATIVE = ("cur", "prev")
FORMATS = {
    "month": (re.compile(r"(\d{4})-(\d{2})"), "YYYY-MM"),
    "week": (re.compile(r"(\d{4})-W(\d{2})", re.IGNORECASE), "YYYY-Www"),
    "day": (re.compile(r"(\d{4})-(\d{2})-(\d{2})"), "YYYY-MM-DD"),
}


class PeriodError(ValueError):
    """A period that names no real month, week or day."""


def iso_week(day: date) -> str:
    """The ISO-8601 week a day falls in, `<year>-W<nn>`. The year is the one
    owning that week's Thursday, so the last days of December can read as week
    01 of the next year — the scheme working, not a rounding error."""
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


@dataclass(frozen=True)
class Period:
    label: str
    first: date
    last: date
    whole_month: bool

    def months(self) -> List[str]:
        months = []
        cursor = self.first.replace(day=1)
        while cursor <= self.last:
            months.append(cursor.strftime("%Y-%m"))
            cursor = (cursor + timedelta(days=32)).replace(day=1)
        return months

    def holds(self, row: SessionCost) -> bool:
        """For a row read from one of `months()`. One with no priced response
        has no day, so it counts toward its month and toward no week or day."""
        started = row.first_response_at
        if started is None:
            return self.whole_month
        return self.first <= date.fromisoformat(started[:10]) <= self.last


def month_of(day: date) -> Period:
    following = (day.replace(day=1) + timedelta(days=32)).replace(day=1)
    return Period(day.strftime("%Y-%m"), day.replace(day=1), following - timedelta(days=1), True)


def week_of(day: date) -> Period:
    monday = day - timedelta(days=day.weekday())
    return Period(iso_week(day), monday, monday + timedelta(days=6), False)


def day_of(day: date) -> Period:
    return Period(day.isoformat(), day, day, False)


def period(kind: str, value: str, today: date) -> Period:
    """`cur` is the period holding `today`, `prev` the one before it. Case is
    ignored: the label is printed in ISO's case whatever was typed."""
    relative = value.lower()
    if relative in RELATIVE:
        current = relative == "cur"
        if kind == "month":
            this = month_of(today)
            return this if current else month_of(this.first - timedelta(days=1))
        if kind == "week":
            return week_of(today if current else today - timedelta(days=7))
        return day_of(today if current else today - timedelta(days=1))
    pattern, shape = FORMATS[kind]
    found = pattern.fullmatch(value)
    if found is None:
        raise PeriodError(f"--{kind} {value!r} is not {shape}, cur or prev")
    numbers = [int(group) for group in found.groups()]
    try:
        if kind == "month":
            return month_of(date(numbers[0], numbers[1], 1))
        if kind == "week":
            return week_of(date.fromisocalendar(numbers[0], numbers[1], 1))
        return day_of(date(numbers[0], numbers[1], numbers[2]))
    except ValueError as error:
        raise PeriodError(f"--{kind} {value!r}: {error}") from error
