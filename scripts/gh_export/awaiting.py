"""The PR export's opening verdict: the posts still waiting on an answer.

`/handle` Step 2's two signals, run here so a reader meets their result before
anything else rather than having to reach the indexes below a long PR body and
the comment bodies that follow it:

- an unresolved thread (or one of unknown resolution) whose newest post is a
  human's — the tail test;
- a human review body or conversation comment posted after the head commit —
  the recency test, the only handle on posts that carry no resolved state.

The head commit's date comes off the timeline's `committed` event for the PR's
head SHA. Without one, every human review and comment counts: missing an
unanswered post costs more than re-reading an answered one.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from gh_export.authorship import attribution, split_agent_footer
from gh_export.markdown import comment_summary
from gh_export.reviews import (
    bodied_reviews,
    exported_threads,
    resolution_label,
    thread_summary,
)

HEADING = "## Awaiting an answer"


def head_commit(
    pr: dict[str, Any], timeline: list[dict[str, Any]]
) -> tuple[str, str | None]:
    """`(short sha, committer date or None)` for the PR's head."""
    sha = (pr.get("head") or {}).get("sha") or ""
    for ev in timeline:
        if ev.get("event") == "committed" and ev.get("sha") == sha:
            return sha[:7], (ev.get("committer") or {}).get("date")
    return sha[:7], None


def awaiting_section(
    pr: dict[str, Any],
    timeline: list[dict[str, Any]],
    comments: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    review_comments: list[dict[str, Any]],
    resolved_by_comment_id: dict[int, bool],
    include_resolved: bool,
) -> str:
    """The section, its heading carrying the count so a zero reads as a verdict
    rather than an absence. Every row links to the body it names."""
    sha, committed = head_commit(pr, timeline)
    cutoff = _instant(committed) if committed else None

    def after_head(stamp: str | None) -> bool:
        return cutoff is None or (bool(stamp) and _instant(stamp) > cutoff)

    rows: list[str] = []
    threads, _ = exported_threads(
        review_comments, reviews, resolved_by_comment_id, include_resolved
    )
    for number, chain in enumerate(threads, start=1):
        if resolution_label(chain, resolved_by_comment_id) == "resolved":
            continue
        tail_by_agent, _ = split_agent_footer(chain[-1].get("body") or "")
        if not tail_by_agent:
            summary = thread_summary(chain, f"T{number:02d}", resolved_by_comment_id)
            rows.append(f"{summary} → [↓](#t{number:02d})")
    for number, review in enumerate(bodied_reviews(reviews), start=1):
        by_agent, _ = split_agent_footer(review["body"])
        if not by_agent and after_head(review.get("submitted_at")):
            who = attribution(review.get("user"), by_agent)
            rows.append(
                f"- **R{number:02d}** review by {who} — "
                f"{review.get('submitted_at', '')} → [↓](#r{number:02d})"
            )
    for number, comment in enumerate(comments, start=1):
        by_agent, _ = split_agent_footer(comment.get("body") or "")
        if not by_agent and after_head(comment.get("created_at")):
            rows.append(f"{comment_summary(number, comment)} → [↓](#c{number:02d})")

    head = f"{sha}, {committed}" if committed else f"{sha}, date not on the timeline"
    rule = (
        "_Unresolved threads whose newest post is a human's, and human reviews "
        f"and comments posted after the head commit ({head}). "
        "Resolved threads never count; an `(agent)` tail is a reply already given._"
    )
    listing = [*rows, ""] if rows else []
    return "\n".join(
        [f"{HEADING}: {len(rows) or 'none'}", "", rule, "", *listing, "---", ""]
    )


def _instant(stamp: str) -> datetime:
    # `fromisoformat` takes no `Z` before Python 3.11.
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))
