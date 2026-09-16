#!/bin/bash
# UserPromptSubmit hook: a session's *first* prompt is the one that gets routed,
# and routing is the step a session skips — it reads the prompt, sees work it
# knows how to do, and starts. What the skipped route costs is the plan-or-not
# call, the quality passes and the PR, so the ladder arrives at the moment the
# call is made rather than waiting in CLAUDE.md to be remembered.
#
# It points at the ladder rather than restating it: CLAUDE.md is resident, so
# the rows are in context already and a copy here would only drift from them.
#
# Only the first prompt. Everything after it is continued work, which CLAUDE.md
# § "Plan mode & questions in web sessions" has the session handle directly —
# re-routing mid-session would open a plan cycle over a follow-up. A prompt that
# opens with `/` is already routed: the operator named the skill themselves.
#
# Never fails the turn: no `jq`, no transcript, no payload — each path is
# stderr plus exit 0, the contract every hook beside it keeps.

set -uo pipefail

. "$(dirname "${BASH_SOURCE[0]}")/lib.sh" || exit 0

need_command jq "skipping the routing notice."
read_payload

prompt="$(field prompt)"
[ -n "$prompt" ] || exit 0
[[ "$prompt" =~ ^[[:space:]]*/ ]] && exit 0

first_prompt || exit 0

read -r -d '' notice <<'NOTICE' || true
This is the session's opening prompt, so the route comes before the work: read
CLAUDE.md § "Plan mode & questions in web sessions"'s entry ladder, say which
row this prompt is, and enter the skill that row names. That route is what
carries a change through the plan-or-not call and the quality passes onto a PR.
NOTICE

emit_context "$notice"
