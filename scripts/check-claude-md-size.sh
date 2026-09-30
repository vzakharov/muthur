#!/bin/sh
# Cap the root CLAUDE.md at MAX_CHARS characters, and fail when the branch would
# land it over. Every character in it is paid on every turn of every session, and
# nothing else pushes back on growth: each addition passes its own test in
# CLAUDE.md § "About this file", and the total drifts up unexamined.
#
# The file measured is the one the branch will land: its staged copy when
# `scripts/staged.sh` has one, else CLAUDE.md itself. Measuring only the real
# file would pass a staged copy grown past the cap, and fail a branch whose
# staged copy is the trim that brings an oversized file back under it.
#
# CLAUDE.md alone, not what it `@`-imports: an import is its own file with its
# own reason to exist, and the cap is on the one file every addition defaults to.
#
# There is deliberately no env override, for `check-squash-message.sh`'s reason:
# an adopter needing more room raises MAX_CHARS in this copy, in a commit that
# says why.
#
# POSIX `/bin/sh`, for the same floor `check-squash-message.sh` states.
#
# Exit codes:
#   0  - within the cap, or there is no CLAUDE.md.
#   1  - over the cap.

set -eu

cd "$(dirname "$0")/.."

PROG="check-claude-md-size"
MAX_CHARS=25000
FILE="CLAUDE.md"

if [ ! -f "$FILE" ]; then
  printf '%s: skipped — no %s\n' "$PROG" "$FILE"
  exit 0
fi

# Optional, so the check runs in a tree without staging.
landing="$FILE"
if [ -x scripts/staged.sh ]; then
  landing=$(scripts/staged.sh resolve "$FILE")
fi

# Characters, not bytes: deleting UTF-8 continuation bytes leaves one byte per
# character, whatever the locale — `check-squash-message.sh`'s `char_len` says
# why `wc -m` is not used.
chars=$(LC_ALL=C tr -d '\200-\277' <"$landing" | wc -c | tr -d ' ')

if [ "$chars" -gt "$MAX_CHARS" ]; then
  printf '%s: %s is %s chars, over the %s cap by %s.\n' \
    "$PROG" "$landing" "$chars" "$MAX_CHARS" "$((chars - MAX_CHARS))" >&2
  printf '%s: move what only matters in one place to a path-scoped rule, a skill or a nested CLAUDE.md;\n' "$PROG" >&2
  printf '%s: CLAUDE.md § "About this file" is the test.\n' "$PROG" >&2
  exit 1
fi

printf '%s: ok — %s is %s/%s chars\n' "$PROG" "$landing" "$chars" "$MAX_CHARS"
