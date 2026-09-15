#!/bin/bash
# The checks that only test this repo's own machinery, behind one vet line.
#
# Membership is "would the adopting repo run this?", not "is it a test":
# `check-skill-catalog.sh` and `check-squash-message.sh` stay outside because
# they measure the adopting repo's own skills and its own branches, while what
# is in here measures code an adopter vendors and never edits.
#
# One line rather than one per check, so that a sync offers the adopter a single
# decision and their `vet.sh`, rewritten for their own stack, has nothing to
# conflict with.
#
# Keyed on the catalog, the signal `check-skill-catalog.sh` and
# `check-repo-identity.sh` also read: the catalog describes the source repo and
# is never vendored, so its absence is what "downstream" looks like.
#
# Python test files run by path, never through `unittest discover`: `scripts/`
# carries no `__init__.py`, and discovery over a namespace package reports
# `Ran 0 tests ... OK` and exits 0 — a line that passes without running a test.
#
# Reports every failure rather than stopping at the first.

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

CATALOG=".claude/skills/update-muthur/catalog.md"
failures=0

if [ ! -f "$CATALOG" ]; then
  echo "check-muthur: skipped — no $CATALOG (expected downstream)"
  exit 0
fi

run() {
  "$@" || failures=$((failures + 1))
}

run scripts/check-repo-identity.sh

shopt -s nullglob
tests=(scripts/test_*.py)
shopt -u nullglob

# An empty glob fails rather than passing quietly: a rename out of the pattern
# is the same silence the by-path rule above guards against.
if [ ${#tests[@]} -eq 0 ]; then
  echo "check-muthur: no scripts/test_*.py matched — did a rename empty the bucket?" >&2
  exit 1
fi

for test in "${tests[@]}"; do
  run "$test"
done

echo
if [ "$failures" -eq 0 ]; then
  echo "check-muthur: OK — repo identity plus ${#tests[@]} test file(s)"
  exit 0
fi
echo "check-muthur: $failures check(s) failed" >&2
exit 1
