#!/bin/bash
# Fail on a Markdown table outside a code fence in any tracked `.md`.
#
# This repo's house style, run by `check-muthur.sh` and so never downstream,
# where tables are the adopter's call. The convention is
# `.claude/rules/markdown.md`'s: Markdown here is read raw,
# by agents and in diffs, where a table row is one physical line and editing any
# cell rewrites the whole row. A table is caught by its delimiter row
# (`| --- | :-: |`), the one line every GitHub table must have. A table inside a
# fence is a template for output read rendered elsewhere, and passes.
#
# Skipped: the working artifacts `/finalize` sweeps before landing, which hold
# GitHub's text verbatim (`docs/issue/`, `docs/pr/`) or reports a script parses
# (`docs/plans/`, `docs/remove-before-merging/`). A staged always-loaded file
# is read through its staged copy, since that is the text the branch will land.

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

staged_view() {
  if [ -x scripts/staged.sh ]; then
    scripts/staged.sh resolve "$1"
  else
    printf '%s\n' "$1"
  fi
}

failures=0
while IFS= read -r path; do
  file=$(staged_view "$path")
  [ -f "$file" ] || continue
  while IFS= read -r line; do
    printf '  ✗ %s:%s has a table — write it as a list or sections\n' "$path" "$line" >&2
    failures=$((failures + 1))
  done < <(
    awk '
      # A fence opens on three or more backticks or tildes and closes on a run
      # of the same character at least as long.
      match($0, /^ *(```+|~~~+)/) {
        run = substr($0, RSTART, RLENGTH)
        sub(/^ */, "", run)
        if (fence == "") { fence = run; next }
        if (substr(run, 1, 1) == substr(fence, 1, 1) && length(run) >= length(fence)) { fence = ""; next }
      }
      fence == "" && /^ *\|? *:?-+:? *(\| *:?-+:? *)+\|? *$/ { print FNR }
    ' "$file"
  )
done < <(
  git ls-files -- '*.md' ':!docs/issue/' ':!docs/pr/' ':!docs/plans/' ':!docs/remove-before-merging/'
)

if [ "$failures" -eq 0 ]; then
  echo "check-markdown-tables: OK"
  exit 0
fi
echo "check-markdown-tables: $failures table(s) outside a code fence" >&2
exit 1
