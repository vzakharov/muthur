#!/usr/bin/env bash
# Post or update one of the loop's sticky PR comments from a file — the
# find → PATCH-or-create that `@.claude/skills/squash-message/SKILL.md` Step 4
# and `@.claude/skills/finalize/SKILL.md` step 7 each need, as one command. The
# interface is fixed and narrow so `.claude/settings.json` can allow exactly
# this command: an allow rule resolves before auto mode's classifier runs, and
# the classifier otherwise reads an inline `gh api -X PATCH` as an external
# write and denies it. The file must lead with its kind's marker, which keeps
# the rule from approving any other comment.
#
# Usage (from the repository root, spelled exactly so, with no `cd … &&` or
# anything else chained in front — the allow rule matches the command text):
#   scripts/pr-comment.sh <kind> [--update-only] <pr-number> <file>
#
# Kinds, each keyed on the marker its body leads with:
#   squash       - `Proposed squash`, the squash proposal.
#   attestation  - `<!-- finalize-attestation`, the finalize attestation.
#
# The comment is the newest one whose body leads with the marker, whoever
# posted it — a session picking up someone else's PR takes over the comment
# their session left. A match already equal to the file is left untouched.
#
# Prints one line, `<outcome> <comment-url>`, the outcome being `posted`,
# `edited` or `current`; or `absent` alone under `--update-only`.
#
# Exit codes:
#   0  - posted, edited, or already current.
#   1  - bad arguments, a file without its kind's marker, or a `gh` failure.
#   3  - `--update-only` and no such comment exists; nothing was created.

set -euo pipefail

PROG="pr-comment"

die() {
  printf '%s: %s\n' "$PROG" "$1" >&2
  exit 1
}

usage() {
  printf 'usage: scripts/pr-comment.sh <squash|attestation> [--update-only] <pr-number> <file>\n' >&2
  exit 1
}

case "${1:-}" in
  squash) MARKER="Proposed squash" ;;
  attestation) MARKER="<!-- finalize-attestation" ;;
  *) usage ;;
esac
shift

UPDATE_ONLY=0
if [[ "${1:-}" == "--update-only" ]]; then
  UPDATE_ONLY=1
  shift
fi
[[ "$#" -eq 2 ]] || usage
PR="$1"
FILE="$2"
[[ "$PR" =~ ^[1-9][0-9]*$ ]] || die "PR number must be a positive integer, got '$PR'"
[[ -f "$FILE" ]] || die "no such file: $FILE"
[[ "$(head -c "${#MARKER}" "$FILE")" == "$MARKER" ]] ||
  die "$FILE does not lead with '$MARKER'"

REPO_ROOT="$(git rev-parse --show-toplevel)"
GH_REPO_PROG="$PROG"
# shellcheck source=scripts/lib/gh-repo.sh
source "${REPO_ROOT}/scripts/lib/gh-repo.sh"
gh_resolve_repo

# Oldest first, as the API lists them, so the last id is the newest.
ID="$(
  gh api "repos/${NWO}/issues/${PR}/comments" --paginate --jq \
    ".[] | select(.body | startswith(\"${MARKER}\")) | .id" | tail -n 1
)"

if [[ -z "$ID" ]]; then
  if [[ "$UPDATE_ONLY" -eq 1 ]]; then
    echo "absent"
    exit 3
  fi
  URL="$(gh api "repos/${NWO}/issues/${PR}/comments" -X POST -F "body=@${FILE}" --jq .html_url)"
  echo "posted ${URL}"
  exit 0
fi

KEEP="repos/${NWO}/issues/comments/${ID}"

# `$(…)` drops trailing newlines on both sides, so a file ending in one still
# reads as equal to the body GitHub stored.
CURRENT="$(gh api "$KEEP" --jq .body)"
if [[ "$CURRENT" == "$(cat "$FILE")" ]]; then
  echo "current $(gh api "$KEEP" --jq .html_url)"
  exit 0
fi

URL="$(gh api "$KEEP" -X PATCH -F "body=@${FILE}" --jq .html_url)"
echo "edited ${URL}"
