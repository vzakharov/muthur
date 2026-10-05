"""A session's human-hour estimate: the task broken into parts, each hours of one
role at one grade with the reason for them, converted to senior-hours only when
read. `.claude/costs/CLAUDE.md` § "Human-hour estimates" carries why, and what
the figure measures.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Mapping, Optional

from lib.shape import ShapeError, is_number, read_number, read_object, read_string, required

COMMENT_LIMIT = 280


@dataclass(frozen=True)
class Part:
    hours: float
    grade: str
    role: str
    # Why this role, at this grade, for these hours. Null only on a part of an
    # estimate that carries one comment for the whole.
    comment: Optional[str] = None

    @property
    def label(self) -> str:
        """How a comment for the whole names this part, before its reason."""
        return f"{self.grade} {self.role}"


@dataclass
class Estimate:
    # UTC, ISO 8601: when it was last set, which decides between two copies of it.
    at: str
    parts: List[Part]
    # One reason for the whole, the older shape: `estimate.py` never writes it,
    # and it stays on a row only where `split_comment` cannot place it.
    comment: Optional[str] = None


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
        if estimate.comment is None:
            _check_comment(part.comment, at)
        elif part.comment is not None:
            raise ShapeError(f"{at}: a comment of its own beside the estimate's comment for the whole")
    if estimate.comment is not None:
        _check_comment(estimate.comment, where)
    return estimate


def _check_comment(comment: Optional[str], where: str) -> None:
    if comment is None:
        raise ShapeError(f"{where}: no comment")
    if not 0 < len(comment) <= COMMENT_LIMIT:
        raise ShapeError(f"{where}: the comment is {len(comment)} characters, not 1–{COMMENT_LIMIT}")


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
                comment=read_string(part, "comment", at),
            )
        )
    return Estimate(
        at=required(read_string, value, "at", where),
        parts=read,
        comment=read_string(value, "comment", where),
    )


def split_comment(estimate: Estimate) -> Optional[Estimate]:
    """The estimate with its comment for the whole moved onto its parts, where
    that comment reads `<grade> <role>: <reason>; <grade> <role>: <reason>` —
    the shape the estimate notice asked for — naming each part exactly once.
    None where there is nothing to split, or anything about the split would be a
    guess: an unlabelled comment, a label matching no part or one part twice, a
    part no label names, two parts sharing a label."""
    if estimate.comment is None:
        return None
    labels = [part.label for part in estimate.parts]
    if len(set(labels)) != len(labels):
        return None
    # A `;` inside a reason stays in it unless what follows reads as a label,
    # and then the split refuses rather than guess which it was.
    pieces = re.split(r";\s+(?=[\w-]+ [\w-]+:)", estimate.comment.strip())
    reasons: Dict[str, str] = {}
    for piece in pieces:
        labelled = re.fullmatch(r"([\w-]+ [\w-]+):\s*(\S.*)", piece, re.DOTALL)
        if labelled is None or labelled[1] not in labels or labelled[1] in reasons:
            return None
        reasons[labelled[1]] = labelled[2].rstrip()
    if len(reasons) != len(labels):
        return None
    return replace(
        estimate,
        parts=[replace(part, comment=reasons[label]) for part, label in zip(estimate.parts, labels)],
        comment=None,
    )


def latest(*estimates: Optional[Estimate]) -> Optional[Estimate]:
    """The copy set last. A row and a running session's pending file can each
    carry one — the file from `estimate.py`, the row from a `--session` edit — and
    whichever was set later is the estimate."""
    present = [estimate for estimate in estimates if estimate is not None]
    return max(present, key=lambda estimate: estimate.at) if present else None


def senior_hours(estimate: Estimate, rates: Rates) -> float:
    return sum(part.hours * rates.roles[part.role] * rates.grades[part.grade] for part in estimate.parts)
