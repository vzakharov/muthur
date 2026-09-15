"""Fit a rendered export into a line budget by hoisting bodies into sibling
files, leaving an index behind.

Knows nothing about GitHub — a caller passes parts and gets back the main
document plus the files to write beside it. Every item is indexed whether or not
it moves, so a consumer's instruction is one sentence in both shapes: read the
index, follow the link.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Iterator, NamedTuple

SPLIT_THRESHOLD_LINES = 400
PREVIEW_CHARS = 60
SLUG_MAX_CHARS = 50


class Hoistable(NamedTuple):
    """One body that may move out, with the index row that survives either way.

    `summary` carries no link — `split_export` appends the arrow and resolves
    the target. `body` opens with its own `anchor_tag(anchor)`.
    """

    anchor: str
    group: str
    summary: str
    body: str


class Stage(NamedTuple):
    """A group of hoistables that move together, in `hoist_order` (lowest first).

    A `target` ending in `/` is a directory, one file per `group`; anything else
    is a single file holding the whole stage.
    """

    target: str
    hoist_order: int
    title: str
    items: list[Hoistable]


def anchor_tag(anchor: str) -> str:
    """What a hoistable's body opens with, so an index row's `#anchor` resolves
    the same whether the body stayed put or moved into a sibling file."""
    return f'<a id="{anchor}"></a>'


def preview(body: str, limit: int = PREVIEW_CHARS) -> str:
    """A post's opening words, flattened to fit on one line of an index row."""
    text = " ".join((body or "").split())
    if not text:
        return '"_empty_"'
    if len(text) > limit:
        text = text[:limit].rstrip() + "…"
    return f'"{text}"'


def hoist_targets(parts: list[Any]) -> list[str]:
    """Every path the stages could occupy. A re-export clears these first, so a
    run that fits under the budget leaves no orphans from one that didn't."""
    return [p.target for p in parts if isinstance(p, Stage)]


def split_export(
    parts: list[Any], budget: int = SPLIT_THRESHOLD_LINES
) -> tuple[str, dict[str, str]]:
    """The main document, and the extra files keyed by path relative to it.

    Stages hoist one at a time in `hoist_order` until the document fits; under
    the budget nothing moves and the extras are empty.
    """
    stages = [p for p in parts if isinstance(p, Stage)]
    order = sorted(stages, key=lambda s: s.hoist_order)

    main = ""
    files: dict[str, str] = {}
    for count in range(len(order) + 1):
        hoisted = order[:count]
        hoisted_ids = {id(stage) for stage in hoisted}
        files = {}
        targets = {
            item.anchor: f"#{item.anchor}" for stage in stages for item in stage.items
        }
        for stage in hoisted:
            stage_files, stage_targets = _hoist(stage, budget)
            files.update(stage_files)
            targets.update(stage_targets)
        main = "\n".join(
            _stage_markdown(part, targets, id(part) not in hoisted_ids)
            if isinstance(part, Stage)
            else part
            for part in parts
        )
        if _line_count(main) <= budget:
            break
    return main, files


def _stage_markdown(stage: Stage, targets: dict[str, str], inline: bool) -> str:
    chunks = [_index_row(item, targets[item.anchor]) for item in stage.items]
    chunks.append("")
    if inline:
        chunks.extend(item.body for item in stage.items)
    return "\n".join(chunks)


def _index_row(item: Hoistable, target: str) -> str:
    label = "↓" if target.startswith("#") else target.split("#", 1)[0]
    return f"{item.summary} → [{label}]({target})"


def _hoist(stage: Stage, budget: int) -> tuple[dict[str, str], dict[str, str]]:
    files: dict[str, str] = {}
    targets: dict[str, str] = {}

    if not stage.target.endswith("/"):
        name = stage.target
        heading = [f"# {stage.title}", ""] if stage.title else []
        files[name] = "\n".join([*heading, *(item.body for item in stage.items)])
        for item in stage.items:
            targets[item.anchor] = f"{name}#{item.anchor}"
        return files, targets

    groups: dict[str, list[Hoistable]] = {}
    for item in stage.items:
        groups.setdefault(item.group, []).append(item)

    # `NN` is the order of the group's first item, so the directory sorts the
    # way the items arrived.
    for number, (group, items) in enumerate(groups.items(), start=1):
        for part, chunk in enumerate(_chunks(items, budget), start=1):
            suffix = "" if part == 1 else f"-{part}"
            name = f"{stage.target}{number:02d}-{_slug(group)}{suffix}.md"
            heading = f"# `{group}`" if group else f"# {stage.title or 'Unattached'}"
            if part > 1:
                heading += " (continued)"
            files[name] = "\n".join([heading, "", *(item.body for item in chunk)])
            for item in chunk:
                targets[item.anchor] = f"{name}#{item.anchor}"
    return files, targets


def _chunks(items: list[Hoistable], budget: int) -> Iterator[list[Hoistable]]:
    """Split one group across files when its bodies alone blow the budget. An
    item larger than the whole budget still gets a file rather than an endless
    split."""
    current: list[Hoistable] = []
    used = 0
    for item in items:
        size = _line_count(item.body)
        if current and used + size > budget:
            yield current
            current, used = [], 0
        current.append(item)
        used += size
    if current:
        yield current


def _slug(text: str) -> str:
    slug = re.sub(r"[^0-9a-z]+", "-", text.lower()).strip("-")
    slug = slug[:SLUG_MAX_CHARS].strip("-")
    if slug:
        return slug
    if not text:
        return "unattached"
    # A group whose every character is stripped (a non-Latin path) still needs a
    # name of its own; the `NN` prefix already keeps filenames unique.
    return "path-" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def _line_count(text: str) -> int:
    return len(text.splitlines())
