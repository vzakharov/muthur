#!/usr/bin/env python3
"""Price one session's transcript and write its row under `sessions/`.

Usage:
  python3 .claude/costs/session_cost.py --transcript <path> [--session-id <id>] [--row-path] [--at-stop] [--out <path>]

The row is rewritten from the whole file each run rather than appended to, which
is what lets a run pick up anything the previous one was too early to see.
`--at-stop` is the Stop hook's: the turn is over, so the transcript should end on
its `end_turn`. `--out` is the hook's too: it writes the row there instead of into
place, since committing it is the hook's job. Stdout is the interface: the row's
path under `--row-path`, for `hooks/stop-session-cost.sh`; a one-line summary
otherwise, for a person running it by hand.

Paths resolve from this file's own location, so it runs from any working
directory. Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
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
from lib.rows import row_text, write_atomic
from lib.shape import ShapeError

COSTS = Path(__file__).resolve().parent


def subagents_of(main: Path) -> List[str]:
    """A subagent's responses are billed to this session and written to their own
    file under `<transcript>/subagents/`, so the directory is read rather than
    assumed empty. A session that spawned none has no directory at all."""
    directory = main.parent / main.stem / "subagents"
    if not directory.is_dir():
        return []
    return [path.read_text(encoding="utf-8") for path in sorted(directory.glob("*.jsonl"))]


def previous(row: Path) -> Optional[SessionCost]:
    """An unwritten-tail warning is what no run can recompute from the
    transcript, so a rewrite reads it back from the last one. An unreadable row
    loses it rather than failing the write — the rewrite is what repairs it —
    and says so."""
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--transcript", required=True, type=Path)
    parser.add_argument("--session-id")
    parser.add_argument("--row-path", action="store_true")
    parser.add_argument("--at-stop", action="store_true")
    parser.add_argument("--out", type=Path)
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
    if before is not None:
        carried = [w for w in before.warnings if is_unwritten_tail(w) and w not in cost.warnings]
        cost.warnings = carried + cost.warnings
    row = row_text(cost)
    if args.out is not None:
        args.out.write_text(row, encoding="utf-8")
    else:
        write_atomic(out, row)

    if args.row_path:
        print(out)
    else:
        print(f"session-cost: {cost.total.responses} responses, ${cost.total.cost_usd:.4f} → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
