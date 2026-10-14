#!/usr/bin/env bash
# Put an unattended routine's run on the one draft PR the routine accumulates
# into, so the operator reviews whatever piled up in one sitting rather than a
# PR per run.
#
# A PR belongs to the routine when it is an open draft touching a path that
# starts with one of the given paths — a directory prefix, or an exact file. A
# ready-for-review PR is the operator's review under way and takes no more runs,
# so it is never picked.
#
#   one draft → `gh pr checkout` it; merging the base is left to /finalize.
#   several   → the oldest, by number; the rest are printed for the report.
#   none      → a new branch `claude/<prefix>-<suffix>` off the default branch,
#               created without an upstream: one tracking the default branch
#               would aim a later bare `git push` at it. `<suffix>` is the
#               random tail of the branch the session is on, or six fresh
#               lowercase letters and digits — the form /branch-rename gives,
#               so /pr leaves the name as it is.
#
# Anything a routine needs beyond picking the branch stays in the routine.
#
# Usage:
#   scripts/routine-branch.sh <branch-prefix> <path>...
#
# Prints what it did, one `routine-branch:` line each. Any gh or git failure
# exits non-zero with its error.

set -euo pipefail

PROG="routine-branch"
GH_REPO_PROG="$PROG"

if [[ $# -lt 2 ]]; then
  echo "usage: scripts/${PROG}.sh <branch-prefix> <path>..." >&2
  exit 2
fi
prefix="$1"
shift

for tool in gh jq git; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "${PROG}: required tool '${tool}' not found on PATH." >&2
    exit 1
  }
done

REPO_ROOT="$(git rev-parse --show-toplevel)"
# shellcheck source=scripts/lib/gh-repo.sh
source "${REPO_ROOT}/scripts/lib/gh-repo.sh"
gh_resolve_repo # sets NWO, REPO_FLAG

prs="$(gh "${REPO_FLAG[@]}" pr list --state open --draft --limit 1000 --json number,isDraft,files)"
drafts=()
while IFS= read -r number; do
  drafts+=("$number")
done < <(jq -r '
  [ .[]
    | select(.isDraft and any(.files[].path as $p | $ARGS.positional[] as $x | $p | startswith($x); .))
    | .number ]
  | sort | .[]' --args "$@" <<<"$prs")

if [[ ${#drafts[@]} -gt 0 ]]; then
  gh "${REPO_FLAG[@]}" pr checkout "${drafts[0]}"
  echo "${PROG}: on draft #${drafts[0]} ($(git branch --show-current))"
  if [[ ${#drafts[@]} -gt 1 ]]; then
    others="$(printf ', #%s' "${drafts[@]:1}")"
    echo "${PROG}: other drafts, not taken: ${others:2}"
  fi
  exit 0
fi

default_branch="$(gh "${REPO_FLAG[@]}" repo view --json defaultBranchRef --jq '.defaultBranchRef.name')"
if [[ -z "$default_branch" || "$default_branch" == "null" ]]; then
  echo "${PROG}: gh returned no default branch for ${NWO}." >&2
  exit 1
fi

current="$(git branch --show-current)"
if [[ "$current" =~ ^claude/.+-([A-Za-z0-9]+)$ ]]; then
  suffix="${BASH_REMATCH[1]}"
else
  chars="abcdefghijklmnopqrstuvwxyz0123456789"
  suffix=""
  for _ in 1 2 3 4 5 6; do
    suffix+="${chars:RANDOM%${#chars}:1}"
  done
fi

branch="claude/${prefix}-${suffix}"
git fetch origin "$default_branch"
git switch --no-track -c "$branch" "origin/${default_branch}"
echo "${PROG}: no open draft — created ${branch} from origin/${default_branch}"
