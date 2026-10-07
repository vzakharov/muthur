"""A period's estimated hours as a team would bill them: plain hours by role
and grade, not senior-hours, so a junior's hour reads as an hour."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Tuple

from lib.estimate import Rates
from lib.period import Period
from lib.rows import SessionCost


@dataclass
class HoursTable:
    period: str
    estimated: int
    rows: int
    # Only what was estimated, each in `rates.json`'s order.
    grades: List[str]
    by_role: Dict[str, Dict[str, float]]


def _ordered(keys: Iterable[str], order: Mapping[str, float]) -> List[str]:
    ranks = {key: rank for rank, key in enumerate(order)}
    return sorted(set(keys), key=lambda key: (ranks.get(key, len(ranks)), key))


def hours_of(rows: Iterable[SessionCost], rates: Rates, period: Period) -> HoursTable:
    """Over the rows that started in `period`. The rows given may span other
    periods, so one with no start date, which no period can place, is left out."""
    inside = [row for row in rows if row.first_response_at is not None and period.holds(row)]
    cells: Dict[Tuple[str, str], float] = {}
    for row in inside:
        for part in row.estimate.parts if row.estimate is not None else []:
            cells[(part.role, part.grade)] = cells.get((part.role, part.grade), 0.0) + part.hours
    grades = _ordered((grade for _, grade in cells), rates.grades)
    return HoursTable(
        period=period.label,
        estimated=sum(1 for row in inside if row.estimate is not None),
        rows=len(inside),
        grades=grades,
        by_role={
            role: {grade: round(cells[(role, grade)], 2) for grade in grades if (role, grade) in cells}
            for role in _ordered((role for role, _ in cells), rates.roles)
        },
    )
