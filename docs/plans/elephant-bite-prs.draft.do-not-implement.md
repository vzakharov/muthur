> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# Elephant bites as child PRs

Port the elephant rework from vzakharov/vovazakharov.com#169 (branch
`claude/multi-app-sliced-design-7bn3oq`): every bite after the first is a PR of
its own, based on the elephant's branch and squash-merged into it, so its
commits and review threads stay off the elephant's PR. The elephant's own PR
still lands everything on the trunk in one merge.

`MUTHUR_ELEPHANT_BITE_PRS=off` turns it off, leaving today's one-PR elephant:
the same `elephant.md` and `/go` text as now, the working files at today's flat
paths.

## What the adopter has, and what travels

- **Travels**: `scripts/working-dir.sh` (a working directory per branch, so a
  bite stops overwriting the elephant's squash draft and reading its relays),
  its callers in `/squash-message`, `/relay` and
  `scripts/check-squash-message.sh`, `/branch-rename` moving the folder,
  `elephant.md` § "Landing a bite", `/finalize` handing a bite's PR to it.
- **Stays there**: § "Unattended runs" (`megabeast/notes`, the adopter's own, as
  its `divergence.md` records), and the unrelated drift on that branch — the
  site-scoped squash title, push-before-vet, the plan handoff, the subagent
  budget notice.
- **Written here, since the adopter keeps it in its plan file**: how a bite gets
  its branch and PR, and that a bite waits for the previous one to land — its
  plan's § "How this elephant is eaten".

## Changes

1. `scripts/working-dir.sh` — the adopter's, plus the switch: `off` prints
   `docs/remove-before-merging` itself. `scripts/test_working_dir.py` covers the
   prefix strip, a named branch, the switch, and a detached HEAD.
2. `/squash-message` (`SKILL.md`, `working-file.md`),
   `scripts/check-squash-message.sh`, `/relay` — the fixed path becomes
   `$(scripts/working-dir.sh)/…`, as in the adopter.
3. `/branch-rename` — moves the folder, skipping when old and new are the same
   path (always, with the switch off).
4. New `.claude/skills/plan/elephant-bite-prs.md`: where a bite is built (first
   bite on the elephant's branch, later ones on `<elephant branch>--bite-<nn>`
   off it), the wait for the previous bite's PR, `/pr` basing the PR on the
   elephant's branch, the plan edits riding the bite's PR, and § "Landing a
   bite".
5. `elephant.md` — one pointer, in § "Taking a bite": unless the switch is
   `off`, load the new file. Nothing else in it changes.
6. `/finalize` — a PR based on an elephant's branch runs § "Landing a bite"
   instead, unless the switch is `off`. `/pr` — a bite's `<base>` is the
   elephant's branch.
7. Catalog (`g2-pr-loop.md`) and `tend-prose`'s path mention follow.

## `/polish` on squashed bites — in scope

Each bite is polished on its own branch, but its squash lands on the elephant's
branch under the PR's title, not `polish:`, so it sits above the elephant's
floor and the elephant's `/finalize` re-reads every bite — on an elephant that
is the whole job, likely past what one subagent can hold.

Fix: landing a bite polishes its head first (scoped from its floor, normally an
empty `polish: nothing to change`), and right after the squash-merge commits an
empty `polish: #<bite PR> landed polished` on the elephant's branch. Everything
below that commit was polished — bite 1 on the branch itself, each later bite on
its own — so the existing lookup in `polish/passes.md` § "The floor" finds it
unchanged; that section gains one sentence saying this marker is the one
`polish:` commit no run made.

## DRY notes

- **One helper for the path**: `working-dir.sh` is the only place that knows the
  working directory's shape and reads the switch for it; every caller calls it
  rather than spelling the path or the switch.
- **The switch is read in three places** — the script, `elephant.md`'s pointer,
  `/finalize`'s pointer. A shared reader (a hook delivering the file, as
  `go-delegation.py` does) would cost a hook and tests for a file that loads
  only on an elephant; `printenv` in prose is what `/go` already does for
  `MUTHUR_DELEGATION` under a hookless harness.
- **No new floor mechanism**: the landing marker reuses the `polish:` subject,
  so `passes.md`'s lookup and `/polish full` work on it as they are.
