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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# The ledger's lib is reached by path, as its own scripts reach it.
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "costs"))

from lib.pricing import (
    SYNTHETIC_MODEL,
    Rates,
    Response,
    is_response_record,
    parse_prices,
    parse_response,
    rate_key,
)

STATE = ROOT / "tmp" / "cold-cache"
PRICES = ROOT / ".claude" / "costs" / "prices.json"
STOP_WORD = "!pass"
DEFAULT_MIN_USD = 0.30

# What the transcript cannot tell, as estimates: the summary /compact writes,
# what it keeps beside the summary, and what a fresh session reads before it
# knows where things are.
SUMMARY_OUT = 8_000
KEPT_AFTER_COMPACT = 15_000
RAMP_UP = 60_000
RAMP_UP_REQUESTS = 10
RAMP_UP_OUT_PER_REQUEST = 700

TTL_1H = 3600
TTL_5M = 300


# --- The cost model -----------------------------------------------------------


@dataclass(frozen=True)
class Session:
    context: int  # tokens the next request re-sends
    shared: int  # the prefix every session in the environment keeps warm
    start: int  # the context a fresh session opens with


@dataclass(frozen=True)
class Option:
    once: float  # USD, paid before the first answer
    per_request: float  # USD, every request after
    context_after: int


def usd(tokens: float, rate: float) -> float:
    return tokens * rate / 1_000_000


def options(s: Session, r: Rates, write: float) -> Dict[str, Option]:
    """Carry on, /compact and a new session. Growth from further work is the
    same under all three, so it is left out: it moves no crossing point."""
    shared = min(s.shared, s.start, s.context)
    cold = s.context - shared
    after_compact = s.start + KEPT_AFTER_COMPACT
    after_fresh = s.start + RAMP_UP
    return {
        "carry on": Option(usd(cold, write) + usd(shared, r.cache_read), usd(s.context, r.cache_read), s.context),
        # A cold /compact bills the history as input, per the Claude Code docs.
        "/compact": Option(
            usd(cold, r.input) + usd(shared, r.cache_read) + usd(SUMMARY_OUT, r.output)
            + usd(after_compact - shared, write),
            usd(after_compact, r.cache_read),
            after_compact,
        ),
        "new session": Option(
            usd(s.start - shared + RAMP_UP, write)
            + usd(RAMP_UP_REQUESTS * (s.start + RAMP_UP / 2), r.cache_read)
            + usd(RAMP_UP_REQUESTS * RAMP_UP_OUT_PER_REQUEST, r.output),
            usd(after_fresh, r.cache_read),
            after_fresh,
        ),
    }


def payback(option: Option, baseline: Option) -> Optional[float]:
    """Requests until `option` has cost less in total than `baseline`: 0 when it
    is cheaper from the start, None when it never catches up."""
    extra = option.once - baseline.once
    saved = baseline.per_request - option.per_request
    if extra <= 0:
        return 0 if saved >= 0 else None
    return extra / saved if saved > 0 else None


# --- Reading the transcript ---------------------------------------------------


@dataclass(frozen=True)
class History:
    first: Response
    last: Response
    ttl: int


def own_responses(transcript: Path):
    for line in transcript.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue  # the line Claude Code is still writing
        if not is_response_record(record):
            continue
        response = parse_response(record, str(transcript), [])
        if not response.is_sidechain and response.model != SYNTHETIC_MODEL:
            yield response


def read_history(transcript: Path) -> Optional[History]:
    first = last = None
    hour = False
    for response in own_responses(transcript):
        first = first or response
        last = response
        hour = hour or response.tokens.cache_write_1h_tokens > 0
    if first is None or last is None:
        return None
    return History(first, last, TTL_1H if hour else TTL_5M)


def context_of(response: Response) -> int:
    t = response.tokens
    return t.input_tokens + t.cache_read_tokens + t.cache_write_5m_tokens + t.cache_write_1h_tokens


def epoch(timestamp: Optional[str]) -> Optional[float]:
    if timestamp is None:
        return None
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()


# --- The two events -----------------------------------------------------------


def flag_path(session: str) -> Path:
    return STATE / f"{session}.json"


def blocked_path(session: str) -> Path:
    return STATE / f"{session}.blocked"


def on_session_start(event: Dict[str, Any], session: str) -> None:
    flag = flag_path(session)
    if event.get("source") in ("resume", "fork") and event.get("prompt_cache_likely_expired") is True:
        STATE.mkdir(parents=True, exist_ok=True)
        fields = ("seconds_since_last_response", "context_tokens", "estimated_cache_write_usd")
        flag.write_text(json.dumps({**{k: event.get(k) for k in fields}, "written_at": time.time()}))
    else:
        flag.unlink(missing_ok=True)


def read_flag(session: str, last_at: Optional[float]) -> Optional[Dict[str, Any]]:
    """The resume's own reading, while no response has landed since it."""
    flag = flag_path(session)
    if not flag.exists():
        return None
    data = json.loads(flag.read_text())
    if last_at is not None and last_at > data["written_at"]:
        flag.unlink()
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
    rates = parse_prices(PRICES.read_text(encoding="utf-8")).rates.get(
        rate_key(history.last.model, history.last.speed)
    )
    if rates is None:
        return None
    write = rates.cache_write_1h if history.ttl == TTL_1H else rates.cache_write_5m
    first = history.first.tokens
    return options(Session(context, first.cache_read_tokens, context_of(history.first)), rates, write)


def on_prompt(event: Dict[str, Any], session: str, min_usd: float) -> Optional[str]:
    """The block reason, or None to let the prompt through."""
    prompt = event.get("prompt") or ""
    transcript = Path(event.get("transcript_path") or "")
    if prompt.lstrip().startswith("/") or STOP_WORD in prompt or not transcript.is_file():
        return None
    history = read_history(transcript)
    if history is None:
        return None
    last_at = epoch(history.last.timestamp)
    flag = read_flag(session, last_at)
    blocked = blocked_path(session)
    if blocked.exists() and blocked.read_text() == history.last.message_id:
        flag_path(session).unlink(missing_ok=True)
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

    STATE.mkdir(parents=True, exist_ok=True)
    blocked.write_text(history.last.message_id)
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
    kind = event.get("hook_event_name")
    if kind == "SessionStart":
        on_session_start(event, session)
    elif kind == "UserPromptSubmit":
        text = on_prompt(event, session, min_usd)
        if text is not None:
            print(json.dumps({"decision": "block", "reason": text}))


if __name__ == "__main__":
    main()
