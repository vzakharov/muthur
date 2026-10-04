#!/usr/bin/env python3
"""Set or show a session's human-hour estimate.

Usage:
  python3 .claude/costs/estimate.py set <comment> --part <hours> <grade> <role> [--part ...] [--session <id>]
  python3 .claude/costs/estimate.py show [--session <id>]

Each `--part` is the hours one role at one grade would spend on the task; the
parts add up to the estimate, and `set` replaces the whole of it. Without
`--session` the session is this one, read off `CLAUDE_CODE_SESSION_ID`: the
estimate goes to `tmp/estimates/<id>.json`, and the row folds it in when the
turn ends. Another session's id edits that session's committed row in place,
which is a change to commit like any other.

Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from lib.estimate import Estimate, Part, Rates, checked, senior_hours, latest, parse_rates
from lib.rows import read_pending_estimate, read_row, row_text, write_atomic, write_pending_estimate
from lib.shape import ShapeError

COSTS = Path(__file__).resolve().parent


def row_path(session_id: str) -> Optional[Path]:
    found = sorted((COSTS / "sessions").glob(f"*/{session_id}.json"))
    return found[0] if found else None


def describe(estimate: Optional[Estimate], rates: Rates) -> str:
    if estimate is None:
        return "no estimate yet"
    parts = " + ".join(f"{part.hours:g} h {part.grade} {part.role}" for part in estimate.parts)
    return f"{parts} = {senior_hours(estimate, rates):g} senior-hours — {estimate.comment}"


def parts_of(raw: List[List[str]]) -> List[Part]:
    parts = []
    for hours, grade, role in raw:
        try:
            parts.append(Part(hours=float(hours), grade=grade, role=role))
        except ValueError as error:
            raise ShapeError(f"`--part {hours} {grade} {role}`: hours are not a number") from error
    return parts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    setting = commands.add_parser("set")
    setting.add_argument("comment")
    setting.add_argument(
        "--part", nargs=3, action="append", required=True, metavar=("HOURS", "GRADE", "ROLE")
    )
    showing = commands.add_parser("show")
    for command in (setting, showing):
        command.add_argument("--session", help="another session's id; this one's by default")
    args = parser.parse_args()

    current = os.environ.get("CLAUDE_CODE_SESSION_ID")
    session_id: Optional[str] = args.session or current
    if session_id is None:
        print("estimate: no CLAUDE_CODE_SESSION_ID; name the session with --session", file=sys.stderr)
        return 1
    rates = parse_rates((COSTS / "rates.json").read_text(encoding="utf-8"))
    running = session_id == current
    path = row_path(session_id)
    if not running and path is None:
        print(f"estimate: no row for session {session_id} under {COSTS / 'sessions'}", file=sys.stderr)
        return 1

    try:
        row = read_row(path)[0] if path is not None else None
        pending = read_pending_estimate(session_id) if running else None
        if args.command == "set":
            pending = checked(
                Estimate(
                    at=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                    parts=parts_of(args.part),
                    comment=args.comment.strip(),
                ),
                rates,
                "the estimate",
            )
            if running:
                write_pending_estimate(session_id, pending)
            else:
                assert row is not None and path is not None
                row.estimate = pending
                write_atomic(path, row_text(row))
        estimate = latest(row.estimate if row is not None else None, pending)
    except ShapeError as error:
        print(f"estimate: {error}", file=sys.stderr)
        return 1

    print(f"estimate for {session_id}: {describe(estimate, rates)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
