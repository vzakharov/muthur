# Stage edits to always-loaded files, swap them in at `/finalize` (#100)

#98 staged its `CLAUDE.md` edit by hand, and the procedure lived only in its plan and PR body. This makes it part of the loop: a rule that fires whenever an always-loaded file is about to be edited, a script that owns the mechanics, and a `/finalize` step that swaps the copies in before anything reads the tree.

## The always-loaded set

What makes a file cost the cache is that its text is rendered into the **prefix** of every request, so an edit rewrites everything after it. Text that enters the conversation at some turn is appended there, and editing its source invalidates nothing before it. So the set is defined by that mechanism, not by a list:

- **In:** the root `CLAUDE.md` and every file it `@`-imports, transitively (today `.claude/voice/voice.md`); every `.claude/rules/*.md` with no `paths:`; a skill's frontmatter `description:`, which sits in the skill listing. A skill **body** loads on invocation, so a body-only edit goes in place — only a change to the `description:` stages the `SKILL.md`.
- **Out:** a nested `CLAUDE.md`, which arrives as an attachment on the first read of its directory, i.e. appended; and hook output such as the `operators/` entry `operator-voice.sh` prints at `SessionStart`, which an edit changes only for the next session, and that one has no cache to lose.

The staged copy's own name is kept out of the loading mechanisms too: it never ends in `CLAUDE.md` (a nested `CLAUDE.md` loads on the first read of its directory) and it lives under `docs/remove-before-merging/`, which no `paths:` glob names.

## Mechanics: `scripts/staged.sh`

One script, so the rule, `/finalize` and the vet run share one implementation. The mapping lives in a manifest, `docs/remove-before-merging/staged.tsv`, one row per staged file: `<staged name>\t<real path>\t<blob the real file had when staged>`. Nothing is ever derived from a file name.

- **`stage <path>…`** — refuses a path that is untracked, missing, or already staged. Copies the file byte-identical to `docs/remove-before-merging/<name>.staged.<ext>`, where `<name>` is the path with `/` → `-` and leading dots stripped (`CLAUDE.md` → `CLAUDE.staged.md`, `.claude/skills/finalize/SKILL.md` → `claude-skills-finalize-SKILL.staged.md`), appends the manifest row, and `git add`s both. The caller commits; that commit carries an unchanged copy, so every later commit reads as a diff against the original.
- **`swap`** — for each row, puts the staged content over the real path and removes the staged file and the row; deletes the manifest when it empties. **If the real file has moved since staging** (its blob differs from the recorded one — a base merge brought an edit in, or someone edited it in place), a blind move would silently drop that edit, so the swap does a three-way `git merge-file` (staged ← recorded blob → current real file) and stops with conflict markers left in the real file for the agent to resolve. `git add`s the result; the caller commits.
- **`check`** — structural, offline, silent when there is no manifest: every row's staged file and real path exist, no real path is listed twice, and no `*.staged.*` sits in the directory without a row. Also reports (without failing) a row whose real file has moved since staging, so a mid-branch vet shows the merge the swap will have to do. **`check --empty`** additionally fails when anything is staged at all — the guard the sweep runs.
- **`resolve <path>`** — prints the staged path when `<path>` is staged, else `<path>`. `check-skill-catalog.sh` assertion 6 reads a cited `CLAUDE.md` through it, so a skill citing a section that exists only in the staged copy does not fail a mid-branch vet (`/sync-branch` runs one), and one citing a section the staged copy removed does.

- **`list`** — prints `<real path>\t<staged copy>` per row, for a reader that needs the pairs (`/polish`, below) without reading the manifest's columns.

Tested by `scripts/test_staged.py` against throwaway git repos: stage/swap round-trip, the refusals, a swap after the real file moved (clean merge and conflict), each `check` failure, `resolve`. It joins `check-muthur.sh` by matching `scripts/test_*.py`.

## Where the rule lives

- **`CLAUDE.md`** gets the rule in one sentence, since it must hold on a turn where no skill is loaded — whoever is about to edit `CLAUDE.md` is the reader: *on a branch, edit an always-loaded file only through a staged copy (`scripts/staged.sh stage`), which `/finalize` swaps in*, with a pointer to the rule file. It goes in § "About this file", which is where the reader editing this file is already looking.
- **New `.claude/rules/staging.md`** is the home of everything else: the set above, the naming constraint, the first-commit-unchanged convention, that the vet run and reviewers read the change in the commits after the staging commit. Its `paths:` are the always-loaded files themselves plus `docs/remove-before-merging/**`, so it arrives exactly when one of them is opened.
- **`.claude/rules/skills.md`** gets one line: a change to a skill's `description:` is an always-loaded edit — stage the `SKILL.md`. That file already loads on every skill edit, which a `SKILL.md` glob in `staging.md` would duplicate on every skill read.
- **`.claude/rules/README.md`** — its "a file with no `paths:` loads on every turn" sentence gets a pointer to `staging.md`.

## `/finalize`

- **A new first thing, before the quality passes:** `scripts/staged.sh swap` and commit (`chore: swap the staged always-loaded files into place`), resolving any merge it stops on. Before the passes because `/polish` should read the real files, and before the vet run because its checks read them. It carries no step number, like the quality passes, so citations of the numbered steps stay put. `no vet` does not skip it.
- **The step-6 sweep of `docs/remove-before-merging/`** runs `scripts/staged.sh check --empty` first, and a failure means swap, never delete.
- **Step 8's `and merge` predicate** counts the swap among the run's mechanical effects, like the sweep — unless it stopped on a conflict, which is a decision and stands the merge down.

## `/polish`

At `/go` a staged copy is a whole new file in `origin/<base>...HEAD`, so the passes would read all of `CLAUDE.md` as this branch's prose. `/polish` § "Scope" says a copy counts by `git diff --no-index <real> <copy>` over the pairs `staged.sh list` prints. At `/finalize` the swap has already run, so the range is ordinary.

## The vet run

`scripts/vet.sh` runs `scripts/staged.sh check`, and its header gets an entry beside the other non-stack lines. It does **not** check whether the PR is ready for review: that needs GitHub, and vet is a fast offline run. The guarantee that a staged copy never lands comes from `/finalize`'s ordering (swap first, `check --empty` before the sweep) rather than from a vet line.

## Dogfooding

This branch edits `CLAUDE.md`, so it stages it through the new script: the script lands first, then `stage CLAUDE.md` in its own commit, then the edit on the staged copy. The branch's `/finalize` is the new one (the `finalize` `SKILL.md` body is edited in place — its description does not change), so it swaps its own copy in.

## Catalog

`update-muthur/catalog.md`: the `.claude/rules/` row names the third rule; a new row for `scripts/staged.sh` in G2 beside `/finalize`, its only non-vet caller (`bash`, `git`); the `scripts/vet.sh` row lists it under what it pulls in.

## Order

1. `scripts/staged.sh` + `scripts/test_staged.py`.
2. `check-skill-catalog.sh` assertion 6 through `resolve`; `vet.sh` line and header.
3. `.claude/rules/staging.md`, the `skills.md` and `README.md` lines.
4. `stage CLAUDE.md` (own commit), then the `CLAUDE.md` sentence on the staged copy.
5. `/finalize` changes.
6. Catalog rows.

## DRY notes

- **Shared:** every staging operation — the name derivation, the manifest format, the merge — lives in `scripts/staged.sh`, and `/finalize`, the vet run and `check-skill-catalog.sh` call it rather than re-reading the manifest. The rule text names the subcommands, never the manifest's columns.
- **Reused:** `docs/remove-before-merging/` and its existing sweep, rather than a new working-artifact directory with a sweep of its own; `git merge-file` for the three-way merge; `check-muthur.sh`'s `test_*.py` glob, so no vet edit for the test.
- **One home for the set:** `staging.md`. `CLAUDE.md` states only the rule, `skills.md` only the skill case, `README.md` only a pointer — each is the thing its reader needs at that moment, not a restatement.
- **Not extracted:** the finalize swap and sweep guard stay two call sites of the script rather than one "finalize-staging" subcommand, because they run at different steps for different reasons (swap before the passes, guard before the sweep), and fusing them would hide the ordering the guarantee depends on.
