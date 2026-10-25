#!/bin/bash
# `UserPromptSubmit` and post-compaction `SessionStart` hook: ask the agent to
# mark the end of its orientation, until it has since the session started or
# last compacted.
#
# This text is the agent-facing home of when to mark;
# `.claude/costs/CLAUDE.md` § "Orientation" carries what the mark ends and what
# the measure does without one.

. "$(dirname "${BASH_SOURCE[0]}")/../../hooks/lib.sh" || exit 0
need_command jq "skipping the orientation notice."
need_command python3 "skipping the orientation notice."
read_payload

root="$(project_root)"
script=".claude/costs/oriented.py"
[ -n "$root" ] && [ -f "$root/$script" ] || exit 0

# A compaction has just opened a fresh stretch, so there is nothing to check.
unread=""
transcript="$(field transcript_path)"
if [ "$(field source)" != "compact" ] && [ -f "$transcript" ]; then
  if state="$(python3 "$root/$script" check "$transcript" 2>&1)"; then
    [ "$state" = "marked" ] && exit 0
  else
    unread=" (The transcript could not be read to tell whether you already have: $state)"
  fi
fi

# One line: the agent reads it unwrapped, and a hard break inside the command
# would split it.
emit_context "Mark the end of your orientation by running \`python3 $script\`, bare, the moment you know what the repository is and what the request is about — before the first step that carries the request out, even one that only reads, such as tracing the callers of the code you are about to change. Details of the ask still open are no reason to wait: orientation is knowing what is what, not having the whole answer, so the mark often comes before an estimate can. The ledger times the session's orientation by it, and without one a write to the repository or a reply to the operator ends it instead, later than it ended. Once per session, and once more after each compaction.$unread"
