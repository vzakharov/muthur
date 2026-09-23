#!/bin/bash
# `UserPromptSubmit` hook: ask the agent to name this session, once.
#
# The transcript holds no title Claude Code generated, and the opening prompt the
# row falls back to is the launch command rather than what the session turned out
# to be about. Only the agent knows that, and only after a turn or two — so the
# row leaves `name` null and this asks for it on the next prompt, going quiet the
# moment one is written.
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

# No row yet is the first turn of a session, before the `Stop` hook has written
# one. There is nothing to name and nothing to ask about.
[ -n "$row" ] || exit 0

jq -e '.name == null' "$row" >/dev/null 2>&1 || exit 0

transcript="$(field transcript_path)"
[ -n "$transcript" ] || exit 0

emit_context "This session's cost row (\`${row#"$root"/}\`) carries no name yet. Once you can say what this session is actually about — which the opening prompt in the row usually cannot — run:

  python3 .claude/costs/session_cost.py --transcript '$transcript' --name '<a few words>'

A short label a person would recognise the session by in a list, in the repo's own terms rather than the prompt's wording. Later runs carry it forward, so it is written once. This asks on each prompt until the field is set and then goes quiet; it does not deserve a turn of its own, so fold it into whatever you were going to run anyway."
