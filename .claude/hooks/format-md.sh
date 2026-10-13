#!/bin/bash
# PostToolUse hook on Edit|Write|MultiEdit: hard-wrap the Markdown file the tool
# just touched, through `scripts/prettier.sh`, so a session never leaves a
# paragraph on one physical line for `vet.sh`'s check to find later.
#
# Only a `.md`, or a staged `.md.staged` copy, inside the project: a draft in
# the scratchpad or anywhere else outside the tree is likely bound for GitHub,
# which renders its newlines as line breaks. Inside the tree, `.prettierignore`
# exempts the same kind of file. Claude Code reports the rewrite to the agent
# as a change on disk, so its next edit starts from the wrapped text.
#
# A prettier failure exits 2 with prettier's message, which Claude Code shows
# the agent: an edit that went through unwrapped in silence would surface only
# at the vet run, far from the edit that caused it.

set -euo pipefail

. "$(dirname "${BASH_SOURCE[0]}")/lib.sh" || exit 0

need_command jq "skipping the Markdown wrap."
read_payload

path="$(jq -r '.tool_input.file_path // empty' <<<"$payload")"
case "$path" in
  *.md | *.md.staged) ;;
  *) exit 0 ;;
esac

root="$(project_root)"
[ -n "$root" ] || exit 0
case "$path" in
  "$root"/*) ;;
  *) exit 0 ;;
esac
[ -f "$path" ] || exit 0

if ! out="$("$root/scripts/prettier.sh" --write --log-level warn "$path" 2>&1)"; then
  printf 'format-md: prettier could not wrap %s:\n%s\n' "$path" "$out" >&2
  exit 2
fi
