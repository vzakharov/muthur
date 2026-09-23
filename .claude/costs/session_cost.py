#!/usr/bin/env python3
"""Price one session's transcript and write its row under `sessions/`.

Usage:
  python3 .claude/costs/session_cost.py --transcript <path> [--session-id <id>] [--row-path] [--at-stop]
  python3 .claude/costs/session_cost.py --transcript <path> --name '<short label>'

The row is rewritten from the whole file each run rather than appended to, which
is what lets a run pick up anything the previous one was too early to see.
`--at-stop` says the turn is over, which is what makes a transcript not ending
on `end_turn` worth a warning. Stdout is the interface: the row's path under
`--row-path`, for `hooks/stop-session-cost.sh`; a one-line summary otherwise,
for a person running it by hand.

Paths resolve from this file's own location, so it runs from any working
directory. Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from lib.pricing import (
    SessionCost,
    TranscriptSources,
    is_unwritten_tail,
    parse_prices,
    parse_session_cost,
    summarise_transcript,
)
from lib.shape import ShapeError, to_json

COSTS = Path(__file__).resolve().parent
ROOT = COSTS.parent.parent


def subagents_of(main: Path) -> List[str]:
    """A subagent's responses are billed to this session and written to their own
    file under `<transcript>/subagents/`, so the directory is read rather than
    assumed empty. A session that spawned none has no directory at all."""
    directory = main.parent / main.stem / "subagents"
    if not directory.is_dir():
        return []
    return [path.read_text(encoding="utf-8") for path in sorted(directory.glob("*.jsonl"))]


def previous(row: Path) -> Optional[SessionCost]:
    """The name and an unwritten-tail warning are what no run can recompute —
    the transcript has caught up by the next one — so a rewrite reads back what
    the last one wrote. An unreadable row loses both rather than failing the
    write — the rewrite is what repairs it — and says so."""
    if not row.exists():
        return None
    try:
        return parse_session_cost(row.read_text(encoding="utf-8"), str(row))
    except (ShapeError, json.JSONDecodeError) as error:
        print(
            f"session-cost: {error}; rewriting the row from the transcript alone",
            file=sys.stderr,
        )
        return None


def month_of(cost: SessionCost) -> str:
    """The month a session is filed under is the month it started, so a session
    running across midnight on the last of the month stays in one file."""
    started = cost.first_response_at or datetime.now(timezone.utc).isoformat()
    return started[:7]


def write_atomic(out: Path, contents: str) -> None:
    """The harness's `Stop` check runs in parallel with the hook and counts a
    half-written file and a stray staging file alike, so a write is staged and
    renamed into place — under the repo's own gitignored `tmp/`, rename being
    atomic only within one filesystem."""
    staged = ROOT / "tmp" / f"{out.name}.staged"
    staged.parent.mkdir(parents=True, exist_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    staged.write_text(contents, encoding="utf-8")
    os.replace(staged, out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--transcript", required=True, type=Path)
    parser.add_argument("--session-id")
    parser.add_argument("--name")
    parser.add_argument("--row-path", action="store_true")
    parser.add_argument("--at-stop", action="store_true")
    args = parser.parse_args()

    transcript: Path = args.transcript
    prices = parse_prices((COSTS / "prices.json").read_text(encoding="utf-8"))
    cost = summarise_transcript(
        TranscriptSources(
            main=transcript.read_text(encoding="utf-8"),
            subagents=subagents_of(transcript),
        ),
        prices,
        args.session_id or transcript.stem,
        at_stop=args.at_stop,
    )

    out = COSTS / "sessions" / month_of(cost) / f"{cost.session_id}.json"
    before = previous(out)
    cost.name = args.name if args.name is not None else (before.name if before else None)
    if before is not None:
        carried = [w for w in before.warnings if is_unwritten_tail(w) and w not in cost.warnings]
        cost.warnings = carried + cost.warnings
    write_atomic(out, json.dumps(to_json(cost), indent=2, ensure_ascii=False) + "\n")

    if args.row_path:
        print(out)
    else:
        print(f"session-cost: {cost.total.responses} responses, ${cost.total.cost_usd:.4f} → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
