> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# Review board: Viewed history, popovers, age shading

Rides on PR 269 (Vova: "нене, давай всё сюда, большой PR, адоптеры возьмут сразу
всё, плюс задогфудим раскраску"). One PR, five parts, in this order.

## Parts

1. **Reliable Viewed writes.** A refused or degraded write is visible (toolbar
   note + the card's checkbox shows "not saved"), and a locally set mark
   survives a later snapshot until its write succeeds (`synced()` keeps `dirty`
   after a failed drain instead of clearing it). Cause on the AT/CB boards is
   unconfirmed; this makes the failure observable and stops the erasure path
   found in code.
2. **Viewed history per file.** `viewedBlob` becomes `viewed: [{blob, at}]`; old
   docs migrate on read (`viewedBlob` → one entry, `at` from the doc). The
   checkbox is derived: ticked iff the `to` blob is in the list. Unticking
   removes only that blob's entry. The file's base shifts to the latest marked
   revision before `to`; on `to` itself the diff stays from the base. A manual
   per-file `from` still wins; base merges are still carried past.
3. **Empty cards hidden.** A card whose diff is empty ("No textual changes") is
   hidden unless "Show viewed" is on.
4. **Popovers instead of selects.** Vanilla-DOM popover (Popover API, top layer)
   for the per-file and board-wide `from`/`to`, listing subject, commit time and
   viewed-at time; commits carrying a Viewed mark are marked in the `from` list.
   Toolbar labels become "Show whitespace" / "Show viewed" only if Vova re-asks
   (dropped for now; defaults unchanged).
5. **Age shading.** Each card gets one shade from the age of the last commit
   that changed the file, relative to the board's `to`, log-scaled so commits
   minutes apart share a shade; base-merge commits ignored; tooltip names the
   commit and time; the yellow focus border is not overridden; both themes
   checked.

## Out of scope

Show/Hide renaming, changed defaults, cross-board settings persistence (artifact
`db` and storage are per artifact).

## Decision: one PR

Take it whole, as a single PR with the parts as separate commits (elephant, not
pizza): the parts share the range/viewed model, and adopters take the board as
one unit. Recommendation in force; Vova already chose it.

## Tests

Unit: history migration, derived checkbox, base shifting (past, on `to`, manual
override, base merge), empty-diff rule, shade bucketing, `synced()` keeps a
dirty value across a snapshot after a failed write. Browser check of popovers
and shading in light and dark themes with Playwright.

## DRY notes

- `effectiveRange()` in `entities/file/model/range.ts` stays the one place that
  decides the file's base and `to`; the history list plugs into it in place of
  `viewedBlob`, no second shifting rule in the UI.
- Doc schemas extend `filePrefsSchema` (narrow type first, per
  `masd/no-pick-omit`); the migration lives in `docs.ts` beside `parseDoc`,
  reused by every reader.
- One popover component under `shared/ui` serves board and card range pickers
  (both take a list of `{value, label, time, viewedAt}` rows); duplicating it
  per site would fork the viewed-mark rendering. `commitLabels` in
  `board/lib/labels.ts` is extended with times rather than adding a parallel
  lookup.
- Shade computation is a pure function in `entities/file/model`, next to
  `commitOrder`/`baseMerges`, reusing them for the base-merge filter; no new
  commit-walk helper.
- `synced()` is fixed in place; no wrapper store is added.
