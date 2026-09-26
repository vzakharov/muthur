# Orientation cost and billed spend in the session ledger

## Goal

Two changes to the ledger under `.claude/costs/`, in one PR:

- **Orientation.** Each cost row records what the session spent **before it
  started acting** — tokens and dollars up to its first write into the
  repository or its first `end_turn` — and `report.py` averages it across rows.
  The number feeds a later call on whether a fresh session or a compact is the
  cheaper way to shed context, so every compaction is measured too, on both of
  its costs: the looking around it forces before the agent acts again, and the
  reading it forces later, when the summary turns out to have left a hole.
- **Billed spend.** Claude Code's OpenTelemetry `api_request` events become the
  ledger's first source: one event per API call, the calls the transcript never
  records included. Pricing the transcript with `prices.json` stays, as the
  fallback for a session without telemetry and as the cross-check on the events.

Split as an **elephant**: the two share the row, the phases and one PR, and
neither is whole alone — orientation priced from estimates is the thing the
events exist to correct, and the events without the phases are a better total
nobody asked for. The first bite also ships the telemetry capture, so the next
session is the one that runs with it on and can check it.

## Definitions

- **An action** is either of:
  - an `Edit`, `Write` or `NotebookEdit` on a path inside the session's `cwd`
    and outside its `tmp/`, or an `AskUserQuestion` or `ExitPlanMode` — in
    **any** transcript of the session, the subagents' included, since a
    delegated `Edit` is the session starting work all the same;
  - a response of the session's **own** with `stop_reason: end_turn`.

  A write to `tmp/`, the scratchpad or anywhere else outside the repository is
  not an action: a probe script is how an agent finds its bearings, not what it
  does with them. A subagent's `end_turn` only hands its result back to the agent
  that spawned it, and a text block in the middle of a turn is narration, so
  neither is an answer to the operator. `AskUserQuestion` and `ExitPlanMode` hand
  the turn to the operator exactly as an `end_turn` does, from inside it.
- **A phase** runs from a starting point to the **acting response** — the
  earliest response carrying an action — and its spend is every priced response
  whose first record is timestamped before that one. The acting response is left
  out: its output is the edit or the answer itself. Timestamps rather than file
  order, because subagent spend sits in other files and timestamps are what order
  it against the main file's. An action is looked for in **every** record of a
  response, since one response is written as one record per content block.
- **Orientation** is the phase that starts at the session's first response.
- **Re-orientation** is the phase that starts at a `compact_boundary` record in
  the session's own transcript. A session compacts as often as it runs out of
  room — plan, compact, implement, compact, handle a review, compact — so every
  boundary opens one, and each is measured on its own.
- **A re-read** is a hole the summary left, found later: a call after a boundary
  that repeats one the session made before it. That is a `Read` of a path read
  before the boundary, whole or over the same range, with no write to that path
  in between; or a `Grep`, `Glob` or `Bash` call whose input is identical to one
  made before the boundary. A re-read is charged to the **most recent** boundary
  before it, wherever in that stretch it falls, which is what catches the hole
  noticed three hours after the compact rather than straight after it.

## What a row gains

```json
"orientation": {
  "endedBy": "Edit",
  "endedOn": "lib/pricing.py",
  "endedAt": "2026-09-25T22:55:01.000Z",
  "contextTokens": 61234,
  "spend": { "...": "a Tally, as in `total`" }
},
"compactions": [
  {
    "at": "2026-09-25T23:40:12.000Z",
    "trigger": "manual",
    "compactedFrom": 230043,
    "summaryChars": 15361,
    "reorientation": { "...": "the same shape as `orientation`" },
    "rereads": {
      "calls": 7,
      "byTool": { "Read": 4, "Bash": 3 },
      "estimatedTokens": 18400,
      "estimatedUsd": 0.41
    }
  }
]
```

- `endedBy` is the tool's name or `end_turn`, and `endedOn` the path it wrote
  (`null` for an answer). Both are `null` when the transcript ends before any
  action, and `spend` is then everything after the phase began.
- `contextTokens` is the acting response's input + cache read + cache write: how
  much context the phase had built by the time the session acted. It is the
  figure that sets a fresh session's size against a compacted one's.
- `trigger`, `compactedFrom` and `summaryChars` are the boundary's
  `compactMetadata.trigger` and `preTokens`, and the length of the summary
  record that follows it: how large the context was, and how much the summary
  kept of it.
- `rereads` is an **estimate**, and the row says so in its field names. A tool
  result has no `usage` of its own, so its tokens are the next response's cache
  write, split between the results that arrived together by their length in
  characters. Its dollars are what carrying those tokens cost: one cache write,
  then a cache read on every later response until the next boundary or the end
  of the session.
- All of it is optional on read. The rows already under `sessions/2026-09/` stay
  without these fields: their transcripts are gone from every container, so
  nothing can be backfilled.

## Report

`report.py` gains an `orientation` section after the totals:

- how many rows carry the measure out of how many there are;
- orientation: mean and median dollars, mean `contextTokens`, and its share of
  each measured session's total — by `endedBy`, and by the opening command
  (`/task`, `/go`, `/handle`, `/from-branch`, or none). A session opened with
  `/handle` or `/from-branch` is the fresh-session side of the comparison: work
  begun elsewhere, picked up by an agent that has to find its bearings from
  scratch;
- compactions: how many, and per compaction the mean and median of the
  re-orientation's dollars and `contextTokens`, of `compactedFrom`, and of the
  re-reads' calls and estimated dollars, with the re-reads by tool so `Bash`
  can be read apart from the rest.

`--json` carries the lot.

## This bite

Orientation over the transcript as it stands, and the telemetry capture switched
on for the next session.

1. `lib/pricing.py`: `Response` gains the tool calls its record carries (name
   and input), read off the `content` blocks, and the record's `requestId`, which
   the next bite joins on. `summarise_transcript` keeps each priced response's
   first timestamp, id, tally and calls, the main file's compaction boundaries
   with their summary's length, and each tool result's length, and hands them to
   the new module. Calls are gathered **before** the dedup `continue`, so a later
   record of an already-seen response still contributes its calls.
2. `lib/orientation.py` (new): the phases, the re-read matching and its estimate.
   `SessionCost` gains `orientation` and `compactions`, parsed back optionally in
   `parse_session_cost`.
3. `lib/totals.py`: the averages above, as an `OrientationSummary` on `Totals`.
4. `report.py`: print the section.
5. Tests in `test_pricing.py` and `test_totals.py`: a subagent `Edit` ending
   orientation before the main file's; the acting response left out; an action
   on the second record of a response; a subagent `end_turn` and a `Write` into
   `tmp/` not ending anything; two boundaries each opening its own
   re-orientation; a re-read charged to the latest boundary, and a `Read` after
   an `Edit` to the same path not counted; a row without the fields parsing and
   being skipped by the summary. The boundary fixture copies the shape this
   session's transcript recorded: `type: system`, `subtype: compact_boundary`,
   `compactMetadata` with `trigger`, `preTokens`, `durationMs`,
   `preservedSegment` and `preservedMessages`, and the summary as the `user`
   record after it, flagged `isCompactSummary`.
6. **The capture.** A stdlib OTLP/HTTP-JSON receiver on `127.0.0.1:4318`,
   started detached by a `SessionStart` hook on `startup|resume` — a container
   that slept loses it — and a no-op when one is already listening. It appends
   each `api_request` event to a per-session file under the repo's `tmp/`,
   keeping only the numeric attributes and `request_id`, `model`, `speed`,
   `query_source` and the timestamp: the events also carry the account's email
   and ids, which have no business on disk. `.claude/settings.json` gains the
   `env` block:
   `CLAUDE_CODE_ENABLE_TELEMETRY=1`, `OTEL_LOGS_EXPORTER=otlp`,
   `OTEL_METRICS_EXPORTER=none`, `OTEL_EXPORTER_OTLP_PROTOCOL=http/json`,
   `OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318`,
   `OTEL_LOGS_EXPORT_INTERVAL=1000`, `NO_PROXY=127.0.0.1,localhost`. A test
   posts a recorded payload to the receiver and reads back the kept fields
   only.
7. `.claude/costs/CLAUDE.md`: a § "Orientation" carrying what the code cannot
   say for itself — why the acting response is left out, why a subagent's
   `end_turn` and a scratch write do not count, why timestamps rather than
   order, how the re-read estimate is made, and what the measure misses (below).
   The capture gets a line saying the events are collected and not yet read.

## Rest of the elephant

The telemetry side, coarse. The first bite leaves events landing on disk; what
is left is reading them.

- **Check the capture works.** Whether the `env` block in `.claude/settings.json`
  reaches Claude Code's telemetry at all decides the operator-facing half below:
  events on disk at this session's start say it does. If it does not, the
  variables move to the environment's own settings and the block goes.
- **The events become the row's total.** Read the session's event file, keep the
  numbers, and join each event to its transcript response by `request_id` against
  the record's `requestId`. A matched response is priced from its event, so the
  phases above sum billed dollars rather than estimates; an unmatched event is a
  call the transcript never saw, and lands in a bucket of its own split by
  `query_source`. The compaction's own call is the `compact` entry there, so each
  compaction in the row gains its billed cost, where today the ledger can only
  record its size.
- **`prices.json` stays**, as the fallback for a session with no events and as
  the cross-check on the ones it has — the events' `cost_usd` is Claude Code's
  own estimate at list price, not an invoice. A row says which source priced it.
- **`.claude/costs/CLAUDE.md` is corrected.** § "Checking the arithmetic" puts
  the calls it cannot see at "a fraction of a percent" and calls them background
  Haiku; this session measured about 8% of spend in Opus calls that read the
  whole context and write almost nothing. § "What the totals do not cover" loses
  "Each compact" once the events price it.
- **The operator is told what to add, and where.** No agent can set an
  environment's settings. If the `env` block does not carry, `ADOPTING.md` gains
  a section beside § "Hand the operator a setup script" — the variables, and the
  same gear-icon route to the environment's settings — and `/detemplate` Step 6,
  `/spinoff`'s report and the catalog's `.claude/costs/` row point at it. Either
  way, a session whose ledger runs without events says so once at start, the way
  `.claude/hooks/gh-shim.sh` reports a missing `gh`, so a missing setting finds
  itself instead of waiting for someone to read a doc.

## What it does not see

- **Edits made through `Bash`** — `sed -i`, a heredoc, a script that writes
  files. Recognising them means parsing shell, which guesses; the house rule has
  file changes go through `Edit`/`Write`, so the miss is the rule's exceptions.
  Such a session's orientation runs long, and `endedBy` shows what ended it.
- **A hole read around rather than re-read** — the same file opened by `cat`
  after a `Read`, a narrower `grep` than the one before, or a hole that shows up
  as a wrong turn rather than as a read. Re-reads count only exact repeats, so
  they are a floor on what a compact cost in lost understanding, not the figure.
- **A repeat that was simply due.** A `git status` before each commit repeats
  by design, and counts as a re-read when a boundary falls between two of them.
  `byTool` is what lets the report read `Bash` apart.
- **The compaction call itself, until the events are read.** The transcript
  records it without `usage`, so this bite records its size and not its price.
  Its size does not bound its price either: the one compaction measured, of a
  230k-token context with a warm cache, cost about $0.22 by Claude Code's own
  counter, of which reading the context was $0.05 and the rest was output — the
  summary and the thinking behind it.
- **A resume in a fresh container.** It reloads the transcript without a
  boundary to restart at, so any looking around it does lands in the work rather
  than in a phase of its own.
- **Events emitted after the last `Stop`.** The row is written at `Stop`, and
  the exporter flushes once a second, so the tail of a session's last turn can
  miss its row. The next bite's rows carry that edge; this bite only collects.

## DRY notes

- **Reused:** `Tally`, `cost_of` and the rate lookup — phases are summed from the
  tallies `summarise_transcript` already prices, never re-priced; the re-read
  estimate prices its tokens at the rates of the response they arrived in; the
  `read_*` helpers in `lib/shape.py` for the new fields; `to_json` for writing
  them; `_parse_tally` for reading `spend` back. The receiver's hook sources
  `.claude/hooks/lib.sh` like the other `SessionStart` hooks.
- **Not re-scanned:** the transcript is read once. The new module takes what the
  existing scan collects, rather than walking the records a second time with its
  own copy of the dedup rule — two walks would be two places to keep `message.id`
  deduplication right. The same scan collects `requestId`, so the next bite's
  join adds no walk of its own.
- **Shared shape:** orientation and each re-orientation are one `Phase` type,
  since they differ only in where they start.
- **Kept apart:** `OrientationSummary` sits beside `Bucket` rather than
  extending it. `Bucket` sums; the summary takes means, medians and shares, and
  folding those into `Bucket` would put fields on every month and branch row that
  mean nothing there.
- **A new module rather than growth:** `lib/pricing.py` is at 454 lines, so the
  phases and re-reads live in `lib/orientation.py`, and pricing gains only the
  fields it hands over. The receiver is its own script under
  `.claude/costs/hooks/`: it runs as a daemon and shares nothing with the
  pricing code but the field names, which it writes and the next bite reads.
