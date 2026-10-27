#!/bin/bash
# `SessionStart` hook: start the receiver Claude Code's telemetry is exported
# to, unless one is already listening. On `resume` too, since a container that
# slept has lost it. Where the exporter variables do not point at it, start
# nothing and print what to set instead — the environment's to set, never the
# repo's.
#
# Also a `PostToolUse` keep-alive: a session that checks out a branch carrying
# this hook gets it registered with its `SessionStart` already past, and a
# receiver can die mid-session. A listening port makes that firing a probe,
# plus `confirm` while the receiver is unconfirmed.
#
# The events land under the repo's `tmp/telemetry/`; `.claude/costs/CLAUDE.md`
# § "Telemetry" says why the repo cannot set the variables, and what reads the
# events.

. "$(dirname "${BASH_SOURCE[0]}")/../../hooks/lib.sh" || exit 0
read_payload

# Overridable so the tests can run beside the session's own receiver.
port="${MUTHUR_TELEMETRY_RECEIVER_PORT:-4318}"
listening() { (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null; }

root="$(project_root)"
[ -n "$root" ] || exit 0
out="$root/tmp/telemetry"
session="$(field session_id)"
[[ "$session" =~ ^[A-Za-z0-9_-]+$ ]] || session=""
events="$out/$session.jsonl"
pending="$out/$session.unconfirmed"

expected=(
  "CLAUDE_CODE_ENABLE_TELEMETRY=1"
  "OTEL_LOGS_EXPORTER=otlp"
  "OTEL_EXPORTER_OTLP_PROTOCOL=http/json"
  "OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:$port"
  "OTEL_METRICS_EXPORTER=none"
  "OTEL_LOGS_EXPORT_INTERVAL=1000"
)

# What every "capture is off" notice says after its first paragraph, `$1`.
notice() {
  cat <<MSG
$1
This session's row is priced from its transcript alone, which misses the calls the
transcript never records.

Agent: do not raise this. Mention it only where the conversation is about the
cost ledger or what sessions cost; the operator may not want the capture at all.
There, give them the list below. Claude Code ignores these variables in a
repository's .claude/settings.json, so no file in this repo can set them. In a
web session they go in the environment's settings (the cloud environment menu
in the session's title bar, then Edit) as environment variables; locally, in
~/.claude/settings.json's "env" or the shell. A new session picks them up:

$(printf '    %s\n' "${expected[@]}")
MSG
}

# A receiver started on `CLAUDE_CODE_ENABLE_TELEMETRY` alone (below) leaves
# `<session>.unconfirmed` holding when it started; the session's first event
# clears it. Until then, a main-thread response that finished since, long enough
# ago for its event to be out (the exporter sends within a second), means Claude
# Code exports elsewhere or not at all, and the notice goes out once. A response
# has finished only once a later one exists: the current one may still be
# streaming, and its tool calls run before it ends.
confirm() {
  local transcript
  [ -n "$session" ] && [ -f "$pending" ] || return 0
  if [ -s "$events" ]; then
    rm -f "$pending"
    return 0
  fi
  transcript="$(field transcript_path)"
  [ -r "$transcript" ] || return 0
  grep '"type":"assistant"' "$transcript" | jq -rs --arg since "$(cat "$pending")" '
    map(select(.type == "assistant" and .message.id and .message.model != "<synthetic>"))
    | (last.message.id) as $current
    | map(select(.message.id != $current)) | group_by(.message.id)
    | map(max_by(.timestamp).timestamp)
    | any(. >= $since and . <= (now - 10 | todate))' | grep -qx true || return 0
  rm -f "$pending"
  emit_context "$(notice "telemetry: the cost ledger's telemetry capture looks off. The receiver on
127.0.0.1:$port was started on CLAUDE_CODE_ENABLE_TELEMETRY=1 alone, the OTEL_*
variables being hidden from hooks, and no event from this session has reached it.")"
}

starting=false
[ "$(field hook_event_name)" = SessionStart ] && starting=true
if ! $starting && listening; then
  confirm
  exit 0
fi

need_command python3 "no telemetry is being captured"

# Claude Code strips `OTEL_*` from everything it spawns, this hook included, so
# what its exporter was given is read from its own process — the nearest
# ancestor named `claude` — where `/proc` shows it.
claude_environ() {
  local pid=$PPID
  while [ "$pid" -gt 1 ] && [ -r "/proc/$pid/stat" ]; do
    if [ "$(cat "/proc/$pid/comm")" = claude ]; then
      tr '\0' '\n' <"/proc/$pid/environ"
      return
    fi
    pid="$(awk '{print $4}' "/proc/$pid/stat")"
  done
  return 1
}

# `OTEL_METRICS_EXPORTER` and the interval only trim the export, so a value of
# the operator's own there is theirs to keep; the rest decide whether events
# reach this port at all. Where that process is out of sight, only
# `CLAUDE_CODE_ENABLE_TELEMETRY` survives into this one to be checked, and the
# receiver starts on it alone, for `confirm` to check against the events.
#
# A `claude` exec'd from a preloaded spare (`claude --preload`) is handed the
# environment's variables after its exec, so its `/proc` environ lacks them
# while what it spawns carries them: one naming no `CLAUDE_CODE_ENABLE_TELEMETRY`
# where this process has it set is that stale copy, and as good as out of sight.
stale() {
  [ "${CLAUDE_CODE_ENABLE_TELEMETRY-}" = 1 ] && ! grep -q '^CLAUDE_CODE_ENABLE_TELEMETRY=' <<<"$exporter_env"
}
checked=("${expected[@]:0:4}")
trusting=false
if exporter_env="$(claude_environ 2>/dev/null)" && ! stale; then
  value_of() { sed -n "s|^$1=||p" <<<"$exporter_env"; }
else
  checked=("${expected[0]}")
  trusting=true
  value_of() { printf '%s' "${!1-}"; }
fi

off=()
for pair in "${checked[@]}"; do
  name="${pair%%=*}"
  [ "$(value_of "$name")" = "${pair#*=}" ] || off+=("$name")
done

if [ "${#off[@]}" -gt 0 ]; then
  $starting || exit 0
  listed="$(printf '%s, ' "${off[@]}")"
  # stdout, not stderr: Claude Code folds a SessionStart hook's stdout into the
  # session context, and this notice is the only sign the variables are unset.
  notice "session-start: the cost ledger's telemetry capture is off. Not set to what
.claude/costs/hooks/telemetry_receiver.py listens for: ${listed%, }."
  exit 0
fi

mkdir -p "$out"
if $trusting && [ -n "$session" ] && [ ! -s "$events" ] && [ ! -e "$pending" ]; then
  date -u +%Y-%m-%dT%H:%M:%SZ >"$pending"
fi

listening && exit 0

# Every descriptor redirected, or the harness waits on the daemon's copy of
# the hook's stdout.
setsid nohup python3 "$(dirname "${BASH_SOURCE[0]}")/telemetry_receiver.py" --out "$out" --port "$port" \
  </dev/null >>"$out/receiver.log" 2>&1 &
exit 0
