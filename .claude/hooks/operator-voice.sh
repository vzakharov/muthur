#!/bin/bash
# SessionStart hook: print who the operator is — their name, their handle, and
# their entry from `.claude/voice/operators/` — into the session context, so the
# agent starts out knowing who it is talking to and how they want to be talked to
# instead of spending a turn resolving it. `.claude/voice/voice.md` is what reads
# this.
#
# Runs everywhere, unlike its two siblings: the agent needs this wherever it runs,
# and `gh` reaches the API through the proxy as well as around it.
#
# The lowercased login is both what the message prints and what names the entry
# file, so the one spelling an agent ever sees is the one the lookup uses. The
# filename is the whole lookup: no parse, so nothing an entry can malform.

set -euo pipefail

OPERATORS_DIR="$(dirname "$0")/../voice/operators"

identity="$(gh api user --jq '[.login, .type, .name] | @tsv' 2>/dev/null || true)"

if [ -z "$identity" ]; then
  echo "session-start: the operator is unresolved (\`gh\` is unavailable or could not reach the API). Ask them for their GitHub handle, then read .claude/voice/operators/<handle>.md yourself."
  exit 0
fi

IFS=$'\t' read -r login type name <<<"$identity"

if [ "$type" != "User" ]; then
  echo "session-start: the GitHub token in this session belongs to ${login}, a ${type} account — that is the agent's own identity, not the operator's. Ask the operator for their handle, then read .claude/voice/operators/<handle>.md yourself."
  exit 0
fi

handle="$(printf '%s' "$login" | tr '[:upper:]' '[:lower:]')"
who="@${handle}"
if [ -n "$name" ]; then
  who="${name} (@${handle})"
fi

# `|| true` because the entry is optional and `set -e` would otherwise take the
# hook down on a missing one — silently, this being a command substitution in an
# assignment.
entry="$(cat "$OPERATORS_DIR/${handle}.md" 2>/dev/null || true)"

if [ -z "$entry" ]; then
  echo "session-start: the operator is ${who} — the GitHub token in this session is that user's own. They have no entry under .claude/voice/operators/."
  exit 0
fi

echo "session-start: the operator is ${who} — the GitHub token in this session is that user's own. How they want to be talked to, from .claude/voice/operators/${handle}.md, applying to every reply:"
echo
echo "$entry"
