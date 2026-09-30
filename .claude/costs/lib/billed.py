"""Claude Code's `api_request` events beside the transcript: one per API call,
the calls the transcript never records included.

`hooks/telemetry_receiver.py` writes them, and this reads them back for the
pricing scan to join to its responses by request id. `.claude/costs/CLAUDE.md`
§ "Telemetry" carries what the events add and what they cannot.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from lib.shape import ShapeError, json_lines, read_count, read_number, read_string, required
from lib.tally import Tally, parse_tally

# The compaction's own request, as Claude Code tags it.
COMPACT = "compact"

# Beyond this, the table and the events disagree about the same responses, so
# one of them is wrong about a rate.
AGREEMENT = 0.01

# The events name the default speed `normal`; the rate table, `standard`.
SPEED_NAMES = {"normal": "standard"}


@dataclass(frozen=True)
class Event:
    request_id: str
    model: str
    speed: str
    query_source: str
    at: str
    tokens: Tally


def parse_events(text: str, where: str) -> Dict[str, Event]:
    """By request id. The exporter may send a batch twice when a delivery is
    retried, so a repeated id is one call, kept once."""
    events: Dict[str, Event] = {}
    for at, _, record in json_lines(text, where):
        if not isinstance(record, dict):
            raise ShapeError(f"{at}: not an object")
        request_id = required(read_string, record, "request_id", at)
        if request_id in events:
            continue
        speed = read_string(record, "speed", at) or "normal"
        events[request_id] = Event(
            request_id=request_id,
            model=required(read_string, record, "model", at),
            speed=SPEED_NAMES.get(speed, speed),
            query_source=read_string(record, "query_source", at) or "unknown",
            at=required(read_string, record, "timestamp", at),
            tokens=Tally(
                input_tokens=required(read_count, record, "input_tokens", at),
                # An event does not split its cache write by TTL, so all of it
                # is filed as the 5-minute kind; the dollars are the event's.
                cache_write_5m_tokens=read_count(record, "cache_creation_tokens", at) or 0,
                cache_read_tokens=read_count(record, "cache_read_tokens", at) or 0,
                output_tokens=required(read_count, record, "output_tokens", at),
                responses=1,
                cost_usd=required(read_number, record, "cost_usd", at),
            ),
        )
    return events


@dataclass
class Telemetry:
    """What the session's events added to its row: the calls no transcript
    recorded, by `query_source`, and the matched responses priced both ways."""

    events: int
    matched: int
    matched_table_usd: float
    matched_event_usd: float
    unseen: Dict[str, Tally] = field(default_factory=dict)


def parse_telemetry(obj: Any, where: str) -> Telemetry:
    if not isinstance(obj, dict):
        raise ShapeError(f"{where}: not an object")
    unseen = obj.get("unseen")
    if not isinstance(unseen, dict):
        raise ShapeError(f"{where}: `unseen` is not an object")
    return Telemetry(
        events=required(read_count, obj, "events", where),
        matched=required(read_count, obj, "matched", where),
        matched_table_usd=required(read_number, obj, "matchedTableUsd", where),
        matched_event_usd=required(read_number, obj, "matchedEventUsd", where),
        unseen={
            source: parse_tally(tally, f"{where} unseen[{source!r}]")
            for source, tally in unseen.items()
        },
    )


def _instant(stamp: str) -> datetime:
    # `fromisoformat` takes a trailing `Z` only from Python 3.11.
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def compaction_costs(unseen: Sequence[Event], boundaries: Sequence[str]) -> List[Optional[float]]:
    """Each boundary's compaction call, priced: the `compact`-tagged call
    nearest it in time. A boundary no tagged call lands nearest stays null."""
    costs: List[Optional[float]] = [None for _ in boundaries]
    if not boundaries:
        return costs
    instants = [_instant(b) for b in boundaries]
    for event in unseen:
        if event.query_source != COMPACT:
            continue
        when = _instant(event.at)
        nearest = min(range(len(instants)), key=lambda i: abs(instants[i] - when))
        costs[nearest] = (costs[nearest] or 0.0) + event.tokens.cost_usd
    return costs


def disagreement(telemetry: Telemetry) -> Optional[str]:
    table, billed = telemetry.matched_table_usd, telemetry.matched_event_usd
    if billed == 0 or abs(table - billed) <= AGREEMENT * billed:
        return None
    return (
        f"prices.json priced the {telemetry.matched} responses the events also"
        f" priced at ${table:.4f}, against the events' ${billed:.4f}: a rate in"
        " the table is likely out of date"
    )
