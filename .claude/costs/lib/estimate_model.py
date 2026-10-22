"""A session's human-hour estimate: the task broken into parts, each hours of one
role at one grade with the reason for them, converted to senior-hours only when
read. `.claude/costs/CLAUDE.md` § "Human-hour estimates" carries why, and what
the figure measures.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Mapping, Optional, Tuple

from lib.shape import ShapeError, is_number, read_number, read_object, read_string, required

COMMENT_LIMIT = 280
SHARED_RATES = "rates.json"
REPO_RATES = "rates.repo.json"
ADDED_ROLE_KEYS = ("multiplier", "grade", "work")


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
class AddedRole:
    """A role one repository rates beside the shared table. It is booked at one
    grade only, so its hours land in that grade's column like any other."""

    grade: str
    # The work booked under it, which the estimate notice spells out.
    work: str


@dataclass(frozen=True)
class Rates:
    """Multipliers against an hour of the reference role at the reference
    grade — each table's `1` — which is what a senior-hour is."""

    roles: Dict[str, float]
    grades: Dict[str, float]
    # The roles `rates.repo.json` adds, each in `roles` too at its multiplier.
    added: Dict[str, AddedRole] = field(default_factory=dict)
    # An added role the shared table has since taken up, to the shared
    # multiplier; `roles` keeps the repository's.
    shadowed: Dict[str, float] = field(default_factory=dict)


def _is_multiplier(value: Any) -> bool:
    return is_number(value) and value > 0


def _multipliers(table: Optional[Dict[str, Any]], where: str) -> Dict[str, float]:
    if not table:
        raise ShapeError(f"{where}: not a non-empty object")
    for name, multiplier in table.items():
        if not _is_multiplier(multiplier):
            raise ShapeError(f"{where}: `{name}` is not a positive multiplier")
    return table


def _json_object(text: str, where: str) -> Dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise ShapeError(f"{where}: not JSON ({error})") from error
    if not isinstance(value, dict):
        raise ShapeError(f"{where}: not an object")
    return value


def parse_rates(text: str, where: str = SHARED_RATES) -> Rates:
    rates = _json_object(text, where)
    return Rates(
        roles=_multipliers(read_object(rates, "roles", where), f"{where} roles"),
        grades=_multipliers(read_object(rates, "grades", where), f"{where} grades"),
    )


def _added_role(entry: Any, shared: Rates, at: str) -> Tuple[float, AddedRole]:
    if not isinstance(entry, dict) or sorted(entry) != sorted(ADDED_ROLE_KEYS):
        raise ShapeError(f"{at}: not an object of exactly {', '.join(ADDED_ROLE_KEYS)}")
    multiplier = entry["multiplier"]
    if not _is_multiplier(multiplier):
        raise ShapeError(f"{at}: `multiplier` is not positive")
    grade = required(read_string, entry, "grade", at)
    if grade not in shared.grades:
        raise ShapeError(f"{at}: grade `{grade}` is not one of {', '.join(shared.grades)} ({SHARED_RATES})")
    work = required(read_string, entry, "work", at).strip()
    if not 0 < len(work) <= COMMENT_LIMIT:
        raise ShapeError(f"{at}: `work` is {len(work)} characters, not 1–{COMMENT_LIMIT}")
    return multiplier, AddedRole(grade=grade, work=work)


def added_roles_of(text: str, where: str) -> Dict[str, Any]:
    """The `roles` object of a repository's table. A key it does not know raises
    rather than being ignored, since a `grades` there would otherwise read as a
    grade added."""
    table = _json_object(text, where)
    unknown = sorted(set(table) - {"roles"})
    if unknown:
        raise ShapeError(f"{where}: only adds roles, not {', '.join(unknown)}")
    roles = read_object(table, "roles", where)
    if not roles:
        raise ShapeError(f"{where} roles: not a non-empty object")
    return roles


def with_added_roles(shared: Rates, text: str, where: str = REPO_RATES) -> Rates:
    """The shared table plus the roles a repository's own table adds. A role
    the shared table has since taken up keeps the repository's multiplier and is
    listed in `shadowed`: its rows were booked against that multiplier, so
    switching them to the shared one would re-rate their history."""
    multipliers = dict(shared.roles)
    added: Dict[str, AddedRole] = {}
    shadowed: Dict[str, float] = {}
    for name, entry in added_roles_of(text, where).items():
        multipliers[name], added[name] = _added_role(entry, shared, f"{where} roles `{name}`")
        if name in shared.roles:
            shadowed[name] = shared.roles[name]
    return Rates(roles=multipliers, grades=shared.grades, added=added, shadowed=shadowed)


def checked_new_role(shared: Rates, name: str, entry: Mapping[str, Any], where: str) -> None:
    """A role a repository may add: never one the shared table rates, since
    re-rating it there would re-rate every row booked under it."""
    at = f"{where} roles `{name}`"
    if name in shared.roles:
        raise ShapeError(f"{at}: {SHARED_RATES} rates this role already")
    _added_role(dict(entry), shared, at)


def role_change(
    shared: Rates, before: Optional[str], name: str, entry: Optional[Mapping[str, Any]], where: str
) -> Tuple[Optional[str], str]:
    """The table `before` becomes with `name` set to `entry`, or dropped where
    `entry` is None — None where no role is left — and the commit's message,
    which is how the ledger's log reads as the table's history."""
    roles = dict(added_roles_of(before, where)) if before is not None else {}
    if entry is None:
        if name not in roles:
            raise ShapeError(f"{where}: no role `{name}` to drop")
        del roles[name]
        message = f"chore: drop estimate role {name}"
    else:
        checked_new_role(shared, name, entry, where)
        roles[name] = dict(entry)
        message = f"chore: estimate role {name} ×{entry['multiplier']:g} at {entry['grade']}"
    if not roles:
        return None, message
    text = json.dumps({"roles": roles}, indent=2, ensure_ascii=False) + "\n"
    with_added_roles(shared, text, where)
    return text, message


def shadow_notes(rates: Rates, repo: str) -> List[str]:
    """One line per shadowed role, naming both multipliers and how to adopt the
    shared one."""
    return [
        f"{repo}: `{role}` is rated ×{rates.roles[role]:g} by its own table and ×{shared:g} by {SHARED_RATES};"
        f" its rows keep ×{rates.roles[role]:g} — `estimate.py role drop {role}` adopts the shared rate"
        for role, shared in rates.shadowed.items()
    ]


def checked(estimate: Estimate, rates: Rates, where: str) -> Estimate:
    """Holds at both ends: `estimate.py` refuses to write a bad estimate, and the
    report refuses a row edited by hand into one."""
    if not estimate.parts:
        raise ShapeError(f"{where}: no parts")
    tables = SHARED_RATES if not rates.added else f"{SHARED_RATES}, {REPO_RATES}"
    for index, part in enumerate(estimate.parts):
        at = f"{where} part {index + 1}"
        if part.hours < 0:
            raise ShapeError(f"{at}: hours are {part.hours:g}, below zero")
        if part.role not in rates.roles:
            raise ShapeError(f"{at}: role `{part.role}` is not one of {', '.join(rates.roles)} ({tables})")
        if part.grade not in rates.grades:
            raise ShapeError(f"{at}: grade `{part.grade}` is not one of {', '.join(rates.grades)} ({SHARED_RATES})")
        added = rates.added.get(part.role)
        if added is not None and part.grade != added.grade:
            raise ShapeError(f"{at}: role `{part.role}` is booked at `{added.grade}` only ({REPO_RATES})")
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
