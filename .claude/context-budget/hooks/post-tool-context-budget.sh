#!/bin/bash
# `PostToolUse` hook: tell the agent when the context its session carries
# crosses the warn line and again at the pause line, once per climb.
# `.claude/context-budget/CLAUDE.md` carries what the reading is and why it is
# taken here; the procedure the notices point at is `/go`'s.

. "$(dirname "${BASH_SOURCE[0]}")/../../hooks/lib.sh" || exit 0
read_payload
need_command jq "no context-budget reading this tool call."

# A subagent's tool call. The notice is for the session holding the plan, and a
# subagent pausing that plan would release it while its parent works on.
[ -z "$(field agent_id)" ] || exit 0

warn="${CONTEXT_BUDGET_WARN:-200000}"
pause="${CONTEXT_BUDGET_PAUSE:-300000}"
requests="${CONTEXT_BUDGET_REQUESTS:-100}"
[[ "$warn" =~ ^[0-9]+$ && "$pause" =~ ^[0-9]+$ && "$requests" =~ ^[1-9][0-9]*$ ]] || {
  say "CONTEXT_BUDGET_WARN / CONTEXT_BUDGET_PAUSE / CONTEXT_BUDGET_REQUESTS must be whole counts; no reading taken."
  exit 0
}

root="$(project_root)"
transcript="$(field transcript_path)"
session="$(field session_id)"
[ -n "$root" ] && [ -f "$transcript" ] || exit 0
case "$session" in '' | */* | .*) exit 0 ;; esac

# Read from the end: the transcript runs to megabytes and this runs on every tool
# call. `first` stops jq at the first match, which is also why there is no
# `pipefail` here — `tac` dying of the closed pipe is the intended exit.
reading="$(tac "$transcript" | grep -F '"type":"assistant"' | jq -rn '
  first(
    inputs
    | select(.type == "assistant" and (.isSidechain | not))
    | select(.message.model != "<synthetic>")
    | .message.usage // empty
    | (.input_tokens // 0) + (.cache_read_input_tokens // 0) + (.cache_creation_input_tokens // 0)
  )' 2>/dev/null)"
[[ "$reading" =~ ^[0-9]+$ ]] || exit 0

state_dir="$root/tmp/context-budget"
state_file="$state_dir/$session"

# Priced where the ledger's lib can price it and no fixed line was set. Cached as
# `<line> <kind> <reading>`; recomputed while the warm-up is an estimate, per 10k.
hooks="$(dirname "${BASH_SOURCE[0]}")"
priced=
if [ -z "${CONTEXT_BUDGET_WARN:-}" ] && [ -f "$hooks/../../costs/lib/restart.py" ] && command -v python3 >/dev/null; then
  line_file="$state_dir/$session.line"
  line= kind= at=
  [ ! -f "$line_file" ] || read -r line kind at <"$line_file"
  if [ "$kind" != observed ] && ! [[ "$at" =~ ^[0-9]+$ && "$reading" -ge "$at" && "$reading" -lt $((at + 10000)) ]]; then
    read -r line kind < <(CONTEXT_BUDGET_REQUESTS="$requests" python3 "$hooks/priced_line.py" line "$transcript")
    mkdir -p "$state_dir" && printf '%s %s %s\n' "${line:--}" "${kind:-unpriced}" "$reading" >"$line_file"
  fi
  if [[ "$line" =~ ^[0-9]+$ ]]; then
    warn="$line"
    priced=1
  fi
fi

# Under the warn line again means a compact landed, which re-arms both notices.
if [ "$reading" -lt "$warn" ]; then
  rm -f "$state_file"
  exit 0
fi

level=warn
[ "$reading" -lt "$pause" ] || level=pause
announced="$(cat "$state_file" 2>/dev/null)"
case "$announced:$level" in pause:* | warn:warn) exit 0 ;; esac

# No record of the notice means it would fire again on every tool call after
# this one, so a notice that cannot be recorded is not sent.
mkdir -p "$state_dir" && printf '%s\n' "$level" >"$state_file" || {
  say "cannot write $state_file; context-budget notice withheld."
  exit 0
}

k() { echo "$(($1 / 1000))k"; }
past() { echo "Context budget: this session is carrying ~$(k "$reading") tokens of context, past the $(k "$1") $2 line."; }
stopping='`@.claude/skills/go/SKILL.md` § "Stopping partway releases the plan" — which also covers work that has no plan yet'
nearly_done="First judge whether the work is nearly done — a small step or a commit or two from finished. If it is, finish it, and say in your report that you did and why rather than stopping."

case "$level" in
  warn)
    breakeven=
    [ -z "$priced" ] || breakeven="$(python3 "$hooks/priced_line.py" notice "$transcript" "$reading")"
    notice="$(past "$warn" warning)${breakeven:+ $breakeven Compare that with the requests the work has left, and give both numbers when you offer the choice.}

${nearly_done}

Otherwise get the work to a committed, pushed stopping point and tell the operator, offering two ways on: \`/compact\` in this session, or a new one. A new session resumes only from a paused plan, so offer to pause it per ${stopping}. Do not pause unasked at this level: at $(k "$pause") this notice returns as the pause itself."
    ;;
  pause)
    notice="$(past "$pause" pause)

${nearly_done}

Otherwise pause now, without asking: follow ${stopping}. Push, tell the operator the session was paused for its context budget, and end the turn with the \`/go <branch>\` handoff block."
    ;;
esac

emit_context "$notice"
