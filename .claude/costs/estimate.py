#!/usr/bin/env python3
"""Set or show a session's human-hour estimate.

Usage:
  python3 .claude/costs/estimate.py set --part <hours> <grade> <role> <why> [--part ...] [--session <id>]
  python3 .claude/costs/estimate.py show [--session <id>]
  python3 .claude/costs/estimate.py rates
  python3 .claude/costs/estimate.py role set <name> <multiplier> <grade> <work>
  python3 .claude/costs/estimate.py role drop <name>

Each `--part` is the hours one role at one grade would spend on the task, and
why that role, at that grade, for those hours; the parts add up to the
estimate, and `set` replaces the whole of it. `rates` prints the table an
estimate is checked against as JSON — `rates.json` plus the roles this
repository's `rates.repo.json` on the `cost-ledger` branch adds, each at its one
grade, and a note per role both rate. `role set` adds a role there or re-rates
one, and `role drop` removes one; both push. Without
`--session` the session is this one, read off `CLAUDE_CODE_SESSION_ID`: the
estimate goes to `tmp/estimates/<id>.json`, and the row folds it in when the
turn ends. Another session's id edits that session's row on the `cost-ledger`
branch, pushing it, and any copy of it in the tree, which is a change to commit
like any other.

Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Tuple

from lib.estimate_model import Estimate, Part, Rates, checked, senior_hours, latest, role_change, shadow_notes
from lib.ledger_branch import (
    BRANCH,
    RATES_ON_LEDGER,
    RATES_PATH,
    REMOTE_REF,
    LedgerError,
    append,
    append_row,
    fetch,
    latest_row,
    ledger_rates,
    rates_text,
    rows_at,
    shared_rates,
)
from lib.rows import ROOT, SESSIONS, SessionCost, place_tree_copy, read_pending_estimate, reshape, row_text, tree_copies, write_pending_estimate
from lib.shape import ShapeError, to_json

def describe(estimate: Optional[Estimate], rates: Rates) -> str:
    if estimate is None:
        return "no estimate yet"
    parts = " + ".join(f"{part.hours:g} h {part.label}" for part in estimate.parts)
    reasons = estimate.comment or "; ".join(f"{part.label}: {part.comment}" for part in estimate.parts)
    return f"{parts} = {senior_hours(estimate, rates):g} senior-hours — {reasons}"


def parts_of(raw: List[List[str]]) -> List[Part]:
    parts = []
    for hours, grade, role, why in raw:
        try:
            parts.append(Part(hours=float(hours), grade=grade, role=role, comment=why.strip()))
        except ValueError as error:
            raise ShapeError(f"`--part {hours} {grade} {role}`: hours are not a number") from error
    return parts


def edit(row: SessionCost) -> None:
    """The ledger takes the edited row, and the tree's copy, where there is
    one, is rewritten to match at the path the ledger filed it at."""
    text = row_text(row)
    filed = ROOT / append_row(text)
    if tree_copies(row.session_id):
        place_tree_copy(filed, text, row.session_id)


def booking(tip: Optional[str], role: str) -> List[str]:
    """The sessions whose ledger rows at `tip` book a part under `role`."""
    rows = (reshape(text, f"{BRANCH}:{path}")[0] for path, text in rows_at(tip)) if tip else ()
    return [row.session_id for row in rows if row.estimate and any(p.role == role for p in row.estimate.parts)]


def push_role(name: str, entry: Optional[Mapping[str, Any]]) -> Optional[str]:
    """`role set` where `entry` is given, `role drop` where it is None. A drop
    is refused while a ledger row books the role and the shared table does not
    rate it, so every role a row names stays rateable."""
    shared = shared_rates()

    def plan(tip: Optional[str]) -> Tuple[Dict[str, Optional[str]], str]:
        before = rates_text(tip)
        if entry is None and name not in shared.roles:
            booked = booking(tip, name)
            if booked:
                raise ShapeError(f"{RATES_ON_LEDGER}: `{name}` is booked by {len(booked)} ledger row(s), {booked[0]} first")
        text, message = role_change(shared, before, name, entry, RATES_ON_LEDGER)
        return ({} if text == before else {RATES_PATH: text}), message

    return append(plan)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    role = commands.add_parser("role").add_subparsers(dest="action", required=True)
    setting_role = role.add_parser("set")
    setting_role.add_argument("name")
    setting_role.add_argument("multiplier", type=float)
    setting_role.add_argument("grade")
    setting_role.add_argument("work")
    role.add_parser("drop").add_argument("name")
    setting = commands.add_parser("set")
    setting.add_argument(
        "--part",
        nargs=4,
        action="append",
        required=True,
        metavar=("HOURS", "GRADE", "ROLE", "WHY"),
        help="WHY: why this role, at this grade, for these hours; not a summary of the work",
    )
    showing = commands.add_parser("show")
    for command in (setting, showing):
        command.add_argument("--session", help="another session's id; this one's by default")
    commands.add_parser("rates")
    args = parser.parse_args()

    try:
        if args.command == "role":
            entry = None
            if args.action == "set":
                entry = {"multiplier": args.multiplier, "grade": args.grade, "work": args.work}
            built = push_role(args.name, entry)
            print(f"estimate: {BRANCH} {'already holds that' if built is None else f'updated in {built[:7]}'}")
            return 0
        # The local copy of the ledger, so a prompt's notice makes no network
        # call; a role it does not rate is fetched for before being refused.
        rates = ledger_rates(REMOTE_REF)
        if args.command == "set" and any(part.role not in rates.roles for part in parts_of(args.part)):
            fetch()
            rates = ledger_rates(REMOTE_REF)
    except (ShapeError, LedgerError) as error:
        print(f"estimate: {error}", file=sys.stderr)
        return 1
    if args.command == "rates":
        print(json.dumps({**to_json(rates), "notes": shadow_notes(rates, "This repository")}, ensure_ascii=False))
        return 0

    current = os.environ.get("CLAUDE_CODE_SESSION_ID")
    session_id: Optional[str] = args.session or current
    if session_id is None:
        print("estimate: no CLAUDE_CODE_SESSION_ID; name the session with --session", file=sys.stderr)
        return 1
    running = session_id == current

    try:
        # A running session's ledger copy is the one its last turn fetched;
        # another session's is edited on the ledger's tip.
        if not running:
            fetch()
        row = latest_row(session_id)
        if not running and row is None:
            print(f"estimate: no row for session {session_id} under {SESSIONS} or on {BRANCH}", file=sys.stderr)
            return 1
        pending = read_pending_estimate(session_id) if running else None
        if args.command == "set":
            pending = checked(
                Estimate(
                    at=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                    parts=parts_of(args.part),
                ),
                rates,
                "the estimate",
            )
            if running:
                write_pending_estimate(session_id, pending)
            else:
                assert row is not None
                row.estimate = pending
                edit(row)
        estimate = latest(row.estimate if row is not None else None, pending)
    except (ShapeError, LedgerError) as error:
        print(f"estimate: {error}", file=sys.stderr)
        return 1

    print(f"estimate for {session_id}: {describe(estimate, rates)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
