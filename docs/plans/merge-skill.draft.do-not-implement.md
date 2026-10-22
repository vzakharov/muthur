> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# `/merge` — one entry for "merge this PR"

## The ask

> давай добавим скилл `/merge`: в большинстве случаев (если ещё не
> финализирован) = `/finalize and merge`; если уже финализирован --
> `/check-merge` (мерджит если можно -- по тем же критериям что и
> `/finalize and merge`; в противном случае делает `/sync-branch` и
> останавливается с тем же комментарием что `/finalize and merge` при запрете
> мерджа) (всё DRY, конечно).

And, mid-turn: should `/merge` point at `/finalize and merge`, or the other way
round?

## What exists today, and the gap

An operator's ask to merge has exactly one route: `/finalize and merge`
(`finalize/SKILL.md`'s description and its `and merge` paragraph; `merge.md` §
"The flag"). That route is defined only for a branch **not yet finalized**. A
branch that _is_ finalized — ready for review, its attestation naming the
current head — has no route at all: re-running land prep on it repeats the whole
run to reach a gate that only needs the base checked. `/merge` fills that gap
and becomes the single name for "merge it".

## Which way the references point

Neither direction wholesale; the split follows what each half is about.

- **`/merge` owns the entry**: reading an operator's ask to merge, the
  "finalized?" test, and the routing. `/merge` → `/finalize and merge` for an
  unfinalized branch, as the ask says.
- **`finalize/merge.md` keeps the gate and the click** (§ "Step 8 — the gate", §
  "Merging", § "Standing down"), and `/merge`'s finalized path loads it. The
  gate is written in `/finalize`'s step numbers, because what it judges is a
  land-prep run; a `/merge` on a finalized branch is that same run cut down to
  its step 6 (`/check-merge`, whose squash reconcile is step 5's criterion), so
  the list applies unchanged — the steps that never ran cannot fire.
- **`/finalize and merge` does not route through `/merge`.** Doing so would
  either loop (`/merge` on an unfinalized branch is `/finalize and merge`) or
  judge only the tail of the run, dropping every stand-down the land-prep steps
  themselves produce. The flag stays `/finalize`'s, and `/finalize` points at
  `/merge` only as the name an operator's ask now lands on.

The reverse — moving the gate into `.claude/skills/merge/` and having
`/finalize` step 8 load it — would leave `/merge`'s own file full of another
skill's step numbers, the coupling pointing the wrong way.

## Changes

1. **New `.claude/skills/merge/SKILL.md`.** Invocation
   `/merge [<branch|#PR|PR-url>] [no vet]`; a target attaches first via
   `/from-branch`, as `/finalize` and `/check-merge` do, and `no vet` rides to
   `/finalize` on the unfinalized path. Description claims the "merge",
   "мерджи", "land it" asks, and says "merge main" stays `/sync-branch`'s. Body:
   - **The reply opens by naming the path taken**, as `merge.md` asks of the
     `/finalize and merge` reading today.
   - **Finalized?** — moved here from `merge.md` § "The flag": the PR is ready
     for review and its `<!-- finalize-attestation -->` marker names the current
     head, give or take what `/finalize` step 7's last rule lets ride past it.
   - **Not finalized → `/finalize and merge`**, forwarding `no vet`. The "an ask
     that also requests changes holds the merge" rule moves here with it.
   - **Finalized → `/check-merge` once**, then:
     - `contained` → walk `merge.md`'s gate over this run (its step 5 and step 6
       entries, and "Anywhere" — the unanswered-feedback export and any point
       where you would have asked), **plus the attestation itself**: a body
       reporting anything short of green — a red vet, a skipped dispatch, the
       two-shot rule — is what the land-prep run would have stood down on, so it
       stands this one down too. Pass → `merge.md` § "Merging" (the attestation
       is already up). Fail → § "Standing down".
     - `advanced` → `/sync-branch` (vet included), let `/check-merge` Step 3
       reconcile the squash record on the merged head, then stand down per
       `merge.md` § "Standing down", naming step 6 as the condition. What clears
       it is `/merge` again: the head is now past its attestation, so that run
       is `/finalize and merge`, which verifies the merged head.
     - `merged` / `closed` / `error` → report and stop, as `/check-merge` does.
2. **`finalize/merge.md`.** § "The flag": the operator's-ask paragraph becomes a
   pointer to `/merge`, which owns it now. Header: loaded by `/finalize` under
   `and merge`, and by `/merge` on a finalized branch.
3. **`finalize/SKILL.md`** — the `and merge` paragraph's "an operator's ask to
   merge … is this flag" repoints to `/merge` (body, in place). Its
   **description** carries the same sentence, so it is staged
   (`scripts/staged.sh stage`) and edited there, per `.claude/rules/staging.md`.
4. **`handle/SKILL.md`** § "Argument shape": the held merge's hand-off line
   `/finalize <branch> and merge` becomes `/merge <branch>` — finalize has just
   run, so that lands on the finalized path and skips a second land prep.
5. **Catalog** — a `/merge` entry in `catalog/g2-pr-loop.md` (pulls in
   `/finalize`, `/check-merge`, `/sync-branch`, `/from-branch`), required by
   `scripts/check-skill-catalog.sh`.

`/from-branch <target> merge` starts dispatching `/merge` on its own, since
`merge` now names a skill directory; no edit needed. `CLAUDE.md`'s loop line
(`/finalize` … "on `and merge`, merges") stays true and is left alone.

## DRY notes

- **Reused, not restated:** `merge.md`'s gate list, § "Merging" and § "Standing
  down" — `/merge` cites them by section; `/check-merge` for detection and the
  squash reconcile; `/sync-branch` for the base merge; `/from-branch` for the
  target.
- **Moved, not copied:** the "finalized?" definition and the reading of an
  operator's ask leave `merge.md` for `/merge`; `merge.md` and `/finalize` keep
  pointers.
- **One genuinely new rule:** on the finalized path the attestation's own body
  is part of the gate. In the land-prep run that verdict is formed by the steps
  that wrote it, so the existing list has no entry for it; it is stated once, in
  `/merge`.
- **Declined:** a shared "merge-gate" file outside `/finalize`. Its only reader
  besides `/finalize` is `/merge`, which needs it whole; a third home would be a
  pointer chain with nothing gained.

## Not in scope

- Re-attesting after the `advanced` path's sync. The ask is sync-and-stop; the
  next `/merge` re-finalizes and attests the merged head.
