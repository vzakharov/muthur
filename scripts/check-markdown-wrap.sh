#!/bin/bash
# Fail on tracked Markdown that prettier would rewrap, as `scripts/prettier.sh`
# pins it and `.prettierrc.json` configures it; `vet.sh` runs this while that
# config exists. A staged always-loaded file is checked through its staged copy,
# since that is the text the branch will land, and the real file waits for
# `/finalize`'s swap. `.prettierignore` exempts what GitHub renders.

set -euo pipefail

cd "$(dirname "$0")/.."

mapfile -t files < <(
  git ls-files -- '*.md' | while IFS= read -r path; do
    [ -f "$path" ] && scripts/staged.sh resolve "$path"
  done
)

scripts/prettier.sh --check --log-level warn "${files[@]}"
echo "check-markdown-wrap: OK"
