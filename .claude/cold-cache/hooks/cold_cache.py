#!/usr/bin/env python3
"""`SessionStart` + `UserPromptSubmit` hook: stop the first prompt after the
prompt cache has expired and price the ways on. `.claude/cold-cache/CLAUDE.md`
carries why it reads what it reads.

Stdout is the interface: nothing lets the prompt through, a `block` decision
stops it. Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

# The ledger's lib is reached by path, as its own scripts reach it.
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "costs"))

from lib.pricing import parse_prices
from lib.restart import (
    History,
    Option,
    after_expiry,
    context_of,
    epoch,
    payback,
    rates_of,
    read_history,
    session_of,
    write_rate,
)

PRICES = ROOT / ".claude" / "costs" / "prices.json"
STOP_WORD = "!pass"
DEFAULT_MIN_USD = 0.30


# --- The two events -----------------------------------------------------------


@dataclass(frozen=True)
class State:
    """`tmp/cold-cache/` under the project: the resume's reading, and the last
    response a block was raised against."""

    dir: Path
    session: str

    @property
    def flag(self) -> Path:
        return self.dir / f"{self.session}.json"

    @property
    def blocked(self) -> Path:
        return self.dir / f"{self.session}.blocked"


def on_session_start(event: Dict[str, Any], state: State) -> None:
    if event.get("source") in ("resume", "fork") and event.get("prompt_cache_likely_expired") is True:
        state.dir.mkdir(parents=True, exist_ok=True)
        fields = ("seconds_since_last_response", "context_tokens", "estimated_cache_write_usd")
        state.flag.write_text(json.dumps({**{k: event.get(k) for k in fields}, "written_at": time.time()}))
    else:
        state.flag.unlink(missing_ok=True)


def read_flag(state: State, last_at: Optional[float]) -> Optional[Dict[str, Any]]:
    """The resume's own reading, while no response has landed since it."""
    if not state.flag.exists():
        return None
    data = json.loads(state.flag.read_text())
    if last_at is not None and last_at > data["written_at"]:
        state.flag.unlink()
        return None
    return data


def span(seconds: float) -> str:
    return f"{seconds / 3600:.1f} h" if seconds >= 5400 else f"{seconds / 60:.0f} min"


def kilo(tokens: float) -> str:
    return f"{tokens / 1000:.0f}k"


def against_carry_on(name: str, option: Option, carry_on: Option) -> str:
    saved = (carry_on.per_request - option.per_request) * 100
    back = payback(option, carry_on)
    if back is None:
        tail = "and never catches up with carrying on"
    elif back == 0:
        tail = "so it is cheaper from the first request"
    else:
        tail = f"so it pays for itself after ~{max(1, round(back))} requests"
    return f"{name}: ≈${option.once:.2f} up front, then {saved:.1f}¢ less per API request, {tail}."


def reason(idle: float, context: int, priced: Optional[Dict[str, Option]], claude_code_usd: Optional[float]) -> str:
    lines = [f"Prompt cache expired: {span(idle)} since the last response, {kilo(context)} tokens to re-cache."]
    if priced is not None:
        carry_on = priced["carry on"]
        lines.append(f"Carry on: ≈${carry_on.once:.2f} up front.")
        lines.append(against_carry_on("/compact", priced["/compact"], carry_on))
        lines.append(against_carry_on("New session", priced["new session"], carry_on))
    elif claude_code_usd is not None:
        lines.append(f"Claude Code estimates re-caching at ${claude_code_usd:.2f}; this model has no row in the price table to compare the options.")
    else:
        lines.append("This model has no row in the price table, so the options are not priced.")
    lines.append(
        "This message was not sent: run /compact first, or click Edit prompt and send it again"
        f" to carry on (a message containing {STOP_WORD} always goes through)."
    )
    return " ".join(lines)


def price(history: History, context: int) -> Optional[Dict[str, Option]]:
    prices = parse_prices(PRICES.read_text(encoding="utf-8"))
    rates = rates_of(history, prices)
    if rates is None:
        return None
    return after_expiry(session_of(history, context, rates), rates, write_rate(rates, history.ttl))


def on_prompt(event: Dict[str, Any], state: State, min_usd: float) -> Optional[str]:
    """The block reason, or None to let the prompt through."""
    prompt = event.get("prompt") or ""
    transcript = Path(event.get("transcript_path") or "")
    if prompt.lstrip().startswith("/") or STOP_WORD in prompt or not transcript.is_file():
        return None
    history = read_history(transcript, parse_prices(PRICES.read_text(encoding="utf-8")))
    if history is None:
        return None
    last_at = epoch(history.last.timestamp)
    flag = read_flag(state, last_at)
    if state.blocked.exists() and state.blocked.read_text() == history.last.message_id:
        state.flag.unlink(missing_ok=True)
        return None

    now = time.time()
    if flag is not None:
        idle = flag["seconds_since_last_response"] + now - flag["written_at"]
        context = flag["context_tokens"]
    elif last_at is not None and now - last_at > history.ttl:
        idle, context = now - last_at, context_of(history.last)
    else:
        return None

    priced = price(history, context)
    claude_code_usd = flag.get("estimated_cache_write_usd") if flag else None
    cost = priced["carry on"].once if priced else claude_code_usd
    if cost is not None and cost < min_usd:
        return None

    state.dir.mkdir(parents=True, exist_ok=True)
    state.blocked.write_text(history.last.message_id)
    return reason(idle, context, priced, claude_code_usd)


def main() -> None:
    if os.environ.get("COLD_CACHE_GUARD") == "off":
        return
    try:
        min_usd = float(os.environ.get("COLD_CACHE_MIN_USD", DEFAULT_MIN_USD))
    except ValueError:
        print("cold-cache: COLD_CACHE_MIN_USD must be a number of dollars; no check made.", file=sys.stderr)
        return
    event = json.load(sys.stdin)
    session = event.get("session_id") or ""
    if not session or "/" in session or session.startswith("."):
        return
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ROOT)
    state = State(project / "tmp" / "cold-cache", session)
    kind = event.get("hook_event_name")
    if kind == "SessionStart":
        on_session_start(event, state)
    elif kind == "UserPromptSubmit":
        text = on_prompt(event, state, min_usd)
        if text is not None:
            print(json.dumps({"decision": "block", "reason": text}))


if __name__ == "__main__":
    main()
