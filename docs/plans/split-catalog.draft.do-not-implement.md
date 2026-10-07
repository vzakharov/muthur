> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# Split `.claude/skills/update-muthur/catalog.md` into parts

## Why

The catalog is 510 lines and every new row lengthens it (G10 just added 14). It is
read two ways — whole, by a person adopting a subset, and **one row at a time**, by
`/update-muthur` Step 4a when a commit adds a skill or an opt-in path — and the
second reader pays for the first's shape. It is also past CLAUDE.md's ~450-line
rule of thumb, and a row added in two concurrent syncs conflicts in one file.

## Shape (recommended, one approach)

`catalog.md` stays where it is and becomes the **index**; the rows move to
`catalog/`, one file per group.

- **`catalog.md` keeps** the never-vendored banner, the intro, "How to read a row",
  "Three dispositions", the Groups table (each group name now links to its part),
  "Closure is not optional", "Reverse closure" and "Keeping this file honest" —
  about 200 lines, all of it prose that is read whole.
- **`catalog/` holds** `g0-sync-path.md`, `g1-prose-principles.md`,
  `g2-pr-loop.md`, `g3-issue-backlog.md`, `g4-remote-plumbing.md`,
  `g5-ci-landing.md`, `g6-stack-stubs.md`, `g7-cost-ledger.md`,
  `g8-context-budget.md`, `g9-cold-cache.md`, `g10-cache-keepalive.md` and
  `never.md`. Each opens with a one-line banner (part of the catalog, never
  vendored), then the group's own intro prose and its table, **moved verbatim**.
- **The index keeps its path.** Everything that decides "is this the source
  repo?" globs `.claude/skills/*/catalog.md` or tests that one file —
  `/detemplate`, `/spinoff`, `check-skill-catalog.sh`, `check-muthur.sh`,
  `check-repo-identity.sh`, root CLAUDE.md's stub banner — so none of them, and
  not CLAUDE.md, changes.

## Steps

1. **Move, then fix the check, in one commit** (they only make sense together:
   the vet run fails the moment rows leave `catalog.md`). Cut each group's
   section out of the index into its part with a throwaway script under `tmp/`
   (a pure move across a dozen files is the case the shell is better for), write
   the Groups table links, and prove the move was lossless: the multiset of table
   rows across `catalog.md` + `catalog/*.md` equals the original's, `git diff
   --color-moved` shows only moves. In the same commit,
   `scripts/check-skill-catalog.sh` reads rows from `catalog.md` and
   `catalog/*.md` through one `CATALOG_FILES` list (assertions 2–3), and
   assertion 5's "the catalog is not a reference" exemption covers the parts too.
2. **Repoint every anchor into a part.** In-index links to a group section
   (`#g6--stack-stubs`, `#never`, …) become `catalog/<part>.md`; the ~12 links in
   `ADOPTING.md` and the ones in `docs/adopting/sync.md` and `web-remote.md` move
   with them, and links from a part to the index (`#closure-is-not-optional`,
   `#three-dispositions-not-two`) become `../catalog.md#…`. Anchors that stay in
   the index (`#three-dispositions-not-two`, `#closure-is-not-optional`) are left
   alone.
3. **Say where a row lives, where readers are told to read one.** `/update-muthur`
   Step 4a reads "the new skill's row in the source's `catalog.md`": it now names
   the lookup — `grep -n '^| `/<name>`' catalog.md catalog/*.md` — and an opt-in
   path is found the same way. The never-vendored carve-out grows from the file
   to the directory wherever it is stated (`ADOPTING.md`'s copy step,
   `/update-muthur`, `/spinoff`, `/detemplate`'s "delete the catalog first", the
   `Never` row for `catalog.md`), and `.claude/skills/CLAUDE.md`'s sentence about
   the row-per-skill check names both locations.
4. **Vet and read the result as the two readers do**: `./scripts/vet.sh`; then
   open `catalog.md` as an adopter (is it still a readable whole?) and pull one
   skill's row and one opt-in row the way Step 4a now says to.

## DRY notes

- **Shared, not duplicated:** the row grammar — one table line whose first cell is
  a single backticked token — is parsed in exactly one place, the check script,
  which gains a file list rather than a second parser. The never-vendored banner
  is one line repeated in twelve parts; extracting an include would cost more than
  the line, and the check script already fails a part that loses its pointer
  because nothing else reaches it.
- **Reused:** assertions 2 and 3 and the anchor links keep their existing logic;
  nothing new is written to find rows.
- **Not extracted:** the "How to read a row" columns table is not repeated in each
  part — each part's table repeats only its header row, the one thing a reader
  of a part alone needs.

## Decisions (answer tersely; the plan holds the recommendation)

1. **Parts per group (recommended) or per theme?** a. One file per group, anchors
   map 1:1 and a new group is a new file. b. Three files — core G0–G6, opt-in
   G7–G10, never — fewer files, but the core file stays ~280 lines and a row
   edit still conflicts across unrelated groups. Rejected: a split of rows from
   prose only (two files), which leaves the rows file at ~330 lines.
2. **Parts under `catalog/` (recommended) or as `catalog-g<N>.md` siblings?**
   a. A subdirectory, so the skill directory's own pages stay readable at a
   glance and assertion 5's `*/*.md` scan does not see them. b. Siblings — no
   new directory to carve out of the copy steps, at the price of a dozen files
   beside `SKILL.md`.

## Out of scope

Rewording any row, regrouping skills between groups, or changing the
dispositions. The split is a move; the only text it adds is the banners, the link
targets and Step 4a's lookup line.
