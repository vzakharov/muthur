#!/usr/bin/env bash
# Proxy-aware "owner/repo" resolution for the scripts that call `gh`
# (scripts/check-merge.sh, scripts/ci-watch-tick.sh, scripts/muthur-sync.sh).
#
# This file is meant to be SOURCED, not executed — it defines a function and
# does not set shell options (the sourcing script owns `set -euo pipefail`).
#
# Callers may set `GH_REPO_PROG` (defaults to "gh-repo") to prefix diagnostic
# messages with the script's name.

# Resolve the gh repo. gh auto-detects from the git remote, which fails when the
# remote points at a sandboxed proxy URL (e.g. cloud agent VMs). Fall back to
# parsing the `origin` remote ourselves. Sets globals NWO ("owner/repo") and
# REPO_FLAG (array, always `-R owner/repo` — never left empty: expanding an empty
# array with `"${REPO_FLAG[@]}"` under `set -u` is an "unbound variable" error on
# the bash 3.2 that ships with macOS, so callers can rely on it being populated).
gh_resolve_repo() {
  local prog="${GH_REPO_PROG:-gh-repo}"
  REPO_FLAG=()
  NWO=""
  if NWO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null)" && [[ -n "$NWO" && "$NWO" != "null" ]]; then
    REPO_FLAG=(-R "$NWO")
    return 0  # gh auto-detected the repo
  fi
  local origin_url
  origin_url="$(git remote get-url origin 2>/dev/null || true)"
  if [[ "$origin_url" =~ github\.com[:/]([^/]+)/([^/]+?)(\.git)?/?$ ]]; then
    NWO="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
    REPO_FLAG=(-R "$NWO")
  fi
  if [[ -z "$NWO" ]]; then
    echo "${prog}: cannot determine OWNER/REPO — gh could not detect it and 'origin' is not a github.com remote." >&2
    exit 1
  fi
}
