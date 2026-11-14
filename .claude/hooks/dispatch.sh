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
# So: the payload's `cwd` names the checkout. When that is another worktree of
# the same repository (same git common dir) and it carries the hook as an
# executable, the hook runs from there with `CLAUDE_PROJECT_DIR` pointed at it.
# Anything else — no `jq`, a cwd outside git (a multi-repo parent), a cwd in
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

target="$anchor"
cwd=""
command -v jq >/dev/null && cwd="$(jq -r '.cwd // empty' <<<"$payload" 2>/dev/null)"
if [ -n "$cwd" ] && [ -d "$cwd" ]; then
  top="$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)"
  anchor_top="$(git -C "$anchor" rev-parse --show-toplevel 2>/dev/null)"
  if [ -n "$top" ] && [ -n "$anchor_top" ] && [ "$top" != "$anchor_top" ] &&
    [ "$(common_dir "$top")" = "$(common_dir "$anchor_top")" ] &&
    [ -x "$top/$hook" ]; then
    target="$top"
  fi
fi

export CLAUDE_PROJECT_DIR="$target"
exec "$target/$hook" "$@" <<<"$payload"
