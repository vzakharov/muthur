"""Token counts and what they cost: the arithmetic both the transcript's pricing
and the orientation measure sum with, so neither has to import the other."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from lib.shape import ShapeError, camel, read_count, read_number, required


@dataclass(frozen=True)
class Rates:
    """USD per million tokens."""

    input: float
    output: float
    cache_write_5m: float
    cache_write_1h: float
    cache_read: float


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

    def context_tokens(self) -> int:
        """Everything the request sent: what the context had grown to."""
        return (
            self.input_tokens
            + self.cache_read_tokens
            + self.cache_write_5m_tokens
            + self.cache_write_1h_tokens
        )


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


def parse_tally(obj: Any, where: str) -> Tally:
    if not isinstance(obj, dict):
        raise ShapeError(f"{where}: not an object")
    return Tally(
        **{
            f.name: required(read_number if f.name == "cost_usd" else read_count, obj, camel(f.name), where)
            for f in fields(Tally)
        }
    )
