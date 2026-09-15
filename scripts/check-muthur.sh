#!/bin/bash
# The checks that only test this repo's own machinery, behind one vet line.
#
# Membership is "would the adopting repo run this?", not "is it a test".
# `check-skill-catalog.sh` and `check-squash-message.sh` stay outside because a
# repo that keeps the loop keeps them: they measure that repo's own skills and
# its own branches. What is in here measures code an adopter vendors and never
# edits, so downstream it asserts things about someone else's repo.
#
# The point of the bundle is the *rate*: a new test file joins by matching
# `scripts/test_*.py` and never touches `vet.sh`, so a sync offers the adopter
# one decision instead of a line per test — and their `vet.sh`, rewritten for
# their own stack, has nothing to conflict with.
#
# Keyed on the catalog, the same signal `check-skill-catalog.sh` and
# `check-repo-identity.sh` read: the catalog describes the source repo and is
# never vendored, so its absence is what "this tree is downstream" looks like.
#
# Python test files run by path, never through `unittest discover`: `scripts/`
# carries no `__init__.py`, and discovery over a namespace package reports
# `Ran 0 tests ... OK` and exits 0 — a line that passes here without running a
# test.
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

# An empty glob is a failure, not a quiet pass: it is what a rename out of the
# pattern looks like, and it is the exact silence the by-path rule above exists
# to avoid.
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
