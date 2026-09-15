> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# Drop the catalog rows for files a skill already carries

Closes #72.

## The rule

A catalog row exists to record a **decision an adopter makes**. A file that lives
inside `.claude/skills/<name>/` carries no such decision: the skill directory is
the unit of copying, so taking the skill takes the file and declining the skill
declines it. Where such a file diverges from that default — it must be rewritten,
or it must *not* travel — the divergence belongs on the skill's own row or in the
skill's own prose, which is where the adopter is already reading.

**The criterion is physical co-location, not conceptual ownership.**
`scripts/check-merge.sh` is the implementation of `/check-merge` and keeps its
row, because copying `.claude/skills/check-merge/` does not bring it along. "Take
the skill, take its files" only holds for files the skill directory actually
contains.

The tree already agrees in three places, which is what makes this a correction
rather than a new policy:

- `.claude/skills/audit-github-backlog/analyst-rules.md` and
  `.claude/skills/plan/exit-dialog.md` sit inside skill directories with no rows,
  and nothing is worse for it.
- `.claude/voice/operators/vzakharov.md` has no row either; its divergence rides
  the parent's disposition — `adopt — **rewrite its `operators/` entries**`. That
  is the exact shape the watermark should have had.

## Rows dropped

| Row | Group | Why it goes |
| --- | --- | --- |
| `.claude/skills/plan/carving.md` | G2 | Travels inside `.claude/skills/plan/`. Nothing to decide. |
| `.claude/skills/update-muthur/watermark.json` | G0 | Travels inside `.claude/skills/update-muthur/`. Its divergence is real and moves to `/update-muthur`'s disposition. |
| `docs/plans/*` | Never | Not muthur's and not declinable — a working artifact of the branch it was cloned from. #72's original ask. |
| `docs/remove-before-merging/*` | Never | Same. |

The two `docs/*` rows fail the rule for a second reason worth stating once: an
adopter's `watermark.json` records a `declined` map of path → why-not, and
`"docs/plans/*": declined` cannot be written truthfully. It reads as declining
the `/plan` lifecycle, which the adopter is taking.

## The row that stays, and why

**`.claude/skills/update-muthur/catalog.md` keeps its `never` row.** With the rule
above in force it becomes the one file in the tree for which the default is
*wrong*: it sits inside a skill directory, so the skill copy brings it along, and
that is precisely what must not happen. Non-travel is a divergence, and the
**Never** table is where non-travel is recorded. `ADOPTING.md` Step 4 already
cites the `#never` anchor for this exact carve-out.

Its ⛔ banner is the enforcement, not a reason to drop the row — the banner
catches an adopter who already copied the file, the row is what stops them.

## Facts to rehome

Nothing a dropped row carried may be lost.

1. **The watermark's `rewrite`-ness.** `/update-muthur`'s row disposition becomes
   `adopt — **rewrite the watermark**`, matching the `adopt — **…**` form already
   used by `CLAUDE.md`, `.claude/voice/`, `.gitignore`, `install-deps.sh`,
   `lib.sh` and `.claude/settings.json`. § "Three dispositions, not two" loses its
   second `rewrite` member, so its "Exactly two files qualify" sentence is
   rewritten around `scripts/vet.sh` alone. The *why* — a placeholder SHA halts
   the skill, a foreign `adopted` set under-filters silently — already lives in
   full in `/update-muthur` § "Never sync the watermark file itself" and
   `ADOPTING.md` § "Hydrate the sync stub"; G0's own prose already says hydrating
   the skill *is* filling in the watermark. No fact needs writing anywhere new.
2. **`carving.md`'s closure, which is the one thing genuinely at risk.** Its row
   is the only place recording that the carve conditionally pulls in
   `/propose-issue` (G3). `/plan` and `/go` both reach `carving.md`, so both rows
   absorb it:
   - `/plan` Pulls in: drop `carving.md`, add `/propose-issue` to the conditional G3 clause.
   - `/go` Pulls in: same.
   § "Closure is not optional"'s `carving.md` bullet is prose about declining G3,
   not a row — it stays untouched.
3. **The Never section's framing.** "**The last two rows should not exist in a
   clone at all.**" and its paragraph collapse to the standing warning #72 asks be
   kept: seeing `docs/plans/` or `docs/remove-before-merging/` in your clone means
   you are looking at working state, not the product. The intro's clause "or a
   working artifact from someone else's branch" goes with the rows — a polar bear
   once nothing in the table is one.

## Files touched

- **`.claude/skills/update-muthur/catalog.md`** — four rows out, three sections
  reworded (§ "Three dispositions", G0 prose, § "Never"), two Pulls-in cells
  amended.
- **`scripts/check-skill-catalog.sh`** — assertion 3's glob branch exists solely
  for the two `docs/*` rows: an eight-line comment plus a tree-parent fallback
  that asserts a swept tree's parent instead of the tree. With no glob row left it
  is dead machinery explaining an accommodation for rows that are gone. Remove the
  tree-parent case and its comment; keep a one-line skip for any glob (a glob
  names no single path to assert) rather than leaving a future glob row to stat a
  literal `*`. Header comment's assertion-3 clause loses its working-artifact half.
- **`ADOPTING.md`** — § "Hydrate the sync stub" links the watermark to the
  `#three-dispositions-not-two` anchor, which will no longer name it. Repoint to
  `#g0--the-sync-path`. The § "Vetting"/`vet.sh` citation of the same anchor is
  unaffected and stays.
- **`README.md`** — no change. Its G0 row already says "ships as a stub; hydrating
  it is filling in the watermark", which survives the sweep intact.

## Verification

`./scripts/vet.sh` — which runs `check-skill-catalog.sh`, so assertions 2 and 3
prove the edited table still covers every skill and names only paths that exist.
Assertion 2 is unaffected by construction: no row for a `/skill` is dropped.

## DRY notes

- **The four dropped rows are duplication, which is the finding.** Each restates
  something already true elsewhere: `carving.md`'s row duplicates `/plan`'s
  directory contents, the watermark's duplicates `/update-muthur` § "Never sync
  the watermark file itself" *and* `ADOPTING.md` § "Hydrate the sync stub", and the
  two `docs/*` rows duplicate the paragraph standing directly above them. Deleting
  the rows is the deduplication; nothing is extracted.
- **No new abstraction, and deliberately so.** The obvious move — a "files that
  travel with their skill" note explaining the rule — would be a fourth statement
  of a default that is now simply true of the table. The rule is enforced by the
  table's contents, not by prose about them. `scripts/check-skill-catalog.sh`
  assertion 2 already machine-checks the half that matters (one row per skill);
  the inside-a-skill-dir half needs no assertion because the failure mode it would
  catch — a redundant row — is what this change removes.
- **The one genuine reuse call is `carving.md`'s Pulls-in cell**, and it is
  duplicated rather than shared: the same `**conditionally** /propose-issue (G3)`
  clause lands on both `/plan` and `/go`. Extracting it is not available — the
  column is a per-row cell and its whole purpose is to be resolvable from one row
  without reading others. Two copies is the format working as designed, the same
  way `**conditionally** /take-issue (G3)` already appears on four rows.
- **`ADOPTING.md`'s two citations of `#three-dispositions-not-two` are not one
  fact cited twice.** One is about `vet.sh`, one about the watermark; only the
  second moves. Repointing both would be the DRY-shaped mistake here.
