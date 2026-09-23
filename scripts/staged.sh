#!/bin/bash
# Stage edits to always-loaded files, and swap them back in at /finalize.
#
#   staged.sh stage <path>...   copy each file, unchanged, to a staged copy
#   staged.sh swap              put every staged copy back over its real file
#   staged.sh check [--empty]   hold the manifest and the directory to each other
#   staged.sh resolve <path>    print the staged copy's path if <path> is staged
#   staged.sh list              print "<real path>\t<staged copy>" per staged file
#
# Why: a file rendered into the prefix of every request (`.claude/rules/staging.md`
# defines the set) invalidates the prompt cache of every session on the branch
# each time it is edited. So the edits go to a copy under
# `docs/remove-before-merging/`, which nothing loads, and the real file changes
# once, when `/finalize` runs `swap`.
#
# The manifest, `docs/remove-before-merging/staged.tsv`, is the only mapping:
# one row per copy, `<staged name>\t<real path>\t<blob of the real file when
# staged>`. Nothing is derived from a name after `stage` picks it, and the
# rules and skills name these subcommands rather than the columns.
#
# `swap` merges rather than moves when the real file changed after staging — a
# base merge brought an edit in, or someone edited it in place — because a move
# would silently drop that edit. The recorded blob is the merge base, and a
# conflict is left as markers in the real file, the way `git merge` leaves one.
#
# Neither `stage` nor `swap` commits: each `git add`s its result, and the caller
# writes the commit. `stage`'s commit carries byte-identical copies, so every
# later commit reads as a diff against the original.
#
# Reports every failure rather than stopping at the first.

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

DIR="docs/remove-before-merging"
MANIFEST="$DIR/staged.tsv"
HEADER="# staged name	real path	blob when staged — written by scripts/staged.sh"
failures=0

fail() {
  printf 'staged: %s\n' "$*" >&2
  failures=$((failures + 1))
}

usage() {
  sed -n '4,8s/^# \{0,1\}//p' "$0" >&2
  exit 2
}

# Manifest rows as "name<TAB>path<TAB>blob", comments and blanks dropped.
rows() {
  [ -f "$MANIFEST" ] || return 0
  grep -vE '^(#|[[:space:]]*$)' "$MANIFEST"
}

# `.claude/skills/go/SKILL.md` → `claude-skills-go-SKILL.staged.md`. Leading dots
# go so the copy is never hidden, and `.staged` sits before the extension, so no
# staged name ends in `CLAUDE.md` — a file with that name loads as a nested
# CLAUDE.md on the first read of its directory.
staged_name() {
  local flat base ext
  flat=$(printf '%s' "$1" | sed -E 's#(^|/)\.+#\1#g; s#/#-#g')
  base=${flat##*/}
  if [[ "$base" == *.* ]]; then
    ext=${base##*.}
    printf '%s.staged.%s\n' "${flat%.*}" "$ext"
  else
    printf '%s.staged\n' "$flat"
  fi
}

write_rows() {
  if [ -z "$1" ]; then
    git rm -q -f --ignore-unmatch -- "$MANIFEST" 2>/dev/null
    rm -f -- "$MANIFEST"
  else
    { printf '%s\n' "$HEADER"; printf '%s\n' "$1"; } > "$MANIFEST"
    git add -- "$MANIFEST"
  fi
}

cmd_stage() {
  [ $# -gt 0 ] || usage
  local existing path name
  existing=$(rows)
  mkdir -p "$DIR"
  for path in "$@"; do
    path=${path#./}
    name=$(staged_name "$path")
    if [[ "$path" == "$DIR"/* ]]; then
      fail "$path is inside $DIR — stage the real file, not a working artifact"
    elif [ ! -f "$path" ]; then
      fail "$path — no such file"
    elif ! git ls-files --error-unmatch -- "$path" >/dev/null 2>&1; then
      fail "$path is not tracked — a staged copy is a diff against a committed file"
    elif printf '%s\n' "$existing" | cut -f2 | grep -qxF -- "$path"; then
      fail "$path is already staged"
    elif [ -e "$DIR/$name" ]; then
      fail "$path would be staged as $DIR/$name, which already exists"
    else
      cp -p -- "$path" "$DIR/$name"
      existing=$(printf '%s\n%s\t%s\t%s' "$existing" "$name" "$path" \
        "$(git hash-object -w -- "$path")" | sed '/^$/d')
      git add -- "$DIR/$name"
      printf 'staged: %s → %s\n' "$path" "$DIR/$name"
    fi
  done
  write_rows "$existing"
}

cmd_swap() {
  [ $# -eq 0 ] || usage
  local remaining="" conflicted=() name path blob staged scratch rc
  scratch=$(mktemp -d)
  while IFS=$'\t' read -r name path blob; do
    staged="$DIR/$name"
    if [ ! -f "$staged" ] || [ ! -f "$path" ]; then
      fail "cannot swap $staged over $path — one of them is missing (staged.sh check says which)"
      remaining=$(printf '%s\n%s\t%s\t%s' "$remaining" "$name" "$path" "$blob")
      continue
    fi
    if [ "$(git hash-object -- "$path")" = "$blob" ]; then
      cp -- "$staged" "$path"
      printf 'staged: swapped %s into %s\n' "$staged" "$path"
    else
      if ! git cat-file blob "$blob" > "$scratch/base" 2>/dev/null; then
        fail "$path changed since it was staged, and its staged-from blob $blob is gone — merge $staged into it by hand"
        remaining=$(printf '%s\n%s\t%s\t%s' "$remaining" "$name" "$path" "$blob")
        continue
      fi
      cp -- "$staged" "$scratch/merged"
      git merge-file -L "$path (staged)" -L "$path (when staged)" -L "$path (current)" \
        "$scratch/merged" "$scratch/base" "$path"
      rc=$?
      if [ "$rc" -lt 0 ] || [ "$rc" -gt 127 ]; then
        fail "git merge-file failed on $path"
        remaining=$(printf '%s\n%s\t%s\t%s' "$remaining" "$name" "$path" "$blob")
        continue
      fi
      cp -- "$scratch/merged" "$path"
      if [ "$rc" -eq 0 ]; then
        printf 'staged: swapped %s into %s, merging what changed there since staging\n' "$staged" "$path"
      else
        conflicted+=("$path")
      fi
    fi
    git rm -q -f -- "$staged"
    git add -- "$path"
  done < <(rows)
  rm -rf -- "$scratch"
  write_rows "$(printf '%s' "$remaining" | sed '/^$/d')"
  if [ ${#conflicted[@]} -gt 0 ]; then
    fail "conflicts left in ${conflicted[*]} — resolve the markers, then git add and commit"
  fi
}

cmd_check() {
  local empty=0
  case "${1-}" in
    --empty) empty=1 ;;
    "") ;;
    *) usage ;;
  esac
  local listed="" name path blob f
  while IFS=$'\t' read -r name path blob; do
    if [ -z "$name" ] || [ -z "$path" ] || ! [[ "$blob" =~ ^[0-9a-f]{40}([0-9a-f]{24})?$ ]]; then
      fail "$MANIFEST has a malformed row: $name	$path	$blob"
      continue
    fi
    listed=$(printf '%s\n%s' "$listed" "$name")
    [ -f "$DIR/$name" ] || fail "$MANIFEST lists $DIR/$name, which does not exist"
    if [ ! -f "$path" ]; then
      fail "$DIR/$name stands for $path, which does not exist"
    elif [ "$(git hash-object -- "$path")" != "$blob" ]; then
      printf 'staged: note — %s changed since it was staged; swap will merge it\n' "$path" >&2
    fi
    [ "$empty" -eq 0 ] || fail "$path is still staged as $DIR/$name — run scripts/staged.sh swap"
  done < <(rows)
  while IFS= read -r f; do
    fail "$f is staged more than once in $MANIFEST"
  done < <(rows | cut -f2 | sort | uniq -d)
  while IFS= read -r f; do
    fail "$DIR/$f is listed more than once in $MANIFEST"
  done < <(rows | cut -f1 | sort | uniq -d)
  if [ -d "$DIR" ]; then
    while IFS= read -r f; do
      f=${f#"$DIR"/}
      printf '%s\n' "$listed" | grep -qxF -- "$f" ||
        fail "$DIR/$f is not in $MANIFEST, so no swap would carry it — add its row or delete it"
    done < <(find "$DIR" -maxdepth 1 -type f \( -name '*.staged.*' -o -name '*.staged' \) | sort)
  fi
}

# Compared with `-ef`, so `./CLAUDE.md` or a `../../CLAUDE.md` link target
# matches the row naming `CLAUDE.md`.
cmd_resolve() {
  [ $# -eq 1 ] || usage
  local name path blob
  while IFS=$'\t' read -r name path blob; do
    if [ "$1" -ef "$path" ]; then
      printf '%s\n' "$DIR/$name"
      return
    fi
  done < <(rows)
  printf '%s\n' "$1"
}

cmd_list() {
  [ $# -eq 0 ] || usage
  rows | awk -F'\t' -v d="$DIR" '{ print $2 "\t" d "/" $1 }'
}

[ $# -gt 0 ] || usage
sub=$1
shift
case "$sub" in
  stage) cmd_stage "$@" ;;
  swap) cmd_swap "$@" ;;
  check) cmd_check "$@" ;;
  resolve) cmd_resolve "$@" ;;
  list) cmd_list "$@" ;;
  *) usage ;;
esac

[ "$failures" -eq 0 ]
