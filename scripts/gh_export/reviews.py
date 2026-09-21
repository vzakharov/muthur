"""The PR-only review section: review bodies, inline comment threads grouped
into reply chains, and each thread's resolved state.

A thread renders as an index row plus a body, so a reader picks the threads
worth opening off the index. The quoted diff is the reviewer's own selection
rather than GitHub's enclosing hunk. Threads the reviewer resolved are dropped
by default (a count line marks how many); `review_parts(..., include_resolved=True)`
keeps them.
"""

from __future__ import annotations

import re
from typing import Any

from gh_export.attachments import rewrite_attachment_refs
from gh_export.authorship import attribution, split_agent_footer
from gh_export.index import Indexed, anchor_tag, preview

HUNK_CONTEXT_LINES = 3
CONTEXT_LINE_CHARS = 200

_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def review_threads(comments: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Group inline review comments into reply chains, oldest root first."""
    by_id = {c["id"]: c for c in comments if c.get("id") is not None}

    def root_of(comment: dict[str, Any]) -> dict[str, Any]:
        seen: set[Any] = set()
        current = comment
        while True:
            parent_id = current.get("in_reply_to_id")
            if parent_id is None or parent_id not in by_id or parent_id in seen:
                return current
            seen.add(parent_id)
            current = by_id[parent_id]

    threads: dict[Any, list[dict[str, Any]]] = {}
    for comment in comments:
        threads.setdefault(root_of(comment)["id"], []).append(comment)

    for chain in threads.values():
        chain.sort(key=lambda c: c.get("created_at") or "")

    return sorted(threads.values(), key=lambda chain: chain[0].get("created_at") or "")


def resolution_label(
    chain: list[dict[str, Any]], resolved_by_comment_id: dict[int, bool]
) -> str:
    """A thread the resolution query didn't return reads as `resolution unknown`
    rather than silently as open — a reader acts on this word."""
    for comment in chain:
        resolved = resolved_by_comment_id.get(comment.get("id"))
        if resolved is not None:
            return "resolved" if resolved else "unresolved"
    return "resolution unknown"


def selection_of(comment: dict[str, Any]) -> tuple[int | None, int | None, str]:
    """`(start_line, line, side)` — the lines the reviewer highlighted.

    The pair is read from one side or the other, never mixed: a comment whose
    line left the diff carries it in `original_line` while `line` is null, and
    the stale `original_start_line` must not pair with a live `line`.
    """
    side = (comment.get("side") or "RIGHT").upper()
    if comment.get("line") is not None:
        return comment.get("start_line"), comment.get("line"), side
    return comment.get("original_start_line"), comment.get("original_line"), side


def trim_hunk(
    hunk: str, start_line: int | None, line: int | None, side: str = "RIGHT"
) -> str:
    """Cut GitHub's enclosing hunk down to the reviewer's selection.

    `diff_hunk` runs from the start of the enclosing hunk to the commented line,
    so a rewritten file arrives as hundreds of lines pointing at three. Nothing
    inside `start_line`..`line` is ever shortened — only the run-up around it,
    and the full hunk stays one click away on GitHub.
    """
    if not hunk:
        return ""
    header, rows = _hunk_rows(hunk)
    if not rows:
        return hunk

    # The hunk ends at the commented line, so its last row is the fallback when
    # the numbering doesn't resolve (a mixed-side selection, a malformed hunk).
    end = _row_index(rows, line, side)
    if end is None:
        end = len(rows) - 1
    start = _row_index(rows, start_line, side) if start_line is not None else end
    if start is None or start > end:
        start = end

    run_up_from = max(0, start - HUNK_CONTEXT_LINES)
    out = [header]
    if run_up_from:
        out.append(_elided(run_up_from))
    out.extend(_cap(rows[i][0]) for i in range(run_up_from, start))
    out.extend(rows[i][0] for i in range(start, end + 1))
    trailing = len(rows) - 1 - end
    if trailing > 0:
        out.append(_elided(trailing))
    return "\n".join(out)


def render_thread(
    chain: list[dict[str, Any]],
    anchor: str,
    url_to_relative: dict[str, str],
    resolved_by_comment_id: dict[int, bool],
) -> str:
    """One thread's body, opening with the anchor its index row links to."""
    root = chain[0]
    start_line, line, side = selection_of(root)
    label = resolution_label(chain, resolved_by_comment_id)
    chunks = [anchor_tag(anchor), "", f"### {_location(root)} — {label}", ""]
    hunk = trim_hunk(root.get("diff_hunk") or "", start_line, line, side)
    if hunk:
        chunks.extend(["```diff", hunk, "```", ""])
    for comment in chain:
        by_agent, body = split_agent_footer(comment.get("body") or "")
        chunks.extend(
            [
                f"**{attribution(comment.get('user'), by_agent)}**"
                f" — {comment.get('created_at', '')}",
                "",
                rewrite_attachment_refs(body or "_empty_", url_to_relative),
                "",
            ]
        )
    chunks.extend(["---", ""])
    return "\n".join(chunks)


def thread_summary(
    chain: list[dict[str, Any]],
    thread_id: str,
    resolved_by_comment_id: dict[int, bool],
) -> str:
    """The index row. Its fields are the ones `/handle`'s tail test selects on —
    the resolved state, the tail author's agent/human label and timestamp —
    so dropping one leaves that test reading bodies again."""
    tail = chain[-1]
    by_agent, body = split_agent_footer(tail.get("body") or "")
    return (
        f"- **{thread_id}** {_location(chain[0])}"
        f" — {resolution_label(chain, resolved_by_comment_id)}"
        f" — last: {attribution(tail.get('user'), by_agent)}"
        f" {tail.get('created_at', '')} — {preview(body)}"
    )


def review_parts(
    reviews: list[dict[str, Any]],
    comments: list[dict[str, Any]],
    url_to_relative: dict[str, str],
    resolved_by_comment_id: dict[int, bool],
    include_resolved: bool = False,
) -> tuple[str, list[Indexed]]:
    """The section heading plus the review bodies, and the threads as indexed
    bodies. Both empty when the PR has neither.

    Resolved threads are dropped unless `include_resolved`, since the reader
    skims every thread the export carries and a closed one is cost with no
    signal. When any are dropped, the heading still carries a one-line count so
    the section never vanishes silently — a PR whose every thread is resolved
    reads as "N omitted", not as no review at all. `resolution unknown` and
    `unresolved` are kept: only the state the reviewer explicitly closed goes.
    """
    bodied = [r for r in reviews if (r.get("body") or "").strip()]
    threads = review_threads(comments)
    if not include_resolved:
        kept = [
            chain
            for chain in threads
            if resolution_label(chain, resolved_by_comment_id) != "resolved"
        ]
        omitted = len(threads) - len(kept)
        threads = kept
    else:
        omitted = 0
    if not bodied and not threads and not omitted:
        return "", []

    chunks = ["## Review threads", ""]
    for review in bodied:
        state = (review.get("state") or "COMMENTED").upper()
        by_agent, body = split_agent_footer(review["body"])
        chunks.extend(
            [
                f"### Review by {attribution(review.get('user'), by_agent)} — {state}",
                "",
                f"_{review.get('submitted_at', '')}_",
                "",
                rewrite_attachment_refs(body or "_empty_", url_to_relative),
                "",
            ]
        )
    if omitted:
        plural = "" if omitted == 1 else "s"
        chunks.extend(
            [
                f"_{omitted} resolved thread{plural} omitted; "
                f"re-run with `--include-resolved` to export {'it' if omitted == 1 else 'them'}._",
                "",
            ]
        )

    items = []
    for number, chain in enumerate(threads, start=1):
        anchor = f"t{number:02d}"
        items.append(
            Indexed(
                anchor=anchor,
                summary=thread_summary(chain, f"T{number:02d}", resolved_by_comment_id),
                body=render_thread(
                    chain, anchor, url_to_relative, resolved_by_comment_id
                ),
            )
        )
    return "\n".join(chunks), items


def _location(root: dict[str, Any]) -> str:
    """`` `path`:line ``, or bare `` `path` `` for a file-level comment, which
    has a path and no line at all."""
    _, line, _ = selection_of(root)
    path = f"`{root.get('path') or '?'}`"
    return f"{path}:{line}" if line else path


def _hunk_rows(hunk: str) -> tuple[str, list[tuple[str, int | None, int | None]]]:
    """The `@@` header, and each row with its old- and new-file line numbers."""
    lines = hunk.split("\n")
    match = _HUNK_HEADER.match(lines[0]) if lines else None
    if not match:
        return (lines[0] if lines else ""), []

    old_no, new_no = int(match.group(1)), int(match.group(2))
    rows: list[tuple[str, int | None, int | None]] = []
    for text in lines[1:]:
        if text.startswith("+"):
            rows.append((text, None, new_no))
            new_no += 1
        elif text.startswith("-"):
            rows.append((text, old_no, None))
            old_no += 1
        elif text.startswith("\\"):
            # "\ No newline at end of file" annotates the row above it.
            rows.append((text, None, None))
        else:
            rows.append((text, old_no, new_no))
            old_no += 1
            new_no += 1
    return lines[0], rows


def _row_index(
    rows: list[tuple[str, int | None, int | None]], number: int | None, side: str
) -> int | None:
    if number is None:
        return None
    field = 1 if side == "LEFT" else 2
    for index, row in enumerate(rows):
        if row[field] == number:
            return index
    return None


def _elided(count: int) -> str:
    return f"… {count} line{'' if count == 1 else 's'} elided …"


def _cap(text: str) -> str:
    """Run-up only. The selection is never passed through here."""
    if len(text) <= CONTEXT_LINE_CHARS:
        return text
    return text[:CONTEXT_LINE_CHARS] + "…"
