#!/usr/bin/env python3
"""The context budget's priced figures, for `post-tool-context-budget.sh`:

- `line <transcript>` prints `<tokens> <observed|estimated>` — the context past
  which a new session pays for itself within `CONTEXT_BUDGET_REQUESTS` requests,
  and whether the warm-up it is costed from has happened yet;
- `notice <transcript> <reading>` prints the break-even sentence for the notice.

Prints nothing when the session cannot be priced, which leaves the caller on
its fixed line. Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Tuple

# The ledger's lib is reached by path, as its own scripts reach it.
COSTS = Path(__file__).resolve().parents[2] / "costs"
sys.path.insert(0, str(COSTS))

from lib.pricing import Rates, parse_prices
from lib.restart import (
    History,
    Session,
    break_even_context,
    payback,
    rates_of,
    read_history,
    session_of,
    while_warm,
    write_rate,
)

DEFAULT_REQUESTS = 100


def priced(transcript: Path, context: Optional[int]) -> Optional[Tuple[History, Session, Rates]]:
    prices = parse_prices((COSTS / "prices.json").read_text(encoding="utf-8"))
    history = read_history(transcript, prices)
    if history is None:
        return None
    rates = rates_of(history, prices)
    if rates is None:
        return None
    return history, session_of(history, context or 0, rates), rates


def pays(back: Optional[float]) -> str:
    if back is None:
        return "does not pay for itself at this size"
    return f"pays for itself after ~{max(1, round(back))} more requests"


def main() -> None:
    command, transcript = sys.argv[1], Path(sys.argv[2])
    budget = float(os.environ.get("CONTEXT_BUDGET_REQUESTS") or DEFAULT_REQUESTS)
    if command == "line":
        found = priced(transcript, None)
        if found is not None:
            history, s, rates = found
            kind = "observed" if history.warm_up is not None else "estimated"
            print(break_even_context(s, rates, budget), kind)
    elif command == "notice":
        found = priced(transcript, int(sys.argv[3]))
        if found is not None:
            history, s, rates = found
            options = while_warm(s, rates, write_rate(rates, history.ttl))
            carry_on = options["carry on"]
            print(
                f"Priced off this session's own warm-up, a new session"
                f" {pays(payback(options['new session'], carry_on))},"
                f" and /compact {pays(payback(options['/compact'], carry_on))}."
            )


if __name__ == "__main__":
    main()
