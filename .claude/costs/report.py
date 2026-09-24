#!/usr/bin/env python3
"""Total the rows under `sessions/` — what the work in this repository would
have cost at Claude API rates.

Usage:
  python3 .claude/costs/report.py [--month YYYY-MM] [--json]

The totals are never written: they are derived from the rows, so the report is
run when a number is wanted rather than kept on disk going stale. A row still
carrying a retired field is rewritten without it, and the report says which. `--json` prints the
whole breakdown for whoever wants to keep one anyway. Rows reach the trunk by
merge, so a month read there is a month of *merged* work: `CLAUDE.md` beside
this file carries what that leaves out.

Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List

from lib.pricing import SessionCost, parse_prices
from lib.rows import read_row
from lib.shape import to_json
from lib.totals import Bucket, totals_of

COSTS = Path(__file__).resolve().parent
SESSIONS = COSTS / "sessions"

# The tolerance for what Claude Code counts and no row can — the background
# Haiku calls and each compact's own request, neither of which reaches the
# transcript as a response. Both ran to a fraction of a percent on every session
# measured. Reading a subagent's file short of its spend, the failure this check
# was added for, ran to seven.
SHORTFALL = 0.02


def rows_in(month: Path) -> List[SessionCost]:
    rows = []
    for path in sorted(month.glob("*.json")):
        row, dropped = read_row(path)
        rows.append(row)
        # Stderr, so `--json` stays parseable. A rewritten row is a change to
        # commit, which is why it is named rather than done quietly.
        if dropped:
            print(f"costs: dropped {', '.join(dropped)} from {path}", file=sys.stderr)
    return rows


def usd(amount: float) -> str:
    return f"${amount:.2f}"


def count(n: int, noun: str) -> str:
    return f"{n} {noun}{'' if n == 1 else 's'}"


def table(title: str, buckets: Dict[str, Bucket]) -> None:
    width = max(len(key) for key in buckets)
    print(f"\n{title}")
    for key, bucket in buckets.items():
        print(
            f"  {key.ljust(width)}  {usd(bucket.cost_usd):>10}"
            f"  {count(bucket.sessions, 'session'):>12}"
            f"  {count(bucket.responses, 'response'):>15}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--month", help="YYYY-MM")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    months = sorted(p for p in SESSIONS.iterdir() if p.is_dir()) if SESSIONS.is_dir() else []
    shown = [m for m in months if args.month is None or m.name == args.month]
    if not shown:
        print(f"costs: no rows under {SESSIONS}{'' if args.month is None else f' for {args.month}'}")
        return 0

    rows = [row for month in shown for row in rows_in(month)]
    totals = totals_of(rows)

    if args.json:
        print(json.dumps(to_json(totals), indent=2, ensure_ascii=False))
        return 0

    # Every grain prints: the month is the bill, the week the trend, the day
    # which session did it.
    for title, buckets in (
        ("month", totals.by_month),
        ("week", totals.by_week),
        ("day", totals.by_day),
        ("branch", totals.by_branch),
        ("operator", totals.by_operator),
    ):
        if buckets:
            table(title, buckets)

    subagents = sum(row.subagents.cost_usd for row in rows)
    delegated = f", {usd(subagents)} of it subagents" if subagents > 0 else ""
    print(f"\ntotal {usd(totals.cost_usd)} over {count(totals.sessions, 'session')}{delegated}")

    # The hand-kept rate table has no published source to check itself against,
    # so the report states its age, and checks the arithmetic against the only
    # second opinion there is: what Claude Code itself counted the session at.
    prices = parse_prices((COSTS / "prices.json").read_text(encoding="utf-8"))
    age = (datetime.now(timezone.utc).date() - date.fromisoformat(prices.as_of)).days
    print(f"\nrates as of {prices.as_of} ({count(age, 'day')} ago), hand-kept in .claude/costs/prices.json")

    stale = sum(1 for row in rows if row.prices_as_of != prices.as_of)
    if stale:
        print(
            f"{count(stale, 'row')} priced under an older table; their transcripts are"
            " gone, so the figures stand as billed at the time"
        )

    # One way only, and that is what makes it sound: Claude Code's figure is read
    # out of the transcript the row was priced from, so it was written at or
    # before the row was. Higher than the row means the row missed something;
    # lower means only that the session kept going, as every row's last turn does.
    for row in rows:
        floor = row.claude_code_total_usd
        if floor is not None and row.total.cost_usd < floor * (1 - SHORTFALL):
            print(
                f"{row.session_id}: priced at {usd(row.total.cost_usd)}, but Claude Code"
                f" had already counted {usd(floor)} — the row is missing a source"
            )

    unchecked = sum(1 for row in rows if row.claude_code_total_usd is None)
    if unchecked:
        print(f"{count(unchecked, 'row')} with no Claude Code total to check against")
    return 0


if __name__ == "__main__":
    sys.exit(main())
