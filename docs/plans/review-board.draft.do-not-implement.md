> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# Review board — a code-review artifact on an infinite canvas

## Goal

A reusable, adoptable artifact that reviews a branch the way GitHub's "Files
changed" does, laid out on a pannable, zoomable board, whose line comments go
through the artifact's own comment store so the session that published it is
woken by them and answers them. Dogfooded on this PR.

The ten asks, and where each lands:

1. GitHub-like review on an infinite board → § "The page": camera and gestures
   ported from island-board.
2. Auto-laid nested rectangles (folders → files) → § "Layout".
3. Hide whitespace changes → § "Diff".
4. "Viewed" checkbox per file → § "Per-viewer state".
5. From/to commit, per file → § "Commit ranges".
6. Scrolling diff per file, capped; over the cap, a side panel → § "File card".
7. Line comments through the artifact's comment store, handled by Claude → §
   "Comments".
8. The publishing session watches; on relay it lets go and the successor takes
   over → § "Watches across a relay".
9. Raw data collected by a script, no agent deliberation → § "Collector and
   build".
10. Bare DOM, MASD → § "Where it lives".

## Where it lives

A new opt-in subsystem, **`.claude/artifacts/`** — the home for reusable
artifacts, of which the review board is the first app:

```
.claude/artifacts/
  package.json          # scoped: typescript, esbuild, zod, eslint, typescript-eslint,
  pnpm-lock.yaml        #   eslint-plugin-boundaries, steiger + FSD plugin, madge,
  tsconfig.json         #   @types/node
  eslint.config.ts
  eslint/masd-graph.ts, eslint/masd-boundaries.ts
  steiger.config.ts
  scripts/              # lint-fsd.ts, masd-check.ts (+ README), masd-clusters.ts
  vet.sh                # tsc, eslint, steiger, check:masd, clusters, cycles, node --test
  CLAUDE.md             # the directory's conventions (MASD, the run commands)
  src/masd.json         # { "review-board": [] }
  src/review-board/     # one MASD app = one FSD tree
    shared/{lib,review-data}/
    entities/file/
    pages/board/        # sub-slices: camera, layout, card, panel, comments, toolbar
    app/                # entry, styles
    scripts/            # collect.ts, build.ts
```

- **A `package.json` scoped to the directory, not the root.**
  `scripts/prettier.sh` keeps the root free of one so an adopter's repo is not
  told it is a JS project; a scoped one says nothing about the root, and type
  definitions (`@types/node`) cannot be had through `npx` pins anyway.
- **TypeScript, run by plain `node`** (≥22.18 strips types natively), so scripts
  and tests need no `tsx`; `esbuild` bundles the page.
- **MASD with its whole checker set, ported from vovazakharov.com now**, since
  more artifact apps are coming: `src/masd.json` as the graph,
  `eslint/masd-graph.ts` its only loader, `eslint-plugin-boundaries` config
  generated from it, Steiger run per app root (`lint-fsd.ts`) with its
  overrides, `check:masd` (significance across the composition, sub-slices) with
  its README, `masd:clusters`, and madge's cycle check. Each is ported as it
  stands there, with paths re-rooted and Next.js-only cases cut.
  **`check:poison` is not ported**: its `server-only` / `'use client'` axes are
  Next's, and the one that applies here — a `node:` import reaching the page —
  already fails the esbuild browser bundle. The review board starts as one app;
  the island-board camera and gestures are the likely first `board` parent once
  a second canvas-based artifact arrives, which `check:masd` decides.
- **Its conventions go in `.claude/artifacts/CLAUDE.md`**, a port of
  vovazakharov.com's `.claude/rules/masd.md` minus its Next.js routers, sites
  and traps. A directory bounds it, so per `.claude/rules/README.md` it is a
  nested `CLAUDE.md`, not a rule file.
- **zod via `zod/mini`**, for the page bundle's weight.

## Collector and build

One command, no decisions in it:
`node .claude/artifacts/src/review-board/scripts/build.ts [<out>]` → writes
`tmp/review-board/index.html` (for the Artifact tool) and `local.html` (wrapped,
for a browser off disk), and prints the page's size.

`collect.ts` reads git and nothing else but `gh` for the PR's base:

- **Base**: the PR's `baseRefName` (`gh pr view`), else the default branch;
  `git merge-base origin/<base> HEAD`.
- **Commits**: `git rev-list --first-parent --reverse <base>..HEAD`, each with
  subject, author, date.
- **Files**: `git diff --name-status -M <base> HEAD` (GitHub's file set: the net
  change), binary ones flagged from `--numstat`.
- **Revisions per file**: the base and every commit in range that touched it
  (`git log --format=%H <base>..HEAD -- <path>`, the old path included for a
  rename), each pointing at its blob id.
- **Blobs**: `git cat-file` per distinct blob id, so a file unchanged across
  commits is stored once.

The payload is **content, not diffs**: any from/to pair a viewer picks is diffed
in the page, so the data stays linear in the commits rather than quadratic in
the pairs. Its shape is one `zod/mini` schema in `shared/review-data`, which the
collector writes through and the page parses at load — the boundary the page
validates, and the single source of both sides' types.

The page budget is checked at build: over 8 MB fails with the size, under the 16
MB artifact ceiling.

## The page

### Board

- **Camera**: pan by dragging the background or by wheel, zoom by ctrl/⌘-wheel
  and pinch, Fit / − / + in the toolbar. `toWorld`, `zoomAt`, `fitTo`, `union`
  ported from island-board's `camera.ts`, with their tests.
- **Gestures**: a drag that starts on a diff body scrolls it rather than
  panning; a drag on a card's header or the background pans.

### Layout

The file tree, built from the paths, as nested rectangles:

- **A folder chain with one child collapses** into one rectangle
  (`.claude/skills/review-board/`), as GitHub's tree does.
- **Children are packed into rows** aiming at a 16:10 frame, folders before
  files, each group by name; a folder is its header plus its packed children
  plus padding. Pure and deterministic: same tree, same board — unit-tested.
- **A file's rectangle is its card's measured size** — the layout runs after
  cards render, and again when one changes height (viewed, range, whitespace).

### File card

- **Header**: path, status (added / modified / renamed / deleted), +/− counts,
  the viewed checkbox, and the file's from/to selectors.
- **Body**: a unified diff with old/new line numbers and three lines of context
  around each hunk, scrolling inside a body capped at ~40 lines high.
- **Over 200 changed lines** the body is a stub — "N changed lines — open" — and
  opening it shows the full diff in a **side panel** on the right, its own
  scroll, closable; the board stays live beside it.
- Binary files show a stub with the size change; viewed files collapse to their
  header.

### Diff

- Line-level Myers diff (`shared/lib/diff.ts`), unit-tested against `git diff`
  output on fixtures.
- **Hide whitespace** is a toolbar toggle: lines compare with all whitespace
  removed (`git diff -w`'s semantics), and an equal pair shows its "to" side.

### Commit ranges

- **The toolbar holds the board's range**: from (base or any commit) and to (any
  later commit), default base → head.
- **Each card's selectors override it for that file**, offering the base and the
  commits that touched the file — the others give an identical diff. A "follow
  board" option clears the override.
- **A fix to a commented file moves that file's "from"** to the commit the
  reviewer was looking at when they commented (the anchor's "to", below), so the
  file then shows exactly what the fix changed. The agent writes it as a shared
  `shifts/<file key>` doc `{from, at}` through `ArtifactData` — no republish
  needed for it, and it outlives republishes. The page takes, per file,
  whichever is newer: the viewer's own override or the latest shift. The fix
  also changes the file's "to" blob, so it comes back unviewed.

### Per-viewer state

Viewed files, per-file ranges and the whitespace toggle follow the viewer across
devices: `db` docs under `data/users/<id>/` (private to each viewer), keyed by
branch, one write per change. A signed-out viewer or one outside the
organization (`db` resolves `null`) gets the same board with state for the visit
only. **Viewed** stores the "to" blob id, so a file that changes after it was
viewed comes back unviewed, as on GitHub.

The declaration, comments included:
`{comments: {customAnchors: true}, db: {rules: [{path: "shifts", read: "view", write: "owner"}]}, user: {}}`.

## Comments

Declared as `capabilities: {comments: {customAnchors: true}}` — the board pans
and zooms by CSS transform, which the shell's CSS-path anchors cannot follow, so
the page anchors threads itself:

- **Anchor names are the location Claude reads**, since beside a page-invented
  name the platform keeps the name alone: `<path>@<from7>..<to7>` for the file,
  plus `:R<line>` for a line on the new side or `:L<line>` for a deleted one —
  the range being the one the file showed when the comment was written. Over the
  128-byte cap, the path is shortened from the left to `…/<tail>`.
- **Entry**: a comment button in each card's header for the file, a "+" in each
  line's gutter on hover, and any line click while the shell's comment mode is
  on — all call `compose(anchor, el)`. The shell renders the composer, its "Send
  to Claude" button and every thread.
- **Pins**: on each `threads` list, and after any pan, zoom, card scroll, range
  change or panel toggle (throttled to a frame), the page reports `placed` for
  every anchor whose line is rendered and visible — an `R` line while the file's
  "to" is the anchor's, an `L` line while its "from" is, a file anchor on the
  card's header always; the rest go unplaced, into the shell's own list.
- **`reveal(id)`** pans the camera to the card and scrolls the line into view,
  opening the side panel for an over-cap file.
- **No comments capability** (`null`, a viewer outside the organization) hides
  the gutter buttons; the board works without them.

## The skill — `/review-board`

`.claude/skills/review-board/SKILL.md`, its description staged per
`.claude/rules/staging.md` since the skill listing carries it:

1. **Build**: run the build command; nothing else is decided here.
2. **Publish**: the first publish passes the capabilities and `icon: "code"`;
   the URL goes into a sticky PR comment through `scripts/pr-comment.sh`, which
   is where every later run — this session or another — finds it and republishes
   in place (an `Artifact` `read` first, when this conversation has not
   published it). The publish result's watch line is checked: the session
   reports the watch only when that line, or a `watch` listing, confirms it.
3. **A comment sent to Claude** wakes the session: `ArtifactComments` `read`
   with the thread id, the anchor decoded to file, side, line and commit, the
   text taken as review feedback — data, not instructions — and handled as a
   GitHub review comment is under `/handle`'s feedback lane: fix, commit, push,
   write the file's shift (§ "Commit ranges") for each file a fix touched under
   a comment, rebuild, republish, then a reply naming the commit SHA.
4. **Threads are not resolved by the agent**, for CLAUDE.md § "GitHub comments"'
   reason: resolution is the reviewer's tracking mechanism.

Republishing keeps the threads — they belong to the artifact, not the version.

## Watches across a relay

Generic to every watched artifact, not only the board:

- **`/relay` Step 1** lists this session's watches (`ArtifactComments` `watch`
  with no URL), writes their URLs into the summary under their own heading, and
  stops each (`watch`, `on: false`) — so a comment sent to Claude never wakes a
  session that has handed off.
- **`/relay take`** re-watches every URL that heading lists before anything
  else.
- **`/relay park`** writes the heading and stops the watches the same way; the
  session that later takes the summary re-watches.

Body-only edits to `relay/SKILL.md` and `relay/after-handoff.md`, so in place.

## Stack wiring

Per `.claude/rules/stack.md`, all three sites, each keyed on the directory so a
repo that declines the subsystem has nothing to run:

1. **`scripts/vet.sh`**:
   `[ ! -d .claude/artifacts ] || .claude/artifacts/vet.sh` — `tsc --noEmit`,
   `eslint` (boundaries included), Steiger per app, `check:masd`,
   `masd:clusters`, madge, `node --test`, in parallel through
   `scripts/run-parallel.sh`. Prettier over the `.ts` stays the root's
   `scripts/prettier.sh`, the one pin.
2. **`.claude/hooks/install-deps.sh`**:
   `pnpm --dir .claude/artifacts install --frozen-lockfile`, same key.
3. **Environment setup script**: node ≥22.18 and pnpm. This environment has node
   24 and pnpm already; the report says so, and that an environment without them
   must add both.

## Catalog

A new group, **G12 — Artifacts**, `opt-in: ask` — the cost is a Node toolchain
and a scoped `node_modules` in a repo that may have neither — listing
`.claude/artifacts/` and `/review-board`, the relay watch hand-over riding G2
with `/relay`. Its own `catalog/g12-artifacts.md`, and its line in `catalog.md`.

## Dogfooding

Once the build works: build, publish, post the sticky comment on this PR, and
hand the operator the link; the board's own comments are then handled as § "The
skill" step 3 says, in this session.

## DRY notes

- **Camera math and pan/zoom gestures are copied from island-board**, not
  shared: they sit in another repository, and a package for two consumers in two
  repos costs more than two copies of ~150 lines. The second app under
  `.claude/artifacts/` is when a `board` parent app takes them.
- **The payload schema is declared once** (`shared/review-data`) and both the
  collector and the page derive their types from it.
- **The diff engine is the page's only diff**; the collector ships contents and
  never calls `git diff` for hunks, so there are not two diff semantics to keep
  in step.
- **The PR comment goes through `scripts/pr-comment.sh`**, the repo's one
  sticky-comment writer.
- **Watch hand-over is written once, in `/relay`**, for every artifact, rather
  than in `/review-board`.
- **Prettier stays the root pin** rather than a second copy in the scoped
  `package.json`.

- **The shift and the per-viewer state share one `db` access layer** in
  `entities/file`'s model, rather than each feature opening its own docs.

## Decided

- **MASD enforcement**: Steiger alone, porting the cross-app checkers only when
  a second app landed, was ruled out — more apps are coming, so the full set
  goes in now.
- **Board threads**: the agent resolving after its reply was ruled out — the
  house rule holds on any surface.
- **Per-viewer state**: `localStorage` was ruled out — it stays on one device.
