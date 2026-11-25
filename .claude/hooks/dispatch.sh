#!/bin/bash
# Usage: dispatch.sh <repo-relative hook> [args…]
#
# Fronts every hook `.claude/settings.json` registers, so a hook runs from the
# checkout the session works in. Claude Code hands hooks `CLAUDE_PROJECT_DIR` =
# the checkout the session was opened on; a session working in a git worktree of
# it has its shell — and every script the agent runs — in the worktree instead.
# Run from `CLAUDE_PROJECT_DIR`, a hook would execute the other branch's code and
# keep its per-session state under the other checkout's `tmp/`, where the
# agent's own scripts never look.
#
# So: the directory the session started in names the checkout — the first `cwd`
# its transcript records, or the payload's own where there is no transcript yet,
# on a session's first event. Not the payload's `cwd` past that: it follows a
# `cd`, and on a delegate's tool call (an Agent with `isolation: "worktree"`)
# names the delegate's worktree, whose `tmp/` the session never reads and which
# is deleted with the delegate. When that start lies in another worktree of the
# same repository (same git common dir) and it carries the hook as an
# executable, the hook runs from there with `CLAUDE_PROJECT_DIR` pointed at it.
# Anything else — no `jq`, a start outside git (a multi-repo parent), a start in
# another repository, a branch predating the hook — runs the hook from the
# anchor exactly as an undispatched registration would.
#
# The hook is `exec`ed with the payload on stdin, so its exit code and stdout
# are the dispatcher's.

hook="${1:?usage: dispatch.sh <repo-relative hook> [args…]}"
shift

anchor="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
# Stdin is a pipe, so it is read once and replayed to the hook.
payload="$(cat)"

common_dir() { git -C "$1" rev-parse --path-format=absolute --git-common-dir 2>/dev/null; }

# Records read for the session's start before giving up on it: the first `cwd`
# rides on the opening records, so a transcript with none there has none to give.
OPENING=50

started_in() {
  local transcript
  transcript="$(jq -r '.transcript_path // empty' <<<"$payload" 2>/dev/null)"
  if [ -n "$transcript" ] && [ -f "$transcript" ]; then
    head -n "$OPENING" "$transcript" | jq -Rr 'fromjson? | .cwd? // empty | strings' 2>/dev/null | head -n 1
  else
    jq -r '.cwd // empty' <<<"$payload" 2>/dev/null
  fi
}

target="$anchor"
start=""
command -v jq >/dev/null && start="$(started_in)"
if [ -n "$start" ] && [ -d "$start" ]; then
  top="$(git -C "$start" rev-parse --show-toplevel 2>/dev/null)"
  anchor_top="$(git -C "$anchor" rev-parse --show-toplevel 2>/dev/null)"
  if [ -n "$top" ] && [ -n "$anchor_top" ] && [ "$top" != "$anchor_top" ] &&
    [ "$(common_dir "$top")" = "$(common_dir "$anchor_top")" ] &&
    [ -x "$top/$hook" ]; then
    target="$top"
  fi
fi

export CLAUDE_PROJECT_DIR="$target"
exec "$target/$hook" "$@" <<<"$payload"
