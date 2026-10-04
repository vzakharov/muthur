"""A session's human-hour estimate: the task broken into parts, each hours of one
role at one grade, with one reason for the whole, converted to senior-hours only
when read. `.claude/costs/CLAUDE.md` § "Human-hour estimates" carries why, and
what the figure measures.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from lib.shape import ShapeError, is_number, read_number, read_object, read_string, required

COMMENT_LIMIT = 280


@dataclass(frozen=True)
class Part:
    hours: float
    grade: str
    role: str


@dataclass
class Estimate:
    # UTC, ISO 8601: when it was last set, which decides between two copies of it.
    at: str
    parts: List[Part]
    comment: str


@dataclass(frozen=True)
class Rates:
    """Multipliers against an hour of the reference role at the reference
    grade — each table's `1` — which is what a senior-hour is."""

    roles: Dict[str, float]
    grades: Dict[str, float]


def _multipliers(table: Optional[Dict[str, Any]], where: str) -> Dict[str, float]:
    if not table:
        raise ShapeError(f"{where}: not a non-empty object")
    for name, multiplier in table.items():
        if not is_number(multiplier) or multiplier <= 0:
            raise ShapeError(f"{where}: `{name}` is not a positive multiplier")
    return table


def parse_rates(text: str, where: str = "rates.json") -> Rates:
    rates = json.loads(text)
    if not isinstance(rates, dict):
        raise ShapeError(f"{where}: not an object")
    return Rates(
        roles=_multipliers(read_object(rates, "roles", where), f"{where} roles"),
        grades=_multipliers(read_object(rates, "grades", where), f"{where} grades"),
    )


def checked(estimate: Estimate, rates: Rates, where: str) -> Estimate:
    """Holds at both ends: `estimate.py` refuses to write a bad estimate, and the
    report refuses a row edited by hand into one."""
    if not estimate.parts:
        raise ShapeError(f"{where}: no parts")
    for index, part in enumerate(estimate.parts):
        at = f"{where} part {index + 1}"
        if part.hours < 0:
            raise ShapeError(f"{at}: hours are {part.hours:g}, below zero")
        if part.role not in rates.roles:
            raise ShapeError(f"{at}: role `{part.role}` is not one of {', '.join(rates.roles)} (rates.json)")
        if part.grade not in rates.grades:
            raise ShapeError(f"{at}: grade `{part.grade}` is not one of {', '.join(rates.grades)} (rates.json)")
    if not 0 < len(estimate.comment) <= COMMENT_LIMIT:
        raise ShapeError(
            f"{where}: the comment is {len(estimate.comment)} characters, not 1–{COMMENT_LIMIT}"
        )
    return estimate


def parse_estimate(value: Any, where: str) -> Optional[Estimate]:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ShapeError(f"{where}: not an object")
    parts = value.get("parts")
    if not isinstance(parts, list):
        raise ShapeError(f"{where}: `parts` is not a list")
    read = []
    for index, part in enumerate(parts):
        at = f"{where} parts[{index}]"
        if not isinstance(part, dict):
            raise ShapeError(f"{at}: not an object")
        read.append(
            Part(
                hours=required(read_number, part, "hours", at),
                grade=required(read_string, part, "grade", at),
                role=required(read_string, part, "role", at),
            )
        )
    return Estimate(
        at=required(read_string, value, "at", where),
        parts=read,
        comment=required(read_string, value, "comment", where),
    )


def latest(*estimates: Optional[Estimate]) -> Optional[Estimate]:
    """The copy set last. A row and a running session's pending file can each
    carry one — the file from `estimate.py`, the row from a `--session` edit — and
    whichever was set later is the estimate."""
    present = [estimate for estimate in estimates if estimate is not None]
    return max(present, key=lambda estimate: estimate.at) if present else None


def senior_hours(estimate: Estimate, rates: Rates) -> float:
    return sum(part.hours * rates.roles[part.role] * rates.grades[part.grade] for part in estimate.parts)
