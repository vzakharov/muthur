#!/usr/bin/env python3
"""The context budget's priced figures, for `post-tool-context-budget.sh`:

- `lines <transcript> <pause-percent>` prints `<warn> <pause>` — the contexts
  at which relaying saves $0, and `<pause-percent>` of what carrying on costs,
  over the next `SLICE` tokens of work; `-` for a line no context reaches;
- `notice <transcript> <reading>` prints the saving sentence for the notice.

Prints nothing when the session cannot be priced, which leaves the caller on
its fixed lines. Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# The ledger's lib is reached by path, as its own scripts reach it.
COSTS = Path(__file__).resolve().parents[2] / "costs"
sys.path.insert(0, str(COSTS))

from lib.prices import parse_prices
from lib.restart import SLICE, Session, line_for, read_history, saving_over, session_of, verdict


def priced(transcript: Path, context: Optional[int]) -> Optional[Session]:
    history = read_history(transcript)
    if history is None:
        return None
    prices = parse_prices((COSTS / "prices.json").read_text(encoding="utf-8"))
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or COSTS.parents[1])
    return session_of(transcript, history, context or 0, prices, project, relay=True)


def main() -> None:
    command, transcript = sys.argv[1], Path(sys.argv[2])
    if command == "lines":
        share = int(sys.argv[3]) / 100
        s = priced(transcript, None)
        if s is not None:
            lines = (line_for(s, SLICE, 0.0), line_for(s, SLICE, share))
            print(*("-" if line is None else line for line in lines))
    elif command == "notice":
        s = priced(transcript, int(sys.argv[3]))
        if s is not None:
            saving = saving_over(s, SLICE)
            print(
                f"Relaying now costs ~${saving.up_front:.2f} up front and {verdict(saving)} over the next"
                f" {SLICE // 1000}k tokens of work, reorientation priced from"
                f" {s.reorientation.source}."
            )


if __name__ == "__main__":
    main()
