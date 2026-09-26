#!/bin/bash
# `SessionStart` hook: start the receiver Claude Code's telemetry is exported
# to, unless one is already listening. On `resume` too, since a container that
# slept has lost it. Where the exporter variables do not point at it, start
# nothing and print what to set instead — the environment's to set, never the
# repo's.
#
# The events land under the repo's `tmp/telemetry/`; `.claude/costs/CLAUDE.md`
# § "Telemetry" says why the repo cannot set the variables, and what reads the
# events.

. "$(dirname "${BASH_SOURCE[0]}")/../../hooks/lib.sh" || exit 0
read_payload
need_command python3 "no telemetry is being captured"

root="$(project_root)"
[ -n "$root" ] || exit 0

port=4318
expected=(
  "CLAUDE_CODE_ENABLE_TELEMETRY=1"
  "OTEL_LOGS_EXPORTER=otlp"
  "OTEL_EXPORTER_OTLP_PROTOCOL=http/json"
  "OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:$port"
  "OTEL_METRICS_EXPORTER=none"
  "OTEL_LOGS_EXPORT_INTERVAL=1000"
)

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
# receiver starts on it alone: a listener nothing exports to costs nothing.
checked=("${expected[@]:0:4}")
if exporter_env="$(claude_environ 2>/dev/null)"; then
  value_of() { sed -n "s|^$1=||p" <<<"$exporter_env"; }
else
  checked=("${expected[0]}")
  value_of() { printf '%s' "${!1-}"; }
fi

off=()
for pair in "${checked[@]}"; do
  name="${pair%%=*}"
  [ "$(value_of "$name")" = "${pair#*=}" ] || off+=("$name")
done

if [ "${#off[@]}" -gt 0 ]; then
  listed="$(printf '%s, ' "${off[@]}")"
  # stdout, not stderr: Claude Code folds a SessionStart hook's stdout into the
  # session context, and this notice is the only sign the variables are unset.
  cat <<MSG
session-start: the cost ledger's telemetry capture is off. Not set to what
.claude/costs/hooks/telemetry_receiver.py listens for: ${listed%, }.
This session's row is priced from its transcript alone, which misses the calls the
transcript never records.

Agent: relay this to the operator once. Claude Code ignores these variables in
a repository's .claude/settings.json, so no file in this repo can set them. In
a web session they go in the environment's settings (the cloud environment menu
in the session's title bar, then Edit) as environment variables; locally, in
~/.claude/settings.json's "env" or the shell. A new session picks them up:

$(printf '    %s\n' "${expected[@]}")
MSG
  exit 0
fi

(exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null && exit 0

out="$root/tmp/telemetry"
mkdir -p "$out"
# Every descriptor redirected, or the harness waits on the daemon's copy of
# the hook's stdout.
setsid nohup python3 "$(dirname "${BASH_SOURCE[0]}")/telemetry_receiver.py" --out "$out" --port "$port" \
  </dev/null >>"$out/receiver.log" 2>&1 &
exit 0
