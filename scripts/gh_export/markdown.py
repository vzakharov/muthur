"""The sections every export carries: the header block and the conversation
comments."""

from __future__ import annotations

from typing import Any

from gh_export.attachments import rewrite_attachment_refs
from gh_export.authorship import attribution, split_agent_footer
from gh_export.index import Indexed, anchor_tag, preview


def header_section(
    item: dict[str, Any], pr: dict[str, Any] | None, body_by_agent: bool
) -> str:
    """`body_by_agent` is the caller's to compute — it holds the item body and
    strips the footer where it renders it."""
    labels = item.get("labels") or []
    labels_md = (
        ", ".join(f"`{(lab.get('name') or '')}`" for lab in labels)
        if labels
        else "_none_"
    )
    state_reason = item.get("state_reason") or ""
    state_suffix = f" ({state_reason})" if state_reason else ""

    lines = [
        f"# {'PR' if pr else 'Issue'} #{item['number']}: {item['title']}",
        "",
        f"- **State:** {item['state']}{state_suffix}",
        f"- **URL:** {item['html_url']}",
        f"- **Author:** {attribution(item.get('user'), body_by_agent)}",
    ]
    if pr:
        base_ref = pr.get("base") or {}
        head_ref = pr.get("head") or {}
        base = base_ref.get("ref") or "?"
        # A fork's head needs its `owner:branch` label to be unambiguous.
        cross_repo = (head_ref.get("repo") or {}).get("full_name") != (
            base_ref.get("repo") or {}
        ).get("full_name")
        head = (head_ref.get("label") if cross_repo else head_ref.get("ref")) or "?"
        lines.extend(
            [
                f"- **Base ← Head:** {base} ← {head}",
                f"- **Draft:** {'yes' if pr.get('draft') else 'no'}",
                f"- **Merged:** {pr.get('merged_at') or '_not merged_'}",
            ]
        )
    lines.extend(
        [
            f"- **Created:** {item['created_at']}",
            f"- **Updated:** {item['updated_at']}",
            f"- **Closed:** {item.get('closed_at') or '_not closed_'}",
            f"- **Labels:** {labels_md}",
            "",
            "---",
            "",
            "## Body",
            "",
        ]
    )
    return "\n".join(lines)


def comments_parts(
    comments: list[dict[str, Any]], url_to_relative: dict[str, str]
) -> tuple[str, list[Indexed]]:
    """The section heading, and each comment as an indexed body. Both empty when
    the item has no conversation comments."""
    if not comments:
        return "", []

    items = []
    for number, c in enumerate(comments, start=1):
        anchor = f"c{number:02d}"
        by_agent, body = split_agent_footer(c.get("body") or "")
        who = attribution(c.get("user"), by_agent)
        created = c.get("created_at", "")
        items.append(
            Indexed(
                anchor=anchor,
                summary=f"- **C{number:02d}** {who} — {created} — {preview(body)}",
                body="\n".join(
                    [
                        anchor_tag(anchor),
                        "",
                        f"### Comment by {who} on {created}",
                        "",
                        f"[{c.get('html_url', '')}]({c.get('html_url', '')})",
                        "",
                        rewrite_attachment_refs(body or "_empty_", url_to_relative),
                        "",
                        "---",
                        "",
                    ]
                ),
            )
        )
    return "## Comments\n", items
