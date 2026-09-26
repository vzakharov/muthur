#!/bin/bash
# `SessionStart` hook: start the receiver Claude Code's telemetry is pointed at
# by `.claude/settings.json`'s `env`, unless one is already listening. On
# `resume` too, since a container that slept has lost it.
#
# The events land under the repo's `tmp/telemetry/`; `.claude/costs/CLAUDE.md`
# § "Telemetry" says what reads them.

. "$(dirname "${BASH_SOURCE[0]}")/../../hooks/lib.sh" || exit 0
read_payload
need_command python3 "no telemetry is being captured"

root="$(project_root)"
[ -n "$root" ] || exit 0

(exec 3<>/dev/tcp/127.0.0.1/4318) 2>/dev/null && exit 0

out="$root/tmp/telemetry"
mkdir -p "$out"
# Every descriptor redirected, or the harness waits on the daemon's copy of
# the hook's stdout.
setsid nohup python3 "$(dirname "${BASH_SOURCE[0]}")/telemetry_receiver.py" --out "$out" \
  </dev/null >>"$out/receiver.log" 2>&1 &
exit 0
