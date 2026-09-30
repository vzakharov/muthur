#!/bin/sh
# Cap the root CLAUDE.md, with hysteresis: the file may grow to CEILING_CHARS,
# but a branch that takes it past the ceiling lands it at TARGET_CHARS or under.
# Every character in it is paid on every turn of every session, and nothing else
# pushes back on growth: each addition passes its own test in
# CLAUDE.md § "About this file", and the total drifts up unexamined. A single
# cap would be trimmed back to just under itself, a few hundred characters per
# session, forever; the gap between the two numbers is what makes one trim buy
# room for many additions.
#
# The file measured is the one the branch will land: the staged copy at
# STAGED_COPY when there is one, else CLAUDE.md itself. Measuring only the real
# file would pass a staged copy grown past the cap, and fail a branch whose
# staged copy is the trim that brings an oversized file back under it.
#
# "Crossed" is read off history, so there is no state to keep: the branch crossed
# when any of its own commits (`<merge-base>..HEAD`), or the worktree, carries a
# landing file over the ceiling. A repo whose base is already over counts as
# crossed on its first commit. With no base to bound the range, only the ceiling
# is checked, and the run says so.
#
# CLAUDE.md alone, not what it `@`-imports: an import is its own file with its
# own reason to exist, and the cap is on the one file every addition defaults to.
#
# There is deliberately no env override, for `check-squash-message.sh`'s reason:
# an adopter who puts the right size elsewhere, in either direction, changes the
# constants in this copy, in a commit that says why.
#
# POSIX `/bin/sh` and `git`, for the floor `check-squash-message.sh` states.
#
# Exit codes:
#   0  - within the ceiling and, on a branch that crossed it, back to the target;
#        or there is no CLAUDE.md.
#   1  - otherwise.

set -eu

cd "$(dirname "$0")/.."

PROG="check-claude-md-size"
CEILING_CHARS=25500
TARGET_CHARS=24500
FILE="CLAUDE.md"
# `scripts/staged.sh`'s mapping, which is the path alone.
STAGED_COPY=".claude/staged/CLAUDE.md.staged"

if [ ! -f "$FILE" ]; then
  printf '%s: skipped — no %s\n' "$PROG" "$FILE"
  exit 0
fi

# Characters, not bytes: deleting UTF-8 continuation bytes leaves one byte per
# character, whatever the locale — `check-squash-message.sh`'s `char_len` says
# why `wc -m` is not used.
count_chars() {
  LC_ALL=C tr -d '\200-\277' | wc -c | tr -d ' '
}

# The same bound `check-squash-message.sh` draws on its history rung, for the
# same reason: a crossing reachable from the base belongs to another branch.
merge_base_with_default() {
  for ref in refs/remotes/origin/HEAD refs/remotes/origin/main refs/remotes/origin/master; do
    git rev-parse --verify --quiet "$ref" >/dev/null || continue
    git merge-base HEAD "$ref" 2>/dev/null && return 0
  done
  return 1
}

# The landing file's size at commit $1, or nothing when it has no CLAUDE.md.
landed_chars_at() {
  if git cat-file -e "$1:$STAGED_COPY" 2>/dev/null; then
    git show "$1:$STAGED_COPY" | count_chars
  elif git cat-file -e "$1:$FILE" 2>/dev/null; then
    git show "$1:$FILE" | count_chars
  fi
}

landing="$FILE"
[ ! -f "$STAGED_COPY" ] || landing="$STAGED_COPY"
chars=$(count_chars <"$landing")

# The oldest of the branch's commits whose landing file is over the ceiling.
crossed_at=""
bounded=0
if base=$(merge_base_with_default); then
  bounded=1
  for commit in $(git rev-list --reverse "$base..HEAD"); do
    at=$(landed_chars_at "$commit")
    if [ -n "$at" ] && [ "$at" -gt "$CEILING_CHARS" ]; then
      crossed_at=$(git rev-parse --short "$commit")
      break
    fi
  done
fi
[ -n "$crossed_at" ] || [ "$chars" -le "$CEILING_CHARS" ] || crossed_at="the worktree"

if [ -n "$crossed_at" ] && [ "$chars" -gt "$TARGET_CHARS" ]; then
  printf '%s: %s is %s chars. The branch took it past the %s ceiling (at %s),\n' \
    "$PROG" "$landing" "$chars" "$CEILING_CHARS" "$crossed_at" >&2
  printf '%s: so it lands at %s or under: cut %s more.\n' \
    "$PROG" "$TARGET_CHARS" "$((chars - TARGET_CHARS))" >&2
  printf '%s: Hand the trim to a subagent. It matters, but it is not what this PR is for,\n' "$PROG" >&2
  printf '%s: and the cut-and-remeasure loop would spend this session'"'"'s context on it.\n' "$PROG" >&2
  printf '%s: Brief it with the target and CLAUDE.md § "About this file" as the test for what moves\n' "$PROG" >&2
  printf '%s: where; it edits %s (`scripts/staged.sh stage CLAUDE.md` first if absent).\n' "$PROG" "$STAGED_COPY" >&2
  exit 1
fi

note=""
[ -z "$crossed_at" ] || note=" (crossed the ceiling at $crossed_at, back under $TARGET_CHARS)"
[ "$bounded" -eq 1 ] || note=" (no base to read the branch's history against: ceiling only)"
printf '%s: ok — %s is %s/%s chars%s\n' "$PROG" "$landing" "$chars" "$CEILING_CHARS" "$note"
