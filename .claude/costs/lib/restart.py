"""What the ways on from a session cost, read off its transcript and priced from
`prices.json`: carrying on against `/relay`, or against a fresh session.
`.claude/context-budget/CLAUDE.md` carries why the model reads what it reads.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

from lib.orientation import Phase, is_boundary
from lib.pricing import (
    SYNTHETIC_MODEL,
    PriceTable,
    Rates,
    Response,
    TranscriptSources,
    UnpricedError,
    is_response_record,
    parse_response,
    subagents_of,
    summarise_transcript,
)
from lib.rows import parse_session_cost

# What the transcript cannot tell, as estimates: what the relay's summary turn
# writes, and — before any orientation has been measured — what a fresh session
# reads before it acts.
SUMMARY_OUT = 8_000
RAMP_UP = 60_000
RAMP_UP_REQUESTS = 10
RAMP_UP_OUT_PER_REQUEST = 700
# How many requests a token of context growth takes, until the session has grown
# far enough since its last boundary to be measured.
REQUESTS_PER_TOKEN = 40 / 100_000
MIN_GROWTH = 20_000

# The opening prompt of a session `/relay` started.
RELAY_TAKE = "/relay take"

TTL_1H = 3600
TTL_5M = 300


# --- The cost model -----------------------------------------------------------


@dataclass(frozen=True)
class Reorientation:
    context: int  # tokens the successor carries once it acts
    cost_usd: float  # what getting there costs it
    source: str  # what it was priced from, as the notices name it


@dataclass(frozen=True)
class Session:
    context: int  # tokens the next request re-sends
    shared: int  # the prefix every session in the environment keeps warm
    requests_per_token: float
    reorientation: Reorientation
    rates: Rates
    write: float  # the cache-write rate the session's TTL bills


@dataclass(frozen=True)
class Saving:
    usd: float  # what relaying saves over the slice, up-front costs included
    share: float  # of what carrying on costs over it
    relay: float  # USD a relay pays before its successor's first action


def usd(tokens: float, rate: float) -> float:
    return tokens * rate / 1_000_000


def recache(s: Session) -> float:
    shared = min(s.shared, s.context)
    return usd(s.context - shared, s.write) + usd(shared, s.rates.cache_read)


def relay_once(s: Session) -> float:
    """The summary turn, one request at the whole context, plus the successor's
    reorientation."""
    return usd(s.context, s.rates.cache_read) + usd(SUMMARY_OUT, s.rates.output) + s.reorientation.cost_usd


def saving_over(s: Session, slice_tokens: int) -> Saving:
    """Carrying on against relaying, over the requests `slice_tokens` of context
    growth takes. New context is written at the same rate under both, so the
    writes cancel out of the saving and stay in carrying on's total."""
    n = slice_tokens * s.requests_per_token
    r = s.rates.cache_read
    growth = usd(slice_tokens, s.write)
    carry = usd(n * (s.context + slice_tokens / 2), r) + growth
    once = relay_once(s)
    relay = once + usd(n * (s.reorientation.context + slice_tokens / 2), r) + growth
    return Saving(carry - relay, (carry - relay) / carry, once)


def verdict(saving: Saving) -> str:
    """What relaying does against carrying on, as both hooks' notices say it."""
    if abs(saving.usd) < 0.01:
        return "about breaks even with carrying on"
    if saving.usd > 0:
        return f"saves ~${saving.usd:.2f} (~{saving.share:.0%})"
    return f"costs ~${-saving.usd:.2f} more than carrying on"


def line_for(s: Session, slice_tokens: int, share: float) -> Optional[int]:
    """The context at which a warm relay's saving over `slice_tokens` reaches
    `share` of carrying on's cost: `saving_over` solved for context. None when
    no context gets there."""
    n = slice_tokens * s.requests_per_token
    r = s.rates.cache_read / 1_000_000
    fixed = usd(SUMMARY_OUT, s.rates.output) + s.reorientation.cost_usd
    per_token = r * (n - 1 - share * n)
    if per_token <= 0:
        return None
    reached = n * r * s.reorientation.context + fixed + share * (
        n * r * slice_tokens / 2 + usd(slice_tokens, s.write)
    )
    return round(reached / per_token)


# --- Reading the transcript ---------------------------------------------------


@dataclass(frozen=True)
class History:
    first: Response
    last: Response
    ttl: int
    # None until the session has grown `MIN_GROWTH` since its last boundary.
    requests_per_token: Optional[float]


def context_of(response: Response) -> int:
    return response.tokens.context_tokens()


def own_responses(transcript: Path) -> Iterator[Optional[Response]]:
    """The session's own responses, each once, with None at each compaction
    boundary: sidechains and `<synthetic>` records are another agent's and no
    model's."""
    seen = set()
    for line in transcript.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue  # the line Claude Code is still writing
        if is_boundary(record):
            yield None
            continue
        if not is_response_record(record):
            continue
        response = parse_response(record, str(transcript), [])
        if response.is_sidechain or response.model == SYNTHETIC_MODEL or response.message_id in seen:
            continue
        seen.add(response.message_id)
        yield response


def read_history(transcript: Path) -> Optional[History]:
    first = last = since = None
    hour = False
    requests = 0
    for response in own_responses(transcript):
        if response is None:
            since, requests = None, 0
            continue
        first = first or response
        last = response
        since = since or response
        requests += 1
        hour = hour or response.tokens.cache_write_1h_tokens > 0
    if first is None or last is None or since is None:
        return None
    growth = context_of(last) - context_of(since)
    rate = (requests - 1) / growth if growth >= MIN_GROWTH else None
    return History(first, last, TTL_1H if hour else TTL_5M, rate)


def rates_of(history: History, prices: PriceTable) -> Optional[Rates]:
    return prices.rates_for(history.last.model, history.last.speed)


def write_rate(r: Rates, ttl: int) -> float:
    return r.cache_write_1h if ttl == TTL_1H else r.cache_write_5m


def epoch(timestamp: Optional[str]) -> Optional[float]:
    if timestamp is None:
        return None
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()


# --- Pricing the successor's reorientation ------------------------------------


def acted(phase: Optional[Phase]) -> Optional[Tuple[int, float]]:
    if phase is None or phase.context_tokens is None:
        return None
    return phase.context_tokens, phase.spend.cost_usd


def relayed(opening_prompt: Optional[str]) -> bool:
    return (opening_prompt or "").startswith(RELAY_TAKE)


def own_orientation(transcript: Path, prices: PriceTable) -> Tuple[bool, Optional[Tuple[int, float]]]:
    """Whether `/relay` started this session, and what its orientation cost —
    subagents included, as the ledger measures it. Unmeasured when any response
    has no rates."""
    sources = TranscriptSources(transcript.read_text(encoding="utf-8"), subagents_of(transcript))
    try:
        cost = summarise_transcript(sources, prices, "")
    except UnpricedError:
        return False, None
    return relayed(cost.opening_prompt), acted(cost.orientation)


def ledger_orientations(sessions: Path, relay: bool) -> List[Tuple[int, float]]:
    """The orientation of each session the ledger records `/relay` starting, or
    of each it records starting any other way."""
    found = []
    for path in sorted(sessions.glob("*/*.json")):
        row = parse_session_cost(path.read_text(encoding="utf-8"), str(path))
        measured = acted(row.orientation)
        if relayed(row.opening_prompt) == relay and measured is not None:
            found.append(measured)
    return found


def estimated(first: Response, r: Rates, write: float) -> Tuple[int, float]:
    start = context_of(first)
    shared = min(first.tokens.cache_read_tokens, start)
    return start + RAMP_UP, (
        usd(start - shared + RAMP_UP, write)
        + usd(RAMP_UP_REQUESTS * (start + RAMP_UP / 2), r.cache_read)
        + usd(RAMP_UP_REQUESTS * RAMP_UP_OUT_PER_REQUEST, r.output)
    )


def reorientation_of(
    transcript: Path, history: History, prices: PriceTable, sessions: Path, r: Rates, relay: bool
) -> Reorientation:
    """What a successor spends before it acts — one `/relay` started, or a fresh
    one. From the first source that has a measurement: this session's own, when
    it started the same way; the ledger's sessions that did; this session's own
    anyway; the `RAMP_UP*` estimate."""
    was_relayed, own = own_orientation(transcript, prices)
    own_name = "this session's own reorientation" if was_relayed else "this session's own orientation"
    if own is not None and was_relayed == relay:
        return Reorientation(*own, own_name)
    ledger = ledger_orientations(sessions, relay)
    if ledger:
        kind = "relayed" if relay else "fresh"
        return Reorientation(
            round(sum(c for c, _ in ledger) / len(ledger)),
            sum(u for _, u in ledger) / len(ledger),
            f"the mean of {len(ledger)} {kind} session{'s' if len(ledger) > 1 else ''} in the ledger",
        )
    if own is not None:
        return Reorientation(*own, own_name)
    return Reorientation(
        *estimated(history.first, r, write_rate(r, history.ttl)),
        "an estimate, no orientation having been measured yet",
    )


def session_of(
    transcript: Path, history: History, context: int, prices: PriceTable, project: Path, relay: bool
) -> Optional[Session]:
    """None when the session's model has no row in the price table. `relay` says
    which successor it is priced against; the ledger read is `project`'s own."""
    r = rates_of(history, prices)
    if r is None:
        return None
    return Session(
        context,
        history.first.tokens.cache_read_tokens,
        history.requests_per_token or REQUESTS_PER_TOKEN,
        reorientation_of(transcript, history, prices, project / ".claude" / "costs" / "sessions", r, relay),
        r,
        write_rate(r, history.ttl),
    )
