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
nobody asked for.

## Eaten so far

- **Orientation is measured over the transcript.** Each row carries
  `orientation` and `compactions` (`lib/orientation.py`, fed by the one scan in
  `lib/pricing.py`); every compaction records its re-orientation, its size and
  summary length, and its re-reads with their estimated tokens and dollars.
  `.claude/costs/CLAUDE.md` § "Orientation" holds the definitions as built and
  what the measure misses. Rows from before parse, and the summary skips them.
- **`report.py` prints the averages** — orientation by what ended it and by
  opening command, then compactions — and `--json` carries them
  (`OrientationSummary` on `Totals`).
- **Each priced response keeps its `requestId`** on `Response`, the key the
  events join on, and `lib/tally.py` now holds `Rates` and `Tally`.
- **The capture waits on the environment.**
  `.claude/costs/hooks/start-telemetry-receiver.sh` starts
  `telemetry_receiver.py` on `127.0.0.1:4318` at `SessionStart` when the
  exporter variables point there, and otherwise prints a notice listing them
  and where they go. Claude Code ignores them in a repository's
  `.claude/settings.json`, so the environment's own settings carry them;
  `ADOPTING.md`, `/detemplate` Step 6, `/spinoff` and the catalog row point at
  the hook's list. Events land in `tmp/telemetry/<session-id>.jsonl`, stripped
  to numbers and the named fields; nothing reads them yet.
- **The capture is checked live.** Claude Code strips `OTEL_*` from what it
  spawns, so the hook reads them from the `claude` process through `/proc`;
  with that, events reached `tmp/telemetry/` in a session whose environment
  set the variables. Every main-thread call there arrived with
  `query_source: "sdk"`.

## This bite

The events become part of the row. What the real file showed shapes it: on 39
matched responses `prices.json` and the events' `cost_usd` agreed to the cent,
and the two calls the transcript lacked were Opus `prompt_suggestion` calls.
So the events' worth is the calls the transcript never sees, and a matched
response keeps its table price, the event checking it.

- **`lib/billed.py` reads the event file** — `tmp/telemetry/<session-id>.jsonl`,
  the id being the transcript's stem — into events keyed by `request_id`,
  parsed with `lib/shape.py`'s readers, a repeated id kept once.
- **The join runs inside the one scan.** Each priced response whose
  `requestId` has an event is counted matched; the rest of the events are
  **unseen** calls, bucketed by `query_source` in the row's new `telemetry`
  object and added to `total` and `byRate` (an event's `speed: "normal"` is the
  table's `standard`). An event does not split its cache write by TTL, so an
  unseen call's write sits under the 5-minute tokens, its dollars being the
  event's own. `total` stops being `ownTurns + subagents` exactly, the
  difference being `telemetry.unseen`.
- **Each compaction gains `billedUsd`**: the `compact`-tagged unseen call
  nearest its boundary in time. None tagged leaves it null; the
  position fallback waits for the first real compaction to show it is needed.
- **The table checks the events.** `telemetry` carries both prices of the
  matched responses; beyond 1% apart, the row warns.
- **No event file, no `telemetry`** — null, as on every older row, which
  parses unchanged. `session_cost.py` takes `--events <path>` for a hand run.
- **The row's shape moves to `lib/rows.py`** (`SessionCost`,
  `parse_session_cost`), keeping `lib/pricing.py` under ~450 lines.
- **`.claude/costs/CLAUDE.md` is corrected**: § "Telemetry" says what reads the
  events and what stripping `OTEL_*` means for the hook; § "Checking the
  arithmetic" loses "background Haiku … a fraction of a percent" for what the
  events show; § "What the totals do not cover" loses "Each compact" where
  events exist.

## Rest of the elephant

- **`report.py` shows the unseen calls** — their share of spend by
  `query_source`, and how many rows were priced with events.
- **The position fallback for an untagged compaction**, if the first real
  compaction in an event file arrives without `compact`.

## What the events are still to cover

- **The compaction call itself.** The transcript records it without `usage`,
  so the row records its size and not its price. Its size does not bound its
  price either: the one compaction measured, of a 230k-token context with a
  warm cache, cost about $0.22 by Claude Code's own counter, of which reading
  the context was $0.05 and the rest was output — the summary and the thinking
  behind it.
- **Events emitted after the last `Stop`.** The row is written at `Stop`, and
  the exporter flushes once a second, so the tail of a session's last turn can
  miss its row.

## DRY notes

- **No second walk for the join.** The scan already keeps each response's
  `requestId`; matching events to responses reads the event file and that list,
  never the transcript again.
- **Pricing from an event reuses `Tally`**: a matched response's tally takes
  the event's `cost_usd` in place of `cost_of`, so the phases and totals sum it
  without knowing which source priced it.
- **The receiver stays apart** from the pricing code: they share only the
  field names it writes and the join reads.
