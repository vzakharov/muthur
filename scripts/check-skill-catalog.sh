#!/bin/bash
# Assert the skill cross-reference and catalog invariants.
#
#   1. Every `@`-reference into `.claude/` resolves to a file that exists. This
#      is the check that makes subset-copying safe: a file copied without its
#      closure leaves a pointer that fails *silently* — the agent follows the
#      surviving prose and skips the step they could not load. Skill pointers are
#      the bulk of them; CLAUDE.md's imports fail the same way, which is why the
#      scope is the directory.
#   2. Every `.claude/skills/*/` directory has exactly one row in
#      `.claude/skills/update-muthur/catalog.md`.
#   3. Every path named in a catalog row's first column exists; a row naming a
#      glob names a set rather than a path, and is skipped.
#   4. A skill's two stub markers agree, and no unhydrated stub is present
#      downstream.
#   5. Every `.md` beside a `SKILL.md` is reachable — something other than the
#      page itself names its path. The reverse of 1: that one catches a pointer
#      to nothing, this one a page nothing points at.
#
# Assertions 2-3 skip when the catalog is absent — the normal downstream
# case, since the catalog describes the source repo and is never vendored. So the
# same script is useful at every link in the adoption chain. Assertion 4 runs
# everywhere but changes verdict on the same signal: the catalog's presence is
# what distinguishes "this repo ships the stubs on purpose" from "a stub was
# copied into a project it was never written for".
#
# Reports every failure rather than stopping at the first.

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

CATALOG=".claude/skills/update-muthur/catalog.md"
failures=0

fail() {
  printf '  ✗ %s\n' "$*" >&2
  failures=$((failures + 1))
}

# The search surface is the durable agent infrastructure: the skills and their
# config, the always-loaded conventions, the acquisition docs, the scripts.
# Working artifacts (`docs/plans/`, `docs/issue/`, `docs/pr/`) are deliberately
# outside it — they discuss references as examples rather than making them, so a
# plan quoting a placeholder skill path is not a broken link. Keep illustrative
# reference syntax out of this file too, for the same reason: it scans itself.
mapfile -t sources < <(
  {
    [ -d .claude ] && find .claude -type f \
      \( -name '*.md' -o -name '*.sh' -o -name '*.json' \) -print
    for f in CLAUDE.md README.md ADOPTING.md; do
      [ -f "$f" ] && printf '%s\n' "$f"
    done
    [ -d scripts ] && find scripts -type f \( -name '*.sh' -o -name '*.py' \) -print
  } 2>/dev/null
)

if [ ${#sources[@]} -eq 0 ]; then
  echo "check-skill-catalog: found no files to scan — wrong directory?" >&2
  exit 1
fi

# --- Assertion 1: no dangling skill reference ------------------------------

echo "1. @-references into .claude/ resolve"

# Emit "file:referenced-path" for every @-reference, then test each target.
while IFS= read -r hit; do
  [ -n "$hit" ] || continue
  src=${hit%%:*}
  ref=${hit#*:}
  ref=${ref#@}
  if [ ! -f "$ref" ]; then
    fail "$src references $ref — no such file"
  fi
done < <(
  grep -oHE '@\.claude/[A-Za-z0-9/_-]+\.md' "${sources[@]}" 2>/dev/null | sort -u
)

# --- Assertions 2 and 3: the catalog covers the inventory -----------------

if [ ! -f "$CATALOG" ]; then
  echo "2-3. Skipped — no $CATALOG (expected downstream)"
else
  # A catalog row is a table line whose first cell is a single backticked
  # token: `/skill-name` for a skill, a repo-relative path for anything else.
  mapfile -t row_items < <(
    grep -E '^\|' "$CATALOG" |
      sed -E 's/^\| *`([^`]+)` *\|.*/\1/;t;d' |
      sort
  )

  echo "2. Every skill directory has exactly one catalog row"
  for dir in .claude/skills/*/; do
    name=$(basename "$dir")
    count=0
    for item in "${row_items[@]}"; do
      [ "$item" = "/$name" ] && count=$((count + 1))
    done
    case $count in
      1) ;;
      0) fail "/$name has no row in $CATALOG" ;;
      *) fail "/$name has $count rows in $CATALOG — groups must partition the inventory" ;;
    esac
  done

  echo "3. Every path in a catalog row exists"
  for item in "${row_items[@]}"; do
    case "$item" in
      # A glob row (`scripts/test_*.py`) names a set, not a path, so there is
      # nothing single to stat.
      *\**) continue ;;
      /*) path=".claude/skills/${item#/}" ;;  # `/skill-name`
      *) path="$item" ;;
    esac
    if [ ! -e "$path" ] && [ ! -e "${path%/}" ]; then
      fail "$CATALOG names \`$item\` — $path does not exist"
    fi
  done
fi

# --- Assertion 4: stub markers ---------------------------------------------
#
# A stub carries its status twice: a `> ⚠️ **STUB.**` banner in the body, and the
# word in its frontmatter `description`. They are separate surfaces — the banner
# is what an agent reads on load, the description is what the operator scans in
# the skills list — and hydration means clearing both. One without the other is a
# half-hydrated skill, which is worse than either state: it either advertises a
# working skill that has no procedure, or hides a procedure behind a stub label.

echo "4. Stub markers agree with hydration state"

stubs=()
for dir in .claude/skills/*/; do
  name=$(basename "$dir")
  file="$dir/SKILL.md"
  [ -f "$file" ] || continue

  banner=0
  grep -qE '^>.*\*\*STUB\.\*\*' "$file" && banner=1

  # Frontmatter only: the lines between the opening `---` and its closer. A
  # description can span lines (`description: >-`), so match the block, not one
  # line — and never the body, which may legitimately discuss stubs.
  declared=0
  case "$(awk '/^---[[:space:]]*$/{n++; next} n==1' "$file")" in
    *STUB*) declared=1 ;;
  esac

  if [ "$banner" -ne "$declared" ]; then
    if [ "$banner" -eq 1 ]; then
      fail "/$name carries a STUB banner but its description does not say so — hydrate both or neither"
    else
      fail "/$name is described as a STUB but has no banner — restore it, or clear the description"
    fi
  elif [ "$banner" -eq 1 ]; then
    stubs+=("$name")
  fi
done

if [ ${#stubs[@]} -eq 0 ]; then
  echo "   no stubs present"
elif [ -f "$CATALOG" ]; then
  # The source repo: stubs are the shipped product, listed rather than flagged.
  printf '   %d unhydrated stub(s), expected here: %s\n' "${#stubs[@]}" "${stubs[*]}"
else
  # No catalog means an adopting tree, where a stub is a stowaway: half-following
  # one against a project it was never written for beats not having it only in
  # appearance. Hydrate it (write your commands in, delete the banner, drop STUB
  # from the description) or delete the skill.
  for name in "${stubs[@]}"; do
    fail "/$name is still an unhydrated stub — hydrate it or delete the skill"
  done
fi

# --- Assertion 5: no orphaned colocated page -------------------------------
#
# A page beside a `SKILL.md` that nothing points at is prose no session loads,
# and it fails the way assertion 1's dangling pointer does: the agent follows the
# surviving skill body and never learns the page is there. The page and its
# pointer are separate edits, so assertion 1 catches losing the page and this one
# catches losing the pointer.
#
# The catalog does not count as a reference. It names a page in its skill's row
# — "Carries `carving.md`" — and that is an inventory entry, not a load path, so
# a page the catalog is alone in naming is still one no session can reach.

echo "5. Every colocated skill page is referenced"

for page in .claude/skills/*/*.md; do
  [ -f "$page" ] || continue
  [ "$(basename "$page")" != "SKILL.md" ] || continue

  referenced=0
  while IFS= read -r hit; do
    [ "$hit" = "$page" ] && continue
    [ "$hit" = "$CATALOG" ] && continue
    referenced=1
    break
  done < <(grep -lF "$page" "${sources[@]}" 2>/dev/null)

  if [ "$referenced" -eq 0 ]; then
    fail "$page is referenced by nothing — no session can reach it"
  fi
done

# --- Report ---------------------------------------------------------------

echo
if [ "$failures" -eq 0 ]; then
  echo "check-skill-catalog: OK"
  exit 0
fi
echo "check-skill-catalog: $failures failure(s)" >&2
exit 1
