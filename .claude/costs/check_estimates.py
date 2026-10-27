#!/usr/bin/env python3
"""Fail when a session the branch carries has no human-hour estimate.

Those sessions are the rows under `sessions/` the branch adds against its merge
base with the default branch, the rows it changes where the session went on
responding, the `cost-ledger` rows filed under the branch's name, and the
running session (`CLAUDE_CODE_SESSION_ID`), whose estimate
counts from its pending file under `tmp/` by `estimate.py show`'s rule. A row
the trunk already carries is left alone, since many predate estimates.

Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import List, Optional, Tuple

from lib.estimate_model import latest, shadow_notes
from lib.ledger_branch import BRANCH, RATES_PATH, REMOTE_REF, LedgerError, fetch, latest_row, ledger_rates, rows_at
from lib.rows import ROOT, SESSIONS, SessionCost, parse_session_cost, read_pending_estimate, union
from lib.shape import ShapeError

PROG = "check-estimates"
DEFAULT_BRANCHES = ("refs/remotes/origin/HEAD", "refs/remotes/origin/main", "refs/remotes/origin/master")


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout


def merge_base() -> Optional[Tuple[str, str]]:
    """The default branch's ref and the merge base with it: the bound
    `scripts/check-squash-message.sh` draws, for its reason — a row reachable
    from the base belongs to another branch."""
    for ref in DEFAULT_BRANCHES:
        try:
            git("rev-parse", "--verify", "--quiet", ref)
            return ref, git("merge-base", "HEAD", ref).strip()
        except subprocess.CalledProcessError:
            continue
    return None


def branch_rows(base: str) -> List[SessionCost]:
    """A changed row whose `lastResponseAt` stayed put is the report rewriting a
    retired shape, not a session that spent on this branch."""
    rows = []
    listed = git("diff", "--name-status", "--no-renames", base, "--", str(SESSIONS.relative_to(ROOT)))
    for line in listed.splitlines():
        status, path = line.split("\t", 1)
        if status not in ("A", "M") or not path.endswith(".json"):
            continue
        row = parse_session_cost((ROOT / path).read_text(encoding="utf-8"), path)
        if status == "M":
            before = parse_session_cost(git("show", f"{base}:{path}"), f"{base}:{path}")
            if before.last_response_at == row.last_response_at:
                continue
        rows.append(row)
    return rows


def ledger_rows(branch: str) -> List[SessionCost]:
    """A finalized branch's rows are on the ledger alone."""
    if not branch:
        return []
    rows = (parse_session_cost(text, f"{BRANCH}:{path}") for path, text in rows_at(REMOTE_REF))
    return [row for row in rows if row.branch == branch]


def running_is_estimated(session_id: str) -> bool:
    row = latest_row(session_id)
    return latest(row.estimate if row is not None else None, read_pending_estimate(session_id)) is not None


def fix_for(session_id: str, running: Optional[str]) -> str:
    named = "" if session_id == running else f" --session {session_id}"
    return f'python3 .claude/costs/estimate.py set --part <hours> <grade> <role> "<why>" [--part ...]{named}'


def main() -> int:
    running = os.environ.get("CLAUDE_CODE_SESSION_ID")
    base = merge_base()
    if (ROOT / RATES_PATH).is_file():
        print(
            f"{PROG}: {RATES_PATH} is in the tree, where nothing reads it; the table lives on {BRANCH}."
            f" Carry it there with `python3 .claude/costs/ledger.py backfill`, then `git rm {RATES_PATH}`.",
            file=sys.stderr,
        )
        return 1
    try:
        # Fetched and read on every run, so a broken or stale table shows here
        # rather than at the next estimate.
        fetch()
        rates = ledger_rates(REMOTE_REF)
        for note in shadow_notes(rates, "this repository"):
            print(f"{PROG}: {note}", file=sys.stderr)
        carried = union(
            [*(branch_rows(base[1]) if base is not None else []), *ledger_rows(git("branch", "--show-current").strip())],
            lambda row: row,
        )
        missing = {row.session_id: row.opening_prompt for row in carried if row.estimate is None}
        missing.pop(running, None)
        if running is not None and not running_is_estimated(running):
            missing[running] = "this session"
    except (ShapeError, ValueError, LedgerError) as error:
        print(f"{PROG}: {error}", file=sys.stderr)
        return 1

    if missing:
        print(f"{PROG}: {len(missing)} session(s) on this branch have no human-hour estimate.", file=sys.stderr)
        for session_id, what in missing.items():
            print(f"{PROG}:   {session_id} ({(what or 'no opening prompt')[:80]!r}):", file=sys.stderr)
            print(f"{PROG}:     {fix_for(session_id, running)}", file=sys.stderr)
        fixed = "".join(f"; {role} at {added.grade} only" for role, added in rates.added.items())
        print(
            f"{PROG}: Each part is the hours one role at one grade would spend on the task, and why"
            f" (roles: {', '.join(rates.roles)}; grades: {', '.join(rates.grades)}{fixed}).",
            file=sys.stderr,
        )
        if base is not None:
            ref, sha = base
            print(
                f"{PROG}: The branch was read against {ref.removeprefix('refs/remotes/')} at {sha[:7]}; where that"
                " ref is stale, the trunk's own rows count as this branch's — `git fetch origin` and rerun.",
                file=sys.stderr,
            )
        return 1

    counted = len({row.session_id for row in carried} | ({running} if running else set()))
    note = "" if base is not None else " (no base to read the branch against: the running session only)"
    print(f"{PROG}: ok — {counted} session(s) on this branch, each with an estimate{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
