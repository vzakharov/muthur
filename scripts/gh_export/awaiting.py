"""The PR export's opening verdict: the posts still waiting on an answer.

`/handle` Step 2's two signals, run here so a reader meets their result before
anything else rather than having to reach the indexes below a long PR body and
the comment bodies that follow it:

- an unresolved thread (or one of unknown resolution) whose newest post is a
  human's — the tail test;
- a human review body or conversation comment the agent has not yet seen, or
  has seen without posting anything since — the novelty test, the only handle
  on posts that carry no resolved state.

"Seen" means carried by the export the branch last committed
(`gh_export.previous`), which `/handle` commits on every read. A timestamp
cutoff cannot stand in for it: the branch's head commit is routinely a
session-cost row pushed after a review it never answered, and the agent's own
last post may answer something else entirely. A post the agent has seen stays
listed while no agent post follows it, so a session that read a review and
lost its context before answering still meets it. With no committed export,
that second clause is the whole test.

A review too large for one context to read through opens the verdict on a
warning, the verdict being what `/handle`'s hook hands the agent before it
reads a line.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple

from gh_export.authorship import attribution, split_agent_footer
from gh_export.markdown import comment_summary
from gh_export.previous import PreviousExport
from gh_export.reviews import (
    bodied_reviews,
    exported_threads,
    posted_at,
    resolution_label,
    thread_summary,
)

HEADING = "## Awaiting an answer"

# The fragments of the GitHub URLs an export renders beside each conversation
# comment and review body — their identities.
_POST_ID = re.compile(r"#((?:issuecomment|pullrequestreview)-\d+)")

# A review is large when one read of its export takes more than this share of
# the context budget's warning line.
LARGE_SHARE_OF_WARN_LINE = 1 / 5
CHARS_PER_TOKEN = 4


class ExportSize(NamedTuple):
    lines: int
    chars: int

    @classmethod
    def of(cls, text: str) -> ExportSize:
        return cls(text.count("\n") + 1, len(text))


def awaiting_section(
    comments: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    review_comments: list[dict[str, Any]],
    resolved_by_comment_id: dict[int, bool],
    include_resolved: bool,
    previous: PreviousExport | None,
    rest: ExportSize,
    warn_line: int,
) -> str:
    """The section, its heading carrying the count so a zero reads as a verdict
    rather than an absence. Every row links to the body it names.

    `rest` measures the export outside this section; `warn_line` is the context
    budget's, in tokens."""
    seen = set(_POST_ID.findall(previous.text)) if previous else None
    last_agent_post = _last_agent_post(comments, reviews, review_comments)

    def awaits(key: str, stamp: str | None) -> bool:
        unseen = seen is not None and key not in seen
        return unseen or (stamp or "") > last_agent_post

    rows: list[str] = []
    threads, _ = exported_threads(
        review_comments, reviews, resolved_by_comment_id, include_resolved
    )
    for number, chain in enumerate(threads, start=1):
        if resolution_label(chain, resolved_by_comment_id) == "resolved":
            continue
        if not _by_agent(chain[-1]):
            summary = thread_summary(chain, f"T{number:02d}", resolved_by_comment_id)
            rows.append(f"{summary} → [↓](#t{number:02d})")
    for number, review in enumerate(bodied_reviews(reviews), start=1):
        key = f"pullrequestreview-{review.get('id')}"
        if not _by_agent(review) and awaits(key, review.get("submitted_at")):
            who = attribution(review.get("user"), False)
            rows.append(
                f"- **R{number:02d}** review by {who} — "
                f"{review.get('submitted_at', '')} → [↓](#r{number:02d})"
            )
    for number, comment in enumerate(comments, start=1):
        key = f"issuecomment-{comment.get('id')}"
        if not _by_agent(comment) and awaits(key, comment.get("created_at")):
            rows.append(f"{comment_summary(number, comment)} → [↓](#c{number:02d})")

    against = (
        f"the export committed at {previous.commit}"
        if previous
        else "no export committed on the branch yet"
    )
    rule = (
        "_Unresolved threads whose newest post is a human's, and human reviews "
        "and comments that are new since the last export or that no agent post "
        f"has followed ({against}). "
        "Resolved threads never count; an `(agent)` tail is a reply already given._"
    )
    listing = [*rows, ""] if rows else []
    heading = [f"{HEADING}: {len(rows) or 'none'}", ""]
    body = [rule, "", *listing, "---", ""]
    own = ExportSize.of("\n".join([*heading, *body]))
    size = ExportSize(rest.lines + own.lines, rest.chars + own.chars)
    return "\n".join([*heading, *_large_review_warning(len(rows), size, warn_line), *body])


def _large_review_warning(awaiting: int, size: ExportSize, warn_line: int) -> list[str]:
    """Empty when nothing awaits, however large the file: there is nothing to
    hand out. No line may be `---`, where `/handle`'s hook stops lifting the
    verdict out of the file."""
    tokens = size.chars // CHARS_PER_TOKEN
    if not awaiting or tokens <= warn_line * LARGE_SHARE_OF_WARN_LINE:
        return []
    return [
        f"> **Large review: {size.lines:,} lines, ~{tokens:,} tokens, {awaiting} "
        "awaiting.** Do not read this file whole. Hand the posts below to "
        "subagents — readers in batches, then executors grouped by topic from "
        "what the readers return — keeping this session for the commits and "
        "replies. `.claude/skills/handle/large-review.md` says how.",
        "",
    ]


def _last_agent_post(
    comments: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    review_comments: list[dict[str, Any]],
) -> str:
    """The newest stamp on anything the agent posted, `""` when it posted
    nothing — every stamp being GitHub's ISO form, as `posted_at` relies on."""
    posted = posted_at(reviews)
    stamps = [
        *(c.get("created_at") or "" for c in comments if _by_agent(c)),
        *(r.get("submitted_at") or "" for r in reviews if _by_agent(r)),
        *(posted(c) for c in review_comments if _by_agent(c)),
    ]
    return max(stamps, default="")


def _by_agent(post: dict[str, Any]) -> bool:
    by_agent, _ = split_agent_footer(post.get("body") or "")
    return by_agent
