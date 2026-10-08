#!/bin/bash
# PermissionDenied + Stop hook pair: when auto mode denies a tool call, make the
# agent end its turn by handing the operator a message that would authorize it.
#
#   permission-denied-phrase.sh mark   (PermissionDenied) — record the call
#   permission-denied-phrase.sh stop   (Stop) — if any were recorded, block the
#                                       stop once with the instruction, and clear
#
# Two events because PermissionDenied cannot reach the agent: its only outputs
# are `retry` and a `systemMessage` the operator sees, not `additionalContext`.
# Stop's `decision: block` hands its `reason` to the agent and continues the
# turn, so the marker carries the denials across to it.
#
# The phrase works because the classifier reads the operator's messages and
# lets a soft-denied action through when one names it directly and specifically.
# `retry: true` is deliberately not returned: a retry before the operator has
# written that message meets the same verdict.
#
# The payload's `classifier_verdict` goes unread: the docs list it, but
# classifier denials arrive without it, so it cannot tell them from rule denials.
#
# A reply already holding a fenced block passes unblocked: CLAUDE.md has the
# agent write the phrase in the reply that met the denial, and blocking that
# reply would only buy a second message saying so. A reply fencing something
# else passes too — the backstop's price for not nagging the ones that complied.
# The marker is consumed either way, so the continuation stops normally unless
# it is itself denied something new.

set -euo pipefail

. "$(dirname "${BASH_SOURCE[0]}")/lib.sh" || exit 0

need_command jq "skipping the permission-denied phrase."
read_payload

root="$(project_root)"
session="$(field session_id)"
[ -n "$root" ] && [ -n "$session" ] || exit 0
marker="$root/tmp/permission-denied/$session.jsonl"

case "${1:-}" in
  mark)
    mkdir -p "$(dirname "$marker")"
    # Inputs are cut at 500 characters: a denied `Write` carries the whole file,
    # and the agent needs only enough to name the action.
    jq -c '{
      tool: .tool_name,
      input: (.tool_input | tojson | if length > 500 then .[:500] + "…" else . end)
    }' <<<"$payload" >>"$marker"
    ;;
  stop)
    [ -s "$marker" ] || exit 0
    denials="$(jq -r '"- \(.tool): \(.input)"' "$marker")"
    rm -f "$marker"
    [[ "$(field last_assistant_message)" == *'```'* ]] && exit 0
    read -r -d '' reason <<REASON || true
Auto mode denied these tool calls during this turn:
$denials

For each one you still need, give the operator a message to send back as their
explicit authorization, in its own fenced code block so it copies in one click.
The classifier reads the operator's messages and lets a soft-denied action
through when one directly and specifically describes it — the exact command,
file, branch or target — while a general "go ahead" does not count. So:

- name the action exactly as it is, never softened or reworded to slip past;
- write it in the language the operator is talking to you in;
- where a phrase cannot help — the denial message names a permission rule in
  the settings rather than the classifier, or the block is a hard one — say so
  and name what would, instead.

If you no longer need the call, say so in one line and stop.
REASON
    jq -n --arg reason "$reason" '{decision: "block", reason: $reason}'
    ;;
  *)
    say "unknown mode '${1:-}'; expected mark or stop."
    ;;
esac
