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
# A table that does not parse — a broken `rates.repo.json`, most likely — would
# refuse every estimate, so it is said rather than skipped.
if ! rates="$(python3 "$root/$script" rates 2>&1)"; then
  emit_context "The human-hour estimate's rate table does not parse, so no estimate can be set until it is fixed: $rates"
  exit 0
fi
shown="$(CLAUDE_CODE_SESSION_ID="$session_id" python3 "$root/$script" show)" || exit 0
current="${shown#*: }"
roles="$(jq -r '.roles | keys_unsorted | join(", ")' <<<"$rates")"
grades="$(jq -r '.grades | keys_unsorted | join(", ")' <<<"$rates")"
usage="python3 $script set --part <hours> <grade> <role> \"<why, at most 280 characters>\" [--part ...]"
# A repository's own role gets a sentence of its own, naming the work booked
# under it: listed among the shared roles, its work went to the nearest of them.
added="$(jq -r '.added | to_entries | map(" This repository adds a role of its own: `\(.key)`, always `\(.value.grade)` — \(.value.work). Book that work under it, `--part <hours> \(.value.grade) \(.key)`, even where a shared role seems to fit.") | join("")' <<<"$rates")"

# One line per paragraph: the agent reads it unwrapped, and a hard break inside
# the command would split it.
if [ "$current" = "no estimate yet" ]; then
  notice="This session has no human-hour estimate yet. Once the size of the work is known, set one — the vet run at \`/finalize\` fails a branch carrying a session without one: \`$usage\` — one part per role and grade the task would take in a team, each the hours that person would spend on it (roles: $roles; grades: $grades).$added A session that only answers a question gets one too. It sizes the task, never the session's own pace: revise it when the task grows or shrinks — scope added, a difficulty no estimator would have foreseen, a relay handing the rest on — and never because the work went slowly. Each part's reason is the case for the team: why that role at that grade for those hours — e.g. \`--part 2 middle developer \"the code is a routine component slot\" --part 1 senior copywriter \"the prose needs judgement of voice\"\` — never a summary of the work, which the row and the commits already carry. A revision replaces the whole estimate, and git keeps the old one, so its reasons justify the parts as they stand, never how the figure moved."
else
  # Correcting a part booked under the wrong role is not a change of size, so
  # it is named apart from the rule that revisions follow the task.
  [ -n "$added" ] && added="$added A part that booked such work under a shared role moves onto it."
  notice="This session's human-hour estimate: $current. If this prompt changes the size of the task — never the pace of the work — revise it with \`$usage\`, each part's reason justifying its role, grade and hours as they now stand — never a summary of the work, nor how the figure moved.$added"
fi

emit_context "$notice"
