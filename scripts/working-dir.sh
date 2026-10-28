#!/bin/sh
# Prints the branch's own working directory under `docs/remove-before-merging/`:
# the branch's full name, less the `claude/` prefix the harness gives every
# session branch (`claude/masd-bite-02` → `docs/remove-before-merging/
# masd-bite-02`). Git gives no two branches one name, so no two branches share a
# folder.
#
# A bite branches off an elephant's branch and inherits its working files, so a
# fixed path would make the bite overwrite the elephant's squash draft and take
# the elephant's latest relay for its own; a folder per branch keeps each one's
# files its own. `MUTHUR_ELEPHANT_BITE_PRS=off`, where no bite has a branch of
# its own, prints the shared `docs/remove-before-merging` instead.
# `@.claude/skills/finalize/SKILL.md` says who sweeps them, and
# `@.claude/skills/branch-rename/SKILL.md` moves the folder with a rename.
#
#   scripts/working-dir.sh            # the path, created on demand by callers
#   scripts/working-dir.sh <branch>   # the path for another branch
set -eu

root=docs/remove-before-merging
if [ "${MUTHUR_ELEPHANT_BITE_PRS:-}" = off ]; then
  printf '%s\n' "$root"
  exit 0
fi

branch=${1:-$(git branch --show-current)}
[ -n "$branch" ] || {
  echo "working-dir.sh: detached HEAD — name the branch" >&2
  exit 1
}
printf '%s/%s\n' "$root" "${branch#claude/}"
