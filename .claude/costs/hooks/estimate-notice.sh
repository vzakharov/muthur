#!/bin/bash
# `UserPromptSubmit` and post-compaction `SessionStart` hook: keep the two
# fields of the session's row the agent sets in front of it. The human-hour
# estimate: with none yet, say how to set one; with one, restate it, since a
# prompt is where scope grows and nothing else would bring the figure back up
# then. The orientation mark: ask for it until the stretch since the session
# started or last compacted has one.
#
# This text is the agent-facing home of when and how to estimate and to mark;
# `.claude/costs/CLAUDE.md` § "Human-hour estimates" and § "Orientation" carry
# what each figure is for and what it cannot tell apart.

. "$(dirname "${BASH_SOURCE[0]}")/../../hooks/lib.sh" || exit 0
need_command jq "skipping the estimate notice."
need_command python3 "skipping the estimate notice."
read_payload

root="$(project_root)"
session_id="$(field session_id)"
[ -n "$root" ] && [ -n "$session_id" ] && [ -f "$root/.claude/costs/rates.json" ] || exit 0

script=".claude/costs/estimate.py"
# The repository's own roles are on `cost-ledger`, and a fresh container has no
# local copy of it until its first `Stop`; without one the notice would leave
# them out, so a failed fetch is said too.
unfetched=""
if ! git -C "$root" rev-parse -q --verify refs/remotes/origin/cost-ledger >/dev/null; then
  error="$(python3 "$root/.claude/costs/ledger.py" fetch 2>&1)" ||
    unfetched=" The \`cost-ledger\` branch could not be fetched, so any role this repository adds of its own is missing from the list: $error"
fi
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
# under it: listed among the shared roles alone, its work goes to the nearest.
added="$(jq -r '.added | to_entries | map(" This repository adds a role of its own: `\(.key)`, always `\(.value.grade)` — \(.value.work). Book that work under it, `--part <hours> \(.value.grade) \(.key)`, even where a shared role seems to fit.") | join("")' <<<"$rates")"
adding=" Work no listed role fits is a role this repository adds, with \`python3 $script role set <name> <multiplier> <grade> \"<the work booked under it>\"\`, which pushes it to \`cost-ledger\`."
shadowed="$(jq -r '.notes | map(" Two rates for one role: \(.).") | join("")' <<<"$rates")"

# One line per paragraph: the agent reads it unwrapped, and a hard break inside
# the command would split it.
if [ "$current" = "no estimate yet" ]; then
  notice="This session has no human-hour estimate yet. Once the size of the work is known, set one — the vet run at \`/finalize\` fails a branch carrying a session without one: \`$usage\` — one part per role and grade the task would take in a team, each the hours that person would spend on it (roles: $roles; grades: $grades).$added$adding A session that only answers a question gets one too. It sizes the task, never the session's own pace: revise it when the task grows or shrinks — scope added, a difficulty no estimator would have foreseen, a relay handing the rest on — and never because the work went slowly. Each part's reason is the case for the team: why that role at that grade for those hours — e.g. \`--part 2 middle developer \"the code is a routine component slot\" --part 1 senior copywriter \"the prose needs judgement of voice\"\` — never a summary of the work, which the row and the commits already carry. A revision replaces the whole estimate, and git keeps the old one, so its reasons justify the parts as they stand, never how the figure moved."
else
  # Correcting a part booked under the wrong role is not a change of size, so
  # it is named apart from the rule that revisions follow the task.
  [ -n "$added" ] && added="$added A part that booked such work under a shared role moves onto it."
  notice="This session's human-hour estimate: $current. If this prompt changes the size of the task — never the pace of the work — revise it with \`$usage\`, each part's reason justifying its role, grade and hours as they now stand — never a summary of the work, nor how the figure moved.$added"
fi

oriented=".claude/costs/oriented.py"
mark="Once you know what the repository is and what the request is about, mark the end of your orientation with \`python3 $oriented\`, bare — even with details of the ask still open, and before the next step that carries it out, even a read such as tracing callers. Skip it when that step is an edit to the repository or a reply to the operator: either ends orientation by itself."
transcript="$(field transcript_path)"
# A compaction has just opened a fresh stretch, so there is nothing to check.
if [ "$(field source)" != "compact" ] && [ -f "$transcript" ]; then
  if state="$(python3 "$root/$oriented" check "$transcript" 2>&1)"; then
    [ "$state" = "marked" ] && mark=""
  else
    mark="$mark (The transcript could not be read to tell whether you already have: $state)"
  fi
fi

emit_context "$notice$shadowed$unfetched${mark:+

$mark}"
