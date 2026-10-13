#!/bin/bash
# Run prettier at the one version this repo formats with: every caller — the
# `PostToolUse` hook, `vet.sh`, `install-deps.sh` — goes through here, so the
# pin lives in this file alone. Arguments pass straight to prettier.
#
# `npx` rather than a `package.json`, because a root `package.json` would tell
# a project adopting this infrastructure that it is a JS project, and collide
# with its own. The first run fetches the version into npm's cache.
#
# It runs from the repo root, where prettier reads `.prettierignore`, so a
# relative path argument is relative to the root too.

set -euo pipefail

cd "$(dirname "$0")/.."

NPM_CONFIG_UPDATE_NOTIFIER=false exec npx --yes prettier@3.8.1 "$@"
