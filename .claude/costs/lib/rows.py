"""A row's file on disk: written by the pricing run, and reshaped by the report."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Tuple

from lib.pricing import SessionCost, parse_session_cost
from lib.shape import to_json

ROOT = Path(__file__).resolve().parents[3]


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
