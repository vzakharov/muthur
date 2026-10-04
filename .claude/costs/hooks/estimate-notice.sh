#!/bin/bash
# `UserPromptSubmit` hook: keep the session's human-hour estimate in front of the
# agent. With none yet, say how to set one; with one, restate it, since a prompt
# is where scope grows and nothing else would bring the figure back up then.
#
# This text is the agent-facing home of when and how to estimate;
# `.claude/costs/CLAUDE.md` § "Human-hour estimates" carries what the figure is
# for and what it cannot tell apart.

. "$(dirname "${BASH_SOURCE[0]}")/../../hooks/lib.sh" || exit 0
need_command jq "skipping the estimate notice."
need_command python3 "skipping the estimate notice."
read_payload

root="$(project_root)"
session_id="$(field session_id)"
[ -n "$root" ] && [ -n "$session_id" ] && [ -f "$root/.claude/costs/rates.json" ] || exit 0

script=".claude/costs/estimate.py"
shown="$(CLAUDE_CODE_SESSION_ID="$session_id" python3 "$root/$script" show)" || exit 0
current="${shown#*: }"
roles="$(jq -r '.roles | keys_unsorted | join(", ")' "$root/.claude/costs/rates.json")"
grades="$(jq -r '.grades | keys_unsorted | join(", ")' "$root/.claude/costs/rates.json")"
usage="python3 $script set \"<why, at most 280 characters>\" --part <hours> <grade> <role> [--part ...]"

# One line per paragraph: the agent reads it unwrapped, and a hard break inside
# the command would split it.
if [ "$current" = "no estimate yet" ]; then
  notice="This session has no human-hour estimate yet. Once the size of the work is known, set one: \`$usage\` — one part per role and grade the task would take in a team, each the hours that person would spend on it (roles: $roles; grades: $grades). A session that only answers a question gets one too. It sizes the task, never the session's own pace: revise it when the task grows or shrinks — scope added, a difficulty no estimator would have foreseen, a relay handing the rest on — and never because the work went slowly. A revision replaces the whole estimate, and git keeps the old one, so the comment says why the task is this size as it stands, never how the figure moved."
else
  notice="This session's human-hour estimate: $current. If this prompt changes the size of the task — never the pace of the work — revise it with \`$usage\`, the comment saying why the task is this size, never how the figure moved."
fi

emit_context "$notice"
