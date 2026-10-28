#!/usr/bin/env python3
"""Mark the end of a session's orientation, or check for the mark.

Usage:
  python3 .claude/costs/oriented.py
  python3 .claude/costs/oriented.py check <transcript>

Run bare, it records nothing itself: the Bash call that ran it, in the
transcript, is the mark, and the ledger reads it there. What it prints is for
the operator, who sees the call's output in the chat: the context the session
has built and what it has spent, priced from the session's own transcript as
the ledger prices it. `check` prints `marked` or `unmarked` for the stretch
since the transcript's latest compaction, so that `hooks/estimate-notice.sh`
asks for a mark only where there is none. `.claude/costs/CLAUDE.md`
§ "Orientation" carries what the mark ends.

Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional

from lib.billed import events_at
from lib.orientation import marked
from lib.prices import PriceTable, parse_prices
from lib.pricing import UnpricedError, summarise_transcript
from lib.rows import ROOT
from lib.shape import ShapeError, json_lines
from lib.transcript import (
    SYNTHETIC_MODEL,
    TranscriptSources,
    is_response_record,
    parse_response,
    subagents_of,
)

COSTS = Path(__file__).resolve().parent
PROJECTS = Path.home() / ".claude" / "projects"


def transcript_of(session_id: str, projects: Path) -> Optional[Path]:
    """The live file where a session's id is under more than one project: it is
    the one being written to."""
    found = sorted(projects.glob(f"*/{session_id}.jsonl"), key=lambda path: path.stat().st_mtime)
    return found[-1] if found else None


def context_now(jsonl: str, label: str) -> Optional[int]:
    """What the session's own latest response sent — the call running this
    script is already in the file, with its usage."""
    latest: Optional[int] = None
    for where, _, record in json_lines(jsonl, label):
        if not is_response_record(record):
            continue
        response = parse_response(record, where, [])
        if not response.is_sidechain and response.model != SYNTHETIC_MODEL:
            latest = response.tokens.context_tokens()
    return latest


def figures(transcript: Path, prices: PriceTable, events: Optional[Path] = None) -> str:
    main = transcript.read_text(encoding="utf-8")
    cost = summarise_transcript(
        TranscriptSources(main=main, subagents=subagents_of(transcript)),
        prices,
        transcript.stem,
        events=events_at(events) if events is not None else None,
    )
    parts: List[str] = []
    context = context_now(main, str(transcript))
    if context is not None:
        parts.append(f"context {context:,} tokens")
    spent = f"${cost.total.cost_usd:.2f} spent"
    phase = cost.compactions[-1].reorientation if cost.compactions else cost.orientation
    if phase is not None and phase.ended_by == "oriented":
        what = "re-orientation since the last compaction" if cost.compactions else "orientation"
        spent += f", ${phase.spend.cost_usd:.2f} of it on {what}"
    parts.append(spent)
    return "; ".join(parts) + "."


def report() -> int:
    print("Orientation marked: the ledger ends this phase here.")
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session_id:
        print("No figures: CLAUDE_CODE_SESSION_ID is not set, so the transcript is unknown.")
        return 0
    transcript = transcript_of(session_id, PROJECTS)
    if transcript is None:
        print(f"No figures: no transcript for session {session_id} under {PROJECTS}.")
        return 0
    try:
        prices = parse_prices((COSTS / "prices.json").read_text(encoding="utf-8"))
        line = figures(transcript, prices, ROOT / "tmp" / "telemetry" / f"{session_id}.jsonl")
    except (OSError, ShapeError, UnpricedError) as error:
        # The mark is the call itself and stands; only the figures failed.
        print(f"oriented.py: the mark stands, but the figures failed: {error}", file=sys.stderr)
        return 1
    print(line[0].upper() + line[1:])
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        return report()
    if len(argv) == 2 and argv[0] == "check":
        path = Path(argv[1])
        try:
            found = marked(path.read_text(encoding="utf-8"), str(path))
        except (OSError, ShapeError) as error:
            print(f"oriented.py: {error}", file=sys.stderr)
            return 1
        print("marked" if found else "unmarked")
        return 0
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
