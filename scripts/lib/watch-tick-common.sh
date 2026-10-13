#!/usr/bin/env bash
# Tick helpers for the CI watch loop (scripts/ci-watch-tick.sh).
#
# This file is meant to be SOURCED, not executed — it defines functions and
# does not set shell options (the sourcing script owns `set -euo pipefail`).
#
# Callers may set `WT_PROG` (defaults to "watch-tick") to prefix diagnostic
# messages with the script's name.

# Sleep for INTERVAL seconds, minus any time already elapsed since the previous
# tick — so a tick fired after the agent spent minutes working doesn't double
# the wait. Reads INTERVAL, which the sourcing script sets.
# Arg 1: the previous tick's ISO-8601 timestamp ("" on the first tick).
wt_smart_sleep() {
  local last_tick_at="${1:-}"
  local now_epoch sleep_secs last_epoch elapsed
  now_epoch="$(date -u +%s)"
  sleep_secs="$INTERVAL"
  if [[ -n "$last_tick_at" ]]; then
    last_epoch="$(date -u -d "$last_tick_at" +%s 2>/dev/null || echo 0)"
    elapsed=$(( now_epoch - last_epoch ))
    if (( elapsed >= INTERVAL )); then
      sleep_secs=0
    else
      sleep_secs=$(( INTERVAL - elapsed ))
    fi
  fi
  if (( sleep_secs > 0 )); then
    sleep "$sleep_secs"
  fi
}

# Remove the state file (used by the `--reset` flag) and exit. Use when the
# agent gave up mid-watch and the next watch needs a clean slate.
# Arg 1: path to the state file.
wt_reset_state() {
  local state_file="$1"
  local prog="${WT_PROG:-watch-tick}"
  if [[ -f "$state_file" ]]; then
    rm "$state_file"
    echo "${prog}: state file removed (${state_file})."
  else
    echo "${prog}: no state file to remove."
  fi
  exit 0
}
