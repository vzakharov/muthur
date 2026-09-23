"""Prices a Claude Code transcript at Claude API rates, for the `Stop` hook that
writes one session's row and the report that sums many.

`.claude/costs/CLAUDE.md` carries the transcript's shape and what the totals
leave out.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set

from lib.identity import (
    cost_state_of,
    kind_of,
    operator_of,
    pr_number_of,
    prompt_text_of,
    session_url_in,
)
from lib.shape import (
    ShapeError,
    camel,
    mistyped,
    read_count,
    read_number,
    read_object,
    read_string,
    required,
)


class UnpricedError(ValueError):
    """A response under a `(model, speed)` pair the rate table has no rates for."""


# --- The rate table -----------------------------------------------------------


@dataclass(frozen=True)
class Rates:
    """USD per million tokens."""

    input: float
    output: float
    cache_write_5m: float
    cache_write_1h: float
    cache_read: float


@dataclass(frozen=True)
class PriceTable:
    as_of: str
    rates: Dict[str, Rates]



def parse_prices(text: str) -> PriceTable:
    table = json.loads(text)
    if not isinstance(table, dict):
        raise ShapeError("prices.json: not an object")
    rates: Dict[str, Rates] = {}
    for key, entry in required(read_object, table, "rates", "prices.json").items():
        where = f"prices.json rates[{key!r}]"
        if not isinstance(entry, dict):
            raise ShapeError(f"{where}: not an object")
        rates[key] = Rates(
            **{f.name: required(read_number, entry, f.name, where) for f in fields(Rates)}
        )
    return PriceTable(as_of=required(read_string, table, "as_of", "prices.json"), rates=rates)


def rate_key(model: str, speed: Optional[str]) -> str:
    """`<model>/<speed>`, the pair a response is billed under."""
    return f"{model}/{speed if speed is not None else 'standard'}"


# --- Tallies ------------------------------------------------------------------


@dataclass
class Tally:
    input_tokens: int = 0
    cache_write_5m_tokens: int = 0
    cache_write_1h_tokens: int = 0
    cache_read_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    responses: int = 0
    cost_usd: float = 0.0

    def add(self, other: Tally) -> None:
        for f in fields(self):
            setattr(self, f.name, getattr(self, f.name) + getattr(other, f.name))


# Thinking tokens are absent: they sit inside `output_tokens` already, so a line
# of their own would charge every turn that thought twice.
BILLED_AT = {
    "input_tokens": "input",
    "cache_write_5m_tokens": "cache_write_5m",
    "cache_write_1h_tokens": "cache_write_1h",
    "cache_read_tokens": "cache_read",
    "output_tokens": "output",
}


def billable_tokens(tally: Tally) -> int:
    return sum(getattr(tally, name) for name in BILLED_AT)


def cost_of(tally: Tally, rates: Rates) -> float:
    usd = 0.0
    for tokens, rate in BILLED_AT.items():
        usd += getattr(tally, tokens) * getattr(rates, rate) / 1e6
    return usd


def _parse_tally(obj: Any, where: str) -> Tally:
    if not isinstance(obj, dict):
        raise ShapeError(f"{where}: not an object")
    return Tally(
        **{
            f.name: required(read_number if f.name == "cost_usd" else read_count, obj, camel(f.name), where)
            for f in fields(Tally)
        }
    )


# --- A session's row ----------------------------------------------------------


@dataclass
class SessionCost:
    session_id: str
    branch: Optional[str]
    cwd: Optional[str]
    # `name` is the agent's own short label, and the one field here the
    # transcript cannot supply: it stays null until a turn fills it in, which is
    # what `hooks/prompt-session-name.sh` asks for. Writing a row therefore
    # carries the existing name forward rather than recomputing it.
    name: Optional[str]
    opening_prompt: Optional[str]
    prs: List[int]
    # The URL a person opens the session at — a different id from the
    # transcript's own, present only in a remote session.
    url: Optional[str]
    # The operator's GitHub handle, lowercased and without the `@`; null when
    # no person was resolved behind the session's token.
    operator: Optional[str]
    first_response_at: Optional[str]
    last_response_at: Optional[str]
    prices_as_of: str
    # What Claude Code itself had counted the session at, off the `cost-state`
    # records it writes into the transcript. Written into the same file partway
    # through, it is a floor rather than a rival total: `report.py` flags a row
    # that came out *under* it.
    claude_code_total_usd: Optional[float]
    total: Tally
    own_turns: Tally
    subagents: Tally
    by_rate: Dict[str, Tally]
    warnings: List[str]


def _list_of(obj: Mapping[str, Any], key: str, where: str, kind: type) -> List[Any]:
    value = obj.get(key)
    if value is None:
        return []
    if not isinstance(value, list) or not all(
        isinstance(item, kind) and not isinstance(item, bool) for item in value
    ):
        raise ShapeError(f"{where}: `{key}` is not a list of {kind.__name__}")
    return value


def parse_session_cost(text: str, where: str = "row") -> SessionCost:
    """Rows are read back in a later process, so they are parsed rather than
    trusted. The naming fields default when absent, so a row written before they
    existed still parses."""
    row = json.loads(text)
    if not isinstance(row, dict):
        raise ShapeError(f"{where}: not an object")
    return SessionCost(
        session_id=required(read_string, row, "sessionId", where),
        branch=read_string(row, "branch", where),
        cwd=read_string(row, "cwd", where),
        name=read_string(row, "name", where),
        opening_prompt=read_string(row, "openingPrompt", where),
        prs=_list_of(row, "prs", where, int),
        url=read_string(row, "url", where),
        operator=read_string(row, "operator", where),
        first_response_at=read_string(row, "firstResponseAt", where),
        last_response_at=read_string(row, "lastResponseAt", where),
        prices_as_of=required(read_string, row, "pricesAsOf", where),
        claude_code_total_usd=read_number(row, "claudeCodeTotalUsd", where),
        total=_parse_tally(row.get("total"), f"{where} total"),
        own_turns=_parse_tally(row.get("ownTurns"), f"{where} ownTurns"),
        subagents=_parse_tally(row.get("subagents"), f"{where} subagents"),
        by_rate={
            key: _parse_tally(tally, f"{where} byRate[{key!r}]")
            for key, tally in required(read_object, row, "byRate", where).items()
        },
        warnings=_list_of(row, "warnings", where, str),
    )


# --- Reading a transcript -----------------------------------------------------

# Claude Code's placeholder for a turn no model served — a cancellation, an
# interrupted request. It is not a model, so the unpriced-pair error would be
# reporting the wrong thing; a warning covers one ever arriving with tokens.
SYNTHETIC_MODEL = "<synthetic>"


@dataclass(frozen=True)
class Response:
    message_id: str
    model: str
    speed: Optional[str]
    session_id: Optional[str]
    git_branch: Optional[str]
    cwd: Optional[str]
    timestamp: Optional[str]
    is_sidechain: bool
    stop_reason: Optional[str]
    tokens: Tally


def _is_response_record(record: Any) -> bool:
    # Prompts, attachments and tool results share the file and carry no usage,
    # so only a record that looks like a billed response is held to the shape.
    if not isinstance(record, dict):
        return False
    message = record.get("message")
    return isinstance(message, dict) and "usage" in message


def _parse_response(record: Dict[str, Any], where: str, warnings: List[str]) -> Response:
    message = required(read_object, record, "message", where)
    message_id = required(read_string, message, "id", where)
    usage = required(read_object, message, "usage", where)
    at = f"{where} usage"

    written = read_count(usage, "cache_creation_input_tokens", at) or 0
    split = read_object(usage, "cache_creation", at) or {}
    split_5m = read_count(split, "ephemeral_5m_input_tokens", at) or 0
    split_1h = read_count(split, "ephemeral_1h_input_tokens", at) or 0
    # A split that does not account for the whole write leaves the rest at the
    # API's own default TTL, and says so rather than rounding it away.
    trust_split = split_5m + split_1h == written
    if not trust_split and written > 0:
        warnings.append(
            f"{message_id}: cache_creation split ({split_5m} + {split_1h}) does not"
            f" account for {written} written tokens; billed at the 5-minute rate"
        )
    details = read_object(usage, "output_tokens_details", at) or {}
    sidechain = record.get("isSidechain")
    if sidechain is not None and not isinstance(sidechain, bool):
        raise mistyped(where, "isSidechain", sidechain, "a boolean")

    return Response(
        message_id=message_id,
        model=required(read_string, message, "model", where),
        speed=read_string(usage, "speed", at),
        session_id=read_string(record, "sessionId", where),
        git_branch=read_string(record, "gitBranch", where),
        cwd=read_string(record, "cwd", where),
        timestamp=read_string(record, "timestamp", where),
        is_sidechain=sidechain is True,
        stop_reason=read_string(message, "stop_reason", where),
        tokens=Tally(
            input_tokens=required(read_count, usage, "input_tokens", at),
            cache_write_5m_tokens=split_5m if trust_split else written,
            cache_write_1h_tokens=split_1h if trust_split else 0,
            cache_read_tokens=read_count(usage, "cache_read_input_tokens", at) or 0,
            output_tokens=required(read_count, usage, "output_tokens", at),
            thinking_tokens=read_count(details, "thinking_tokens", at) or 0,
        ),
    )


@dataclass(frozen=True)
class TranscriptSources:
    """A session's transcripts: the main file, and one per subagent it spawned.

    A subagent's responses are billed to the session that spawned it and are
    written to a **separate file**, so a reading that opens only the main
    transcript prices the session short by however much it delegated — silently,
    since the shortfall looks exactly like a session that delegated nothing.
    """

    main: str
    subagents: Sequence[str] = ()


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
) -> SessionCost:
    """Raises `UnpricedError` when a transcript names a `(model, speed)` pair the
    table cannot price, and `ShapeError` when a response record does not parse:
    an unpriced response silently counted as free is the one failure that makes
    the whole ledger a lie.

    `at_stop` says the turn is over, so the session's own last response should
    be the `end_turn` that closed it; anything else is warned about as a tail
    the file had not yet been given."""
    warnings: List[str] = []
    last_own: Optional[Response] = None
    seen: Set[str] = set()
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

    # `delegated` forces the bucket for a subagent's own file. Its records carry
    # `isSidechain` too, but the file they are in is the fact that does not
    # depend on a flag having been set.
    def scan(jsonl: str, label: str, delegated: bool) -> None:
        nonlocal session_id, branch, cwd, opening_prompt, url, operator
        nonlocal claude_code_total_usd, last_own
        for number, line in enumerate(jsonl.split("\n"), start=1):
            if line.strip() == "":
                continue
            where = f"{label} line {number}"
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ShapeError(f"{where}: not JSON ({error})") from error

            kind = kind_of(record)
            # The session's own identity, which only its own file describes.
            if not delegated:
                if kind == "pr-link":
                    pr = pr_number_of(record)
                    if pr is not None:
                        prs.add(pr)
                    continue
                if kind == "user":
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

            if not _is_response_record(record):
                continue
            response = _parse_response(record, where, warnings)
            if not (delegated or response.is_sidechain or response.model == SYNTHETIC_MODEL):
                last_own = response
            # One API response is written as one record per content block, each
            # carrying the whole response's usage, so the id counts it once.
            if response.message_id in seen:
                continue
            seen.add(response.message_id)

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

            key = rate_key(response.model, response.speed)
            rates = prices.rates.get(key)
            if rates is None:
                unpriced.add(key)
                continue

            tokens.responses = 1
            tokens.cost_usd = cost_of(tokens, rates)
            by_rate.setdefault(key, Tally()).add(tokens)
            total.add(tokens)
            (subagents if delegated or response.is_sidechain else own_turns).add(tokens)

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

    in_order = sorted(timestamps)
    return SessionCost(
        session_id=session_id if session_id is not None else fallback_session_id,
        branch=branch,
        cwd=cwd,
        name=None,
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
    )
