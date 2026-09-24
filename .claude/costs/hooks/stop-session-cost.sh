#!/bin/bash
# `Stop` hook: price the session and commit its cost row to the branch.
#
# It shares the event with the harness's own `Stop` check, which refuses to end a
# turn on an unclean or unpushed tree. `.claude/costs/CLAUDE.md` § "Running
# beside the harness's Stop check" carries how the row is committed without the
# tree ever looking unfinished, and what the closing verdict covers when the tree
# was unclean before this ran.

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

# Whether the row already differed from HEAD when the turn ended — a hand run of
# `session_cost.py` writes it in place. The check read the same tree, so it was
# counting the row.
row_left=false

place_row() { mkdir -p -- "$(dirname "$2")" && mv -f -- "$1" "$2"; }

# The row reaches origin, then the branch, then the tree. The commit is built in
# a throwaway index, so work the agent has staged stays out of it, and pushed
# before the branch moves, so the branch is never ahead of origin while a push is
# in flight. What is left is two steps — the ref move and the rename — between
# which the tree differs from HEAD.
commit_row() {
  local staged=$1 row=$2 top path head blob was now subject index tree commit
  local sign=()

  top="$(repo rev-parse --show-toplevel)" &&
    path="${row#"$top"/}" &&
    head="$(repo rev-parse -q --verify HEAD)" &&
    blob="$(git -C "$top" hash-object -w --path "$path" -- "$staged")" ||
    return 1

  if [ "$blob" = "$(repo rev-parse -q --verify "HEAD:$path")" ]; then
    place_row "$staged" "$row"
    return 0
  fi

  # The turn's spend is measured from the row as last committed, not as last
  # written: a hand run between turns rewrites the file too.
  was="$(repo show "HEAD:$path" 2>/dev/null | jq -r '.total.costUsd // 0' 2>/dev/null)"
  now="$(jq -r '.total.costUsd' "$staged")"
  subject="$(awk -v was="${was:-0}" -v now="$now" \
    'BEGIN { printf "chore: session cost +%.2f USD, total %.2f USD", now - was, now }')"

  # `commit-tree` signs only when told to, where `commit` reads the config.
  [ "$(repo config --type=bool commit.gpgsign 2>/dev/null)" = true ] && sign=(-S)

  index="$staged.index"
  GIT_INDEX_FILE="$index" repo read-tree "$head" &&
    GIT_INDEX_FILE="$index" repo update-index --add --cacheinfo "100644,$blob,$path" &&
    tree="$(GIT_INDEX_FILE="$index" repo write-tree)"
  local built=$?
  rm -f -- "$index"
  [ "$built" -eq 0 ] &&
    commit="$(repo commit-tree "${sign[@]}" -p "$head" -m "$subject" "$tree")" ||
    return 1

  local pushed=false
  repo push -q origin "$commit:refs/heads/$branch" 2>/dev/null && pushed=true

  # `place_row`, split so the directory is made first and the ref move and the
  # rename run back to back.
  mkdir -p -- "$(dirname "$row")" &&
    repo update-ref -m "$subject" "refs/heads/$branch" "$commit" "$head" &&
    mv -f -- "$staged" "$row" &&
    git -C "$top" update-index --add -- "$path" ||
    return 1

  state=committed
  [ "$pushed" = false ] || state=pushed
}

run_ledger() {
  local transcript staged row
  transcript="$(field transcript_path)"
  [ -n "$transcript" ] && [ -f "$transcript" ] || return 0

  # The last moment before anything here touches the tree, and so the latest —
  # which is what gives the look for the check's process time to find it.
  wait_out_harness_check

  # Priced off the tree: `tmp/` is ignored, and on the row's filesystem, so the
  # rename that puts the row in place is atomic.
  staged="$root/tmp/cost-row.$$.json"
  mkdir -p -- "$root/tmp" &&
    row="$(python3 "$root/.claude/costs/session_cost.py" \
      --transcript "$transcript" \
      --session-id "$(field session_id)" \
      --row-path --at-stop --out "$staged")" ||
    { rm -f -- "$staged"; state=unpriced; return 0; }

  ! dirty "$row" || row_left=true

  commit_row "$staged" "$row" && return 0

  # A row that could not be committed still goes in place, for the verdict to
  # name rather than for the turn to lose.
  [ ! -f "$staged" ] || place_row "$staged" "$row"
  state=uncommitted
}

run_ledger

# The harness check's two conditions, re-read once the row is in: a push that
# failed leaves a commit it would refuse on the next turn, blamed on nobody.
outstanding() {
  dirty && return 0
  repo rev-parse -q --verify "$upstream" >/dev/null 2>&1 || return 1
  [ "$(repo rev-list "$upstream..HEAD" --count 2>/dev/null || echo 0)" -gt 0 ]
}

# The only channel a `Stop` hook has to the agent, spent only where a block is
# already happening — and never on a re-fired `Stop`, which the harness's check
# bails out of and this must bail with or the turn never ends.
[ "$state" = unpriced ] && say "pricing failed; no cost row written this turn"
[ "$(field stop_hook_active)" != "true" ] || exit 0

case "$state" in
  committed | uncommitted | pushed)
    if outstanding; then
      case "$state" in
        pushed) did="committed and pushed" ;;
        committed) did="committed but not pushed" ;;
        *) did="written but not committed" ;;
      esac
      say "this session's cost row is ${did}. A git check complaining above may be counting it rather than your work: read \`git status\` before acting, push whatever is outstanding, and then just stop — the check passes on the next try and nothing here needs redoing."
      exit 2
    fi
    ;;
esac

# Nothing is outstanding, but the check read the row before it was committed.
# Its exit 2 is continuing the turn already, so saying so costs no turn — which
# is also why this stays silent where no check is registered to have read it.
if [ "$row_left" = true ] && ! outstanding && harness_check_registered; then
  say "this session's cost row was left uncommitted when the turn ended, so a git check complaining above was counting it. The row is committed and pushed now and nothing is outstanding: just stop."
  exit 2
fi

exit 0
