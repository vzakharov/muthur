#!/bin/bash
# UserPromptSubmit hook: tell a session in native plan mode that this repo plans
# on disk, and that the exit is plan mode's own.
#
# This has to be a hook rather than prose. Plan mode's injected instructions end
# with "this supercedes any other instructions you have received", so anything
# already in CLAUDE.md or the skill loses to them; additionalContext lands after
# that message and re-fires every prompt, so it cannot be argued away or
# forgotten mid-session. (The first firing is the operator's task message —
# `/plan` is client-side and submits no prompt of its own.)
#
# Remote-only, matching .claude/hooks/gh-shim.sh: CLAUDE.md § "Plan mode &
# questions in web sessions" leaves native plan mode alone on the local CLI,
# where the answer-losing bug this routes around does not bite.

set -euo pipefail

[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0

. "$(dirname "${BASH_SOURCE[0]}")/lib.sh" || exit 0

need_command jq "skipping the plan-mode notice."
read_payload

[ "$(field permission_mode)" = "plan" ] || exit 0

read -r -d '' notice <<'NOTICE' || true
This repo plans on disk: the deliverable is a git-tracked
`docs/plans/<slug>.draft.do-not-implement.md` on a draft PR, and plan mode holds
the session to read-only work, so writing it means leaving first.

Take plan mode's own exit now — plan mode's own, not an override of it — by
following `@.claude/skills/plan/native-plan-mode.md`. It owns the steps, the
dialog copy that goes in front of the operator, and what a rejected approval
means. Questions go as numbered prose, never `AskUserQuestion`.

Two things that page cannot assume you read. The restriction gates
`Edit`/`Write` and not Bash, so the plan file is writable from in here — writing
it anyway takes the operator's approval instead of asking for it. And this
notice re-fires on every prompt while the mode is on, so if the operator
rejected the exit or said to stay, it is already answered: don't re-raise it.
NOTICE

emit_context "$notice"
