#!/bin/bash
# Stage edits to always-loaded files, and swap them back in at /finalize.
#
#   staged.sh stage <path>...   copy each file, unchanged, to .claude/staged/<path>.staged
#   staged.sh swap              put every staged copy back over its real file
#   staged.sh check [--empty]   every staged copy stands for a tracked real file
#   staged.sh resolve <path>    print the staged copy's path if <path> is staged
#   staged.sh list              print "<real path>\t<staged copy>" per staged file
#
# Why: a file rendered into the prefix of every request (`.claude/rules/staging.md`
# defines the set) invalidates the prompt cache of every session on the branch
# each time it is edited. So the edits go to a copy, and the real file changes
# once, when `/finalize` runs `swap`.
#
# The copy of `<path>` is `.claude/staged/<path>.staged`: the path is the whole
# mapping, and the suffix is what keeps the copy from loading. Claude Code picks
# a nested `CLAUDE.md` or `SKILL.md` up by its exact name and a rule by its
# `.md`, so a mirrored copy under either name would load as live instructions —
# a skill's description in every listing — while it is still under review. The
# directory is under `.claude/` because this infrastructure owns that tree, so
# no project using the infrastructure has a `staged/` of its own there.
#
# `swap` merges rather than copies when the real file changed after staging — a
# base merge brought an edit in, or someone edited it in place — because a copy
# would silently drop that edit. The merge base is the real file as it stood in
# the commit that added its staged copy, and a conflict is left as markers in
# the real file, the way `git merge` leaves one.
#
# Neither `stage` nor `swap` commits: each `git add`s its result, and the caller
# writes the commit. `stage`'s commit carries byte-identical copies, so every
# later commit reads as a diff against the original.
#
# Reports every failure rather than stopping at the first.

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

DIR=".claude/staged"
SUFFIX=".staged"
failures=0

fail() {
  printf 'staged: %s\n' "$*" >&2
  failures=$((failures + 1))
}

usage() {
  sed -n '4,8s/^# \{0,1\}//p' "$0" >&2
  exit 2
}

# Real paths with a staged copy, one per line.
staged_paths() {
  [ -d "$DIR" ] || return 0
  find "$DIR" -type f -name "*$SUFFIX" | sed -e "s#^$DIR/##" -e "s#$SUFFIX\$##" | sort
}

copy_of() {
  printf '%s\n' "$DIR/$1$SUFFIX"
}

# The real file as it stood when its copy was staged: in the commit that last
# added the copy, or HEAD while that commit is still to be written. Renames are
# off so a moved copy counts as added where it landed.
base_of() {
  local added
  added=$(git log -1 --no-renames --diff-filter=A --format=%H -- "$(copy_of "$1")")
  git rev-parse --verify --quiet "${added:-HEAD}:$1"
}

cmd_stage() {
  [ $# -gt 0 ] || usage
  local path staged
  for path in "$@"; do
    path=${path#./}
    if [[ "$path" == "$DIR"/* ]]; then
      fail "$path is already inside $DIR — stage the real file"
    elif [ ! -f "$path" ]; then
      fail "$path — no such file"
    elif ! git ls-files --error-unmatch -- "$path" >/dev/null 2>&1; then
      fail "$path is not tracked — a staged copy is a diff against a committed file"
    elif [ -e "$(copy_of "$path")" ]; then
      fail "$path is already staged"
    else
      staged=$(copy_of "$path")
      mkdir -p "$(dirname "$staged")"
      cp -p -- "$path" "$staged"
      git add -- "$staged"
      printf 'staged: %s → %s\n' "$path" "$staged"
    fi
  done
}

cmd_swap() {
  [ $# -eq 0 ] || usage
  local conflicted=() path staged base scratch rc
  scratch=$(mktemp -d)
  while IFS= read -r path; do
    staged=$(copy_of "$path")
    if [ ! -f "$path" ]; then
      fail "cannot swap $staged — $path does not exist"
      continue
    fi
    if ! base=$(base_of "$path"); then
      fail "cannot find $path as it stood when $staged was added — merge it by hand"
      continue
    fi
    if [ "$(git hash-object -- "$path")" = "$base" ]; then
      cp -- "$staged" "$path"
      printf 'staged: swapped %s into %s\n' "$staged" "$path"
    else
      git cat-file blob "$base" > "$scratch/base"
      cp -- "$staged" "$scratch/merged"
      git merge-file -L "$path (staged)" -L "$path (when staged)" -L "$path (current)" \
        "$scratch/merged" "$scratch/base" "$path"
      rc=$?
      if [ "$rc" -gt 127 ]; then
        fail "git merge-file failed on $path"
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
  done < <(staged_paths)
  rm -rf -- "$scratch"
  [ ! -d "$DIR" ] || find "$DIR" -depth -type d -empty -delete
  if [ ${#conflicted[@]} -gt 0 ]; then
    fail "conflicts left in ${conflicted[*]} — resolve the markers, then git add and commit"
  fi
}

cmd_check() {
  local empty=0 path base
  case "${1-}" in
    --empty) empty=1 ;;
    "") ;;
    *) usage ;;
  esac
  while IFS= read -r path; do
    fail "$path is in $DIR without the $SUFFIX suffix, so it loads as the real thing would — stage the real file instead"
  done < <([ ! -d "$DIR" ] || find "$DIR" -type f ! -name "*$SUFFIX" | sort)
  while IFS= read -r path; do
    if ! git ls-files --error-unmatch -- "$path" >/dev/null 2>&1; then
      fail "$(copy_of "$path") stands for $path, which is not a tracked file"
    elif base=$(base_of "$path") && [ "$(git hash-object -- "$path")" != "$base" ]; then
      printf 'staged: note — %s changed since it was staged; swap will merge it\n' "$path" >&2
    fi
    [ "$empty" -eq 0 ] || fail "$path is still staged as $(copy_of "$path") — run scripts/staged.sh swap"
  done < <(staged_paths)
}

# Compared with `-ef`, so `./CLAUDE.md` or a `../../CLAUDE.md` link target
# resolves like `CLAUDE.md`.
cmd_resolve() {
  [ $# -eq 1 ] || usage
  local path
  while IFS= read -r path; do
    if [ "$1" -ef "$path" ]; then
      copy_of "$path"
      return
    fi
  done < <(staged_paths)
  printf '%s\n' "$1"
}

cmd_list() {
  [ $# -eq 0 ] || usage
  staged_paths | awk -v d="$DIR" -v s="$SUFFIX" '{ print $0 "\t" d "/" $0 s }'
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
