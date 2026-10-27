"""The rate table `prices.json` holds, and the lookup that picks a response's
rates out of it."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, fields
from typing import Any, Dict, Optional

from lib.shape import ShapeError, read_count, read_number, read_object, read_string, required
from lib.tally import Rates

# A snapshot id's release-date suffix, as in `claude-haiku-4-5-20251001`.
_DATED = re.compile(r"-\d{8}$")


@dataclass(frozen=True)
class LongPrompt:
    """A request whose prompt runs past `prompt_tokens` is billed whole, output
    included, at `rates`."""

    prompt_tokens: int
    rates: Rates


@dataclass(frozen=True)
class RateCard:
    rates: Rates
    above: Optional[LongPrompt] = None

    def for_prompt(self, prompt_tokens: int) -> Rates:
        if self.above is not None and prompt_tokens > self.above.prompt_tokens:
            return self.above.rates
        return self.rates


@dataclass(frozen=True)
class PriceTable:
    as_of: str
    rates: Dict[str, RateCard]

    def rates_for(self, model: str, speed: Optional[str], prompt_tokens: int) -> Optional[Rates]:
        """`prompt_tokens` is everything the request sent, cache reads and writes
        included. A dated snapshot id with no row of its own is priced at its
        undated alias's row; a dated row, where there is one, wins."""
        card = self.rates.get(rate_key(model, speed))
        if card is None and _DATED.search(model):
            card = self.rates.get(rate_key(_DATED.sub("", model), speed))
        return None if card is None else card.for_prompt(prompt_tokens)


def parse_rates(entry: Dict[str, Any], where: str) -> Rates:
    return Rates(**{f.name: required(read_number, entry, f.name, where) for f in fields(Rates)})


def parse_prices(text: str) -> PriceTable:
    table = json.loads(text)
    if not isinstance(table, dict):
        raise ShapeError("prices.json: not an object")
    rates: Dict[str, RateCard] = {}
    for key, entry in required(read_object, table, "rates", "prices.json").items():
        where = f"prices.json rates[{key!r}]"
        if not isinstance(entry, dict):
            raise ShapeError(f"{where}: not an object")
        above = read_object(entry, "above", where)
        rates[key] = RateCard(
            rates=parse_rates(entry, where),
            above=None
            if above is None
            else LongPrompt(
                prompt_tokens=required(read_count, above, "prompt_tokens", f"{where}.above"),
                rates=parse_rates(above, f"{where}.above"),
            ),
        )
    return PriceTable(as_of=required(read_string, table, "as_of", "prices.json"), rates=rates)


def rate_key(model: str, speed: Optional[str]) -> str:
    """`<model>/<speed>`, the pair a response is billed under."""
    return f"{model}/{speed if speed is not None else 'standard'}"
