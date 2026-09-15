#!/bin/bash
# UserPromptSubmit hook: a prompt that *ends* in a GitHub reference — `#<N>` or
# a pasted thread URL — is an operator handing that thread over, so export it
# and name the export in the turn's context. The session then starts holding the
# thread instead of spending a round trip fetching it.
#
# Only a trailing reference counts. A number mid-sentence is usually about
# something else ("what should rule #1 be?"), and the match is bash's own, so a
# prompt that ends in anything else costs one `jq` and nothing further runs.
#
# An export that lands may still be one nobody wanted, so the injected context
# names it as untracked and the agent's to delete. Deleting a stray export is
# the cheap direction: `@.claude/skills/take-issue/SKILL.md` Step 2's commit
# stays the agent's, so nothing reaches the branch they did not put there. This
# hook commits nothing itself, for `.claude/hooks/session-images.sh`'s reason: a
# hook that commits lands on whatever branch HEAD happens to be on, and a
# `/from-branch` session abandons the branch it starts on.
#
# Never fails the turn: a failure here — no `jq`, no token, a private repo, a
# dead network — costs one round trip back to the loop the agent already had,
# so each path is stderr plus exit 0.

set -uo pipefail

payload="$(cat)"

say() { echo "prompt-issue-export: $*" >&2; }

command -v jq >/dev/null || { say "jq not found; skipping the export."; exit 0; }

prompt="$(jq -r '.prompt // empty' <<<"$payload")"
[ -n "$prompt" ] || exit 0

# `#90?` and `#90.` hand a thread over the way `#90` does, so trailing space and
# sentence punctuation come off before the reference has to sit at the end. The
# closers are listed rather than matched as "any non-alphanumeric tail", which
# under an unset locale swallows Cyrillic and matches a reference mid-sentence;
# and they are a `case` glob rather than a bracket class, which inside
# `[[ =~ ]]` loses its escaping before the regex sees it.
while [ -n "$prompt" ]; do
  case "${prompt: -1}" in
    [[:space:]] | . | , | ';' | : | '!' | '?' | '"' | "'" | ')' | ']') prompt="${prompt%?}" ;;
    *) break ;;
  esac
done

# The leading boundary is what keeps a hex colour, a fragment and a path out:
# `#` may not sit against a word character, a `/` or another `#`. Held in a
# variable for the quoting reason above.
reference_re='(^|[^[:alnum:]_/#])(#|https://github\.com/[^[:space:]/]+/[^[:space:]/]+/(issues|pull)/)([0-9]+)$'
[[ "$prompt" =~ $reference_re ]] || exit 0

reference="${BASH_REMATCH[2]}${BASH_REMATCH[4]}"
number="${BASH_REMATCH[4]}"

project="${CLAUDE_PROJECT_DIR:-$(jq -r '.cwd // empty' <<<"$payload")}"
[ -n "$project" ] && [ -d "$project" ] || exit 0
command -v python3 >/dev/null || { say "python3 not found; skipping the export."; exit 0; }
cd "$project" || exit 0
[ -f scripts/export-github-item.py ] || exit 0

# Both roots are candidates for any number: whether it names an issue or a PR
# resolves from the API, never from the prompt.
landed_export() {
  local path
  for path in "docs/issue/$1/issue.md" "docs/pr/$1/pr.md"; do
    [ -f "$path" ] && { printf '%s\n' "$path"; return 0; }
  done
  return 1
}

failure=""
if ! landed="$(landed_export "$number")"; then
  # The exporter exits non-zero on a partial run too — the Markdown written, an
  # attachment missing — so a failure is reported with its output rather than
  # swallowed or retried: which of those happened is the agent's to read.
  if ! output="$(timeout 50 python3 scripts/export-github-item.py "$reference" 2>&1)"; then
    failure="$(tail -n 5 <<<"$output")"
  fi
  landed="$(landed_export "$number")" || true
fi

context=""
if [ -n "$landed" ]; then
  context+=$'The GitHub thread this prompt ends in is on disk already — this hook ran\n'
  context+="\`scripts/export-github-item.py\` for it before the turn: $landed"
  context+=$'\n\nSo `/take-issue` Step 1 is done: read that export end to end, and open the files '
  context+=$'under its `attachments/` when you need pixels. Do not re-export it, and do not '
  context+=$'reach for `gh issue view`, the GitHub MCP tools or `WebFetch` in its place.'
  context+=$'\n\nNothing is committed. Step 2\'s commit is yours for a thread you are taking on — '
  context+=$'and where the number turns out to have been something else (a rule, a version, a '
  context+=$'quantity), delete the export instead. The prompt says what the session is about; '
  context+=$'this fetch only guessed.'
elif [ -n "$failure" ]; then
  context+="This export failed ahead of the turn — \`$reference\`: $failure"
  context+=$'\n\nMost often that means the number was never a thread reference, in which case '
  context+=$'there is nothing to fetch and nothing to do. Where the prompt really is handing a '
  context+=$'thread over, run `scripts/export-github-item.py` yourself per `/take-issue` Step 1, '
  context+=$'and stop and report rather than working from the title if it fails there too.'
else
  exit 0
fi

jq -n --arg ctx "$context" '{
  hookSpecificOutput: {
    hookEventName: "UserPromptSubmit",
    additionalContext: $ctx
  }
}'
