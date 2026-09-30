#!/bin/sh
# Cap the root CLAUDE.md and everything it `@`-imports, with hysteresis: the
# total may grow to CEILING_CHARS, but a branch that takes it past the ceiling
# lands it at TARGET_CHARS or under. Every character of it is paid on every turn
# of every session, and nothing else pushes back on growth: each addition passes
# its own test in CLAUDE.md § "About this file", and the total drifts up
# unexamined. A single cap would be trimmed back to just under itself, a few
# hundred characters per session, forever; the gap between the two numbers is
# what makes one trim buy room for many additions.
#
# The imports count because the harness expands them into the same prefix as
# CLAUDE.md itself, so moving text into one moves the cost without cutting it.
# What counts as an import is the harness's rule: an `@<path>` at the start of a
# line or after whitespace, outside code spans and fenced blocks, naming a file
# that exists, resolved against the importing file's directory, followed up to
# MAX_IMPORT_HOPS deep. A backticked `@.claude/…` citation is a reference, not an
# import, and loads nothing. `.claude/rules/` is outside the count.
#
# Each file is measured as the branch will land it: its staged copy under
# STAGED_DIR when there is one, else the file itself. Measuring only the real
# file would pass a staged copy grown past the cap, and fail a branch whose
# staged copy is the trim that brings an oversized file back under it.
#
# "Crossed" is read off history, so there is no state to keep: the branch crossed
# when any of its own commits (`<merge-base>..HEAD`), or the worktree, carries a
# total over the ceiling. A repo whose base is already over counts as crossed on
# its first commit. With no base to bound the range, only the ceiling is
# checked, and the run says so.
#
# There is deliberately no env override, for `check-squash-message.sh`'s reason:
# an adopter with its own idea of the right size changes the constants in this
# copy, in a commit that says why.
#
# POSIX `/bin/sh` and `git`, for the floor `check-squash-message.sh` states.
#
# Exit codes:
#   0  - within the ceiling and, on a branch that crossed it, back to the target;
#        or there is no CLAUDE.md.
#   1  - otherwise.

# No globbing: import paths are split on whitespace unquoted, and none may expand.
set -euf

cd "$(dirname "$0")/.."

PROG="check-claude-md-size"
CEILING_CHARS=30000
TARGET_CHARS=29000
FILE="CLAUDE.md"
MAX_IMPORT_HOPS=5
# `scripts/staged.sh`'s mapping: `<path>` is staged at `$STAGED_DIR/<path>.staged`.
STAGED_DIR=".claude/staged"

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

# File access at revision $1, where an empty $1 is the worktree.
has_file() {
  if [ -z "$1" ]; then [ -f "$2" ]; else git cat-file -e "$1:$2" 2>/dev/null; fi
}
cat_file() {
  if [ -z "$1" ]; then cat "$2"; else git show "$1:$2"; fi
}

# The file that lands for path $2 at revision $1, or nothing when there is none.
landing_of() {
  if has_file "$1" "$STAGED_DIR/$2.staged"; then
    printf '%s\n' "$STAGED_DIR/$2.staged"
  elif has_file "$1" "$2"; then
    printf '%s\n' "$2"
  fi
}

# The import candidates in the text on stdin, one repo-relative path per line,
# resolved against directory $1. A `~` or absolute path names a file outside what
# the branch lands, and a path that climbs out of the repo resolves to nothing.
imports_in() {
  awk -v dir="$1" '
    function normalize(p,   parts, n, i, k, out, j) {
      n = split(p, parts, "/")
      k = 0
      for (i = 1; i <= n; i++) {
        if (parts[i] == "" || parts[i] == ".") continue
        if (parts[i] == "..") { if (k == 0) return ""; k--; continue }
        out[++k] = parts[i]
      }
      p = ""
      for (j = 1; j <= k; j++) p = p (j > 1 ? "/" : "") out[j]
      return p
    }
    /^[ \t]*(```|~~~)/ { fenced = !fenced; next }
    fenced { next }
    {
      gsub(/`[^`]*`/, "")
      n = split($0, words, /[ \t]+/)
      for (i = 1; i <= n; i++) {
        if (words[i] !~ /^@[^~\/]/) continue
        path = normalize(dir "/" substr(words[i], 2))
        if (path != "") print path
      }
    }
  '
}

# "<chars>\t<landing file>" for CLAUDE.md and each file it imports, transitively,
# at revision $1. Call it in a command substitution: POSIX `sh` has no locals.
closure_at() {
  queue="$FILE" seen=" " hops=0
  while [ -n "$queue" ] && [ "$hops" -le "$MAX_IMPORT_HOPS" ]; do
    next=""
    for path in $queue; do
      case "$seen" in *" $path "*) continue ;; esac
      seen="$seen$path "
      landed=$(landing_of "$1" "$path")
      [ -n "$landed" ] || continue
      printf '%s\t%s\n' "$(cat_file "$1" "$landed" | count_chars)" "$landed"
      next="$next $(cat_file "$1" "$landed" | imports_in "$(dirname "$path")")"
    done
    queue=$next
    hops=$((hops + 1))
  done
}

total_of() {
  awk -F '\t' '{ total += $1 } END { print total + 0 }'
}

breakdown_of() {
  awk -F '\t' '{ printf "%s%s %s", (NR > 1 ? ", " : ""), $2, $1 }'
}

closure=$(closure_at "")
chars=$(printf '%s\n' "$closure" | total_of)
files=$(printf '%s\n' "$closure" | breakdown_of)

# The oldest of the branch's commits whose total is over the ceiling.
crossed_at=""
bounded=0
if base=$(merge_base_with_default); then
  bounded=1
  for commit in $(git rev-list --reverse "$base..HEAD"); do
    at=$(closure_at "$commit" | total_of)
    if [ "$at" -gt "$CEILING_CHARS" ]; then
      crossed_at=$(git rev-parse --short "$commit")
      break
    fi
  done
fi
[ -n "$crossed_at" ] || [ "$chars" -le "$CEILING_CHARS" ] || crossed_at="the worktree"

if [ -n "$crossed_at" ] && [ "$chars" -gt "$TARGET_CHARS" ]; then
  printf '%s: %s and its imports are %s chars (%s).\n' "$PROG" "$FILE" "$chars" "$files" >&2
  printf '%s: The branch took them past the %s ceiling (at %s),\n' \
    "$PROG" "$CEILING_CHARS" "$crossed_at" >&2
  printf '%s: so it lands at %s or under: cut %s more.\n' \
    "$PROG" "$TARGET_CHARS" "$((chars - TARGET_CHARS))" >&2
  printf '%s: Hand the trim to a subagent. It matters, but it is not what this PR is for,\n' "$PROG" >&2
  printf '%s: and the cut-and-remeasure loop would spend this session'"'"'s context on it.\n' "$PROG" >&2
  printf '%s: Brief it with the target and CLAUDE.md § "About this file" as the test for what moves\n' "$PROG" >&2
  printf '%s: where — moving text into another import cuts nothing. It edits the files'"'"' staged copies\n' "$PROG" >&2
  printf '%s: under %s (`scripts/staged.sh stage <path>` first where there is none).\n' "$PROG" "$STAGED_DIR" >&2
  exit 1
fi

note=""
[ -z "$crossed_at" ] || note=" (crossed the ceiling at $crossed_at, back under $TARGET_CHARS)"
[ "$bounded" -eq 1 ] || note=" (no base to read the branch's history against: ceiling only)"
printf '%s: ok — %s and its imports are %s/%s chars (%s)%s\n' \
  "$PROG" "$FILE" "$chars" "$CEILING_CHARS" "$files" "$note"
