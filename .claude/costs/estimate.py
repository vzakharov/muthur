#!/usr/bin/env python3
"""Set or show a session's human-hour estimate.

Usage:
  python3 .claude/costs/estimate.py set <hours> <grade> <comment> [--session <id>]
  python3 .claude/costs/estimate.py show [--session <id>]

Without `--session` the session is this one, read off `CLAUDE_CODE_SESSION_ID`:
a revision goes to `tmp/estimates/<id>.json`, and the row folds it in when the
turn ends. Another session's id edits that session's committed row in place,
which is a change to commit like any other. Every `set` appends a revision; the
last one is the estimate.

Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from lib.estimate import Revision, checked, junior_hours, merged, parse_grades
from lib.rows import read_pending_estimates, read_row, row_text, write_atomic, write_pending_estimates
from lib.shape import ShapeError

COSTS = Path(__file__).resolve().parent


def row_path(session_id: str) -> Optional[Path]:
    found = sorted((COSTS / "sessions").glob(f"*/{session_id}.json"))
    return found[0] if found else None


def describe(revisions: List[Revision], grades: Dict[str, float]) -> str:
    if not revisions:
        return "no estimate yet"
    current = revisions[-1]
    return (
        f"{current.hours:g} {current.grade}-hours ({junior_hours(current, grades):g} junior-hours)"
        f" — {current.comment}  [{len(revisions)} revision{'' if len(revisions) == 1 else 's'}]"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    setting = commands.add_parser("set")
    setting.add_argument("hours", type=float)
    setting.add_argument("grade")
    setting.add_argument("comment")
    showing = commands.add_parser("show")
    for command in (setting, showing):
        command.add_argument("--session", help="another session's id; this one's by default")
    args = parser.parse_args()

    current = os.environ.get("CLAUDE_CODE_SESSION_ID")
    session_id: Optional[str] = args.session or current
    if session_id is None:
        print("estimate: no CLAUDE_CODE_SESSION_ID; name the session with --session", file=sys.stderr)
        return 1
    grades = parse_grades((COSTS / "grades.json").read_text(encoding="utf-8"))
    # The running session's row is rewritten at every `Stop`, so its revisions go
    # where that rewrite reads them; a finished session's row is edited directly.
    running = session_id == current
    path = row_path(session_id)
    if not running and path is None:
        print(f"estimate: no row for session {session_id} under {COSTS / 'sessions'}", file=sys.stderr)
        return 1

    try:
        row = read_row(path)[0] if path is not None else None
        pending = read_pending_estimates(session_id) if running else []
        if args.command == "set":
            revision = checked(
                Revision(
                    at=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                    hours=args.hours,
                    grade=args.grade,
                    comment=args.comment.strip(),
                ),
                grades,
                "the revision",
            )
            if running:
                pending.append(revision)
                write_pending_estimates(session_id, pending)
            else:
                assert row is not None and path is not None
                row.estimates = merged(row.estimates, [revision])
                write_atomic(path, row_text(row))
        revisions = merged(row.estimates if row is not None else [], pending)
    except ShapeError as error:
        print(f"estimate: {error}", file=sys.stderr)
        return 1

    print(f"estimate for {session_id}: {describe(revisions, grades)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
