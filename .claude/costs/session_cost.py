#!/usr/bin/env python3
"""Price one session's transcript and write its row under `sessions/`.

Usage:
  python3 .claude/costs/session_cost.py --transcript <path> [--session-id <id>] [--row-path] [--at-stop] [--out <path>]
  python3 .claude/costs/session_cost.py --transcript <path> [--session-id <id>] --name '<short label>'

The row is rewritten from the whole file each run rather than appended to, which
is what lets a run pick up anything the previous one was too early to see.
`--at-stop` is the Stop hook's: the turn is over, so the transcript should end on
its `end_turn`. `--out` is the hook's too: it writes the row there instead of into
place, since committing it is the hook's job. Stdout is the interface: the row's
path under `--row-path`, for `hooks/stop-session-cost.sh`; a one-line summary
otherwise, for a person running it by hand.

`--name` prices nothing and writes no row. It records the name under `tmp/`, and
the next run that writes the row takes it from there — so naming a session never
leaves the tracked tree dirty for the harness's `Stop` check to find.

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
    """The name and any unwritten-tail warning are what no run can recompute
    from the transcript, so a rewrite reads them back from the last one. An
    unreadable row loses both rather than failing the write — the rewrite is
    what repairs it — and says so."""
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


def name_file(session_id: str) -> Path:
    """Where `--name` leaves a session's name. `hooks/prompt-session-name.sh`
    reads the same path, to go quiet once a name is waiting here."""
    return ROOT / "tmp" / "costs" / "names" / session_id


def recorded_name(session_id: str) -> Optional[str]:
    path = name_file(session_id)
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip() or None


def write_atomic(out: Path, contents: str) -> None:
    """A write cut off halfway leaves the old file rather than half a new one,
    so it is staged and renamed into place — under the repo's own gitignored
    `tmp/`, where a stray staging file is invisible to git and the rename is
    on the same filesystem."""
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
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    transcript: Path = args.transcript
    if args.name is not None:
        path = name_file(args.session_id or transcript.stem)
        write_atomic(path, args.name + "\n")
        print(f"session-cost: named {args.name!r}; the Stop hook puts it in this turn's row")
        return 0

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
    cost.name = recorded_name(cost.session_id) or (before.name if before else None)
    if before is not None:
        carried = [w for w in before.warnings if is_unwritten_tail(w) and w not in cost.warnings]
        cost.warnings = carried + cost.warnings
    row = json.dumps(to_json(cost), indent=2, ensure_ascii=False) + "\n"
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
