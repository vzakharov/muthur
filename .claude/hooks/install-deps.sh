#!/bin/bash
# SessionStart hook: re-sync installed dependencies with the lockfile.
#
# Remote/web sessions can resume with a stale dependency tree if the lockfile
# advanced since the environment snapshot was built (the setup script runs once
# at snapshot build time, then is cached — see
# https://code.claude.com/docs/en/claude-code-on-the-web#setup-scripts).
# Re-running on every session start keeps the install tree tracking the current
# lockfile.
#
# Remote-only: a local session installs its own dependencies when it wants them,
# and paying an install on every `claude` launch is not what anyone wants.
#
# TODO (new project): implement the install for your stack, e.g.
#   pnpm install --frozen-lockfile     # Node / pnpm
#   poetry install --sync              # Python / poetry
#   cargo fetch                        # Rust
#   go mod download                    # Go
#
# Until that line exists this hook no-ops cleanly, which is the correct state for
# a repo with no stack yet. It is the paired site of `scripts/vet.sh`: a stack
# that lands wires both, per CLAUDE.md § "Vetting".

set -euo pipefail

[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

# TODO: install dependencies for your stack
