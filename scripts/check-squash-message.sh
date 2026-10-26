#!/bin/sh
# Hold the squash proposal's copy-pasteable text to the rules
# `@.claude/skills/squash-message/SKILL.md` states as prose — size caps, and no
# session link in the body — and fail when one breaks. The skill's Step 3 is an
# agent reading their own output; this is the part of that target a machine can
# settle. A proposal is the body alone, or a title block then the body; the PR
# title outside a title block is beyond this script's reach.
#
# There is deliberately no env override: a hatch in the template teaches
# reaching for it instead of tightening. An adopter needing more room edits this
# copy instead — raising a constant below, or adding the mechanics that decide
# when a wider cap applies.
#
# Usage:
#   scripts/check-squash-message.sh [<path-to-proposal>]
#
# With no argument the proposal is located by the ladder in `resolve_source`,
# because `/finalize` sweeps `docs/remove-before-merging/` before a re-vet can
# run and the file is usually already gone by the time this executes. Finding
# nothing is normal — every lane that vets before `/squash-message` has run has
# no proposal — so that case reports the absence and passes.
#
# POSIX `/bin/sh` with `git` for the history rungs: `scripts/vet.sh` is the one
# entrypoint every adopter must have, so a check it calls must not add an
# interpreter or a `jq`/`gh` prerequisite to the floor.
#
# Exit codes:
#   0  - every rule held, or there is no proposal to measure.
#   1  - a cap was exceeded, the body carried a session link, the proposal was
#        unparseable, or bad arguments.

set -eu

# shellcheck source=lib/chars.sh
. "$(dirname "$0")/lib/chars.sh"

PROG="check-squash-message"

TITLE_MAX_CHARS=80
BODY_MAX_LINES=40
BODY_MAX_WIDTH=72

TRACKED_PATH="docs/remove-before-merging/squash-message.md"
TMP_PATH="tmp/squash-message.md"

NL='
'

die() {
  printf '%s: %s\n' "$PROG" "$1" >&2
  exit 1
}

usage() {
  cat >&2 <<EOF
usage: scripts/check-squash-message.sh [<path-to-proposal>]

  Measures the squash proposal's title block, if any, and body against the
  size caps.
  With no argument, locates the proposal itself (worktree, tmp/, then git
  history) and passes quietly when there is none.
EOF
  exit 1
}

case "${1:-}" in
  -h | --help) usage ;;
esac
[ "$#" -le 1 ] || usage

if REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null); then
  IN_REPO=1
else
  REPO_ROOT="."
  IN_REPO=0
fi

TMPFILE=""
cleanup() {
  [ -z "$TMPFILE" ] || rm -f "$TMPFILE"
}
trap cleanup EXIT HUP INT TERM

# Bounds the history rung to this branch's own commits. `origin/HEAD` is absent
# from a clone made without it — agent sessions get one of those — hence the
# default names after it. An unresolvable base returns 1 rather than widening to
# the whole history: a swept proposal reachable from the base belongs to another
# branch, and measuring it would fail this branch for someone else's words.
merge_base_with_default() {
  for ref in refs/remotes/origin/HEAD refs/remotes/origin/main refs/remotes/origin/master; do
    git rev-parse --verify --quiet "$ref" >/dev/null || continue
    git merge-base HEAD "$ref" 2>/dev/null && return 0
  done
  return 1
}

# Sets SRC_FILE (what to read) and SRC_DESC (what to tell the operator it was).
# Returns 1 when no proposal exists anywhere, which is a pass, not an error.
resolve_source() {
  if [ -n "${1:-}" ]; then
    [ -f "$1" ] || die "no such file: $1"
    SRC_FILE="$1"
    SRC_DESC="$1 (given)"
    return 0
  fi

  if [ -f "$REPO_ROOT/$TRACKED_PATH" ]; then
    SRC_FILE="$REPO_ROOT/$TRACKED_PATH"
    SRC_DESC="$TRACKED_PATH (worktree)"
    return 0
  fi

  if [ -f "$REPO_ROOT/$TMP_PATH" ]; then
    SRC_FILE="$REPO_ROOT/$TMP_PATH"
    SRC_DESC="$TMP_PATH (worktree)"
    return 0
  fi

  [ "$IN_REPO" -eq 1 ] || return 1

  TMPFILE="${TMPDIR:-/tmp}/$PROG.$$"

  if git cat-file -e "HEAD:$TRACKED_PATH" 2>/dev/null; then
    git show "HEAD:$TRACKED_PATH" >"$TMPFILE"
    SRC_FILE="$TMPFILE"
    SRC_DESC="HEAD:$TRACKED_PATH (sweep staged, not committed)"
    return 0
  fi

  base=$(merge_base_with_default) || return 1
  deleted_in=$(git log --diff-filter=D -1 --format=%h "$base..HEAD" -- "$TRACKED_PATH")
  if [ -n "$deleted_in" ]; then
    git show "$deleted_in^:$TRACKED_PATH" >"$TMPFILE"
    SRC_FILE="$TMPFILE"
    SRC_DESC="$TRACKED_PATH (swept in $deleted_in, read from history)"
    return 0
  fi

  return 1
}

is_blank() {
  case $1 in
    *[![:space:]]*) return 1 ;;
    *) return 0 ;;
  esac
}

# The caps are terminal columns, so they count characters.
char_len() {
  s=$(printf '%s' "$1" | one_byte_per_char)
  printf '%s' "${#s}"
}

# True when the line still holds whitespace once its own indent and any trailing
# spaces are gone — i.e. it is more than one unwrappable token and so had a
# wrapped form available to it.
is_wrappable() {
  s=${1#"${1%%[![:space:]]*}"}
  s=${s%"${s##*[![:space:]]}"}
  case $s in
    *[![:space:]]*[[:space:]]*) return 0 ;;
    *) return 1 ;;
  esac
}

resolve_source "${1:-}" || {
  printf '%s: no squash proposal on this branch — nothing to measure.\n' "$PROG"
  exit 0
}

# The body is the last block, so the count has to be known before the read.
fences=$(grep -c '^```' "$SRC_FILE" || true)
total_blocks=$((fences / 2))

blocks=0
in_block=0
title_lines=0
title_over=""
title_widest=0
body_lines=0
body_blanks_held=0
body_over=""
body_over_count=0
body_widest=0
body_session=""
body_session_count=0

while IFS= read -r line || [ -n "$line" ]; do
  case $line in
    '```'*)
      if [ "$in_block" -eq 1 ]; then
        in_block=0
      else
        blocks=$((blocks + 1))
        in_block=1
      fi
      continue
      ;;
  esac

  [ "$in_block" -eq 1 ] || continue

  if [ "$total_blocks" -eq 2 ] && [ "$blocks" -eq 1 ]; then
    if is_blank "$line"; then
      continue
    fi
    title_lines=$((title_lines + 1))
    len=$(char_len "$line")
    [ "$len" -le "$title_widest" ] || title_widest=$len
    if [ "$len" -gt "$TITLE_MAX_CHARS" ]; then
      title_over="${title_over}${NL}    ${len} chars: ${line}"
    fi
    continue
  fi
  [ "$blocks" -eq "$total_blocks" ] || continue

  # Trailing blank lines are not part of the body, so blanks are held back and
  # only counted once a further non-blank line proves they were interior.
  if is_blank "$line"; then
    body_blanks_held=$((body_blanks_held + 1))
    continue
  fi
  body_lines=$((body_lines + body_blanks_held + 1))
  body_blanks_held=0

  # Both spellings: the trailer key the harness attribution emits, and a bare
  # session URL that reached the prose some other way. The key is anchored to
  # the head of its line, so a body writing *about* this rule isn't a hit.
  case ${line#"${line%%[![:space:]]*}"} in
    Claude-Session:* | *claude.ai/code/session*)
      body_session_count=$((body_session_count + 1))
      body_session="${body_session}${NL}    line ${body_lines}: ${line}"
      ;;
  esac

  # Exempt lines stay out of the widest-line figure, so a passing run never
  # reports a width above the cap.
  if is_wrappable "$line"; then
    len=$(char_len "$line")
    [ "$len" -le "$body_widest" ] || body_widest=$len
    if [ "$len" -gt "$BODY_MAX_WIDTH" ]; then
      body_over_count=$((body_over_count + 1))
      body_over="${body_over}${NL}    line ${body_lines} (${len} chars): ${line}"
    fi
  fi
done <"$SRC_FILE"

failures=""
fail() {
  failures="${failures}${NL}  $1"
}

if [ "$blocks" -lt 1 ] || [ "$blocks" -gt 2 ] || [ $((fences % 2)) -ne 0 ]; then
  fail "found $blocks fenced block(s); a proposal is the body, or a title block then the body"
else
  if [ "$blocks" -eq 2 ]; then
    if [ "$title_lines" -eq 0 ]; then
      fail "title block is empty"
    elif [ "$title_lines" -gt 1 ]; then
      fail "title is $title_lines lines; a squash title is one line, and a wrapped one pastes broken"
    fi
    if [ -n "$title_over" ]; then
      fail "title over $TITLE_MAX_CHARS chars:$title_over"
    fi
  fi
  if [ "$body_lines" -eq 0 ]; then
    fail "body block is empty"
  elif [ "$body_lines" -gt "$BODY_MAX_LINES" ]; then
    fail "body is $body_lines lines, cap $BODY_MAX_LINES"
  fi
  if [ -n "$body_over" ]; then
    fail "$body_over_count body line(s) over $BODY_MAX_WIDTH chars:$body_over"
  fi
  if [ -n "$body_session" ]; then
    fail "$body_session_count body line(s) carry a session link; a squash record takes none:$body_session"
  fi
fi

if [ -n "$failures" ]; then
  printf '%s: FAIL — %s%s\n' "$PROG" "$SRC_DESC" "$failures" >&2
  printf '%s: fix it — /squash-message steps 2–3, then re-run.\n' "$PROG" >&2
  exit 1
fi

title_report=""
[ "$blocks" -ne 2 ] || title_report="title $title_widest/$TITLE_MAX_CHARS chars, "
printf '%s: ok — %s (%sbody %s/%s lines, widest %s/%s)\n' \
  "$PROG" "$SRC_DESC" "$title_report" \
  "$body_lines" "$BODY_MAX_LINES" \
  "$body_widest" "$BODY_MAX_WIDTH"
