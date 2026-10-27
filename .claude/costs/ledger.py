#!/usr/bin/env python3
"""Read and write the `cost-ledger` branch.

Usage:
  python3 .claude/costs/ledger.py backfill [<ref>...]
  python3 .claude/costs/ledger.py fetch
  python3 .claude/costs/ledger.py display <branch>
  python3 .claude/costs/ledger.py append-row <path> <file>

`backfill` carries into the ledger every row the named refs hold that it lacks
or holds older — by default every branch on `origin` and every PR's head — and
prints how many sessions the ledger holds after. It pushes, and a second run
commits nothing.

The rest are the hooks'. `display` prints `display=yes|no`: whether the branch
still gets the row's display copy, which it does until it is finalized —
`hooks/stage-cost-row.sh` asks it. `append-row` commits and pushes the row to
the ledger, for `hooks/stop-session-cost.sh`.

Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib.finalized import finalized
from lib.github import Client
from lib.ledger_branch import BRANCH, LedgerError, append_row, backfill, every_ref, fetch

TRUNKS = ("", "main", "master")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("backfill").add_argument("refs", nargs="*")
    commands.add_parser("fetch")
    commands.add_parser("display").add_argument("branch")
    appending = commands.add_parser("append-row")
    appending.add_argument("path")
    appending.add_argument("file", type=Path)
    args = parser.parse_args()

    try:
        if args.command == "backfill":
            held, built = backfill(args.refs or every_ref())
            print(f"ledger: {held} sessions in {BRANCH}{f', carried in {built[:7]}' if built else ', nothing to carry'}")
        elif args.command == "fetch":
            fetch()
        elif args.command == "display":
            # The trunk has no PR to finalize, and no branch to carry a copy.
            display = args.branch not in TRUNKS and not finalized(args.branch, Client())
            print(f"display={'yes' if display else 'no'}")
        else:
            append_row(args.path, args.file.read_text(encoding="utf-8"))
    except LedgerError as error:
        print(f"ledger: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
