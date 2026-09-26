"""Sums the session rows for `report.py` — the same spend by month, by ISO week,
by day, by the branch that spent it, and by the operator whose session it was —
and averages what the rows measured of orientation.

Nothing here is written to disk: the totals are wholly derived from the rows,
and a derived file committed beside its own sources is a merge conflict every
branch pays for.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from statistics import mean, median
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from lib.orientation import Phase
from lib.pricing import SessionCost


@dataclass
class Bucket:
    sessions: int = 0
    responses: int = 0
    cost_usd: float = 0.0

    def count(self, row: SessionCost) -> None:
        self.sessions += 1
        self.responses += row.total.responses
        self.cost_usd += row.total.cost_usd


@dataclass
class Totals:
    sessions: int
    responses: int
    cost_usd: float
    by_month: Dict[str, Bucket] = field(default_factory=dict)
    by_week: Dict[str, Bucket] = field(default_factory=dict)
    by_day: Dict[str, Bucket] = field(default_factory=dict)
    by_branch: Dict[str, Bucket] = field(default_factory=dict)
    by_operator: Dict[str, Bucket] = field(default_factory=dict)
    orientation: Optional[OrientationSummary] = None


@dataclass
class Spread:
    mean: float
    median: float


@dataclass
class PhaseStats:
    phases: int
    usd: Spread
    # Over the phases that acted: one that never did has no context to report.
    context_tokens: Optional[Spread]
    share_of_session: Spread


@dataclass
class CompactionStats:
    compactions: int
    reorientation: PhaseStats
    compacted_from: Optional[Spread]
    reread_calls: Spread
    reread_estimated_usd: Spread
    rereads_by_tool: Dict[str, int]


@dataclass
class OrientationSummary:
    """Means rather than sums, which is why it is not a `Bucket`: a mean on
    every month and branch row would mean nothing there."""

    measured: int
    rows: int
    orientation: Optional[PhaseStats]
    by_ended_by: Dict[str, PhaseStats]
    by_opening_command: Dict[str, PhaseStats]
    compactions: Optional[CompactionStats]


def iso_week(day: date) -> str:
    """The ISO-8601 week a day falls in, `<year>-W<nn>`. The year is the one
    owning that week's Thursday, so the last days of December can read as week
    01 of the next year — the scheme working, not a rounding error."""
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def branch_label(row: SessionCost) -> str:
    """The branch a session's spend is filed under, with the pull requests it
    touched named beside it: the branch says roughly what the work was, the
    numbers are what a reader clicks through to. The spend is the branch's
    rather than each PR's, since a session that touched two would otherwise be
    counted twice."""
    return " ".join([row.branch or "(no branch)", *(f"#{pr}" for pr in row.prs)])


def operator_label(row: SessionCost) -> str:
    return f"@{row.operator}" if row.operator is not None else "(unknown)"


# Rounded where it is written rather than where it is read: a sum of floats
# carries digits no price has, and the output is read by people.
def _rounded(buckets: Dict[str, Bucket]) -> Dict[str, Bucket]:
    return {
        key: Bucket(bucket.sessions, bucket.responses, round(bucket.cost_usd, 4))
        for key, bucket in sorted(buckets.items())
    }


def spread_of(values: Sequence[float], digits: int) -> Optional[Spread]:
    if not values:
        return None
    return Spread(round(mean(values), digits), round(median(values), digits))


def _spread(values: Sequence[float], digits: int) -> Spread:
    found = spread_of(values, digits)
    assert found is not None, "a group is built from at least one phase"
    return found


def phase_stats(phases: Sequence[Tuple[Phase, SessionCost]]) -> PhaseStats:
    return PhaseStats(
        phases=len(phases),
        usd=_spread([phase.spend.cost_usd for phase, _ in phases], 4),
        context_tokens=spread_of(
            [phase.context_tokens for phase, _ in phases if phase.context_tokens is not None], 0
        ),
        share_of_session=_spread(
            [
                phase.spend.cost_usd / row.total.cost_usd if row.total.cost_usd > 0 else 0.0
                for phase, row in phases
            ],
            4,
        ),
    )


def opening_command(row: SessionCost) -> str:
    """The slash command a session opened with. A `/handle` or `/from-branch`
    session is the fresh-session side of the comparison orientation feeds: work
    begun elsewhere, picked up from scratch."""
    prompt = row.opening_prompt or ""
    return prompt.split(" ", 1)[0] if prompt.startswith("/") else "(none)"


def _grouped(
    phases: Sequence[Tuple[Phase, SessionCost]], label: Callable[[Phase, SessionCost], str]
) -> Dict[str, PhaseStats]:
    groups: Dict[str, List[Tuple[Phase, SessionCost]]] = {}
    for pair in phases:
        groups.setdefault(label(*pair), []).append(pair)
    return {key: phase_stats(group) for key, group in sorted(groups.items())}


def orientation_of(rows: Sequence[SessionCost]) -> OrientationSummary:
    phases = [(row.orientation, row) for row in rows if row.orientation is not None]
    compacted = [(c, row) for _, row in phases for c in row.compactions]
    by_tool: Dict[str, int] = {}
    for compaction, _ in compacted:
        for tool, calls in compaction.rereads.by_tool.items():
            by_tool[tool] = by_tool.get(tool, 0) + calls
    return OrientationSummary(
        measured=len(phases),
        rows=len(rows),
        orientation=phase_stats(phases) if phases else None,
        by_ended_by=_grouped(phases, lambda phase, _: phase.ended_by or "(nothing)"),
        by_opening_command=_grouped(phases, lambda _, row: opening_command(row)),
        compactions=(
            CompactionStats(
                compactions=len(compacted),
                reorientation=phase_stats([(c.reorientation, row) for c, row in compacted]),
                compacted_from=spread_of(
                    [c.compacted_from for c, _ in compacted if c.compacted_from is not None], 0
                ),
                reread_calls=_spread([c.rereads.calls for c, _ in compacted], 2),
                reread_estimated_usd=_spread([c.rereads.estimated_usd for c, _ in compacted], 4),
                rereads_by_tool=dict(sorted(by_tool.items())),
            )
            if compacted
            else None
        ),
    )


def totals_of(rows: Iterable[SessionCost]) -> Totals:
    """A session is filed under where it **started**, the rule that already picks
    its row's month, so one running past midnight stays whole. A row with no
    priced response has no day to file under and lands in the grand total, its
    branch and its operator alone."""
    grand = Bucket()
    by_month: Dict[str, Bucket] = {}
    by_week: Dict[str, Bucket] = {}
    by_day: Dict[str, Bucket] = {}
    by_branch: Dict[str, Bucket] = {}
    by_operator: Dict[str, Bucket] = {}
    rows = list(rows)

    for row in rows:
        grand.count(row)
        by_branch.setdefault(branch_label(row), Bucket()).count(row)
        by_operator.setdefault(operator_label(row), Bucket()).count(row)
        started_at = row.first_response_at
        if started_at is None:
            continue
        by_month.setdefault(started_at[:7], Bucket()).count(row)
        by_week.setdefault(iso_week(date.fromisoformat(started_at[:10])), Bucket()).count(row)
        by_day.setdefault(started_at[:10], Bucket()).count(row)

    return Totals(
        sessions=grand.sessions,
        responses=grand.responses,
        cost_usd=round(grand.cost_usd, 4),
        by_month=_rounded(by_month),
        by_week=_rounded(by_week),
        by_day=_rounded(by_day),
        by_branch=_rounded(by_branch),
        by_operator=_rounded(by_operator),
        orientation=orientation_of(rows),
    )
