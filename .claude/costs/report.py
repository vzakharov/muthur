#!/usr/bin/env python3
"""Total the rows under `sessions/` — what the work in this repository would
have cost at Claude API rates.

Usage:
  python3 .claude/costs/report.py [--all-my-repos | --repo OWNER/NAME ...]
                                  [--month YYYY-MM | --week YYYY-Www | --day YYYY-MM-DD] [--json]

Each period also takes `cur` or `prev`. Without one, every row is totalled and
the hours by role and grade cover the current month.

The totals are never written: they are derived from the rows, so the report is
run when a number is wanted rather than kept on disk going stale. A row in a
retired shape is rewritten in the current one, and the report says which.
`--json` prints the whole breakdown for whoever wants to keep one anyway. Rows
reach the trunk by merge, so a month read there is a month of *merged* work:
`CLAUDE.md` beside this file carries what that leaves out.

`--all-my-repos` reads every repository the `gh` user can see whose default
branch carries a ledger, and `--repo` (repeatable) just the ones named, off
GitHub rather than this checkout, adding a table by repository.

Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from lib.estimate import Rates, parse_rates
from lib.github import REPO, Client, GitHubError, remote_ledger
from lib.hours import HoursTable
from lib.period import FORMATS, KINDS, Period, PeriodError, month_of, period
from lib.pricing import parse_prices
from lib.rows import SessionCost, read_row
from lib.shape import to_json
from lib.totals import (
    Bucket,
    EffortSummary,
    OrientationSummary,
    PhaseStats,
    Rate,
    Spread,
    TelemetrySummary,
    Totals,
    by_repo,
    totals_of,
)

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
        row, changes = read_row(path)
        rows.append(row)
        # Stderr, so `--json` stays parseable. A rewritten row is a change to
        # commit, which is why it is named rather than done quietly.
        if changes:
            print(f"costs: {'; '.join(changes)} in {path}", file=sys.stderr)
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


def tokens(spread: Optional[Spread]) -> str:
    return "—" if spread is None else f"{spread.mean / 1000:.0f}k mean, {spread.median / 1000:.0f}k median"


def phase_line(label: str, width: int, stats: PhaseStats) -> str:
    return (
        f"  {label.ljust(width)}  {usd(stats.usd.mean):>7} mean  {usd(stats.usd.median):>7} median"
        f"  {stats.share_of_session.mean:>4.0%} of the session"
        f"  context {tokens(stats.context_tokens)}  ({count(stats.phases, 'phase')})"
    )


def phase_table(title: str, groups: Dict[str, PhaseStats]) -> None:
    width = max(len(key) for key in groups)
    print(f"\n{title}")
    for key, stats in groups.items():
        print(phase_line(key, width, stats))


def orientation(summary: OrientationSummary) -> None:
    print(f"\norientation, measured on {summary.measured} of {count(summary.rows, 'row')}")
    if summary.orientation is None:
        return
    print(phase_line("before acting", 13, summary.orientation))
    phase_table("orientation by what ended it", summary.by_ended_by)
    phase_table("orientation by opening command", summary.by_opening_command)
    compactions = summary.compactions
    if compactions is None:
        return
    print(f"\n{count(compactions.compactions, 'compaction')}")
    print(phase_line("re-orientation", 14, compactions.reorientation))
    print(f"  compacted from {tokens(compactions.compacted_from)}")
    by_tool = ", ".join(f"{tool} {calls}" for tool, calls in compactions.rereads_by_tool.items())
    print(
        f"  re-reads {compactions.reread_calls.mean:.1f} mean, {compactions.reread_calls.median:.1f}"
        f" median, est. {usd(compactions.reread_estimated_usd.mean)} mean"
        f" {usd(compactions.reread_estimated_usd.median)} median"
        f"{f' — {by_tool}' if by_tool else ''}"
    )


def telemetry(summary: TelemetrySummary) -> None:
    print(
        f"\npriced with events: {summary.priced} of {count(summary.rows, 'row')},"
        f" {usd(summary.priced_usd)} of spend"
    )
    if not summary.unseen:
        return
    print("calls only the events saw")
    width = max(len(source) for source in summary.unseen)
    for source, bucket in summary.unseen.items():
        share = bucket.cost_usd / summary.priced_usd if summary.priced_usd > 0 else 0.0
        print(
            f"  {source.ljust(width)}  {usd(bucket.cost_usd):>10}  {share:>5.1%} of it"
            f"  {count(bucket.sessions, 'session'):>12}  {count(bucket.responses, 'call'):>10}"
        )


def rate_table(title: str, rates: Dict[str, Rate]) -> None:
    if not rates:
        return
    width = max(len(key) for key in rates)
    print(f"\n{title}")
    for key, rate in rates.items():
        per_hour = "—" if rate.usd_per_senior_hour is None else usd(rate.usd_per_senior_hour)
        print(
            f"  {key.ljust(width)}  {per_hour:>8} per senior-hour"
            f"  {rate.senior_hours:>7.1f} h  {usd(rate.cost_usd):>10}"
            f"  {count(rate.sessions, 'session'):>12}"
        )


def effort(summary: EffortSummary) -> None:
    print(f"\nestimated: {summary.estimated} of {count(summary.rows, 'row')}")
    if summary.estimated == 0:
        return
    rate_table("per senior-hour", {"all": summary.overall})
    rate_table("per senior-hour by month", summary.by_month)
    rate_table("per senior-hour by week", summary.by_week)
    rate_table("per senior-hour by day", summary.by_day)
    rate_table("per senior-hour by model", summary.by_model_month)


def hours(summary: HoursTable) -> None:
    print(f"\nhours by role and grade, {summary.period}: estimated {summary.estimated} of {count(summary.rows, 'row')}")
    if not summary.by_role:
        return
    width = max(len("total"), *(len(role) for role in summary.by_role))
    columns = [*summary.grades, "total"]

    def line(label: str, cells: Dict[str, float]) -> str:
        figures = [*(cells.get(grade, 0.0) for grade in summary.grades), sum(cells.values())]
        return f"  {label.ljust(width)}" + "".join(
            f"  {'—' if figure == 0 else f'{figure:.1f}':>{max(len(column), 7)}}"
            for column, figure in zip(columns, figures)
        )

    print(f"  {''.ljust(width)}" + "".join(f"  {column:>{max(len(column), 7)}}" for column in columns))
    for role, cells in summary.by_role.items():
        print(line(role, cells))
    column_totals: Dict[str, float] = {}
    for cells in summary.by_role.values():
        for grade, figure in cells.items():
            column_totals[grade] = column_totals.get(grade, 0.0) + figure
    print(line("total", column_totals))


def repo_name(value: str) -> str:
    if not REPO.fullmatch(value):
        raise argparse.ArgumentTypeError(f"{value!r} is not OWNER/NAME")
    return value


def today() -> date:
    """UTC, as every row's dates are."""
    return datetime.now(timezone.utc).date()


def this_repo(span: Optional[Period], as_json: bool, rates: Rates) -> int:
    months = sorted(p for p in SESSIONS.iterdir() if p.is_dir()) if SESSIONS.is_dir() else []
    shown = [m for m in months if span is None or m.name in span.months()]
    rows = [
        row
        for shown_month in shown
        for row in rows_in(shown_month)
        if span is None or span.holds(row)
    ]
    if not rows:
        print(f"costs: no rows under {SESSIONS}{'' if span is None else f' for {span.label}'}")
        return 0

    totals = totals_of(rows, rates, hours_period=span or month_of(today()))
    if as_json:
        print(json.dumps(to_json(totals), indent=2, ensure_ascii=False))
        return 0
    report(rows, totals)
    return 0


class Status:
    """What a cross-repo run is doing, on stderr so `--json` stays parseable:
    one line rewritten in place on a terminal, a line per step otherwise."""

    def __init__(self) -> None:
        self.live = sys.stderr.isatty()

    def __call__(self, message: str) -> None:
        if self.live:
            sys.stderr.write(f"\r\033[K{message}…")
            sys.stderr.flush()
        else:
            print(f"costs: {message}", file=sys.stderr)

    def clear(self) -> None:
        if self.live:
            sys.stderr.write("\r\033[K")
            sys.stderr.flush()


def across_repos(only: Optional[List[str]], span: Optional[Period], as_json: bool, rates: Rates) -> int:
    status = Status()
    try:
        ledger = remote_ledger(Client(progress=status), only, None if span is None else span.months())
    finally:
        status.clear()
    rows = [row for row in ledger.rows if span is None or span.holds(row)]
    totals = totals_of(rows, rates, ledger.repo_of, span or month_of(today()))
    repos = by_repo(rows, ledger.repo_of)
    if as_json:
        print(
            json.dumps(
                {
                    **to_json(totals),
                    "repos": [
                        {**to_json(repo), **to_json(repos.get(repo.name, Bucket()))}
                        for repo in ledger.repos
                    ],
                    "withoutLedger": ledger.without_ledger,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    for repo in ledger.repos:
        for warning in repo.warnings:
            print(f"{repo.name}: {warning}")
    if ledger.without_ledger:
        print(f"muthur, no ledger: {', '.join(ledger.without_ledger)}")
    if not rows:
        print(f"costs: no rows in {count(ledger.seen, 'repo')}{'' if span is None else f' for {span.label}'}")
        return 0
    table("repo", repos)
    report(rows, totals)
    return 0


def report(rows: List[SessionCost], totals: Totals) -> None:
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
    if totals.orientation is not None:
        orientation(totals.orientation)
    if totals.telemetry is not None:
        telemetry(totals.telemetry)
    if totals.effort is not None:
        effort(totals.effort)
    if totals.hours is not None:
        hours(totals.hours)

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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--all-my-repos",
        action="store_true",
        help="every repo the gh user can see whose default branch has a ledger",
    )
    scope.add_argument(
        "--repo",
        action="append",
        type=repo_name,
        metavar="OWNER/NAME",
        help="this repo's ledger on GitHub; repeatable",
    )
    when = parser.add_mutually_exclusive_group()
    for kind in KINDS:
        when.add_argument(
            f"--{kind}",
            metavar=f"{FORMATS[kind][1]}|cur|prev",
            help=f"only the sessions that started in this {kind}, UTC",
        )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    named = [(kind, getattr(args, kind)) for kind in KINDS if getattr(args, kind) is not None]
    try:
        span = period(*named[0], today()) if named else None
    except PeriodError as error:
        parser.error(str(error))
    rates = parse_rates((COSTS / "rates.json").read_text(encoding="utf-8"))
    if not (args.all_my_repos or args.repo):
        return this_repo(span, args.json, rates)
    try:
        return across_repos(
            None if args.all_my_repos else list(dict.fromkeys(args.repo)), span, args.json, rates
        )
    except GitHubError as error:
        print(f"costs: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
