#!/bin/bash
# UserPromptSubmit hook: a session's *first* prompt ending in `#<N>` is an
# operator handing that thread over — the shape a title copied out of GitHub's
# own UI arrives in — so export the thread and name the export in the turn's
# context. The session then starts holding the thread instead of spending a
# round trip fetching it.
#
# Only that first prompt. A `#<N>` later in the session is the agent's call,
# they having by then the context to weigh whether the number names a thread at
# all — the judgement a launch prompt arrives with nobody to make.
#
# An export that lands may still be one nobody wanted, so the injected context
# names it as untracked and the agent's to delete. Deleting a stray export is
# the cheap direction: `@.claude/skills/take-issue/SKILL.md` Step 2's commit
# stays the agent's, so nothing reaches the branch they did not put there. This
# hook commits nothing itself, for `.claude/hooks/session-images.sh`'s reason: a
# hook that commits lands on whatever branch HEAD happens to be on, and a
# `/from-branch` session abandons the branch it starts on.
#
# Never fails the turn: a failure here — no `jq`, no token, a private repo, a
# dead network — costs one round trip back to the loop the agent already had,
# so each path is stderr plus exit 0.

set -uo pipefail

. "$(dirname "${BASH_SOURCE[0]}")/lib.sh" || exit 0

need_command jq "skipping the export."
read_payload

prompt="$(field prompt)"
[ -n "$prompt" ] || exit 0

number_re='#([0-9]+)$'
[[ "$prompt" =~ $number_re ]] || exit 0
number="${BASH_REMATCH[1]}"

first_prompt || exit 0

project="$(project_root)"
[ -n "$project" ] || exit 0
need_command python3 "skipping the export."
cd "$project" || exit 0
[ -f scripts/export-github-item.py ] || exit 0

# Both roots are candidates for any number: whether it names an issue or a PR
# resolves from the API, never from the prompt.
landed_export() {
  local path
  for path in "docs/issue/$1/issue.md" "docs/pr/$1/pr.md"; do
    [ -f "$path" ] && { printf '%s\n' "$path"; return 0; }
  done
  return 1
}

failure=""
if ! landed="$(landed_export "$number")"; then
  # The exporter exits non-zero on a partial run too — the Markdown written, an
  # attachment missing — so a failure is reported with its output rather than
  # swallowed or retried: which of those happened is the agent's to read.
  if ! output="$(timeout 50 python3 scripts/export-github-item.py "$number" 2>&1)"; then
    failure="$(tail -n 5 <<<"$output")"
  fi
  landed="$(landed_export "$number")" || true
fi

context=""
if [ -n "$landed" ]; then
  context+=$'The GitHub thread this prompt ends in is on disk already — this hook ran\n'
  context+="\`scripts/export-github-item.py\` for it before the turn: $landed"
  context+=$'\n\nSo `/take-issue` Step 1 is done: read that export end to end, opening the files '
  context+=$'under its `attachments/` when you need pixels, and consult the thread only through '
  context+=$'it — never re-exporting it or fetching it some other way.'
  context+=$'\n\nNothing is committed. Step 2\'s commit is yours for a thread you are taking on — '
  context+=$'and where the number turns out to have been something else (a rule, a version, a '
  context+=$'quantity), delete the export instead. The prompt says what the session is about; '
  context+=$'this fetch only guessed.'
elif [ -n "$failure" ]; then
  context+="This export failed ahead of the turn — \`#$number\`: $failure"
  context+=$'\n\nMost often that means the number was never a thread reference, in which case '
  context+=$'there is nothing to fetch and nothing to do. Where the prompt really is handing a '
  context+=$'thread over, run `scripts/export-github-item.py` yourself per `/take-issue` Step 1, '
  context+=$'and stop and report rather than working from the title if it fails there too.'
else
  exit 0
fi

emit_context "$context"
