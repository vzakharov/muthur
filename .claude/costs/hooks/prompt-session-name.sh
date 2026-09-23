#!/bin/bash
# `UserPromptSubmit` hook: ask the agent to name this session, once.
#
# The transcript holds no title Claude Code generated, and the opening prompt the
# row falls back to is the launch command rather than what the session turned out
# to be about. Only the agent knows that, and only by the end of a turn — so this
# asks from the session's first prompt, before any row exists, and goes quiet the
# moment a name is written. Waiting for the row would skip every session that is
# one turn long, a `/plan` that ends on its handoff block being the usual one.
#
# `.claude/costs/CLAUDE.md` § "What names a session" carries the field.

. "$(dirname "${BASH_SOURCE[0]}")/../../hooks/lib.sh" || exit 0
read_payload
need_command jq ""

root="$(project_root)"
[ -n "$root" ] || exit 0

session="$(field session_id)"
[ -n "$session" ] || exit 0

# The row is filed under the month the session started, which this hook has no
# reason to work out for itself.
row="$(find "$root/.claude/costs/sessions" -name "$session.json" -type f 2>/dev/null | head -1)"

# No row yet is a session's first turn, before the `Stop` hook has written one;
# the `--name` run below writes it.
[ -z "$row" ] || jq -e '.name == null' "$row" >/dev/null 2>&1 || exit 0

transcript="$(field transcript_path)"
[ -n "$transcript" ] || exit 0

emit_context "This session has no name in the cost ledger (\`.claude/costs/sessions/\`) yet. Before this turn ends — it may be the session's only one — and once you can say what the session is actually about, which its opening prompt usually cannot, run:

  python3 .claude/costs/session_cost.py --transcript '$transcript' --name '<a few words>'

A short label a person would recognise the session by in a list, in the repo's own terms rather than the prompt's wording. Later runs carry it forward, so it is written once, and the \`Stop\` hook commits it with the row. This asks on each prompt until the field is set and then goes quiet; it does not deserve a turn of its own, so fold it into whatever you were going to run anyway."
