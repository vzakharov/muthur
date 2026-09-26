"""A session's row: its shape, and its file on disk — written by the pricing run,
and reshaped by the report."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from lib.billed import Telemetry, parse_telemetry
from lib.orientation import Compaction, Phase, parse_compaction, parse_phase
from lib.shape import ShapeError, read_number, read_object, read_string, required, to_json
from lib.tally import Tally, parse_tally

ROOT = Path(__file__).resolve().parents[3]


@dataclass
class SessionCost:
    session_id: str
    branch: Optional[str]
    cwd: Optional[str]
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
    # `ownTurns + subagents`, plus `telemetry.unseen` where there were events.
    total: Tally
    own_turns: Tally
    subagents: Tally
    by_rate: Dict[str, Tally]
    warnings: List[str]
    # Null on a row written before orientation was measured, and on a session
    # with no priced response to measure it over.
    orientation: Optional[Phase] = None
    compactions: List[Compaction] = field(default_factory=list)
    # Null where the session left no events, and on every row from before.
    telemetry: Optional[Telemetry] = None


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
    trusted. The naming, orientation and telemetry fields default when absent,
    so a row written before they existed still parses."""
    row = json.loads(text)
    if not isinstance(row, dict):
        raise ShapeError(f"{where}: not an object")
    return SessionCost(
        session_id=required(read_string, row, "sessionId", where),
        branch=read_string(row, "branch", where),
        cwd=read_string(row, "cwd", where),
        opening_prompt=read_string(row, "openingPrompt", where),
        prs=_list_of(row, "prs", where, int),
        url=read_string(row, "url", where),
        operator=read_string(row, "operator", where),
        first_response_at=read_string(row, "firstResponseAt", where),
        last_response_at=read_string(row, "lastResponseAt", where),
        prices_as_of=required(read_string, row, "pricesAsOf", where),
        claude_code_total_usd=read_number(row, "claudeCodeTotalUsd", where),
        total=parse_tally(row.get("total"), f"{where} total"),
        own_turns=parse_tally(row.get("ownTurns"), f"{where} ownTurns"),
        subagents=parse_tally(row.get("subagents"), f"{where} subagents"),
        by_rate={
            key: parse_tally(tally, f"{where} byRate[{key!r}]")
            for key, tally in required(read_object, row, "byRate", where).items()
        },
        warnings=_list_of(row, "warnings", where, str),
        orientation=(
            None
            if row.get("orientation") is None
            else parse_phase(row["orientation"], f"{where} orientation")
        ),
        compactions=[
            parse_compaction(item, f"{where} compactions[{index}]")
            for index, item in enumerate(_list_of(row, "compactions", where, dict))
        ],
        telemetry=(
            None
            if row.get("telemetry") is None
            else parse_telemetry(row["telemetry"], f"{where} telemetry")
        ),
    )


def row_text(cost: SessionCost) -> str:
    return json.dumps(to_json(cost), indent=2, ensure_ascii=False) + "\n"


def write_atomic(out: Path, contents: str) -> None:
    """A write cut off halfway leaves the old file rather than half a new one,
    so it is staged and renamed into place — under the repo's own gitignored
    `tmp/`, where a stray staging file is invisible to git and the rename is
    on the same filesystem."""
    staged = ROOT / "tmp" / f"{out.name}.staged"
    staged.parent.mkdir(parents=True, exist_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    staged.write_text(contents, encoding="utf-8")
    os.replace(staged, out)


def read_row(path: Path) -> Tuple[SessionCost, List[str]]:
    """A row carrying keys the current shape does not write is rewritten in
    that shape as it is read, and the keys it lost are returned. That is how a
    retired field leaves the ledger — in every repository it runs in, on the
    first report there — with no migration for anyone to remember to run."""
    text = path.read_text(encoding="utf-8")
    row = parse_session_cost(text, str(path))
    dropped = sorted(set(json.loads(text)) - set(to_json(row)))
    if dropped:
        write_atomic(path, row_text(row))
    return row, dropped
