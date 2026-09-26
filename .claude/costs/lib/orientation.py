"""What a session spent finding its bearings before it acted — at its start, and
again after each compaction — and what each compaction cost later in reads of
things its summary left out.

It takes what `summarise_transcript` collects on its one pass over the
transcript rather than walking the records itself, so the dedup rule for
`message.id` has one home. `.claude/costs/CLAUDE.md` § "Orientation" carries
what counts as acting, and what the measure misses.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from lib.shape import (
    ShapeError,
    read_count,
    read_number,
    read_object,
    read_string,
    required,
)
from lib.tally import Rates, Tally, parse_tally

# --- What the scan hands over -------------------------------------------------


@dataclass(frozen=True)
class ToolCall:
    id: Optional[str]
    name: str
    input: Mapping[str, Any]


@dataclass
class Priced:
    """One priced response. `at` is its first record's timestamp, and `calls`
    gathers the tool calls of every record it was written as."""

    message_id: str
    at: str
    # Scan order, which breaks a tie between two responses stamped alike.
    seq: int
    own: bool
    ended_turn: bool
    cwd: Optional[str]
    tokens: Tally
    rates: Rates
    calls: List[ToolCall]


@dataclass
class Boundary:
    at: str
    trigger: Optional[str]
    compacted_from: Optional[int]
    summary_chars: Optional[int] = None


@dataclass
class Trail:
    responses: List[Priced] = field(default_factory=list)
    boundaries: List[Boundary] = field(default_factory=list)
    # A tool result's length in characters, by the `tool_use_id` it answers.
    result_chars: Dict[str, int] = field(default_factory=dict)


def calls_in(message: Mapping[str, Any], where: str) -> Tuple[ToolCall, ...]:
    content = message.get("content")
    if not isinstance(content, list):
        return ()
    calls = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            calls.append(
                ToolCall(
                    id=read_string(block, "id", where),
                    name=required(read_string, block, "name", where),
                    input=required(read_object, block, "input", where),
                )
            )
    return tuple(calls)


def content_chars(content: Any) -> int:
    """A message's or tool result's text, measured in characters; an image or
    any block without text counts nothing."""
    if isinstance(content, str):
        return len(content)
    if not isinstance(content, list):
        return 0
    return sum(
        len(block["text"])
        for block in content
        if isinstance(block, dict) and isinstance(block.get("text"), str)
    )


def note_results(record: Mapping[str, Any], result_chars: Dict[str, int]) -> None:
    message = record.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list):
        return
    for block in content:
        if (
            isinstance(block, dict)
            and block.get("type") == "tool_result"
            and isinstance(block.get("tool_use_id"), str)
        ):
            result_chars[block["tool_use_id"]] = content_chars(block.get("content"))


def is_boundary(record: Mapping[str, Any]) -> bool:
    return record.get("type") == "system" and record.get("subtype") == "compact_boundary"


def boundary_of(record: Mapping[str, Any], where: str) -> Boundary:
    meta = read_object(record, "compactMetadata", where) or {}
    at = f"{where} compactMetadata"
    return Boundary(
        at=required(read_string, record, "timestamp", where),
        trigger=read_string(meta, "trigger", at),
        compacted_from=read_count(meta, "preTokens", at),
    )


def summary_chars_of(record: Mapping[str, Any]) -> Optional[int]:
    """The summary a compaction leaves arrives as the `user` record after its
    boundary, flagged as one."""
    if record.get("isCompactSummary") is not True:
        return None
    message = record.get("message")
    return content_chars(message.get("content")) if isinstance(message, dict) else 0


# --- What a row records -------------------------------------------------------


@dataclass
class Phase:
    """From a starting point to the first response that acted, that response
    left out. The four `ended*`/`context*` fields are null when the stretch ran
    out before anything acted."""

    ended_by: Optional[str]
    ended_on: Optional[str]
    ended_at: Optional[str]
    context_tokens: Optional[int]
    spend: Tally


@dataclass
class Rereads:
    calls: int = 0
    by_tool: Dict[str, int] = field(default_factory=dict)
    estimated_tokens: int = 0
    estimated_usd: float = 0.0


@dataclass
class Compaction:
    at: str
    trigger: Optional[str]
    compacted_from: Optional[int]
    summary_chars: Optional[int]
    reorientation: Phase
    rereads: Rereads
    # The compaction call's own price, off the session's events; null without
    # them, since the transcript records that call with no usage.
    billed_usd: Optional[float] = None


def parse_phase(obj: Any, where: str) -> Phase:
    if not isinstance(obj, dict):
        raise ShapeError(f"{where}: not an object")
    return Phase(
        ended_by=read_string(obj, "endedBy", where),
        ended_on=read_string(obj, "endedOn", where),
        ended_at=read_string(obj, "endedAt", where),
        context_tokens=read_count(obj, "contextTokens", where),
        spend=parse_tally(obj.get("spend"), f"{where} spend"),
    )


def parse_compaction(obj: Any, where: str) -> Compaction:
    if not isinstance(obj, dict):
        raise ShapeError(f"{where}: not an object")
    rereads = required(read_object, obj, "rereads", where)
    at = f"{where} rereads"
    by_tool = required(read_object, rereads, "byTool", at)
    return Compaction(
        at=required(read_string, obj, "at", where),
        trigger=read_string(obj, "trigger", where),
        compacted_from=read_count(obj, "compactedFrom", where),
        summary_chars=read_count(obj, "summaryChars", where),
        reorientation=parse_phase(obj.get("reorientation"), f"{where} reorientation"),
        rereads=Rereads(
            calls=required(read_count, rereads, "calls", at),
            by_tool={tool: required(read_count, by_tool, tool, at) for tool in by_tool},
            estimated_tokens=required(read_count, rereads, "estimatedTokens", at),
            estimated_usd=required(read_number, rereads, "estimatedUsd", at),
        ),
        billed_usd=read_number(obj, "billedUsd", where),
    )


# --- Measuring ----------------------------------------------------------------

# The tool, and the input field naming the path it writes.
WRITES = {"Edit": "file_path", "Write": "file_path", "NotebookEdit": "notebook_path"}
# Tools that hand the turn to the operator from inside it, as an `end_turn` does.
HANDOVERS = {"AskUserQuestion", "ExitPlanMode"}
REPEATABLE = {"Grep", "Glob", "Bash"}


def in_repo(path: Any, root: Optional[str]) -> Optional[str]:
    """`path` relative to the session's root, or `None` when it lies outside the
    repository or inside its `tmp/`, where writing is looking around."""
    if not isinstance(path, str) or root is None:
        return None
    relative = os.path.relpath(os.path.normpath(os.path.join(root, path)), root)
    if relative == "." or relative.split(os.sep)[0] in ("..", "tmp"):
        return None
    return relative


def action_of(response: Priced, root: Optional[str]) -> Optional[Tuple[str, Optional[str]]]:
    for call in response.calls:
        if call.name in HANDOVERS:
            return call.name, None
        key = WRITES.get(call.name)
        if key is not None:
            path = in_repo(call.input.get(key), root)
            if path is not None:
                return call.name, path
    # A subagent's `end_turn` only hands its result to whoever spawned it.
    if response.own and response.ended_turn:
        return "end_turn", None
    return None


def phase_over(stretch: Sequence[Priced], root: Optional[str]) -> Phase:
    for response in stretch:
        action = action_of(response, root)
        if action is None:
            continue
        spend = Tally()
        # By timestamp, not by position: a subagent's spend sits in another file,
        # and its clock is what orders it against the main file's.
        for earlier in stretch:
            if earlier.at < response.at:
                spend.add(earlier.tokens)
        ended_by, ended_on = action
        return Phase(ended_by, ended_on, response.at, response.tokens.context_tokens(), spend)
    spend = Tally()
    for response in stretch:
        spend.add(response.tokens)
    return Phase(None, None, None, None, spend)


def _repeat_key(call: ToolCall) -> Optional[Tuple[Any, ...]]:
    if call.name == "Read":
        path = call.input.get("file_path")
        if not isinstance(path, str):
            return None
        where = tuple(call.input.get(k) for k in ("offset", "limit", "pages"))
        return ("Read", os.path.normpath(path), *where)
    if call.name in REPEATABLE:
        # `description` is the agent's gloss on the call, reworded each time.
        same = {k: v for k, v in call.input.items() if k != "description"}
        return (call.name, json.dumps(same, sort_keys=True))
    return None


def _written_paths(ordered: Sequence[Priced]) -> Dict[str, List[str]]:
    """When each path was written, in any transcript: a subagent's edit changes
    the file all the same."""
    written: Dict[str, List[str]] = {}
    for response in ordered:
        for call in response.calls:
            key = WRITES.get(call.name)
            path = call.input.get(key) if key is not None else None
            if isinstance(path, str):
                written.setdefault(os.path.normpath(path), []).append(response.at)
    return written


def _carry_estimate(
    call: ToolCall, index: int, own: Sequence[Priced], until: Optional[str], trail: Trail
) -> Tuple[int, float]:
    """A tool result has no usage of its own, so its tokens are its share, by
    characters, of the cache write of the response it arrived in; its dollars,
    that write plus a cache read on each later response until `until`."""
    response = own[index]
    if index + 1 == len(own):
        return 0, 0.0
    arrived = own[index + 1]
    written = arrived.tokens.cache_write_5m_tokens + arrived.tokens.cache_write_1h_tokens
    together = sum(trail.result_chars.get(c.id or "", 0) for c in response.calls)
    mine = trail.result_chars.get(call.id or "", 0)
    if written == 0 or together == 0:
        return 0, 0.0
    tokens = round(written * mine / together)
    rates = arrived.rates
    write_rate = (
        arrived.tokens.cache_write_5m_tokens * rates.cache_write_5m
        + arrived.tokens.cache_write_1h_tokens * rates.cache_write_1h
    ) / written
    later = sum(1 for r in own[index + 2 :] if until is None or r.at < until)
    return tokens, tokens * (write_rate + later * rates.cache_read) / 1e6


def _rereads(
    ordered: Sequence[Priced], boundaries: Sequence[Boundary], trail: Trail
) -> List[Rereads]:
    """A call after a boundary repeating one made before it, charged to the
    latest boundary before it. A repeat of a call already repeated since that
    boundary is not a hole: its answer is back in the context."""
    found = [Rereads() for _ in boundaries]
    own = [r for r in ordered if r.own]
    written = _written_paths(ordered)
    latest: Dict[Tuple[Any, ...], str] = {}
    for index, response in enumerate(own):
        stretch = sum(1 for b in boundaries if b.at < response.at) - 1
        for call in response.calls:
            key = _repeat_key(call)
            if key is None:
                continue
            before = latest.get(key)
            latest[key] = response.at
            if stretch < 0 or before is None or before >= boundaries[stretch].at:
                continue
            if call.name == "Read" and any(
                before <= at < response.at for at in written.get(key[1], [])
            ):
                continue
            until = boundaries[stretch + 1].at if stretch + 1 < len(boundaries) else None
            tokens, usd = _carry_estimate(call, index, own, until, trail)
            tally = found[stretch]
            tally.calls += 1
            tally.by_tool[call.name] = tally.by_tool.get(call.name, 0) + 1
            tally.estimated_tokens += tokens
            tally.estimated_usd += usd
    return found


def measure(trail: Trail) -> Tuple[Optional[Phase], List[Compaction]]:
    """The session's orientation and its compactions, each phase cut off at the
    next boundary so no response is counted in two of them."""
    ordered = sorted(trail.responses, key=lambda r: (r.at, r.seq))
    if not ordered:
        return None, []
    # Where the session started: the repository whose files are its work.
    root = next((r.cwd for r in ordered if r.own and r.cwd is not None), None)
    boundaries = sorted(trail.boundaries, key=lambda b: b.at)
    cuts = [b.at for b in boundaries]

    def between(after: Optional[str], until: Optional[str]) -> List[Priced]:
        return [
            r
            for r in ordered
            if (after is None or r.at > after) and (until is None or r.at < until)
        ]

    orientation = phase_over(between(None, cuts[0] if cuts else None), root)
    rereads = _rereads(ordered, boundaries, trail)
    compactions = [
        Compaction(
            at=boundary.at,
            trigger=boundary.trigger,
            compacted_from=boundary.compacted_from,
            summary_chars=boundary.summary_chars,
            reorientation=phase_over(
                between(boundary.at, cuts[i + 1] if i + 1 < len(cuts) else None), root
            ),
            rereads=rereads[i],
        )
        for i, boundary in enumerate(boundaries)
    ]
    return orientation, compactions
