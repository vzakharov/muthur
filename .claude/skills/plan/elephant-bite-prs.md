# Bites as PRs of their own

Loaded beside `@.claude/skills/plan/elephant.md` unless
`MUTHUR_ELEPHANT_BITE_PRS` is `off` (`printenv MUTHUR_ELEPHANT_BITE_PRS`).

The elephant's PR, based on the repo's default branch, is the whole elephant and
lands it in one merge. Every bite after the first is a PR of its own based on
the elephant's branch and squash-merged into it, so each bite's commits and
review threads stay off the elephant's PR and are reviewed one bite at a time.

## Where a bite is built

**The first bite is built on the elephant's branch**, where the plan was
approved. **A later bite gets a branch of its own, made before `/go` Step 1's
flip**, so the flip and everything after it land on the bite's branch while the
elephant's branch keeps the plan `*.paused.md`:

1. **The previous bite has landed.**
   `gh pr list --base <elephant branch> --state open` lists nothing; an open PR
   there means stop and report it. Until that PR squashes in, the elephant's
   plan still reads as it stood before that bite, and a bite built on it builds
   on a plan that is already out of date.
2. **Branch** `<elephant branch>-bite-<nn>` off the elephant's fetched head,
   `<nn>` two digits: the count of PRs ever based on the elephant's branch plus
   two, the first bite having none —
   `gh pr list --base <elephant branch> --state all --json number --jq length`.
3. **Flip, push, and open the draft PR before building** — `/go` Step 1's flip,
   then `@.claude/skills/pr/SKILL.md`, whose `<base>` for a bite is the
   elephant's branch — so a session checking step 1 sees this bite from its
   first commit.

The bite's plan edits — `## This bite`, its fold into `## Eaten so far`, the
pause — ride its PR, and the elephant's branch takes them with the squash. Its
working files go in its own folder (`scripts/working-dir.sh`), apart from the
elephant's it inherits. The pause's handoff block names the elephant's branch,
and says the bite's PR lands first.

## Landing a bite

A bite's PR lands without `/finalize`: the sweeps, the staged swap, the squash
record and the attestation are the elephant's finalize's, run once over
everything its bites landed. What the next bite needs is a branch it can build
on, polished as far as it goes:

1. **`/polish` on the bite's head** (`@.claude/skills/polish/SKILL.md`), scoped
   from its floor, so a review round after `/go`'s own pass is covered; on a
   bite with none it is an empty `polish: nothing to change`.
2. **`./scripts/vet.sh` green on the bite's head**, with the elephant's branch
   merged in first when it moved (`@.claude/skills/sync-branch/SKILL.md`).
3. **On the operator's ask, squash-merge into the elephant's branch** under the
   PR's title, its working files included — they go at the elephant's sweep.
4. **Mark the elephant's branch polished**, straight on top of the squash with
   nothing between:

   ```bash
   git fetch origin <elephant branch> && git checkout <elephant branch> &&
     git merge --ff-only origin/<elephant branch> &&
     git commit --allow-empty -m 'polish: #<bite PR> landed polished' &&
     git push origin <elephant branch>
   ```

   The squash commit carries the PR's title, not `polish:`, so without the mark
   it sits above the elephant's floor (`@.claude/skills/polish/passes.md` § "The
   floor") and the elephant's `/finalize` re-reads every bite at once. Under the
   mark everything was polished — the first bite on the elephant's branch, each
   later one on its own.

**`/finalize` on the elephant's PR comes once, after its last bite has landed**,
and sweeps every bite's working folder with the elephant's.
