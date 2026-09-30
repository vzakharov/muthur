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
pause_saving="${CONTEXT_BUDGET_PAUSE_SAVING:-20}"
lines="${CONTEXT_BUDGET_LINES:-priced}"
[[ "$warn" =~ ^[0-9]+$ && "$pause" =~ ^[0-9]+$ && "$pause_saving" =~ ^[0-9]+$ && "$pause_saving" -lt 100 ]] || {
  say "CONTEXT_BUDGET_WARN / CONTEXT_BUDGET_PAUSE must be whole counts, CONTEXT_BUDGET_PAUSE_SAVING a percentage under 100; no reading taken."
  exit 0
}
[[ "$lines" == priced || "$lines" == fixed ]] || {
  say "CONTEXT_BUDGET_LINES must be \`priced\` or \`fixed\`; no reading taken."
  exit 0
}
# What "nearly done" means, and the slice of work a relay's saving is priced over.
finish=100000

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

# Priced where the ledger's lib can price it, each line capped at its fixed one;
# a hand-set line stays fixed. Cached as `<warn> <pause> <reading>`, recomputed
# per 10k of growth, since a Python start-up per tool call is what this bash hook
# avoids.
hooks="$(dirname "${BASH_SOURCE[0]}")"
priced=
if [ "$lines" = priced ] && [ -z "${CONTEXT_BUDGET_WARN:-}" -o -z "${CONTEXT_BUDGET_PAUSE:-}" ] \
  && [ -f "$hooks/../../costs/lib/restart.py" ] && command -v python3 >/dev/null; then
  line_file="$state_dir/$session.line"
  priced_warn= priced_pause= at=
  [ ! -f "$line_file" ] || read -r priced_warn priced_pause at <"$line_file"
  if ! [[ "$at" =~ ^[0-9]+$ && "$reading" -ge "$at" && "$reading" -lt $((at + 10000)) ]]; then
    read -r priced_warn priced_pause < <(python3 "$hooks/priced_line.py" lines "$transcript" "$finish" "$pause_saving")
    mkdir -p "$state_dir" && printf '%s %s %s\n' "${priced_warn:--}" "${priced_pause:--}" "$reading" >"$line_file"
  fi
  if [ -z "${CONTEXT_BUDGET_WARN:-}" ] && [[ "$priced_warn" =~ ^[0-9]+$ ]]; then
    priced=1
    [ "$priced_warn" -ge "$warn" ] || warn="$priced_warn"
  fi
  if [ -z "${CONTEXT_BUDGET_PAUSE:-}" ] && [[ "$priced_pause" =~ ^[0-9]+$ ]]; then
    priced=1
    [ "$priced_pause" -ge "$pause" ] || pause="$priced_pause"
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
relay='`/relay` (`@.claude/skills/relay/SKILL.md`), which hands the branch to a fresh session starting from a summary of this one — the summary `/compact` would make, written to a file instead'
nearly_done() { echo "First judge whether the work is nearly done — the open bite, when the plan has a \`## This bite\` section: by your own estimate, under ~$(k "$finish") more tokens of context to finish$1. If it is, finish it, and say in your report that you did and why rather than stopping."; }

saving=
[ -z "$priced" ] || saving="$(python3 "$hooks/priced_line.py" notice "$transcript" "$reading" "$finish")"
priced_past() { echo "$(past "$@")${saving:+ $saving Give the operator those figures when you offer the choice.}"; }

case "$level" in
  warn)
    notice="$(priced_past "$warn" warning)

$(nearly_done " — roughly, less than half of what this session has already carried")

Otherwise get the work to a committed, pushed stopping point and tell the operator, offering ${relay}. Do not relay unasked at this level: at $(k "$pause") this notice returns as the pause itself."
    ;;
  pause)
    notice="$(priced_past "$pause" pause)

$(nearly_done "")

Otherwise pause now, without asking: follow ${stopping}. Push, tell the operator the session was paused for its context budget, and end the turn offering ${relay}; the new session resumes the paused plan."
    ;;
esac

emit_context "$notice"
