#!/usr/bin/env python3
"""Weigh one delegation: what the subagent cost against what doing its work in
the delegating session would have cost, both at `prices.json` rates.

Usage:
  python3 .claude/costs/delegation.py <agent-id> [--turns <n>] [--projects <dir>]

`<agent-id>` is the id the `Agent` result names. `--turns` is how many turns the
delegating model would have taken itself — the one input no transcript holds, a
stronger model often needing fewer; it defaults to the subagent's own count,
which makes the in-session figure an upper bound. `--projects` is where Claude
Code keeps transcripts, `~/.claude/projects` by default.

The subagent's side is measured. The in-session side replays the subagent's
turns at the delegator's rates over the delegator's context — each turn a cache
read of that context plus what the subagent's own had grown by, its output at
the delegator's output rate, the growth written once. What the work goes on
costing afterwards is per later turn: the delegator re-reads whatever it took on
— the brief and the report when it delegated, the work itself when it did not.

Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from lib.prices import PriceTable, parse_prices, rate_key
from lib.pricing import UnpricedError, summarise_transcript
from lib.shape import ShapeError, json_lines, read_string, required
from lib.tally import Rates
from lib.transcript import SYNTHETIC_MODEL, Response, TranscriptSources, is_response_record, merged, parse_response

COSTS = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Weighing:
    subagent_usd: float
    subagent_turns: int
    brief_usd: float
    in_session_usd: float
    in_session_turns: int
    # USD each later turn of the delegating session re-reads; `None` while no
    # turn of it has followed the subagent yet.
    carried_delegated_usd: Optional[float]
    carried_in_session_usd: float
    later_turns: int
    warnings: List[str]

    @property
    def delegated_usd(self) -> float:
        return self.subagent_usd + self.brief_usd


def responses_of(text: str, label: str, warnings: List[str]) -> List[Response]:
    """Billed responses once each, in file order, the placeholder model skipped."""
    seen: Dict[str, Response] = {}
    for where, _, record in json_lines(text, label):
        if not is_response_record(record):
            continue
        response = parse_response(record, where, warnings)
        if response.model == SYNTHETIC_MODEL:
            continue
        earlier = seen.get(response.message_id)
        seen[response.message_id] = response if earlier is None else merged(earlier, response)
    return list(seen.values())


def rates_or_raise(prices: PriceTable, response: Response) -> Rates:
    rates = prices.rates_for(response.model, response.speed, response.tokens.context_tokens())
    if rates is None:
        raise UnpricedError(f"No rates for {rate_key(response.model, response.speed)} in prices.json")
    return rates


def weigh(main: str, subagent: str, tool_use_id: str, prices: PriceTable, turns: Optional[int] = None) -> Weighing:
    warnings: List[str] = []
    own = [r for r in responses_of(main, "transcript", warnings) if not r.is_sidechain]
    launch = next((r for r in own if any(c.id == tool_use_id for c in r.calls)), None)
    if launch is None:
        raise ValueError(f"no response in the transcript calls tool use {tool_use_id}")
    worked = [r for r in responses_of(subagent, "subagent transcript", warnings) if r.timestamp is not None]
    if not worked:
        raise ValueError("the subagent's transcript holds no timed response")

    measured = summarise_transcript(TranscriptSources(main=subagent), prices, "subagent")
    warnings.extend(measured.warnings)

    rates = rates_or_raise(prices, launch)
    write_rate = rates.cache_write_1h if launch.tokens.cache_write_1h_tokens else rates.cache_write_5m
    base = launch.tokens.context_tokens()
    first = worked[0].tokens.context_tokens()
    growth = max(0, worked[-1].tokens.context_tokens() - first)
    output = sum(r.tokens.output_tokens for r in worked)
    taken = turns if turns is not None else len(worked)

    reads = sum(base + r.tokens.context_tokens() - first for r in worked) * taken / len(worked)
    in_session = (reads * rates.cache_read + output * rates.output + growth * write_rate) / 1e6

    finished = max(r.timestamp for r in worked if r.timestamp is not None)
    after = [r for r in own if r.timestamp is not None and r.timestamp > finished]
    carried = None if not after else max(0, after[0].tokens.context_tokens() - base) * rates.cache_read / 1e6

    return Weighing(
        subagent_usd=measured.total.cost_usd,
        subagent_turns=len(worked),
        brief_usd=launch.tokens.output_tokens * rates.output / 1e6,
        in_session_usd=in_session,
        in_session_turns=taken,
        carried_delegated_usd=carried,
        carried_in_session_usd=growth * rates.cache_read / 1e6,
        later_turns=len(after),
        warnings=warnings,
    )


def report(w: Weighing) -> str:
    lines = [
        f"delegated:  ${w.delegated_usd:.2f} — subagent ${w.subagent_usd:.2f} over {w.subagent_turns} turns,"
        f" brief ${w.brief_usd:.2f}",
        f"in-session: ${w.in_session_usd:.2f} over {w.in_session_turns} turns",
    ]
    if w.carried_delegated_usd is None:
        lines.append(
            f"each later turn re-reads ${w.carried_in_session_usd:.4f} had it been done in-session;"
            " what the delegation added is measurable once a turn follows it"
        )
    else:
        lines.append(
            f"each later turn re-reads ${w.carried_delegated_usd:.4f} delegated against"
            f" ${w.carried_in_session_usd:.4f} in-session; {w.later_turns} have followed so far"
        )
    lines.extend(f"warning: {warning}" for warning in w.warnings)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("agent_id")
    parser.add_argument("--turns", type=int)
    parser.add_argument("--projects", type=Path, default=Path.home() / ".claude" / "projects")
    args = parser.parse_args()

    found = sorted(args.projects.glob(f"*/*/subagents/agent-{args.agent_id}.jsonl"))
    if len(found) != 1:
        print(f"delegation: {len(found)} transcripts for agent {args.agent_id} under {args.projects}", file=sys.stderr)
        return 1
    subagent = found[0]
    session = subagent.parent.parent
    meta = subagent.with_name(f"agent-{args.agent_id}.meta.json")
    tool_use_id = parse_tool_use_id(meta)
    prices = parse_prices((COSTS / "prices.json").read_text(encoding="utf-8"))
    weighing = weigh(
        session.with_suffix(".jsonl").read_text(encoding="utf-8"),
        subagent.read_text(encoding="utf-8"),
        tool_use_id,
        prices,
        args.turns,
    )
    print(report(weighing))
    return 0


def parse_tool_use_id(meta: Path) -> str:
    record = json.loads(meta.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ShapeError(f"{meta}: not an object")
    return required(read_string, record, "toolUseId", str(meta))


if __name__ == "__main__":
    sys.exit(main())
