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
[ -n "$root" ] && [ -n "$session_id" ] && [ -f "$root/.claude/costs/grades.json" ] || exit 0

script=".claude/costs/estimate.py"
shown="$(CLAUDE_CODE_SESSION_ID="$session_id" python3 "$root/$script" show)" || exit 0
current="${shown#*: }"
grades="$(jq -r 'keys_unsorted | join(", ")' "$root/.claude/costs/grades.json")"

# One line per paragraph: the agent reads it unwrapped, and a hard break inside
# the command would split it.
if [ "$current" = "no estimate yet" ]; then
  notice="This session has no human-hour estimate yet. Once the size of the work is known, set one: \`python3 $script set <hours> <grade> \"<why, at most 280 characters>\"\` — the hours a person of that grade ($grades) would take over the whole task, the grade being the one a team would hand it to. A session that only answers a question gets one too. It sizes the task, never the session's own pace: revise it when the task grows or shrinks — scope added, a difficulty no estimator would have foreseen, a relay handing the rest on — and never because the work went slowly."
else
  notice="This session's human-hour estimate: $current. If this prompt changes the size of the task — never the pace of the work — revise it with \`python3 $script set <hours> <grade> \"<why>\"\`."
fi

emit_context "$notice"
