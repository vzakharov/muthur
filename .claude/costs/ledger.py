#!/usr/bin/env python3
"""Read and write the `cost-ledger` branch.

Usage:
  python3 .claude/costs/ledger.py backfill [<ref>...]
  python3 .claude/costs/ledger.py fetch
  python3 .claude/costs/ledger.py stop-plan <branch>
  python3 .claude/costs/ledger.py commit-row <parent> <path> <file>
  python3 .claude/costs/ledger.py append-row <path> <file>

`backfill` carries into the ledger every row the named refs hold that it lacks
or holds older — by default every branch on `origin` and every PR's head — and
prints how many sessions the ledger holds after. It pushes, and a second run
commits nothing.

The rest are `hooks/stop-session-cost.sh`'s. `stop-plan` prints
`display=yes|no`: whether the branch still gets the row's display copy, which
it does until it is finalized. `commit-row` prints the commit of `<file>` at
`<path>` on `<parent>`, or nothing where `<parent>` already holds it.
`append-row` commits and pushes the row to the ledger.

Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib.finalized import finalized
from lib.github import Client
from lib.ledger_branch import BRANCH, LedgerError, append_row, backfill, commit, every_ref, fetch, row_change

TRUNKS = ("", "main", "master")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("backfill").add_argument("refs", nargs="*")
    commands.add_parser("fetch")
    commands.add_parser("stop-plan").add_argument("branch")
    committing = commands.add_parser("commit-row")
    committing.add_argument("parent")
    appending = commands.add_parser("append-row")
    for command in (committing, appending):
        command.add_argument("path")
        command.add_argument("file", type=Path)
    args = parser.parse_args()

    try:
        if args.command == "backfill":
            held, built = backfill(args.refs or every_ref())
            print(f"ledger: {held} sessions in {BRANCH}{f', carried in {built[:7]}' if built else ', nothing to carry'}")
        elif args.command == "fetch":
            fetch()
        elif args.command == "stop-plan":
            # The trunk has no PR to finalize, and no branch to carry a copy.
            display = args.branch not in TRUNKS and not finalized(args.branch, Client())
            print(f"display={'yes' if display else 'no'}")
        elif args.command == "commit-row":
            rows, message = row_change(args.parent, args.path, args.file.read_text(encoding="utf-8"))
            if rows:
                print(commit(args.parent, rows, message))
        else:
            append_row(args.path, args.file.read_text(encoding="utf-8"))
    except LedgerError as error:
        print(f"ledger: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
