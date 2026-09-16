"""Render a run of bodies as an index plus the bodies themselves.

Knows nothing about GitHub — a caller passes items and gets one section back.
Every item gets a row, so a consumer's instruction is one sentence: read the
index, follow the link.
"""

from __future__ import annotations

from typing import NamedTuple

PREVIEW_CHARS = 60


class Indexed(NamedTuple):
    """One body, with the index row that points at it.

    `summary` carries no link — `indexed_section` appends the arrow. `body`
    opens with its own `anchor_tag(anchor)`.
    """

    anchor: str
    summary: str
    body: str


def anchor_tag(anchor: str) -> str:
    """What a body opens with, so its index row's `#anchor` resolves."""
    return f'<a id="{anchor}"></a>'


def preview(body: str, limit: int = PREVIEW_CHARS) -> str:
    """A post's opening words, flattened to fit on one line of an index row."""
    text = " ".join((body or "").split())
    if not text:
        return '"_empty_"'
    if len(text) > limit:
        text = text[:limit].rstrip() + "…"
    return f'"{text}"'


def indexed_section(items: list[Indexed]) -> str:
    """The rows, then every body below them in the same order."""
    rows = [f"{item.summary} → [↓](#{item.anchor})" for item in items]
    return "\n".join([*rows, "", *(item.body for item in items)])
