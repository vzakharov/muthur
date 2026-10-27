#!/usr/bin/env python3
"""Read and write the `cost-ledger` branch.

Usage:
  python3 .claude/costs/ledger.py backfill [<ref>...]
  python3 .claude/costs/ledger.py fetch
  python3 .claude/costs/ledger.py stop-plan <branch>
  python3 .claude/costs/ledger.py commit-row <parent> <path> <file>
  python3 .claude/costs/ledger.py append-row <file>
  python3 .claude/costs/ledger.py path-for <file>

`backfill` carries into the ledger every row the named refs hold that it lacks
or holds older — by default every branch on `origin` and every PR's head — and
prints how many sessions the ledger holds after. It pushes, and a second run
commits nothing.

The rest are `hooks/stop-session-cost.sh`'s. `stop-plan` prints
`display=yes|no`: whether the branch still gets the row's display copy, which
it does until it is finalized. `append-row` files the row on the ledger,
commits and pushes it, and prints the path it was filed at; `path-for` prints
where the local copy of the ledger would file it, for a turn whose fetch
failed. `commit-row` prints the commit of `<file>` at `<path>` on `<parent>`,
removing the session's other copies there, or nothing where `<parent>` already
holds it alone.

Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib.finalized import finalized
from lib.github import Client
from lib.ledger_branch import BRANCH, LedgerError, append_row, backfill, commit, display_change, every_ref, fetch, path_for

TRUNKS = ("", "main", "master")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("backfill").add_argument("refs", nargs="*")
    commands.add_parser("fetch")
    commands.add_parser("stop-plan").add_argument("branch")
    committing = commands.add_parser("commit-row")
    committing.add_argument("parent")
    committing.add_argument("path")
    for command in (committing, commands.add_parser("append-row"), commands.add_parser("path-for")):
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
            rows, message = display_change(args.parent, args.path, args.file.read_text(encoding="utf-8"))
            if rows:
                print(commit(args.parent, rows, message))
        elif args.command == "append-row":
            print(append_row(args.file.read_text(encoding="utf-8")))
        else:
            print(path_for(args.file.read_text(encoding="utf-8")))
    except LedgerError as error:
        print(f"ledger: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
