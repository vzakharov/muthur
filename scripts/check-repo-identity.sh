#!/bin/bash
# Assert that this repo's own `owner/repo` lives in one place.
#
# The canonical name is the `repo` field of
# `.claude/skills/update-muthur/watermark.json`. That field means "the repo I
# took this from", so in a tree with no source above it the shipped watermark
# names itself — which is exactly the predicate `/detemplate`, `/spinoff` and
# `CLAUDE.md`'s opening stub compare `origin` against instead of carrying the
# name themselves.
#
#   1. The canonical name appears only in files that cannot interpolate it:
#      clone lines, a `gh api` recipe, a filled-in watermark example, and one
#      frontmatter `description` the client reads before any file can be
#      resolved.
#   2. No file in the search surface names a *different* repo under the
#      canonical owner. That is what a half-finished rename looks like.
#   3. `git remote get-url origin` agrees with the canonical name — a warning,
#      never a failure. A rename lands on GitHub only once the tree describing
#      it is green, so failing here would deadlock the vet run that gates it.
#
# The whole run skips without the catalog, the same signal
# `check-skill-catalog.sh` reads: downstream the watermark names someone else's
# repo, and the allowlist below describes a tree that was pruned.
#
# Reports every failure rather than stopping at the first.

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

WATERMARK=".claude/skills/update-muthur/watermark.json"
CATALOG=".claude/skills/update-muthur/catalog.md"
failures=0

fail() {
  printf '  ✗ %s\n' "$*" >&2
  failures=$((failures + 1))
}

if [ ! -f "$CATALOG" ]; then
  echo "check-repo-identity: skipped — no $CATALOG (expected downstream)"
  exit 0
fi

if [ ! -f "$WATERMARK" ]; then
  echo "check-repo-identity: $WATERMARK is missing — nothing to check against" >&2
  exit 1
fi

CANONICAL=$(jq -r '.repo' "$WATERMARK")
case "$CANONICAL" in
  */*) ;;
  *)
    echo "check-repo-identity: $WATERMARK has no usable \`repo\` field" >&2
    exit 1
    ;;
esac
OWNER=${CANONICAL%%/*}

# Files that carry the literal because a reader copies them by hand, plus the
# watermark that defines it. Everything else derives the name from the
# watermark at read time.
allowed=(
  "$WATERMARK"
  README.md
  ADOPTING.md
  .claude/skills/detemplate/SKILL.md
)

# The durable agent infrastructure, as git tracks it. Tracked is what matters —
# an untracked file reaches nobody else's tree — and it keeps
# `.claude/settings.local.json` out, a per-machine permission log quoting
# whatever commands a session ran. `docs/` is outside the surface too: a plan
# discussing a rename quotes both names by necessity. So is the cost ledger's
# `sessions/`: each row quotes its session's opening prompt, which may name any
# sibling repository.
mapfile -t sources < <(
  git ls-files -z -- \
    '.claude/*.md' '.claude/*.sh' '.claude/*.json' \
    ':!:.claude/costs/sessions/*' \
    CLAUDE.md README.md ADOPTING.md \
    'scripts/*.sh' 'scripts/*.py' 2>/dev/null | tr '\0' '\n'
)

if [ ${#sources[@]} -eq 0 ]; then
  echo "check-repo-identity: found no files to scan — wrong directory?" >&2
  exit 1
fi

is_allowed() {
  local f=${1#./}
  local a
  for a in "${allowed[@]}"; do
    [ "$f" = "$a" ] && return 0
  done
  return 1
}

echo "1. The canonical name appears only where a human copies it"

while IFS= read -r hit; do
  [ -n "$hit" ] || continue
  is_allowed "${hit%%:*}" ||
    fail "${hit} names \`$CANONICAL\` — derive it from $WATERMARK instead"
done < <(grep -Fn --with-filename -- "$CANONICAL" "${sources[@]}" 2>/dev/null | cut -d: -f1,2)

echo "2. No stale name under the same owner"

while IFS= read -r hit; do
  [ -n "$hit" ] || continue
  stale=${hit##*:}
  [ "$stale" = "$CANONICAL" ] && continue
  fail "${hit%:*} names \`$stale\` — a rename that did not finish, or \`$CANONICAL\` is wrong"
done < <(
  grep -oEn --with-filename -- "$OWNER/[A-Za-z0-9._-]+" "${sources[@]}" 2>/dev/null |
    sort -u
)

echo "3. \`origin\` agrees with the watermark"

remote=$(git remote get-url origin 2>/dev/null)
if [ -z "$remote" ]; then
  printf '   no `origin` remote to compare against\n'
else
  # https://github.com/owner/repo(.git) and git@github.com:owner/repo(.git)
  slug=${remote%.git}
  slug=${slug#*github.com[:/]}
  if [ "$slug" = "$CANONICAL" ]; then
    printf '   %s\n' "$slug"
  else
    printf '  ⚠ origin is `%s`, watermark says `%s` — expected only between a\n' \
      "$slug" "$CANONICAL" >&2
    printf '    rename landing on GitHub and the tree describing it\n' >&2
  fi
fi

echo
if [ "$failures" -eq 0 ]; then
  echo "check-repo-identity: OK"
  exit 0
fi
echo "check-repo-identity: $failures failure(s)" >&2
exit 1
