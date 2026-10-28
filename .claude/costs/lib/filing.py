"""Where the ledger files a row: `sessions/<YYYY-MM>/<branch>/<N>/<id>.json`.

`<YYYY-MM>` is the month of the branch's first filed session, so a branch never
splits across months, and `<N>` the session's 1-based ordinal on the branch:
one past the highest held, so the gap a moved row leaves is never reused. A
branchless row goes under its own month's `.no-branch/`, a name git forbids as
a ref component. A filed row moves only when its session changes branch.

`refile` brings every row of a ledger listing to its place, and runs on every
ledger write. That pass is the migration from the month-only layout, and what
folds in the rows branches without this code keep writing in it. Its steady
state reads names only: a misplaced row shows in the listing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

from lib.rows import ROOT, SESSIONS, SessionCost, parse_session_cost, union

PREFIX = SESSIONS.relative_to(ROOT).as_posix()
NO_BRANCH = ".no-branch"
MONTH = re.compile(r"\d{4}-\d{2}")
# No leading zero, so an ordinal has one spelling.
ORDINAL = re.compile(r"[1-9]\d*")


@dataclass(frozen=True)
class Place:
    month: str
    # The branch's name, or `NO_BRANCH`.
    folder: str
    ordinal: int

    def path(self, session_id: str) -> str:
        return f"{PREFIX}/{self.month}/{self.folder}/{self.ordinal}/{session_id}.json"


def is_row(path: str) -> bool:
    return path.startswith(f"{PREFIX}/") and path.endswith(".json")


def session_of(path: str) -> str:
    return path.rsplit("/", 1)[-1][: -len(".json")]


def parse_path(path: str) -> Optional[Place]:
    """The place a row path names; None for any other row path, the month-only
    layout among them."""
    parts = path[len(PREFIX) + 1 :].split("/")
    if len(parts) < 4 or not MONTH.fullmatch(parts[0]) or not ORDINAL.fullmatch(parts[-2]):
        return None
    return Place(parts[0], "/".join(parts[1:-2]), int(parts[-2]))


def folder_of(row: SessionCost) -> str:
    return row.branch or NO_BRANCH


def started(row: SessionCost) -> str:
    return row.first_response_at or row.last_response_at or ""


def start_order(row: SessionCost) -> Tuple[str, str]:
    return started(row), row.session_id


def month_started(row: SessionCost) -> str:
    """A row with no response to date it — none priced yet — is this month's."""
    return started(row)[:7] or datetime.now(timezone.utc).strftime("%Y-%m")


@dataclass
class Index:
    """The places already taken."""

    # Each branch's month. `NO_BRANCH` has none: each of its rows goes under
    # its own.
    months: Dict[str, str] = field(default_factory=dict)
    # The session in each ordinal, by month and folder.
    taken: Dict[Tuple[str, str], Dict[int, str]] = field(default_factory=dict)

    def add(self, place: Place, session_id: str) -> None:
        if place.folder != NO_BRANCH:
            self.months.setdefault(place.folder, place.month)
        self.taken.setdefault((place.month, place.folder), {})[place.ordinal] = session_id

    def free(self, place: Place, session_id: str) -> bool:
        """Whether `session_id` can hold `place` without a second month for
        its branch or a second session in its ordinal."""
        month = self.months.get(place.folder, place.month)
        holder = self.taken.get((place.month, place.folder), {}).get(place.ordinal, session_id)
        return month == place.month and holder == session_id

    def next_place(self, row: SessionCost) -> Place:
        folder = folder_of(row)
        month = month_started(row) if folder == NO_BRANCH else self.months.get(folder) or month_started(row)
        held = self.taken.get((month, folder), {})
        return Place(month, folder, max(held, default=0) + 1)


@dataclass
class Filing:
    # Path to its new text, or to None for a copy removed.
    changes: Dict[str, Optional[str]] = field(default_factory=dict)
    # Where each re-filed session's row sits after the changes.
    placed: Dict[str, str] = field(default_factory=dict)


Read = Callable[[str], str]


def _contested(settled: Dict[str, Place], row_at: Callable[[str, Place], SessionCost]) -> Set[str]:
    """The sessions whose place another one's makes wrong, read only where
    there is such a pair: a branch under two months keeps the earliest, and
    two sessions in one ordinal leave it to the one that started first."""
    months: Dict[str, Set[str]] = {}
    for place in settled.values():
        if place.folder != NO_BRANCH:
            months.setdefault(place.folder, set()).add(place.month)
    contested = {
        session for session, place in settled.items() if place.folder in months and place.month != min(months[place.folder])
    }
    sharing: Dict[Place, List[str]] = {}
    for session, place in settled.items():
        if session not in contested:
            sharing.setdefault(place, []).append(session)
    for place, sessions in sharing.items():
        if len(sessions) > 1:
            first = min(sessions, key=lambda session: start_order(row_at(session, place)))
            contested.update(session for session in sessions if session != first)
    return contested


def refile(listing: Sequence[str], read: Read, incoming: Sequence[str] = ()) -> Filing:
    """The changes that file `incoming` — row texts that replace every held
    copy of their sessions — and bring every other row of `listing` to its
    place, and where each row they touch ends up. `read` gives a listed path's
    text, and is called only for a row that has to move or be compared. A pass
    over its own result changes nothing."""
    texts: Dict[str, str] = {}

    def text_of(path: str) -> str:
        if path not in texts:
            texts[path] = read(path)
        return texts[path]

    def row_of(path: str) -> SessionCost:
        return parse_session_cost(text_of(path), path)

    copies: Dict[str, List[str]] = {}
    for path in listing:
        if is_row(path):
            copies.setdefault(session_of(path), []).append(path)
    given = {row.session_id: (text, row) for text in incoming for row in [parse_session_cost(text, "incoming row")]}
    moving = set(given) | {s for s, paths in copies.items() if len(paths) > 1 or parse_path(paths[0]) is None}
    settled = {s: place for s, paths in copies.items() if s not in moving for place in [parse_path(paths[0])] if place}
    moving |= _contested(settled, lambda s, place: row_of(place.path(s)))

    index = Index()
    for session, place in settled.items():
        if session not in moving:
            index.add(place, session)

    def winner(session: str) -> Tuple[str, SessionCost]:
        if session in given:
            return given[session]
        held = [(text_of(path), row_of(path)) for path in copies[session]]
        return union(held, lambda item: item[1])[0]

    rows = {session: winner(session) for session in moving}
    order = sorted(moving, key=lambda s: start_order(rows[s][1]))
    # A row keeps a place it already holds before any row takes a new one, so
    # a new ordinal never lands on one a moving row could have kept.
    places: Dict[str, Place] = {}
    for session in order:
        for place in map(parse_path, copies.get(session, [])):
            if place is not None and place.folder == folder_of(rows[session][1]) and index.free(place, session):
                places[session] = place
                index.add(place, session)
                break
    for session in order:
        if session not in places:
            places[session] = index.next_place(rows[session][1])
            index.add(places[session], session)

    filing = Filing()
    for session in order:
        text, held, path = rows[session][0], copies.get(session, []), places[session].path(session)
        filing.placed[session] = path
        filing.changes.update({old: None for old in held if old != path})
        if path not in held or text_of(path) != text:
            filing.changes[path] = text
    return filing
