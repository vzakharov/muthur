#!/bin/bash
# `Stop` hook: price the session and append its cost row to the ledger.
#
# It shares the event with the harness's own `Stop` check, which refuses to end a
# turn on an unclean or unpushed tree.
# `.claude/costs/CLAUDE.md` § "Running beside the harness's Stop check" carries
# why a row left in the tree is put back, and what the closing verdict covers.

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

ledger() { python3 "$root/.claude/costs/ledger.py" "$@"; }

branch="$(repo branch --show-current 2>/dev/null)"
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
      say "the harness's Stop check has run for 5s; putting the row back without waiting for it"
      return 0
    }
  done
}

# What the verdict at the foot reads: `unpriced`, or what became of a row left
# in the tree — `put_back` or `stuck`.
state=none

# The row back at HEAD's copy, index and file alike, or gone where HEAD has
# none.
put_back() {
  if repo cat-file -e "HEAD:$1" 2>/dev/null; then
    repo restore --source=HEAD --staged --worktree -- "$1"
  else
    repo rm -q --cached --ignore-unmatch -- "$1" && rm -f -- "$root/$1"
  fi
}

# What the pricing step and the ledger write said when they failed, for the
# agent to be told.
unpriced_reason=''
ledger_error=''

last_line() { awk 'NF { line = $0 } END { print line }' "$1" 2>/dev/null; }

# Git spreads one refusal over several lines, the last of which alone names
# nothing.
all_lines() { awk 'NF { printf "%s%s", sep, $0; sep = " " }' "$1" 2>/dev/null; }

run_ledger() {
  local transcript staged row path err
  transcript="$(field transcript_path)"
  [ -n "$transcript" ] && [ -f "$transcript" ] || return 0

  # Priced into the ignored `tmp/`: nothing up to the put-back touches the tree
  # or the branch, so none of it waits for the harness's check.
  staged="$root/tmp/cost-row.$$.json"
  err="$root/tmp/cost-row.$$.err"
  mkdir -p -- "$root/tmp" || return 0

  # The ledger's copy is fetched first, since the pricing run carries the
  # estimate over from it. A row priced without it could drop an estimate the
  # ledger holds, so a failed fetch writes nothing there.
  local fetched=true
  ledger fetch 2>"$err" || {
    ledger_error="$(all_lines "$err")"
    fetched=false
  }

  row="$(python3 "$root/.claude/costs/session_cost.py" \
    --transcript "$transcript" \
    --session-id "$(field session_id)" \
    --row-path --at-stop --out "$staged" 2>"$err")" ||
    {
      unpriced_reason="$(last_line "$err")"
      rm -f -- "$staged" "$err"
      state=unpriced
      return 0
    }
  path="${row#"$(repo rev-parse --show-toplevel)"/}"

  if [ "$fetched" = true ]; then
    ledger append-row "$path" "$staged" 2>"$err" || ledger_error="$(all_lines "$err")"
  fi
  rm -f -- "$staged" "$err"

  # A row differing from HEAD is one no commit took, and the ledger holds this
  # turn's anyway.
  dirty "$row" || return 0

  # The last moment before anything here touches the tree, and so the latest —
  # which is what gives the look for the check's process time to find it.
  wait_out_harness_check

  if put_back "$path"; then state=put_back; else state=stuck; fi
}

run_ledger

# The harness check's two conditions, re-read once the row is put back.
outstanding() {
  dirty && return 0
  repo rev-parse -q --verify "$upstream" >/dev/null 2>&1 || return 1
  [ "$(repo rev-list "$upstream..HEAD" --count 2>/dev/null || echo 0)" -gt 0 ]
}

# The only channel a `Stop` hook has to the agent is an exit 2, so a row that
# could not be priced blocks the turn once with the reason: a stderr line on a
# turn that ends anyway reaches nobody, and the ledger would lose sessions
# silently. Never on a re-fired `Stop`, which the harness's check bails out of
# and this must bail with or the turn never ends.
[ "$(field stop_hook_active)" != "true" ] || exit 0

if [ "$state" = unpriced ]; then
  say "pricing failed; no cost row written this turn. ${unpriced_reason:-session_cost.py exited non-zero without a message.} Fix that — a missing model is a new row in \`.claude/costs/prices.json\` — then just stop; the next turn's row covers this one too."
  exit 2
fi

# The ledger is the accounting, and the branch's copy goes when the branch is
# finalized, so a row the ledger missed is lost unless someone is told.
if [ -n "$ledger_error" ]; then
  say "the cost ledger (\`cost-ledger\` on origin) did not take this turn's row: ${ledger_error} Fix what that names if it is yours to fix, then just stop; the next turn's row covers this one too."
  exit 2
fi

if [ "$state" = stuck ]; then
  say "this session's cost row differs from HEAD and could not be put back, so a git check complaining above is counting it. Restore it to HEAD's copy (\`git restore --source=HEAD --staged --worktree -- <row>\`, or \`git rm --cached\` and delete it where HEAD has none) — the ledger already holds this turn's row — then just stop."
  exit 2
fi

# Nothing is outstanding, but the check read the row before it was put back. Its
# exit 2 is continuing the turn already, so saying so costs no turn — which is
# also why this stays silent where no check is registered to have read it.
if [ "$state" = put_back ] && ! outstanding && harness_check_registered; then
  say "this session's cost row was left in the tree with no commit to carry it, so a git check complaining above was counting it. It is back at HEAD's copy now — the ledger holds this turn's row, and your next commit carries a fresh one — and nothing is outstanding: just stop."
  exit 2
fi

exit 0
