#!/usr/bin/env python3
"""Fail when a session the branch carries has no human-hour estimate.

Those sessions are the rows under `sessions/` the branch adds against its merge
base with the default branch, the rows it changes where the session went on
responding, and the running session (`CLAUDE_CODE_SESSION_ID`), whose estimate
counts from its pending file under `tmp/` by `estimate.py show`'s rule. A row
the trunk already carries is left alone, since many predate estimates.

Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from lib.estimate import latest, parse_rates
from lib.rows import ROOT, SESSIONS, SessionCost, parse_session_cost, read_pending_estimate, row_path
from lib.shape import ShapeError

PROG = "check-estimates"
COSTS = Path(__file__).resolve().parent
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


def running_is_estimated(session_id: str) -> bool:
    path = row_path(session_id)
    row = parse_session_cost(path.read_text(encoding="utf-8"), str(path)) if path is not None else None
    return latest(row.estimate if row is not None else None, read_pending_estimate(session_id)) is not None


def fix_for(session_id: str, running: Optional[str]) -> str:
    named = "" if session_id == running else f" --session {session_id}"
    return f'python3 .claude/costs/estimate.py set --part <hours> <grade> <role> "<why>" [--part ...]{named}'


def main() -> int:
    running = os.environ.get("CLAUDE_CODE_SESSION_ID")
    base = merge_base()
    try:
        carried = branch_rows(base[1]) if base is not None else []
        missing = {row.session_id: row.opening_prompt for row in carried if row.estimate is None}
        missing.pop(running, None)
        if running is not None and not running_is_estimated(running):
            missing[running] = "this session"
    except (ShapeError, ValueError) as error:
        print(f"{PROG}: {error}", file=sys.stderr)
        return 1

    if missing:
        rates = parse_rates((COSTS / "rates.json").read_text(encoding="utf-8"))
        print(f"{PROG}: {len(missing)} session(s) on this branch have no human-hour estimate.", file=sys.stderr)
        for session_id, what in missing.items():
            print(f"{PROG}:   {session_id} ({(what or 'no opening prompt')[:80]!r}):", file=sys.stderr)
            print(f"{PROG}:     {fix_for(session_id, running)}", file=sys.stderr)
        print(
            f"{PROG}: Each part is the hours one role at one grade would spend on the task, and why"
            f" (roles: {', '.join(rates.roles)}; grades: {', '.join(rates.grades)}).",
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
