#!/bin/bash
# Sourced by the `UserPromptSubmit` hooks beside it: the payload read, the one
# JSON shape the event accepts, and the guards each of them needs before it can
# do anything.
#
# Every hook sources it as `. "$(dirname "${BASH_SOURCE[0]}")/lib.sh" || exit 0`,
# so a tree holding a hook without this file skips that hook instead of failing
# the turn — the same contract each hook keeps for its own failures. Which is
# also why taking any one hook means taking this file:
# `.claude/skills/update-muthur/catalog.md` has the row saying so.
#
# `need_command` exits the *hook*, not just itself: a sourced function's `exit`
# ends the script that sourced it, which is the intent — a hook with no `jq` has
# nothing to contribute to the turn.

# The event payload, read once — stdin is a pipe, so a second read gets nothing.
# `field` reads what this leaves behind.
read_payload() { payload="$(cat)"; }

field() { jq -r --arg k "$1" '.[$k] // empty' <<<"$payload"; }

# Diagnostics go to stderr under the hook's own name, where the harness surfaces
# them without touching the turn.
say() { echo "$(basename "$0" .sh): $*" >&2; }

need_command() { command -v "$1" >/dev/null || { say "$1 not found; $2"; exit 0; }; }

# True on the prompt a session opens with — the one whose transcript holds
# nothing the agent wrote. `UserPromptSubmit` fires before the prompt is
# recorded, so an assistant record in there means an earlier turn already ran;
# tool results are `user` records too, which is why the agent's own record is the
# mark to grep for. A missing or unreadable transcript reads as a first prompt —
# a firing too many costs a turn's context, a launch slept through costs the
# thing the hook was for.
first_prompt() {
  local transcript
  transcript="$(field transcript_path)"
  [ -n "$transcript" ] || return 0
  ! grep -q '"type":"assistant"' "$transcript" 2>/dev/null
}

# Empty output is the whole signal — a hook that cannot find the tree has no work
# in it — and the status stays 0 so that assigning from this under `set -e` is
# not itself the failure.
project_root() {
  local root="${CLAUDE_PROJECT_DIR:-$(field cwd)}"
  [ -n "$root" ] && [ -d "$root" ] && printf '%s\n' "$root"
  return 0
}

emit_context() {
  jq -n --arg ctx "$1" '{
    hookSpecificOutput: {
      hookEventName: "UserPromptSubmit",
      additionalContext: $ctx
    }
  }'
}
