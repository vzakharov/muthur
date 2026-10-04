"""A session's human-hour estimate: hours at a grade with a reason, revised as
the size of the task becomes known.

A revision stores the grade and that grade's hours, never junior-hours:
`grades.json` converts at read time, so a retuned multiplier re-rates the whole
history alike. `.claude/costs/CLAUDE.md` § "Human-hour estimates" carries what
the figure measures.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping

from lib.shape import ShapeError, is_number, read_number, read_string, required

COMMENT_LIMIT = 280


@dataclass(frozen=True)
class Revision:
    # UTC, ISO 8601. It is the revision's identity when two histories merge.
    at: str
    hours: float
    grade: str
    comment: str


def parse_grades(text: str, where: str = "grades.json") -> Dict[str, float]:
    grades = json.loads(text)
    if not isinstance(grades, dict) or not grades:
        raise ShapeError(f"{where}: not a non-empty object")
    for grade, multiplier in grades.items():
        if not is_number(multiplier) or multiplier <= 0:
            raise ShapeError(f"{where}: `{grade}` is not a positive multiplier")
    return grades


def checked(revision: Revision, grades: Mapping[str, float], where: str) -> Revision:
    """Holds at both ends: `estimate.py` refuses to write a bad revision, and a
    row edited by hand is refused when it is read."""
    if revision.hours < 0:
        raise ShapeError(f"{where}: hours are {revision.hours}, below zero")
    if revision.grade not in grades:
        raise ShapeError(
            f"{where}: grade `{revision.grade}` is not one of {', '.join(grades)} (grades.json)"
        )
    if not 0 < len(revision.comment) <= COMMENT_LIMIT:
        raise ShapeError(
            f"{where}: the comment is {len(revision.comment)} characters, not 1–{COMMENT_LIMIT}"
        )
    return revision


def parse_revisions(value: Any, where: str) -> List[Revision]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ShapeError(f"{where}: not a list")
    revisions = []
    for index, item in enumerate(value):
        at = f"{where}[{index}]"
        if not isinstance(item, dict):
            raise ShapeError(f"{at}: not an object")
        revisions.append(
            Revision(
                at=required(read_string, item, "at", at),
                hours=required(read_number, item, "hours", at),
                grade=required(read_string, item, "grade", at),
                comment=required(read_string, item, "comment", at),
            )
        )
    return revisions


def merged(row: Iterable[Revision], pending: Iterable[Revision]) -> List[Revision]:
    """The union of the row's revisions and the ones `estimate.py` left for it,
    oldest first. Where both carry the same moment the row's wins: the script
    only ever appends, so a difference there is a person's edit to the row."""
    by_moment = {revision.at: revision for revision in pending}
    by_moment.update({revision.at: revision for revision in row})
    return sorted(by_moment.values(), key=lambda revision: revision.at)


def junior_hours(revision: Revision, grades: Mapping[str, float]) -> float:
    return revision.hours * grades[revision.grade]
