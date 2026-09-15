#!/bin/bash
# UserPromptSubmit hook: when a prompt names a GitHub issue or PR — `#<N>`, or a
# pasted thread URL — run the exporter for it and name the export in the turn's
# context, so the session starts holding the thread instead of spending a round
# trip fetching it.
#
# `SessionStart` is where this belongs by intent and cannot carry it: the
# `SessionStart` payload has no prompt field, and in a web session that hook's
# record precedes the prompt's own by ~79 seconds. `UserPromptSubmit` is the
# first event that sees the prompt, and sees it before the agent does.
#
# So every prompt is in scope, not only the opening one, and that costs nothing:
# an export already on disk is skipped, leaving the fetches to prompts naming a
# thread this branch has not taken.
#
# Commits nothing, for `.claude/hooks/session-images.sh`'s reason: a hook that
# commits lands on whatever branch HEAD happens to be on, and a `/from-branch`
# session abandons the branch it starts on. The commit is
# `@.claude/skills/take-issue/SKILL.md` Step 2, and it stays the agent's.
#
# Never fails the turn: a failure here — no `jq`, no token, a private repo, a
# dead network — costs one round trip back to the loop the agent already had,
# so each path is stderr plus exit 0.

set -uo pipefail

payload="$(cat)"

say() { echo "prompt-issue-export: $*" >&2; }

command -v jq >/dev/null || { say "jq not found; skipping the export."; exit 0; }
command -v python3 >/dev/null || { say "python3 not found; skipping the export."; exit 0; }

prompt="$(jq -r '.prompt // empty' <<<"$payload")"
project="${CLAUDE_PROJECT_DIR:-$(jq -r '.cwd // empty' <<<"$payload")}"

[ -n "$prompt" ] || exit 0
[ -n "$project" ] && [ -d "$project" ] || exit 0
[ -f "$project/scripts/export-github-item.py" ] || exit 0

cd "$project" || exit 0

# At most three, so a prompt that pastes a log or a diff cannot turn the turn
# into a fetch queue. Deduped by number, since a bare `#55` and a URL ending in
# 55 land in the same export directory.
mapfile -t targets < <(python3 - "$prompt" <<'PY'
import re
import sys

pattern = re.compile(
    r"https://github\.com/[\w.-]+/[\w.-]+/(?:issues|pull)/(\d+)"
    r"|(?<![\w/#])#(\d+)(?![\w-])"
)
seen, found = set(), []
for match in pattern.finditer(sys.argv[1]):
    number = match.group(1) or match.group(2)
    if number in seen:
        continue
    seen.add(number)
    found.append(match.group(0))
print("\n".join(found[:3]))
PY
)

# Both roots are candidates for any number: whether it names an issue or a PR
# resolves from the API, never from the prompt.
landed_export() {
  local path
  for path in "docs/issue/$1/issue.md" "docs/pr/$1/pr.md"; do
    [ -f "$path" ] && { printf '%s\n' "$path"; return 0; }
  done
  return 1
}

exports=()
failures=()

for target in "${targets[@]}"; do
  [ -n "$target" ] || continue
  number="${target##*/}"
  number="${number#\#}"

  if landed="$(landed_export "$number")"; then
    exports+=("$landed")
    continue
  fi

  # The exporter exits non-zero on a partial run too — the Markdown written, an
  # attachment missing — so a failure is reported with its output rather than
  # swallowed or retried: which of those happened is the agent's to read.
  if ! output="$(timeout 50 python3 scripts/export-github-item.py "$target" 2>&1)"; then
    failures+=("$target: $(tail -n 5 <<<"$output")")
    continue
  fi

  if landed="$(landed_export "$number")"; then
    exports+=("$landed")
  fi
done

[ ${#exports[@]} -gt 0 ] || [ ${#failures[@]} -gt 0 ] || exit 0

context=""
if [ ${#exports[@]} -gt 0 ]; then
  context+="The GitHub threads this prompt names are on disk already — this hook ran "
  context+=$'`scripts/export-github-item.py` for each before the turn:\n'
  context+="$(printf '  %s\n' "${exports[@]}")"
  context+=$'\n\nSo `/take-issue` Step 1 is done for these: read each export end to end, and '
  context+=$'open the files under its `attachments/` when you need pixels. Do not re-export '
  context+=$'them, and do not reach for `gh issue view`, the GitHub MCP tools or `WebFetch` '
  context+=$'in their place. Nothing is committed — Step 2\'s commit is still yours for a '
  context+=$'thread you are taking on, and it happens before any planning.'
fi

if [ ${#failures[@]} -gt 0 ]; then
  [ -n "$context" ] && context+=$'\n\n'
  context+=$'These exports failed ahead of the turn. Run `scripts/export-github-item.py` '
  context+=$'yourself per `/take-issue` Step 1 — and if it fails there too, stop and report '
  context+=$'it rather than working from the title:\n'
  context+="$(printf '  %s\n' "${failures[@]}")"
fi

jq -n --arg ctx "$context" '{
  hookSpecificOutput: {
    hookEventName: "UserPromptSubmit",
    additionalContext: $ctx
  }
}'
