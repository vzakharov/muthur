#!/bin/bash
# The artifacts project's checks, run in parallel; exits non-zero when any fails.

set -euo pipefail

cd "$(dirname "$0")"

exec ../../scripts/run-parallel.sh \
  typecheck='pnpm run typecheck' \
  lint='pnpm run lint' \
  lint:fsd='pnpm run lint:fsd' \
  check:masd='pnpm run check:masd' \
  masd:clusters='pnpm run masd:clusters' \
  check:cycles='pnpm run check:cycles' \
  test='pnpm run test' \
  prettier='../../scripts/prettier.sh --check .claude/artifacts'
