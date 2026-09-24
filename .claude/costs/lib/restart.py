"""What each way on from a session costs — carry on, `/compact`, or a new
session — read off its transcript and priced from `prices.json`. The cold-cache
guard prices them after the prompt cache expired, the context budget hook while
it is warm; `.claude/cold-cache/CLAUDE.md` carries why the model reads what it
reads.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from lib.pricing import (
    SYNTHETIC_MODEL,
    PriceTable,
    Rates,
    Response,
    cost_of,
    is_response_record,
    parse_response,
    rate_key,
)

# What the transcript cannot tell, as estimates: the summary /compact writes,
# what it keeps beside the summary, and — for a session that has not finished
# warming up — what a fresh one reads before it knows where things are.
SUMMARY_OUT = 8_000
KEPT_AFTER_COMPACT = 15_000
RAMP_UP = 60_000
RAMP_UP_REQUESTS = 10
RAMP_UP_OUT_PER_REQUEST = 700

TTL_1H = 3600
TTL_5M = 300

# The tool calls that end the warm-up: the session stopped looking and started
# producing. A Bash call counts when it commits.
WRITE_TOOLS = ("Edit", "Write", "NotebookEdit")


# --- The cost model -----------------------------------------------------------


@dataclass(frozen=True)
class WarmUp:
    context: int  # tokens carried when the session started producing
    cost_usd: float  # what getting there cost, start-up write included


@dataclass(frozen=True)
class Session:
    context: int  # tokens the next request re-sends
    shared: int  # the prefix every session in the environment keeps warm
    start: int  # the context a fresh session opens with
    warm_up: WarmUp  # what a fresh session pays to get back to work


@dataclass(frozen=True)
class Option:
    once: float  # USD, paid before the first answer
    per_request: float  # USD, every request after
    context_after: int


def usd(tokens: float, rate: float) -> float:
    return tokens * rate / 1_000_000


def estimated_warm_up(start: int, shared: int, r: Rates, write: float) -> WarmUp:
    shared = min(shared, start)
    return WarmUp(
        start + RAMP_UP,
        usd(start - shared + RAMP_UP, write)
        + usd(RAMP_UP_REQUESTS * (start + RAMP_UP / 2), r.cache_read)
        + usd(RAMP_UP_REQUESTS * RAMP_UP_OUT_PER_REQUEST, r.output),
    )


def new_session(s: Session, r: Rates) -> Option:
    return Option(s.warm_up.cost_usd, usd(s.warm_up.context, r.cache_read), s.warm_up.context)


def after_expiry(s: Session, r: Rates, write: float) -> Dict[str, Option]:
    """The three options once the cache has expired. Growth from further work is
    the same under all three, so it is left out: it moves no crossing point."""
    shared = min(s.shared, s.start, s.context)
    cold = s.context - shared
    after_compact = s.start + KEPT_AFTER_COMPACT
    return {
        "carry on": Option(usd(cold, write) + usd(shared, r.cache_read), usd(s.context, r.cache_read), s.context),
        # A cold /compact bills the history as input, per the Claude Code docs.
        "/compact": Option(
            usd(cold, r.input) + usd(shared, r.cache_read) + usd(SUMMARY_OUT, r.output)
            + usd(after_compact - shared, write),
            usd(after_compact, r.cache_read),
            after_compact,
        ),
        "new session": new_session(s, r),
    }


def while_warm(s: Session, r: Rates, write: float) -> Dict[str, Option]:
    """The three options with the cache still warm, where carrying on costs
    nothing up front and the others trade a one-off for a smaller context."""
    shared = min(s.shared, s.start)
    after_compact = s.start + KEPT_AFTER_COMPACT
    return {
        "carry on": Option(0.0, usd(s.context, r.cache_read), s.context),
        "/compact": Option(
            usd(s.context, r.cache_read) + usd(SUMMARY_OUT, r.output)
            + usd(after_compact - shared, write) + usd(shared, r.cache_read),
            usd(after_compact, r.cache_read),
            after_compact,
        ),
        "new session": new_session(s, r),
    }


def break_even_context(s: Session, r: Rates, requests: float) -> int:
    """The context at which a new session pays for itself within `requests`,
    against carrying on while warm: `payback` of the two, solved for context."""
    return s.warm_up.context + round(s.warm_up.cost_usd / usd(requests, r.cache_read))


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
    # None until the session has produced something, or when a response on the
    # way there has no row in the price table.
    warm_up: Optional[WarmUp]


def context_of(response: Response) -> int:
    t = response.tokens
    return t.input_tokens + t.cache_read_tokens + t.cache_write_5m_tokens + t.cache_write_1h_tokens


def ends_warm_up(record: Dict[str, Any], response: Response) -> bool:
    if response.stop_reason == "end_turn":
        return True
    content = record["message"].get("content")
    for block in content if isinstance(content, list) else []:
        if not isinstance(block, dict) or block.get("type") != "tool_use":
            continue
        name = block.get("name")
        command = (block.get("input") or {}).get("command")
        if name in WRITE_TOOLS or (name == "Bash" and isinstance(command, str) and "git commit" in command):
            return True
    return False


def read_history(transcript: Path, prices: PriceTable) -> Optional[History]:
    """The session's own responses: sidechains and `<synthetic>` records are
    another agent's and no model's."""
    first = last = warm_up = None
    hour = False
    seen = set()
    spent: Optional[float] = 0.0
    for line in transcript.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue  # the line Claude Code is still writing
        if not is_response_record(record):
            continue
        response = parse_response(record, str(transcript), [])
        if response.is_sidechain or response.model == SYNTHETIC_MODEL:
            continue
        first = first or response
        last = response
        hour = hour or response.tokens.cache_write_1h_tokens > 0
        if warm_up is not None:
            continue
        # One response is written as one record per content block, each
        # carrying the whole response's usage.
        if response.message_id not in seen and spent is not None:
            seen.add(response.message_id)
            rates = prices.rates.get(rate_key(response.model, response.speed))
            spent = None if rates is None else spent + cost_of(response.tokens, rates)
        if ends_warm_up(record, response) and spent is not None:
            warm_up = WarmUp(context_of(response), spent)
    if first is None or last is None:
        return None
    return History(first, last, TTL_1H if hour else TTL_5M, warm_up)


def rates_of(history: History, prices: PriceTable) -> Optional[Rates]:
    return prices.rates.get(rate_key(history.last.model, history.last.speed))


def write_rate(r: Rates, ttl: int) -> float:
    return r.cache_write_1h if ttl == TTL_1H else r.cache_write_5m


def session_of(history: History, context: int, r: Rates) -> Session:
    shared = history.first.tokens.cache_read_tokens
    start = context_of(history.first)
    warm_up = history.warm_up or estimated_warm_up(start, shared, r, write_rate(r, history.ttl))
    return Session(context, shared, start, warm_up)


def epoch(timestamp: Optional[str]) -> Optional[float]:
    if timestamp is None:
        return None
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()
