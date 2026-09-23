#!/bin/bash
# `Stop` hook: price the session and commit its cost row to the branch.
#
# It shares the event with the harness's own `Stop` check, which refuses to end a
# turn on an unclean or unpushed tree. `.claude/costs/CLAUDE.md` carries how the
# wait below narrows the race for the working tree, and what the closing verdict
# covers when it does not.

. "$(dirname "${BASH_SOURCE[0]}")/../../hooks/lib.sh" || exit 0
read_payload
need_command jq "the session's cost row was not written"
need_command python3 "the session's cost row was not written"

root="$(project_root)"
[ -n "$root" ] && [ -f "$root/.claude/costs/prices.json" ] || exit 0

repo() { git -C "$root" "$@"; }

# `status --porcelain`, not `diff HEAD`: a session's first row is an untracked
# file, which a diff against HEAD reports as no change at all.
dirty() { [ -n "$(repo status --porcelain -- "$@" 2>/dev/null)" ]; }

# A row is a branch's to carry. On the trunk there is no branch to carry it, and
# a hook that commits to `main` behind the operator's back is worse than a
# missing row.
branch="$(repo branch --show-current 2>/dev/null)"
case "$branch" in '' | main | master) exit 0 ;; esac
upstream="origin/$branch"

# The check leaves nothing on disk, so its process is the only thing there is to
# wait on, and the launcher's config is what says it will run at all — read in
# place of the script's presence, since a rename or a removal leaves the file
# lying there and takes the entry away.
launcher_settings="${HOME}/.claude/launcher-settings.json"
harness_check=stop-hook-git-check

harness_check_registered() {
  jq -e --arg name "$harness_check" \
    '[.hooks.Stop[]?.hooks[]?.command] | any(contains($name))' \
    "$launcher_settings" >/dev/null 2>&1
}

# The processes this hook runs under. The check is a sibling, never an ancestor,
# so an ancestor carrying its name merely mentions it — a shell invoking it, a
# test driving it — and waiting on one would outlast the turn.
ancestry() {
  local pid=$$
  while [ "${pid:-0}" -gt 1 ]; do
    printf ' %s' "$pid"
    pid="$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d '[:space:]')"
  done
  printf ' '
}

ancestors=''

harness_check_running() {
  local hit
  for hit in $(pgrep -f "$harness_check" 2>/dev/null); do
    case "$ancestors" in *" $hit "*) ;; *) return 0 ;; esac
  done
  return 1
}

wait_out_harness_check() {
  # No launcher config at all is a session running outside the harness, where
  # there was never a check to race.
  [ -f "$launcher_settings" ] || return 0
  harness_check_registered || {
    say "the harness no longer registers a \`${harness_check}\` Stop hook. The race this hook waits out may be gone, or the check may have been renamed — either way \`.claude/costs/CLAUDE.md\` § \"Running beside the harness's Stop check\" is written on an arrangement that has changed, and wants revisiting."
    return 0
  }
  command -v pgrep >/dev/null && command -v ps >/dev/null || return 0

  local waited=0
  ancestors="$(ancestry)"
  while harness_check_running; do
    sleep 0.05
    waited=$((waited + 1))
    [ "$waited" -lt 100 ] || {
      say "the harness's Stop check has run for 5s; writing the row without waiting for it"
      return 0
    }
  done
}

# Only the states that touch git can be mistaken for the agent's own work, which
# is what the verdict at the foot reads this for.
state=none

run_ledger() {
  local transcript row
  transcript="$(field transcript_path)"
  [ -n "$transcript" ] && [ -f "$transcript" ] || return 0

  # The last moment before anything here touches the tree, and so the latest —
  # which is what gives the look for the check's process time to find it.
  wait_out_harness_check

  row="$(python3 "$root/.claude/costs/session_cost.py" \
    --transcript "$transcript" \
    --session-id "$(field session_id)" \
    --row-path --at-stop)" || { state=unpriced; return 0; }

  dirty "$row" || return 0

  # The turn's spend is measured from the row as last committed, not as last
  # written: a hand run between turns rewrites the file too.
  local was now subject
  was="$(git -C "$(dirname "$row")" show "HEAD:./$(basename "$row")" 2>/dev/null |
    jq -r '.total.costUsd // 0' 2>/dev/null)"
  now="$(jq -r '.total.costUsd' "$row")"
  subject="$(awk -v was="${was:-0}" -v now="$now" \
    'BEGIN { printf "chore: session cost +%.2f USD, total %.2f USD", now - was, now }')"

  # `commit -- <path>` stages nothing else, so work the agent has in flight
  # stays where it is.
  repo add -- "$row" &&
    repo commit -q -m "$subject" -- "$row" ||
    { state=uncommitted; return 0; }

  state=committed
  repo push -q origin "$branch" 2>/dev/null && state=pushed
}

run_ledger

# The harness check's two conditions, re-read once the row is in: a push that
# failed leaves a commit it would refuse on the next turn, blamed on nobody.
outstanding() {
  dirty && return 0
  repo rev-parse -q --verify "$upstream" >/dev/null 2>&1 || return 1
  [ "$(repo rev-list "$upstream..HEAD" --count 2>/dev/null || echo 0)" -gt 0 ]
}

case "$state" in
  # The only channel a `Stop` hook has to the agent, spent only where a block is
  # already happening — and never on a re-fired `Stop`, which the harness's check
  # bails out of and this must bail with or the turn never ends.
  committed | uncommitted | pushed)
    if [ "$(field stop_hook_active)" != "true" ] && outstanding; then
      case "$state" in
        pushed) did="committed and pushed" ;;
        committed) did="committed but not pushed" ;;
        *) did="written but not committed" ;;
      esac
      say "this session's cost row is ${did}. A git check complaining above may be counting it rather than your work: read \`git status\` before acting, push whatever is outstanding, and then just stop — the check passes on the next try and nothing here needs redoing."
      exit 2
    fi
    ;;
  unpriced) say "pricing failed; no cost row written this turn" ;;
esac

exit 0
