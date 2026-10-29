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

warn="${MUTHUR_CONTEXT_BUDGET_WARN:-300000}"
pause="${MUTHUR_CONTEXT_BUDGET_PAUSE:-400000}"
warn_saving="${MUTHUR_CONTEXT_BUDGET_WARN_SAVING_USD:-0.20}"
pause_saving="${MUTHUR_CONTEXT_BUDGET_PAUSE_SAVING_USD:-0.80}"
lines="${MUTHUR_CONTEXT_BUDGET_LINES:-priced}"
dollars='^[0-9]+(\.[0-9]+)?$'
[[ "$warn" =~ ^[0-9]+$ && "$pause" =~ ^[0-9]+$ && "$warn_saving" =~ $dollars && "$pause_saving" =~ $dollars ]] \
  && awk -v warn="$warn_saving" -v pause="$pause_saving" 'BEGIN { exit !(warn < pause) }' || {
  say "MUTHUR_CONTEXT_BUDGET_WARN / MUTHUR_CONTEXT_BUDGET_PAUSE must be whole counts, MUTHUR_CONTEXT_BUDGET_WARN_SAVING_USD and MUTHUR_CONTEXT_BUDGET_PAUSE_SAVING_USD dollar amounts with the warning's under the pause's; no reading taken."
  exit 0
}
# The pause's percentage knob is named while an environment still sets it,
# rather than ignored.
[ -z "${MUTHUR_CONTEXT_BUDGET_PAUSE_SAVING:-}" ] ||
  say "MUTHUR_CONTEXT_BUDGET_PAUSE_SAVING is no longer read; use MUTHUR_CONTEXT_BUDGET_PAUSE_SAVING_USD, in dollars."
[[ "$lines" == priced || "$lines" == fixed ]] || {
  say "MUTHUR_CONTEXT_BUDGET_LINES must be \`priced\` or \`fixed\`; no reading taken."
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

# Priced where the ledger's lib can price it, each line capped at its fixed one;
# a hand-set line stays fixed. Cached as `<warn> <pause> <reading>`.
hooks="$(dirname "${BASH_SOURCE[0]}")"
priced=
cap='its fixed cap, there for context quality and the hard window rather than for cost'
warn_why="$cap" pause_why="$cap"
[ -z "${MUTHUR_CONTEXT_BUDGET_WARN:-}" ] || warn_why='set by MUTHUR_CONTEXT_BUDGET_WARN'
[ -z "${MUTHUR_CONTEXT_BUDGET_PAUSE:-}" ] || pause_why='set by MUTHUR_CONTEXT_BUDGET_PAUSE'
if [ "$lines" = priced ] && [ -z "${MUTHUR_CONTEXT_BUDGET_WARN:-}" -o -z "${MUTHUR_CONTEXT_BUDGET_PAUSE:-}" ] \
  && [ -f "$hooks/../../costs/lib/restart.py" ] && command -v python3 >/dev/null; then
  line_file="$state_dir/$session.line"
  priced_warn= priced_pause= at=
  [ ! -f "$line_file" ] || read -r priced_warn priced_pause at <"$line_file"
  if ! [[ "$at" =~ ^[0-9]+$ && "$reading" -ge "$at" && "$reading" -lt $((at + 10000)) ]]; then
    read -r priced_warn priced_pause < <(python3 "$hooks/priced_line.py" lines "$transcript" "$warn_saving" "$pause_saving")
    mkdir -p "$state_dir" && printf '%s %s %s\n' "${priced_warn:--}" "${priced_pause:--}" "$reading" >"$line_file"
  fi
  if [ -z "${MUTHUR_CONTEXT_BUDGET_WARN:-}" ] && [[ "$priced_warn" =~ ^[0-9]+$ ]]; then
    priced=1
    [ "$priced_warn" -ge "$warn" ] || {
      warn="$priced_warn"
      warn_why="where relaying saves \$${warn_saving}"
    }
  fi
  if [ -z "${MUTHUR_CONTEXT_BUDGET_PAUSE:-}" ] && [[ "$priced_pause" =~ ^[0-9]+$ ]]; then
    priced=1
    [ "$priced_pause" -ge "$pause" ] || {
      pause="$priced_pause"
      pause_why="where relaying saves \$${pause_saving}"
    }
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

# A manual-relay switch reads as `yes`, `no`, or empty for unset; a value that is
# neither a yes nor a no is named on stderr, so a typo does not pass silently for
# the default.
switch() {
  case "$(printf '%s' "$2" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')" in
    true | yes | on | 1) echo yes ;;
    false | no | off | 0) echo no ;;
    '') ;;
    *) say "$1 is neither a yes nor a no; read as unset." ;;
  esac
}
# `unasked` holds the operator's switch path while they have no answer on record.
manual_relay= unasked=
if [ "$(switch MUTHUR_MANUAL_CONTEXT_BUDGET_RELAY "${MUTHUR_MANUAL_CONTEXT_BUDGET_RELAY:-}")" = yes ]; then
  manual_relay=1
else
  # The operator is keyed as `.claude/hooks/operator-voice.sh` keys voice entries:
  # the lowercased login of a `User` token. Resolved only here, with a notice
  # about to go out, since that is an API call.
  handle="$(gh api user 2>/dev/null | jq -r 'select(.type == "User") | .login | ascii_downcase' 2>/dev/null)"
  if [[ "$handle" =~ ^[a-z0-9-]+$ ]]; then
    operator_switch=".claude/context-budget/manual-relay/$handle"
    case "$(switch "manual-relay/$handle" "$(cat "$root/$operator_switch" 2>/dev/null)")" in
      yes) manual_relay=1 ;;
      no) ;;
      *) unasked="$operator_switch" ;;
    esac
  fi
fi

k() { echo "$(($1 / 1000))k"; }
past() { echo "Context budget: this session is carrying ~$(k "$reading") tokens of context, past the $(k "$1") $2 line — $3."; }
stopping='`@.claude/skills/go/SKILL.md` § "Stopping partway releases the plan" — which also covers work that has no plan yet'
relay='`/relay` (`@.claude/skills/relay/SKILL.md`), which hands the branch to a fresh session starting from a summary of this one — the summary `/compact` would make, written to a file instead'
# The warning's room: what the work may still spend, either finishing or
# reaching a good place to pause. The pause line is where that estimate missed,
# so it leaves room only for a last step.
room=$((pause - warn))
last_step=20000

# However a pause is reached, it ends in the relay, asked first under manual relay.
ends="then, without asking and with no argument, run ${relay}. Its report tells the operator the session was paused for its context budget and relayed on its own"
# The offer is made until the operator answers it, and the answer is a file
# whichever way it goes, so it is made once.
[ -z "$unasked" ] || ends="${ends}, and ends by offering, in the operator's language and in words like these, \"if you'd rather I ask before relaying, say so\" — naming no file, setting or section, since their part is the answer alone. Whichever session hears that answer writes it, a no included, to \`${unasked}\` as \`.claude/context-budget/CLAUDE.md\` § \"Manual relay\" says"
[ -z "$manual_relay" ] || ends="tell the operator the session was paused for its context budget, and end the turn offering ${relay}"
paused="follow ${stopping}. Push, ${ends}; the new session resumes the paused plan."

saving=
[ -z "$priced" ] || saving="$(python3 "$hooks/priced_line.py" notice "$transcript" "$reading")"
priced_past() { echo "$(past "$@")${saving:+ $saving Give the operator those figures, and why the line sits where it does, when you offer the choice.}"; }

case "$level" in
  warn)
    notice="$(priced_past "$warn" warning "$warn_why")

Judge whether the work fits — the open bite, when the plan has a \`## This bite\` section: by your own estimate, under ~$(k "$room") more tokens of context to finish, roughly less than half of what this session has already carried. If it fits, carry on and finish it, and say in your report that the warning came and why you did not pause.

If it does not fit, steer to a pause within that same ~$(k "$room"): pick the best stopping point you can reach — the step in hand finished, nothing half-edited, what is left easy to state — and start nothing you cannot finish before it. There, pause without asking: ${paused}

At $(k "$pause") this notice returns as the pause itself, which stops wherever the work stands."
    ;;
  pause)
    notice="$(priced_past "$pause" pause "$pause_why")

Pause now, without asking, wherever the work stands: there is no room left to steer to a better stopping point. The one exception is work literally a step from done — under ~$(k "$last_step") more tokens of context — which you finish first, saying in your report why. Otherwise commit what is in hand, leave the branch just resumable rather than tidy, and ${paused}"
    ;;
esac

emit_context "$notice"
