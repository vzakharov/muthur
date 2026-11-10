# Review board: Viewed history, popovers, age shading

Rides on PR 269 (Vova: "нене, давай всё сюда, большой PR, адоптеры возьмут сразу
всё, плюс задогфудим раскраску"). One PR, six parts, eaten as an elephant.

## Eaten so far

All six parts landed in one session (b4344af parts 1–2, d25374e parts 3 and 6,
96d43bc part 5, 43013a6 part 4).

1. **Reliable Viewed writes.** A refused or degraded write is visible (toolbar
   note + the card's checkbox shows "not saved"), and a locally set mark
   survives a later snapshot until its write succeeds. Two paths in `synced()`
   and its writers clear `dirty` today and both stop: a drain whose write
   throws, and a write that returns without writing because the store is
   unwritable (`writable()` null: degraded or no uid) — that one resolves as if
   it had saved, and the next snapshot then erases the mark. Cause on the AT/CB
   boards is unconfirmed; this makes the failure observable and closes the
   erasure paths found in code.
2. **Viewed history per file.** `viewedBlob` becomes `viewed: [{blob, at}]`; old
   docs migrate on read (`viewedBlob` → one entry, `at` from the doc). The
   checkbox is derived: ticked iff the `to` blob is in the list. Unticking
   removes only that blob's entry. The file's base shifts to the latest marked
   revision before `to`; on `to` itself the diff stays from the base. A manual
   per-file `from` still wins; base merges are still carried past.

3. **Empty cards hidden.** A card whose diff is empty ("No textual changes") is
   hidden like a viewed one: whenever the existing "Hide viewed" toggle is on.
4. **Popovers instead of selects.** Vanilla-DOM popover (Popover API, top layer,
   placed from the anchor's screen rect, since the board world is CSS-
   transformed) for the per-file and board-wide `from`/`to`, listing subject,
   commit time and viewed-at time; commits carrying a Viewed mark are marked in
   the `from` list.
5. **Age shading.** Each card gets one shade from the last commit that changed
   the file, at or before the board's `to`, base-merge commits ignored. Commits
   are grouped by time: a gap over a threshold (on the order of 15 minutes)
   between consecutive branch commits starts a new group, so a run of quick
   follow-up commits shares one shade. Groups are shaded by the age of their
   newest commit relative to `to`, log-scaled across groups so that "an hour
   ago" and "three days ago" both stay apart. A plain log of each commit's own
   age would do the opposite near `to`, spreading commits minutes apart over
   different shades. Tooltip names the commit and time; the yellow focus border
   is not overridden; both themes checked.
6. **File-name filter.** A text field in the toolbar narrows the board as you
   type, like GitHub's "Filter changed files": a case-insensitive substring
   match against the file's full path, folders included (the old path too for a
   rename). It combines with "Hide viewed" and "Focus only" as one more reason
   to hide a card, and the tally keeps counting the whole board.

## Out of scope

Show/Hide renaming, changed defaults, cross-board settings persistence (artifact
`db` and storage are per artifact).

## Decision: one PR, an elephant

One PR (Vova chose it): the parts share the range/viewed model and adopters take
the board as one unit. It was planned as bites, and Vova let the session walk
between them unprompted, so one session ate all six.

## Tests

Unit: history migration, derived checkbox, base shifting (past, on `to`, manual
override, base merge), empty-diff rule, shade grouping and bucketing, `synced()`
keeps a dirty value across a snapshot after a failed write and after a write
against an unwritable store. Browser check of popovers and shading in light and
dark themes with Playwright.

## DRY notes

- `effectiveRange()` in `entities/file/model/range.ts` stays the one place that
  decides the file's base and `to`; the history list plugs into it in place of
  `viewedBlob`, no second shifting rule in the UI.
- Doc schemas extend `filePrefsSchema` (narrow type first, per
  `masd/no-pick-omit`); the migration lives in `docs.ts` beside `parseDoc`,
  reused by every reader.
- One picker, `shared/lib/picker.ts`, serves board and card range pickers (rows
  of `{value, label, lines, marked}`); duplicating it per site would fork the
  viewed-mark rendering. Which commits carry a mark is `markedCommits` in the
  file entity, and `commitTimes` sits beside `commitLabels` in
  `board/lib/labels.ts`.
- Shade computation is a pure function in `entities/file/model`, next to
  `commitOrder`/`baseMerges`, reusing them for the base-merge filter; no new
  commit-walk helper.
- `synced()` is fixed in place; no wrapper store is added.
- The filter joins the `hidden` set `mount-board.ts` already builds for "Hide
  viewed" and "Focus only"; it is one more predicate there, not a second hiding
  path. The path match is a pure function beside `viewFileUrl`, tested alone.
