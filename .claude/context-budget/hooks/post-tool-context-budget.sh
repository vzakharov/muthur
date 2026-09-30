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
[[ "$warn" =~ ^[0-9]+$ && "$pause" =~ ^[0-9]+$ ]] || {
  say "CONTEXT_BUDGET_WARN / CONTEXT_BUDGET_PAUSE must be whole token counts; no reading taken."
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

# The operator's auto-relay setting, keyed as `.claude/hooks/operator-voice.sh`
# keys voice entries: the lowercased login of a `User` token. Read only here,
# with a notice about to go out, since resolving the operator is an API call.
auto_relay=unresolved
handle="$(gh api user 2>/dev/null | jq -r 'select(.type == "User") | .login | ascii_downcase' 2>/dev/null)"
if [[ "$handle" =~ ^[a-z0-9-]+$ ]]; then
  setting=".claude/context-budget/auto-relay/$handle"
  case "$(tr -d '[:space:]' 2>/dev/null <"$root/$setting")" in
    on) auto_relay=on ;;
    off) auto_relay=off ;;
    *) auto_relay=unset ;;
  esac
fi

k() { echo "$(($1 / 1000))k"; }
past() { echo "Context budget: this session is carrying ~$(k "$reading") tokens of context, past the $(k "$1") $2 line."; }
stopping='`@.claude/skills/go/SKILL.md` § "Stopping partway releases the plan" — which also covers work that has no plan yet'
relay='`/relay` (`@.claude/skills/relay/SKILL.md`), which hands the branch to a fresh session starting from a summary of this one — the summary `/compact` would make, written to a file instead'
# The warning's room: what the work may still spend, either finishing or
# reaching a good place to pause. The pause line is where that estimate missed,
# so it leaves room only for a last step.
room=$((pause - warn))
last_step=20000

# However a pause is reached, the operator's setting decides how it ends.
auto='`@.claude/skills/relay/SKILL.md` § "Auto-relay"'
ends="tell the operator the session was paused for its context budget, and end the turn offering ${relay}"
[ "$auto_relay" != on ] || ends="then, without asking and with no argument, run ${relay}. Do so because this operator turned auto-relay on (\`${setting}\`, ${auto}); its report tells the operator the session was paused for its context budget and relayed on its own"
paused="follow ${stopping}. Push, ${ends}; the new session resumes the paused plan."

case "$level" in
  warn)
    notice="$(past "$warn" warning)

Judge whether the work fits — the open bite, when the plan has a \`## This bite\` section: by your own estimate, under ~$(k "$room") more tokens of context to finish, roughly less than half of what this session has already carried. If it fits, carry on and finish it, and say in your report that the warning came and why you did not pause.

If it does not fit, steer to a pause within that same ~$(k "$room"): pick the best stopping point you can reach — the step in hand finished, nothing half-edited, what is left easy to state — and start nothing you cannot finish before it. There, pause without asking: ${paused}

At $(k "$pause") this notice returns as the pause itself, which stops wherever the work stands."
    ;;
  pause)
    notice="$(past "$pause" pause)

Pause now, without asking, wherever the work stands: there is no room left to steer to a better stopping point. The one exception is work literally a step from done — under ~$(k "$last_step") more tokens of context — which you finish first, saying in your report why. Otherwise commit what is in hand, leave the branch just resumable rather than tidy, and ${paused}"
    ;;
esac

# An operator who has never answered is asked alongside the offer, once a
# session; their answer is what writes the setting.
[ "$auto_relay" != unset ] || notice="$notice

This operator (@${handle}) has not said whether to relay on their own. Unless you already asked in this session, add to the offer: from now on, whenever the context budget pauses a session, you can run \`/relay\` without asking. Record their answer, yes or no, per ${auto}."

emit_context "$notice"
