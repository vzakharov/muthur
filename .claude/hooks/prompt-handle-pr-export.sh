#!/bin/bash
# UserPromptSubmit hook: a `/handle` prompt names the branch whose PR is about
# to be the session's whole input, so re-export that PR before the turn.
#
# A PR moves while the branch works, which is what separates this from
# `.claude/hooks/prompt-issue-export.sh`, whose issue thread is a snapshot taken
# once and read forever. So this one fires on *every* prompt rather than a
# session's first, and re-exports whatever is already on disk: the case it
# exists for is a second `/handle` on the same branch, after a compaction
# boundary, reading "nothing changed" off an export an hour old.
#
# It then says what arrived, that question answered from memory being the failure
# itself. `/handle` Step 2 commits each export, so the answer is a `git diff`
# against the one the previous turn read — which is also what lets the operator
# see, in the branch's own history, what the agent was reacting to.
#
# The branch is resolved by name through `gh`, never off the working tree: at a
# session's first prompt `/from-branch` has not checked anything out yet, and the
# target named in the prompt is not the branch HEAD is on.
#
# Never fails the turn: a failure here — no `jq`, no `gh`, a dead network — costs
# the round trip the agent would have spent anyway, so each path is stderr plus
# exit 0. It commits nothing, for `.claude/hooks/prompt-issue-export.sh`'s
# reason: a hook that commits lands on whatever branch HEAD happens to be on,
# and a `/from-branch` session abandons the branch it starts on.

set -uo pipefail

. "$(dirname "${BASH_SOURCE[0]}")/lib.sh" || exit 0

need_command jq "skipping the export."
read_payload

prompt="$(field prompt)"
[ -n "$prompt" ] || exit 0

# The leading slash is optional because `/handle`'s own description takes bare
# `handle <branch>` as the same invocation. Over-matching is free: a prompt that
# merely opens with the verb ends in something that is not a branch, and the
# resolution below drops it.
[[ "$prompt" =~ ^[[:space:]]*/?handle([[:space:]]|$) ]] || exit 0

project="$(project_root)"
[ -n "$project" ] || exit 0
cd "$project" || exit 0
[ -f scripts/export-github-item.py ] || exit 0
need_command gh "skipping the export."
need_command python3 "skipping the export."

# Existence is the whole predicate for the target. A pattern for "looks like a
# branch" would have to guess at `#NNN`, a URL and a bare slug alike, and would
# read the trailing word of `/handle <branch> and finalize` as one; that
# invocation instead misses, and the agent exports it itself.
last="$(tr -s '[:space:]' '\n' <<<"$prompt" | sed '/^$/d' | tail -n1)"
branch=""
if [ -n "$last" ] && {
  git rev-parse --verify --quiet "refs/heads/$last" >/dev/null 2>&1 ||
    git ls-remote --exit-code --heads origin "$last" >/dev/null 2>&1
}; then
  branch="$last"
else
  # No target names the branch the session is already on — `/handle`'s bare form.
  branch="$(git branch --show-current 2>/dev/null)"
fi
[ -n "$branch" ] || exit 0

# A trunk is never `/handle`'s target, and exporting the PR of whatever landed
# there last would hand the session someone else's review threads.
trunk="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)" || trunk=""
case "$branch" in
"${trunk#origin/}" | main | master)
  say "$branch is the trunk; skipping the export."
  exit 0
  ;;
esac

# Open first: a branch whose PR was closed and replaced has both, and the open
# one is the thread `/handle` is being pointed at.
pr_number() {
  gh pr list --head "$branch" --state "$1" --limit 1 \
    --json number --jq '.[0].number // empty' 2>&1
}

if ! number="$(pr_number open)"; then
  say "gh could not list PRs for $branch: $(tail -n 2 <<<"$number")"
  exit 0
fi
if [ -z "$number" ] && ! number="$(pr_number all)"; then
  say "gh could not list PRs for $branch: $(tail -n 2 <<<"$number")"
  exit 0
fi
# A fresh harness auto-branch has no PR, so this doubles as the gate keeping a
# session's first prompt from exporting something it was never pointed at.
[ -n "$number" ] || exit 0

export_dir="docs/pr/$number"
export_path="$export_dir/pr.md"

failure=""
# A partial run exits non-zero too (`/take-issue` Step 1 owns what that covers),
# so a failure is reported with its output rather than swallowed or retried.
if ! output="$(timeout 50 python3 scripts/export-github-item.py "$number" 2>&1)"; then
  failure="$(tail -n 5 <<<"$output")"
fi

context=""
if [ -f "$export_path" ]; then
  context+="PR #$number is exported fresh at \`$export_path\` — this hook ran "
  context+=$'`scripts/export-github-item.py` for it before the turn.'
  # `/handle` Step 2 commits each export, so the re-export lands as a working-tree
  # change against the last one and git states what arrived. An empty diff on a
  # branch whose export is committed is the answer, not an absence of one.
  arrived="$(git diff -- "$export_dir" 2>/dev/null)"
  if [ -n "$arrived" ]; then
    context+=$' Against the export committed last time, this is what arrived:\n\n```diff\n'
    context+="$(head -n 40 <<<"$arrived")"
    context+=$'\n```\n\nTruncated at 40 lines — `git diff -- '"$export_dir"$'` has the rest.'
  elif git ls-files --error-unmatch "$export_path" >/dev/null 2>&1; then
    context+=$' `git diff` against the export committed last time is empty, so nothing has '
    context+=$'arrived on the PR since. That is the answer to "has anything changed?" — do not '
    context+=$'reach it any other way.'
  fi
  context+=$'\n\nSo `/handle` Step 2\'s export is done, but its commit is still yours: commit the '
  context+=$'export before working the lane, so the next turn diffs against what you read. '
  context+=$'Nothing here decides which lane runs.'
elif [ -n "$failure" ]; then
  context+="This PR export failed ahead of the turn — \`#$number\` on \`$branch\`: $failure"
  context+=$'\n\nRun `scripts/export-github-item.py` yourself per `/handle` Step 2, and stop and '
  context+=$'report rather than reading the PR some other way if it fails there too.'
fi

[ -n "$context" ] || exit 0

emit_context "$context"
