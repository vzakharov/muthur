#!/bin/bash
# Vet: the fast checks the agent runs before pushing review-ready work.
#
# ADOPTERS: what this file must exit is CLAUDE.md → Vetting's contract. Read it
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
# The five lines below are not stack-specific. Replacing everything around them
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
#   check-repo-identity.sh — holds the repo's own `owner/repo` to one home, the
#     watermark's `repo` field, plus the handful of clone lines and recipes a
#     human copies. It is the one line here that is *this* repo's alone: it
#     keys on the catalog and exits 0 downstream, so a rewrite drops it.
#   test_authorship.py — the export's agent/human labelling, which `/handle`
#     reads to tell its own replies from an operator's. Run by path, never
#     through `unittest discover`: `scripts/` carries no `__init__.py`, and
#     discovery over a namespace package reports `Ran 0 tests ... OK` and exits
#     0, so the line would pass here without running a test.
#   test_export_split.py — the export's hunk trimming and its index-plus-hoist
#     layout. Run by path for the same reason. What it guards above all is that
#     a trimmed hunk still carries the reviewer's selection byte for byte.
#
# See CLAUDE.md → Vetting for the contract.

set -euo pipefail

"$(dirname "$0")/check-skill-catalog.sh"
"$(dirname "$0")/check-squash-message.sh"
"$(dirname "$0")/check-repo-identity.sh"
"$(dirname "$0")/test_authorship.py"
"$(dirname "$0")/test_export_split.py"

echo "vet: no stack-specific checks are configured; the checks above are the run." >&2
echo "vet: a repo whose stack is present and unchecked exits 1 here instead" >&2
echo "     (see CLAUDE.md → Vetting for the contract)." >&2
exit 0
