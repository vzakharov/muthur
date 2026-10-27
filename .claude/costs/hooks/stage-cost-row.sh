#!/bin/bash
# `PreToolUse` hook on `Bash`: stage the session's cost row before a
# `git commit` runs, so the branch's display copy rides the agent's own commit.
#
# It never blocks the command: every way out is exit 0, and a row it could not
# price or stage is the `Stop` hook's to report, or to put back.
# `.claude/costs/CLAUDE.md` § "Where rows live" carries when it stages nothing.

. "$(dirname "${BASH_SOURCE[0]}")/../../hooks/lib.sh" || exit 0
read_payload
need_command jq "the cost row was not staged"
need_command python3 "the cost row was not staged"

root="$(project_root)"
[ -n "$root" ] && [ -f "$root/.claude/costs/prices.json" ] && cd "$root" || exit 0

command="$(jq -r '.tool_input.command // empty' <<<"$payload")"

# `git`, any `-c k=v` / `-C dir` options, then the subcommand: `commit-tree` and
# a `commit` inside `log --grep` do not match.
git_word='(^|[;&|({[:space:]])git([[:space:]]+-[cC][[:space:]]+[^[:space:]]+)*[[:space:]]+'
[[ $command =~ ${git_word}commit([[:space:]]|$) ]] || exit 0
rest="${command#*"${BASH_REMATCH[0]}"}"
commit_args="${rest%%[;&|]*}"

# A command naming the rows' directory manages the rows itself — `/finalize`'s
# sweep, where a staged row would make `git rm` refuse or put back what it
# deletes.
[[ $command == *.claude/costs/sessions* ]] && exit 0

top="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0

# A commit made in another work tree — a delegate's worktree — leaves this
# index alone, unless the command names this one, as a multi-repo session's
# `cd <repo> &&` does.
names_top() {
  local word
  read -ra words <<<"$command"
  for word in "${words[@]}"; do
    word="${word//[\"\']/}"
    word="${word%%[;&|)]*}"
    [ "${word%/}" = "$top" ] && return 0
  done
  return 1
}
here="$(git -C "$(field cwd)" rev-parse --show-toplevel 2>/dev/null)"
[ "$here" = "$top" ] || names_top || exit 0

# Concluding a merge, cherry-pick, revert or rebase commits exactly what git
# left, which `/sync-branch` relies on.
for marker in MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD rebase-merge rebase-apply; do
  [ -e "$(git rev-parse --git-path "$marker")" ] && exit 0
done

branch="$(git branch --show-current)"
[ -n "$branch" ] || exit 0
[ "$(python3 .claude/costs/ledger.py display "$branch" 2>/dev/null)" = display=yes ] || exit 0

transcript="$(field transcript_path)"
[ -n "$transcript" ] && [ -f "$transcript" ] || exit 0
mkdir -p tmp || exit 0
staged="tmp/cost-row.$$.json"
row="$(python3 .claude/costs/session_cost.py \
  --transcript "$transcript" \
  --session-id "$(field session_id)" \
  --row-path --out "$staged" 2>/dev/null)" || {
  rm -f -- "$staged"
  exit 0
}
path="${row#"$top"/}"

# A commit with nothing else to take would otherwise succeed as a row-only
# commit under the agent's message, where git would have said "nothing to
# commit".
stages="${git_word}(add|rm|mv)([[:space:]]|$)"
whole='(^|[[:space:]])(-[[:alpha:]]*a[[:alpha:]]*|--all|--amend)([[:space:]]|$)'
if ! [[ $command =~ $stages ]] && ! [[ $commit_args =~ $whole ]] &&
  git diff --cached --quiet -- . ":(exclude)$path"; then
  rm -f -- "$staged"
  exit 0
fi

mkdir -p -- "$(dirname "$path")" && mv -f -- "$staged" "$path" && git add -- "$path" ||
  rm -f -- "$staged"
exit 0
