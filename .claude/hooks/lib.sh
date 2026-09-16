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

# The project root, preferring the harness's own variable over the payload's
# `cwd`. Empty output is the whole signal, and callers read it as nothing to do:
# a hook that cannot find the tree has no work in it. The status stays 0 so that
# `root="$(project_root)"` under `set -e` is not itself the failure.
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
