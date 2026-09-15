# Picking the working file when neither is on disk

Loaded by `@.claude/skills/squash-message/SKILL.md` Step 2 when
`docs/remove-before-merging/squash-message.md` is **not** on the branch. Absence
has two causes, and the PR's draft state tells them apart.

## Draft PR — nothing has been created yet

A **draft** PR has not been through a finalize, so absence means not-yet-created:
make `docs/remove-before-merging/squash-message.md` (create the tree; it carries
no `.gitkeep`, since `git rm -r` is the sweep). This is the first creation, at
PR-open. Step 5 commits and pushes it.

## Ready PR — a finalize may already have swept it

On a PR that is already **ready**, absence means one of two things and git
history tells them apart. If the branch ever carried the file, a finalize swept
it — so **restore it** instead of starting over:

```bash
P=docs/remove-before-merging/squash-message.md
DEL=$(git log --diff-filter=D -1 --format=%H -- "$P")
mkdir -p "$(dirname "$P")" && git show "$DEL^:$P" > "$P"
```

The sweep ends the doc's life on the branch, not its history, so the last text it
reached is still the starting point — which is what matters when an
operator-initiated `/check-merge` finds an advanced base carrying something the
record should mention. Step 5's restored-file bullet governs what happens to it
afterwards: committed, pushed, then swept again before the turn ends.

## No history either — compose fresh in `tmp/`

If history has nothing, the branch never had the file: a bare `/squash-message`
on a branch no PR-opening lane ever ran on. Use `tmp/squash-message.md`
(`mkdir -p tmp`; `tmp/` is gitignored), which Step 5 `rm`s — with nothing prior
on disk, that path composes fresh every time.
