#!/bin/bash
# UserPromptSubmit hook: a `/handle` prompt names the branch whose PR is about
# to be the session's whole input, so re-export that PR before the turn.
#
# Two things separate this from `.claude/hooks/prompt-issue-export.sh`, and both
# follow from what the two exports are. An issue export is a snapshot: taken
# once, read forever. A PR export is a moving target — `/handle`'s review lane
# is defined against what arrived since the last push — so:
#
#   - it fires on *every* prompt, not the session's first. The case it exists
#     for is a second `/handle` on the same branch, after a compaction boundary,
#     where the agent holds an export it took an hour ago and reads "nothing
#     changed" off it;
#   - it re-exports unconditionally. "Already on disk" is what makes that case
#     worse, not a reason to skip.
#
# It then says whether the re-export changed anything, because the whole failure
# it addresses is that question answered from memory. Untracked files make `git
# diff` no help here — `docs/pr/` is a working-tree artifact `/finalize` sweeps,
# never committed — so the comparison is against a copy taken before the run.
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

project="${CLAUDE_PROJECT_DIR:-$(field cwd)}"
[ -n "$project" ] && [ -d "$project" ] || exit 0
cd "$project" || exit 0
[ -f scripts/export-github-item.py ] || exit 0
need_command gh "skipping the export."
need_command python3 "skipping the export."

# The target is the prompt's last token, accepted only if it names a branch that
# exists. Existence is the whole predicate — no pattern for "looks like a
# branch", which would have to guess at `#NNN`, a URL and a bare slug alike, and
# would read the trailing word of `/handle <branch> and finalize` as a target.
# That invocation simply misses, and the agent exports it itself.
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
# No PR on the branch is the ordinary state of a fresh harness auto-branch, so
# this is also what keeps a session's first prompt from exporting anything it
# was never pointed at.
[ -n "$number" ] || exit 0

export_path="docs/pr/$number/pr.md"
previous=""
if [ -f "$export_path" ]; then
  previous="$(mktemp)" && cp "$export_path" "$previous" || previous=""
fi

failure=""
# The exporter exits non-zero on a partial run too — the Markdown written, an
# attachment missing — so a failure is reported with its output rather than
# swallowed or retried: which of those happened is the agent's to read.
if ! output="$(timeout 50 python3 scripts/export-github-item.py "$number" 2>&1)"; then
  failure="$(tail -n 5 <<<"$output")"
fi

context=""
if [ -f "$export_path" ]; then
  context+="PR #$number is exported fresh at \`$export_path\` — this hook ran "
  context+=$'`scripts/export-github-item.py` for it before the turn.'
  if [ -n "$previous" ] && cmp -s "$previous" "$export_path"; then
    context+=$' It is byte-identical to the export that was already on disk, so nothing has '
    context+=$'arrived on the PR since that one was taken. That is the answer to "has anything '
    context+=$'changed?", established by comparing two exports — do not reach it any other way.'
  elif [ -n "$previous" ]; then
    context+=$' It differs from the export that was already on disk, so something has arrived on '
    context+=$'the PR since that one was taken:\n\n```diff\n'
    context+="$(diff -u "$previous" "$export_path" | tail -n +3 | head -n 40)"
    context+=$'\n```\n\nThat diff is truncated at 40 lines — read the export for the rest.'
  fi
  context+=$'\n\nSo `/handle` Step 2\'s export is done: read the export\'s thread index and open the '
  context+=$'threads its tail test selects. Nothing is committed, and nothing here decides which '
  context+=$'lane runs.'
elif [ -n "$failure" ]; then
  context+="This PR export failed ahead of the turn — \`#$number\` on \`$branch\`: $failure"
  context+=$'\n\nRun `scripts/export-github-item.py` yourself per `/handle` Step 2, and stop and '
  context+=$'report rather than reading the PR some other way if it fails there too.'
fi

[ -n "$previous" ] && rm -f "$previous"
[ -n "$context" ] || exit 0

emit_context "$context"
