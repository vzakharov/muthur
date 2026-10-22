#!/usr/bin/env python3
"""Set or show a session's human-hour estimate.

Usage:
  python3 .claude/costs/estimate.py set --part <hours> <grade> <role> <why> [--part ...] [--session <id>]
  python3 .claude/costs/estimate.py show [--session <id>]
  python3 .claude/costs/estimate.py rates

Each `--part` is the hours one role at one grade would spend on the task, and
why that role, at that grade, for those hours; the parts add up to the
estimate, and `set` replaces the whole of it. `rates` prints the table an
estimate is checked against as JSON — `rates.json` plus the roles this
repository's `rates.repo.json` adds, each at its one grade. Without
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
from pathlib import Path
from typing import List, Optional

<<<<<<< HEAD
from lib.estimate import Estimate, Part, Rates, checked, senior_hours, latest, load_rates
from lib.rows import SESSIONS, read_pending_estimate, read_row, row_path, row_text, write_atomic, write_pending_estimate
from lib.shape import ShapeError, to_json
=======
from lib.estimate import Estimate, Part, Rates, checked, senior_hours, latest, parse_rates
from lib.ledger import BRANCH, LedgerError, append_row, fetch, latest_row, path_of
from lib.rows import ROOT, SESSIONS, SessionCost, read_pending_estimate, row_path, row_text, write_atomic, write_pending_estimate
from lib.shape import ShapeError
>>>>>>> origin/main

COSTS = Path(__file__).resolve().parent


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
    one, is rewritten to match."""
    text = row_text(row)
    path = row_path(row.session_id)
    if path is not None:
        write_atomic(path, text)
    held = path_of(row.session_id)
    if held is None:
        assert path is not None, "the row came from the tree or the ledger"
        held = path.relative_to(ROOT).as_posix()
    append_row(held, text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
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
        rates = load_rates(COSTS)
    except ShapeError as error:
        print(f"estimate: {error}", file=sys.stderr)
        return 1
    if args.command == "rates":
        print(json.dumps(to_json(rates), ensure_ascii=False))
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
