"""Prices a Claude Code transcript at Claude API rates, for the `Stop` hook that
writes one session's row and the report that sums many.

`.claude/costs/CLAUDE.md` carries the transcript's shape and what the totals
leave out.
"""

from __future__ import annotations

from typing import Dict, List, Mapping, Optional, Set

from lib.billed import Event, Telemetry, compaction_costs, disagreement
from lib.identity import (
    cost_state_of,
    kind_of,
    operator_of,
    pr_number_of,
    prompt_text_of,
    session_url_in,
)
from lib.orientation import (
    Priced,
    Trail,
    boundary_of,
    is_boundary,
    measure,
    note_results,
    summary_chars_of,
)
from lib.prices import PriceTable, rate_key
from lib.rows import SessionCost
from lib.shape import json_lines
from lib.tally import Tally, billable_tokens, cost_of
from lib.transcript import (
    SYNTHETIC_MODEL,
    Response,
    TranscriptSources,
    is_response_record,
    merged,
    parse_response,
)


class UnpricedError(ValueError):
    """A response under a `(model, speed)` pair the rate table has no rates for."""


# Marks the warning `at_stop` raises, which is what lets a rewrite of the row
# carry it forward: the next run reads a transcript that has caught up.
UNWRITTEN_TAIL = "not yet written when the Stop hook read the transcript"


def is_unwritten_tail(warning: str) -> bool:
    return UNWRITTEN_TAIL in warning


def summarise_transcript(
    sources: TranscriptSources,
    prices: PriceTable,
    fallback_session_id: str,
    at_stop: bool = False,
    events: Optional[Mapping[str, Event]] = None,
) -> SessionCost:
    """Raises `UnpricedError` when a transcript names a `(model, speed)` pair the
    table cannot price, and `ShapeError` when a response record does not parse:
    an unpriced response silently counted as free is the one failure that makes
    the whole ledger a lie.

    `at_stop` says the turn is over, so the session's own last response should
    be the `end_turn` that closed it; anything else is warned about as a tail
    the file had not yet been given.

    `events` are the session's telemetry by request id. A response they cover
    keeps its table price, the event's checking it; an event no response
    matches is a call the transcript never recorded, and is added to the
    totals at the event's own price."""
    warnings: List[str] = []
    last_own: Optional[Response] = None
    # Each response as merged from its records so far, by message id.
    seen: Dict[str, Response] = {}
    by_rate: Dict[str, Tally] = {}
    total, own_turns, subagents = Tally(), Tally(), Tally()
    unpriced: Set[str] = set()
    timestamps: List[str] = []
    prs: Set[int] = set()
    session_id: Optional[str] = None
    branch: Optional[str] = None
    cwd: Optional[str] = None
    opening_prompt: Optional[str] = None
    url: Optional[str] = None
    operator: Optional[str] = None
    claude_code_total_usd: Optional[float] = None
    trail = Trail()
    # The priced responses by id, which a later record of one adds its calls to.
    held: Dict[str, Priced] = {}
    matched: Set[str] = set()
    matched_event_usd = 0.0
    matched_table_usd = 0.0
    unfinished = 0

    # `delegated` forces the bucket for a subagent's own file. Its records carry
    # `isSidechain` too, but the file they are in is the fact that does not
    # depend on a flag having been set.
    def scan(jsonl: str, label: str, delegated: bool) -> None:
        nonlocal session_id, branch, cwd, opening_prompt, url, operator
        nonlocal claude_code_total_usd, last_own, matched_event_usd, matched_table_usd
        nonlocal unfinished
        for where, line, record in json_lines(jsonl, label):
            kind = kind_of(record)
            # The session's own identity, which only its own file describes.
            if not delegated:
                if kind == "pr-link":
                    pr = pr_number_of(record)
                    if pr is not None:
                        prs.add(pr)
                    continue
                if is_boundary(record):
                    trail.boundaries.append(boundary_of(record, where))
                    continue
                if kind == "user":
                    note_results(record, trail.result_chars)
                    summary = summary_chars_of(record)
                    if summary is not None and trail.boundaries:
                        trail.boundaries[-1].summary_chars = summary
                    if opening_prompt is None:
                        opening_prompt = prompt_text_of(record)
                    continue
                if kind == "cost-state":
                    # Last write wins: Claude Code rewrites this as it goes.
                    state = cost_state_of(record)
                    if state is not None:
                        claude_code_total_usd = state
                    continue
                if kind == "attachment":
                    if url is None:
                        url = session_url_in(record, line)
                    # The first one any SessionStart resolved, since a resume
                    # runs the hook again.
                    if operator is None:
                        operator = operator_of(record)
                    continue

            if not is_response_record(record):
                continue
            response = parse_response(record, where, warnings)
            if not (delegated or response.is_sidechain or response.model == SYNTHETIC_MODEL):
                last_own = response
            earlier = seen.get(response.message_id)
            if earlier is not None:
                whole = seen[response.message_id] = merged(earlier, response)
                priced = held.get(response.message_id)
                if priced is not None:
                    priced.calls = list(whole.calls)
                    priced.ended_turn = whole.stop_reason == "end_turn"
                continue
            seen[response.message_id] = response

            if not delegated:
                if session_id is None:
                    session_id = response.session_id
                # Last write wins: a session that renames its branch mid-flight
                # is filed under where its work ended up.
                if response.git_branch is not None:
                    branch = response.git_branch
                if response.cwd is not None:
                    cwd = response.cwd
            if response.timestamp is not None:
                timestamps.append(response.timestamp)

            tokens = response.tokens
            if response.model == SYNTHETIC_MODEL:
                billable = billable_tokens(tokens)
                if billable > 0:
                    warnings.append(
                        f"{response.message_id}: a {SYNTHETIC_MODEL} record carries"
                        f" {billable} billable tokens and was not priced"
                    )
                continue

            # `byRate` keeps the id the response named, as telemetry's own
            # events do, whichever row priced it.
            key = rate_key(response.model, response.speed)
            rates = prices.rates_for(response.model, response.speed, tokens.context_tokens())
            if rates is None:
                unpriced.add(key)
                continue

            event = events.get(response.request_id or "") if events else None
            # A record with no `stop_reason` carries the usage the stream
            # started with, its output a partial count; the event has the final.
            if event is not None:
                tokens.output_tokens = event.tokens.output_tokens
            elif response.stop_reason is None:
                unfinished += 1
            tokens.responses = 1
            tokens.cost_usd = cost_of(tokens, rates)
            if event is not None:
                matched.add(event.request_id)
                matched_event_usd += event.tokens.cost_usd
                matched_table_usd += tokens.cost_usd
            by_rate.setdefault(key, Tally()).add(tokens)
            total.add(tokens)
            own = not (delegated or response.is_sidechain)
            (own_turns if own else subagents).add(tokens)
            # A response with no timestamp has no place among the phases.
            if response.timestamp is not None:
                held[response.message_id] = Priced(
                    message_id=response.message_id,
                    at=response.timestamp,
                    seq=len(trail.responses),
                    own=own,
                    ended_turn=response.stop_reason == "end_turn",
                    cwd=response.cwd,
                    tokens=tokens,
                    rates=rates,
                    calls=list(response.calls),
                )
                trail.responses.append(held[response.message_id])

    scan(sources.main, "transcript", False)
    for index, delegated in enumerate(sources.subagents, start=1):
        scan(delegated, f"subagent transcript {index}", True)

    if unpriced:
        raise UnpricedError(
            f"No rates for {', '.join(sorted(unpriced))} in the price table (as of"
            f" {prices.as_of}). Add them to .claude/costs/prices.json — a response"
            " counted as free is worse than no ledger at all."
        )

    if at_stop and last_own is not None and last_own.stop_reason != "end_turn":
        warnings.append(
            f"{last_own.message_id}: the session's last response stopped on"
            f" `{last_own.stop_reason}` rather than `end_turn` — the turn's tail was"
            f" {UNWRITTEN_TAIL}"
        )

    if unfinished:
        warnings.append(
            f"{unfinished} responses were written with the usage their stream started"
            " with — no `stop_reason`, as a subagent's transcript writes each one —"
            " and no event to correct it, so their output tokens are a floor"
        )

    telemetry: Optional[Telemetry] = None
    unseen: List[Event] = []
    if events is not None:
        telemetry = Telemetry(
            events=len(events),
            matched=len(matched),
            matched_table_usd=matched_table_usd,
            matched_event_usd=matched_event_usd,
        )
        unseen = [event for key, event in events.items() if key not in matched]
        for event in unseen:
            total.add(event.tokens)
            by_rate.setdefault(rate_key(event.model, event.speed), Tally()).add(event.tokens)
            telemetry.unseen.setdefault(event.query_source, Tally()).add(event.tokens)
        mismatch = disagreement(telemetry)
        if mismatch is not None:
            warnings.append(mismatch)

    in_order = sorted(timestamps)
    orientation, compactions = measure(trail)
    for compaction, billed in zip(
        compactions, compaction_costs(unseen, [c.at for c in compactions])
    ):
        compaction.billed_usd = billed
    return SessionCost(
        session_id=session_id if session_id is not None else fallback_session_id,
        branch=branch,
        cwd=cwd,
        opening_prompt=opening_prompt,
        prs=sorted(prs),
        url=url,
        operator=operator,
        first_response_at=in_order[0] if in_order else None,
        last_response_at=in_order[-1] if in_order else None,
        prices_as_of=prices.as_of,
        claude_code_total_usd=claude_code_total_usd,
        total=total,
        own_turns=own_turns,
        subagents=subagents,
        by_rate=by_rate,
        warnings=warnings,
        orientation=orientation,
        compactions=compactions,
        telemetry=telemetry,
    )
