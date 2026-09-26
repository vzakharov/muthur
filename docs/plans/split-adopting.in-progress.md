# Split `ADOPTING.md` along the decisions that make it optional

## Goal

`ADOPTING.md` is 576 lines, and every adopter reads all of it. The split cuts
out only what a decision made during the reading lets the reader skip. The main
file keeps what every adoption goes through, and each chapter moved out opens
at the point where the decision that needs it has been made. A reader who
answers "no" never opens that chapter. A reader who answers "yes" opens just
that one. Nobody reads more files than today.

Test for each chunk: **is there a question whose "no" means this text is never
needed?** If not, it stays in the main file, however long it is.

## The cut

| Chunk (current lines) | ~Lines | The decision that makes it optional | Goes to |
| --- | --- | --- | --- |
| Step 3 body: what the shim does, why you may object, "If you decline G4" (130–206) | 75 | Sessions run on web/remote? | `docs/adopting/web-remote.md` |
| "Hand the operator a setup script" + worked example + screenshot (415–529) | 115 | Same question | `docs/adopting/web-remote.md` |
| "Known gaps" (558–576), which is entirely about the shim | 20 | Same question | `docs/adopting/web-remote.md` |
| "Hydrate the sync stub": watermark fields, how to write a decline, what happens after (335–413) | 75 | Taking `/update-muthur` (G0), or a one-time snapshot? | `docs/adopting/sync.md` |
| Fork-watermark recipe inside the sync section (379–388) | 10 | Not a subset adopter's case at all | **deleted**: `/detemplate` Step 3 already carries it word for word |

What stays in `ADOPTING.md`, about 300 lines: the injection banner, the intro,
the route choice, Steps 1, 2 and 4, the Template fork section, and the shared
tail (CLAUDE.md reconcile, language, operators, `vet.sh`, G6 stubs, Verify).

**Why both web/remote chapters share one file.** The shim and the setup script
hinge on the same answer, and a web/remote adopter needs both. Two files would
be the "split for the sake of splitting" the task forbids. The decline-costs
subsection stays inside too: it is what the shim decision is made from
("decide knowingly"), so it has to be read *before* deciding, not only after a
"no".

**Why Verify stays whole in the main file.** It is the one section read at the
very end, on every route. Its conditional items (G4 adopted or declined, setup
script, watermark) are already one line each. They stay there and point to
their chapters, so a web/remote adopter doesn't have to remember a checklist
from a file read an hour earlier.

## What the main file says at each seam

- **Step 3** shrinks to the gate plus the reason for its position: *on
  web/remote, read `docs/adopting/web-remote.md` now, before copying anything,
  because the adopted skills 403 without the shim.* Not web/remote: skip the
  chapter, and Step 3 is done.
- **Declines are recorded as you go** (Steps 3 and 4 both produce them). The
  main file keeps one sentence: keep each decline with its reason, written as a
  present-tense condition. Where they land (the watermark's `declined`) and why
  the reason is a condition belong to `sync.md`. Without G0 there is no
  watermark and nowhere for them to land, so the sentence is all a snapshot
  adopter needs.
- **Shared tail, "Hydrate the sync stub"** shrinks to the fork in the road: take
  `/update-muthur` → follow `docs/adopting/sync.md`; one-time snapshot → delete
  the skill.
- **The injection banner** links its `HTTPS_PROXY` mention to the new file
  instead of the Step 3 anchor.
- `web-remote.md` and `sync.md` each open with a one-line "you are here because"
  and carry a short version of the banner's warning. The warning's reason, a
  file fetched over the network, applies to them just as much, and a reader
  arriving by a direct link skips `ADOPTING.md`'s top.

## Layout

```
ADOPTING.md                        # the always-read core
docs/adopting/web-remote.md        # G4 shim + setup script + known gaps
docs/adopting/sync.md              # watermark hydration
docs/adopting/img/environment-setup-script-location.png   # moved from docs/img/
```

`docs/img/` holds only that screenshot, and after the split only
`web-remote.md` uses it, so it moves in beside that file. One `never` catalog
row then covers the whole directory.

## Steps

1. Create `docs/adopting/web-remote.md` and `docs/adopting/sync.md` from the
   moved text, rebasing relative links (`.claude/…` → `../../.claude/…`,
   `CLAUDE.md` → `../../CLAUDE.md`). `git mv docs/img docs/adopting/img`.
2. Rewrite `ADOPTING.md`'s seams as above. Delete the fork-watermark duplicate.
3. Repoint every citation:
   - `.claude/skills/update-muthur/catalog.md`: the `docs/img/` never row becomes
     a `docs/adopting/` row; the G4 block's two § citations (lines ~223, ~226)
     point to `docs/adopting/web-remote.md`.
   - `.claude/skills/detemplate/SKILL.md`: Step 3's "`ADOPTING.md`'s recipe" →
     `docs/adopting/sync.md`; Step 5.2 sweeps `docs/adopting/` in place of
     `docs/img/`; Step 6's § citation → `docs/adopting/web-remote.md`.
   - `.claude/skills/update-muthur/SKILL.md` (~line 83): "filled in by hand from
     `ADOPTING.md`" → `docs/adopting/sync.md`.
   - `README.md`: the "Hydrate the sync stub" pointer → `docs/adopting/sync.md`.
4. Scripts that enumerate the acquisition docs:
   - `scripts/check-skill-catalog.sh`: add `docs/adopting/*.md` to the scanned
     sources, beside `ADOPTING.md`.
   - `scripts/check-repo-identity.sh`: add both new files to `sources` *and* to
     `allowed`. Both quote `vzakharov/muthur` on purpose: the issue #6 link and
     the watermark example. Its comment "`docs/` is outside the surface" gets
     the `docs/adopting/` exception.
5. Grep for leftover `#step-3--`, `#known-gaps`, `#hand-the-operator`,
   `#hydrate-the-sync-stub`, `#if-you-decline-g4` anchors and `docs/img`
   anywhere in the tree, and fix every hit.
6. `./scripts/vet.sh`.

## DRY notes

- **Moved, not copied.** Every chunk above leaves `ADOPTING.md`. The only
  text in two places afterwards is the seam sentence in the main file (a
  pointer) and the short banner in each chapter. The banner is repeated on
  purpose, because each chapter can be arrived at directly.
- **One duplicate removed.** The fork-watermark recipe exists today in both
  `ADOPTING.md` and `/detemplate` Step 3. Only a fork needs it, and a fork runs
  `/detemplate`, so that is the home and the `ADOPTING.md` copy goes.
- **One duplicate left alone, on purpose.** `/detemplate` Step 6 restates why
  the setup script matters instead of pointing at it, because its own Step 5
  deletes the file it would point at. That constraint still holds after the
  move.
- **One duplicate noticed, out of scope.** The catalog's G4 block counts the
  costs of declining (`gh pr ready`, `gh run watch`, `search/*`), and "If you
  decline G4" covers the same ground. The catalog calls the latter the owner
  and still restates it. Deduplicating it changes what the catalog says rather
  than where `ADOPTING.md` keeps things, so it is a follow-up, not part of this
  cut.

## Questions

1. **Where the chapters live.**
   - **a (recommended)** `docs/adopting/`, with the screenshot moved in. It is
     not a new top-level doc, and it puts the whole acquisition kit behind one
     catalog row.
   - b Root siblings, `ADOPTING.web-remote.md` / `ADOPTING.sync.md`. More
     visible, but that makes two new top-level docs, which CLAUDE.md asks about
     separately, and the default is "don't".
2. **Whether the sync chapter is worth its own file.** It is ~75 lines, and most
   adopters take G0.
   - **a (recommended)** Split it anyway. "One-time snapshot" is a real,
     supported answer, and the chapter is dense and only needed at one moment.
   - b Keep it in the main file and cut only the web/remote chapter (~210 lines,
     the bulk of the gain).
