> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# Orientation cost in the session ledger

## Goal

Each cost row records what the session spent **before it started acting** — tokens
and dollars up to its first `Edit`/`Write` or its first `end_turn` — and
`report.py` averages it across rows. The number feeds a later call on whether a
fresh session or a compact is the cheaper way to shed context, so the same
measurement is taken after every compaction too: that is the compact side of the
comparison, and without it the ledger prices only one of the two options.

## Definitions

- **An action** is either of:
  - a `tool_use` block named `Edit`, `Write`, `NotebookEdit`, `AskUserQuestion`
    or `ExitPlanMode`, in **any** transcript of the session, the subagents'
    included — a delegated `Edit` is the session starting work all the same;
  - a response of the session's **own** with `stop_reason: end_turn`. A
    subagent's `end_turn` only hands its result back to the agent that spawned
    it, so it is not an answer to the operator and does not count. A text block
    in the middle of a turn does not count either.
  `AskUserQuestion` and `ExitPlanMode` are in the list because each hands the
  turn to the operator exactly as an `end_turn` does, just from inside it.
- **Orientation** is every priced response whose first record is timestamped
  before the **acting response**, which is the earliest response carrying an
  action. The acting response is left out: its output is the edit or the answer
  itself. Timestamps rather than file order, because subagent spend sits in
  other files and timestamps are what orders it against the main file's.
  An action is looked for in **every** record of a response, since one response is
  written as one record per content block and the `Edit` is often not the first
  of them.
- **Re-orientation** is the same measure, restarted at each `compact_boundary`
  record in the session's own transcript: the responses after the boundary and
  before the next acting response.

## What a row gains

```json
"orientation": {
  "endedBy": "Edit",
  "endedAt": "2026-09-25T22:55:01.000Z",
  "contextTokens": 61234,
  "spend": { "...": "a Tally, as in `total`" }
},
"reorientations": [
  { "compactedFrom": 912345, "endedBy": "Edit", "endedAt": "…",
    "contextTokens": 48210, "spend": { "...": "a Tally" } }
]
```

- `endedBy` is the tool's name or `end_turn`; `null` when the transcript ends
  before any action, in which case `spend` is everything after the phase began.
- `contextTokens` is the acting response's input + cache read + cache write: how
  much context orientation had built by the time the session acted. It is the
  figure that sets a fresh session's size against a compacted one's.
- `compactedFrom` is the boundary's `preTokens`: how large the context was when
  it was compacted.
- Both fields are optional on read. The fifteen rows already under
  `sessions/2026-09/` stay without them, because their transcripts are gone from
  every container; nothing can be backfilled.

## Report

`report.py` gains an `orientation` section after the totals:

- how many rows carry the measure out of how many there are;
- mean and median dollars, mean context tokens, and the share of each measured
  session's total that went on orientation;
- the same by `endedBy`, since a session ending its first turn with an answer
  and one ending it with an `Edit` did different amounts of looking around;
- re-orientations beside it: count, mean and median dollars, mean `contextTokens`
  and `compactedFrom`.

`--json` carries the lot.

## Steps

1. `lib/pricing.py`: `Response` gains the action it carries (`acts: Optional[str]`),
   read off the record's `content` blocks; `summarise_transcript` keeps each
   priced response's `(first timestamp, message id, tally, action)` and the
   main file's compaction boundaries, and hands them to the new module. Actions
   are gathered **before** the dedup `continue`, so a later record of an
   already-seen response still marks it as acting.
2. `lib/orientation.py` (new): the phases — orientation from the session's first
   response, a re-orientation from each boundary — each summed as a `Tally` up to
   its acting response. `SessionCost` gains `orientation` and `reorientations`,
   parsed back optionally in `parse_session_cost`.
3. `lib/totals.py`: the averages above, as an `OrientationSummary` on `Totals`.
4. `report.py`: print the section.
5. Tests in `test_pricing.py` and `test_totals.py`: a subagent `Edit` ending
   orientation before the main file's; the acting response left out;
   an action on the second record of a response; a subagent `end_turn` not
   counting; a re-orientation after a boundary; a row without the fields
   parsing and being skipped by the summary.
6. `.claude/costs/CLAUDE.md`: a § "Orientation" carrying the definitions above
   that are not recoverable from the code — why the acting response is left out,
   why a subagent's `end_turn` does not count, why timestamps rather than order,
   and that edits made through `Bash` are not seen (below).
7. Confirm the `compact_boundary` shape (`type: system`, `subtype:
   compact_boundary`, `compactMetadata.preTokens`) against a real transcript
   before the fixture is written from it. This session's own has none, so the
   check is a session that compacts on this branch; failing that, the shape
   ships under a test that says where it came from.

## What it does not see

- **Edits made through `Bash`** — `sed -i`, a heredoc, a script that writes
  files. Recognising them means parsing shell, which guesses; the house rule has
  file changes go through `Edit`/`Write`, so the miss is the rule's exceptions.
  Such a session's orientation runs long, and `endedBy` shows what ended it.
- **The compaction call itself.** It carries no `usage` in the transcript (see
  § "What the totals do not cover"), so the compact side of the comparison is
  re-orientation plus a compact the ledger can only bound — `compactedFrom` at
  the cache-read rate — rather than price.
- **A resume in a fresh container.** It reloads the transcript without a
  boundary to restart at, so any looking around it does lands in the turn's work
  rather than in a phase of its own.

## Open questions

1. **Re-orientation after a compact.**
   (a) **Measure it** (recommended, and what this plan does) — it is the other
   half of the new-session-vs-compact comparison the number is for.
   (b) Orientation at session start only; re-orientation is a follow-up.
2. **What ends orientation.**
   (a) **`Edit`/`Write`/`NotebookEdit`, `AskUserQuestion`/`ExitPlanMode`, the
   session's own `end_turn`** (recommended, as above).
   (b) Also a `git commit` through `Bash`, which catches `/take-issue`'s export
   and other scripted writes, but also counts committing a plan nobody has
   read as starting work.
3. **Writes into `tmp/` or the scratchpad.**
   (a) **Count them** (recommended) — writing a scratch file is still the agent
   producing something, and the path is not in the row to filter on later
   anyway.
   (b) Skip them, so only a write the repository keeps ends orientation.

## DRY notes

- **Reused:** `Tally`, `cost_of` and the rate lookup — orientation is summed from
  the tallies `summarise_transcript` already prices, never re-priced; the
  `read_*` helpers in `lib/shape.py` for the new fields; `to_json` for writing
  them; `_parse_tally` for reading `spend` back.
- **Not re-scanned:** the transcript is read once. The new module takes the
  priced responses the existing scan produces, rather than walking the records
  a second time with its own copy of the dedup rule — two walks would be two
  places to keep `message.id` deduplication right.
- **Shared shape:** orientation and each re-orientation are one `Phase` type,
  since they differ only in where they start.
- **Kept apart:** `OrientationSummary` sits beside `Bucket` rather than
  extending it. `Bucket` sums; the summary takes means, medians and shares, and
  folding those into `Bucket` would put fields on every month and branch row that
  mean nothing there.
- **A new module rather than growth:** `lib/pricing.py` is at 454 lines, so the
  phases live in `lib/orientation.py` and pricing gains only the fields it hands
  over.
