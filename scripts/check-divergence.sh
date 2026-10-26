#!/bin/bash
# Hold `/update-muthur`'s state to its shape: the watermark carries the sync's
# position and nothing else, and the divergence record stays within a size every
# sync can read whole. `.claude/skills/update-muthur/SKILL.md` § "The divergence
# record" owns both.
#
# Each physical line of the record counts ceil(characters / WIDTH): a
# prettier-wrapped file's line count, and the wrapped length of one that is not.
# Characters, not bytes, by `check-claude-md-size.sh`'s `count_chars` trick, so
# a non-Latin record is not measured as two or three times its length. An
# adopter with its own idea of the right size changes MAX_LINES in its copy, in
# a commit that says why.

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

PROG="check-divergence"
WATERMARK=".claude/skills/update-muthur/watermark.json"
RECORD=".claude/skills/update-muthur/divergence.md"
WIDTH=80
MAX_LINES=450

failures=0

# A key spelled inside a string value has its quotes escaped, so only a real key
# matches.
if [ -f "$WATERMARK" ] && grep -Eq '"(adopted|declined)"[[:space:]]*:' "$WATERMARK"; then
  printf '  ✗ %s still carries `adopted`/`declined` — the watermark holds repo, lastSyncedSha, lastSyncedAt and lineage only;\n' "$WATERMARK" >&2
  printf '    write what differs from the source into %s per .claude/skills/update-muthur/SKILL.md § "The divergence record", and drop what was taken verbatim\n' "$RECORD" >&2
  failures=$((failures + 1))
fi

if [ -f "$RECORD" ]; then
  lines=$(LC_ALL=C tr -d '\200-\277' <"$RECORD" | awk -v w="$WIDTH" '
    { n += (length($0) == 0 ? 1 : int((length($0) + w - 1) / w)) }
    END { print n + 0 }
  ')
  if [ "$lines" -gt "$MAX_LINES" ]; then
    printf '  ✗ %s is %s lines at %s columns, over %s — rewrite it to the current difference (history out, a cross-cutting difference stated once), not into parts\n' \
      "$RECORD" "$lines" "$WIDTH" "$MAX_LINES" >&2
    failures=$((failures + 1))
  fi
fi

if [ "$failures" -eq 0 ]; then
  echo "$PROG: OK"
  exit 0
fi
exit 1
