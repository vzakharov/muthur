"""Steno waves on the ledger branch: each wave's forecast beside what it
measured, so later forecasts calibrate from the ones before. One file per agent
id, so two sessions never write the same path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Sequence, Tuple

from lib.rows import ROOT, SESSIONS
from lib.shape import ShapeError, read_object, required, read_number, to_json
from lib.tally import Rates

DELEGATIONS = SESSIONS.parent / "delegations"
PREFIX = DELEGATIONS.relative_to(ROOT).as_posix()
# The first measured wave's Haiku run, standing in while the ledger holds none.
SEED_RUN_USD = 0.06


@dataclass(frozen=True)
class Forecast:
    turns: int
    waves: int
    context_tokens: int
    # One delegating turn's re-read of that context.
    turn_usd: float
    # The subagent's run in one wave.
    run_usd: float
    runs_measured: int
    direct_usd: float
    steno_usd: float

    @property
    def wave_usd(self) -> float:
        return self.steno_usd / self.waves


def reread_usd(context_tokens: int, rates: Rates) -> float:
    """One turn's cache read of `context_tokens`: the unit both the forecast and
    the measured wave price a delegating turn in, so the two compare."""
    return context_tokens * rates.cache_read / 1e6


def forecast(turns: int, waves: int, context_tokens: int, rates: Rates, runs: Sequence[float]) -> Forecast:
    """Direct editing re-reads the context once a turn; each steno wave re-reads
    it twice — dictating and reviewing — and pays the subagent's run. Output is
    left out of both: the edits' text is written once either way."""
    if turns < 1 or waves < 1:
        raise ValueError("turns and waves are each at least 1")
    turn_usd = reread_usd(context_tokens, rates)
    run_usd = sum(runs) / len(runs) if runs else SEED_RUN_USD
    return Forecast(
        turns=turns,
        waves=waves,
        context_tokens=context_tokens,
        turn_usd=turn_usd,
        run_usd=run_usd,
        runs_measured=len(runs),
        direct_usd=turns * turn_usd,
        steno_usd=waves * (run_usd + 2 * turn_usd),
    )


def describe(f: Forecast) -> str:
    source = f"mean of {f.runs_measured} measured" if f.runs_measured else "seed, no wave measured yet"
    verdict = "steno is cheaper" if f.steno_usd < f.direct_usd else "direct is cheaper"
    return "\n".join(
        [
            f"direct: ${f.direct_usd:.2f} — {f.turns} turns at ${f.turn_usd:.3f}, context {f.context_tokens:,} tokens",
            f"steno:  ${f.steno_usd:.2f} — {f.waves} waves at ${f.wave_usd:.3f}"
            f" (two turns + Haiku run ${f.run_usd:.3f}, {source})",
            verdict,
        ]
    )


@dataclass(frozen=True)
class Measured:
    run_usd: float
    run_turns: int
    # The dictating turn's and the reviewing turn's re-reads; the review is
    # None while no turn has followed the subagent.
    dictate_usd: float
    review_usd: Optional[float]
    # The list's output, left out of the forecast, which prices both ways alike.
    brief_usd: float
    # `delegation.py`'s replay of the subagent's turns at the delegator's
    # rates: the direct side measured, where the forecast counts re-reads only.
    in_session_usd: float


@dataclass(frozen=True)
class Wave:
    agent_id: str
    session_id: str
    branch: Optional[str]
    model: str
    recorded_at: str
    forecast: Forecast
    measured: Measured


def path_of(wave: Wave, now: datetime) -> str:
    return f"{PREFIX}/{now:%Y-%m}/{wave.agent_id}.json"


def text_of(wave: Wave) -> str:
    return json.dumps(to_json(wave), indent=2) + "\n"


def measured_run(text: str, where: str) -> float:
    """A row's subagent run in USD, the one figure the forecast reads back."""
    try:
        record = json.loads(text)
    except ValueError as error:
        raise ShapeError(f"{where}: not JSON ({error})") from error
    if not isinstance(record, dict):
        raise ShapeError(f"{where}: not an object")
    return required(read_number, required(read_object, record, "measured", where), "runUsd", where)


def runs_of(rows: Iterable[Tuple[str, str]], leaving_out: Optional[str] = None) -> List[float]:
    """The measured runs of `(path, text)` rows, the agent `leaving_out` names
    excluded so a wave never calibrates its own forecast."""
    return [
        measured_run(text, path)
        for path, text in rows
        if path.endswith(".json") and not (leaving_out and path.endswith(f"/{leaving_out}.json"))
    ]
