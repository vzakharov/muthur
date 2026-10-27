#!/usr/bin/env python3
"""Price one session's transcript and write its row under `sessions/`.

Usage:
  python3 .claude/costs/session_cost.py --transcript <path> [--session-id <id>] [--events <path>] [--at-stop] [--out <path>]

The row is rewritten from the whole file each run rather than appended to, which
is what lets a run pick up anything the previous one was too early to see.
`--at-stop` is the Stop hook's: the turn is over, so the transcript should end on
its `end_turn`. `--out` is the hook's too: it writes the row there instead of into
place, since filing and committing it is the hook's job. Without it, the row goes
where the local copy of the ledger would file it, and the session's other copies
in the tree go. `--events` names the session's
telemetry file where it is not the receiver's `tmp/telemetry/<session-id>.jsonl`;
a session with none is priced from its transcript alone.

Paths resolve from this file's own location, so it runs from any working
directory. Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

from lib.billed import Event, parse_events
from lib.prices import parse_prices
from lib.pricing import is_unwritten_tail, summarise_transcript
from lib.transcript import TranscriptSources, subagents_of
from lib.estimate_model import latest
from lib.ledger_branch import copies, path_for
from lib.rows import (
    ROOT,
    SessionCost,
    parse_session_cost,
    place_tree_copy,
    read_pending_estimate,
    row_text,
    union,
)
from lib.shape import ShapeError

COSTS = Path(__file__).resolve().parent


def previous(session_id: str) -> Optional[SessionCost]:
    """An unwritten-tail warning and the estimate are what no run can recompute
    from the transcript, so a rewrite reads them back from the last one — the
    later of the tree's copy and the ledger's, since a finalized branch's tree
    has none. An unreadable copy is passed over rather than failing the write
    — the rewrite is what repairs it — and says so."""
    rows = []
    for where, text in copies(session_id):
        try:
            rows.append(parse_session_cost(text, where))
        except (ShapeError, json.JSONDecodeError) as error:
            print(f"session-cost: {error}; rewriting the row without that copy", file=sys.stderr)
    kept = union(rows, lambda row: row)
    return kept[0] if kept else None


def events_at(path: Path) -> Optional[Dict[str, Event]]:
    if not path.exists():
        return None
    return parse_events(path.read_text(encoding="utf-8"), str(path))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--transcript", required=True, type=Path)
    parser.add_argument("--session-id")
    parser.add_argument("--events", type=Path)
    parser.add_argument("--at-stop", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    transcript: Path = args.transcript
    session_id: str = args.session_id or transcript.stem
    events = events_at(args.events or ROOT / "tmp" / "telemetry" / f"{session_id}.jsonl")
    prices = parse_prices((COSTS / "prices.json").read_text(encoding="utf-8"))
    cost = summarise_transcript(
        TranscriptSources(
            main=transcript.read_text(encoding="utf-8"),
            subagents=subagents_of(transcript),
        ),
        prices,
        session_id,
        at_stop=args.at_stop,
        events=events,
    )

    before = previous(cost.session_id)
    if before is not None:
        carried = [w for w in before.warnings if is_unwritten_tail(w) and w not in cost.warnings]
        cost.warnings = carried + cost.warnings
    # The previous row is what keeps the estimate through a resume in a fresh
    # container, whose `tmp/` starts empty.
    cost.estimate = latest(
        before.estimate if before is not None else None,
        read_pending_estimate(cost.session_id),
    )
    row = row_text(cost)
    if args.out is not None:
        args.out.write_text(row, encoding="utf-8")
        out = args.out
    else:
        out = ROOT / path_for(row)
        place_tree_copy(out, row, cost.session_id)
    print(f"session-cost: {cost.total.responses} responses, ${cost.total.cost_usd:.4f} → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
