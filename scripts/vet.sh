#!/bin/bash
# Vet: the fast checks the agent runs before pushing review-ready work.
#
# ADOPTERS: what this file must exit is `.claude/rules/stack.md`'s contract. Read it
# there rather than inferring it from what this stub does — the exit turns on
# whether your repo has a stack yet, which is not a thing this file can see.
#
# Wire these up for your stack (lint, type-check, format-check, fast tests).
# Serial:
#   pnpm lint && pnpm typecheck && pnpm test:unit
#   cargo clippy --all-targets -- -D warnings && cargo test
#   ruff check . && mypy . && pytest -q
#   go vet ./... && go test -short ./...
#
# Parallel, printing only what failed (worth it once the serial run is the wait):
#   exec scripts/run-parallel.sh lint='pnpm lint' typecheck='pnpm typecheck' test='pnpm test:unit'
#
# The lines below are not stack-specific. Replacing everything around them
# is what this file is for, so decide each on its own rather than sweeping it
# away with the stack:
#
#   check-skill-catalog.sh — asserts that every `@`-reference into
#     `.claude/` resolves, and that no unhydrated stub stowed away. A
#     dangling reference fails silently: the agent follows the surviving prose
#     past the step they could not load. Dropping this line puts the check back
#     on the agent's memory, which is where it was when it went unrun.
#   check-squash-message.sh — holds the squash proposal to the rules
#     `/squash-message` states, passing quietly when a branch has no proposal.
#     Dropping it leaves nothing catching a proposal edited by hand or outgrown
#     by a later base merge.
#   staged.sh check — holds each staged copy of an always-loaded file under
#     `docs/staged/` to a tracked file it stands for and to the `.staged` suffix
#     that keeps it from loading, passing quietly when nothing is staged.
#     Dropping it lets a copy of nothing ride to `/finalize`, or a live one load.
#   check-muthur.sh — everything that tests only this repo's own machinery: the
#     repo-identity check and every `scripts/test_*.py`. One line because an
#     adopting repo drops them together; it keys on the catalog and exits 0
#     downstream, so the line is harmless if a rewrite leaves it.
#   the opt-in loop — the tests of the session cost ledger (`.claude/costs/`)
#     and of the context budget hook (`.claude/context-budget/`), run by path
#     for `check-muthur.sh`'s reason. Each is opt-in, so the loop keys on its
#     directory: a repo that said yes keeps it through the rewrite, and one that
#     said no has nothing for it to find.
#
# See `.claude/rules/stack.md` for the contract.

set -euo pipefail

"$(dirname "$0")/check-skill-catalog.sh"
"$(dirname "$0")/check-squash-message.sh"
"$(dirname "$0")/staged.sh" check
"$(dirname "$0")/check-muthur.sh"
for test in "$(dirname "$0")"/../.claude/{costs,context-budget}/test_*.py; do
  [ ! -f "$test" ] || python3 "$test"
done

echo "vet: no stack-specific checks are configured; the checks above are the run." >&2
echo "vet: a repo whose stack is present and unchecked exits 1 here instead" >&2
echo "     (see .claude/rules/stack.md for the contract)." >&2
exit 0
