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

## Rest of the elephant

The telemetry side, coarse. The capture is ready for the environment to switch
on; what is left is checking it and reading the events.

- **Check the capture works**, in the first session started after the operator
  sets the variables the hook's notice lists: events in `tmp/telemetry/` after its first turn. An environment whose
  `NO_PROXY` lacks `127.0.0.1` sends the export through its proxy;
  `tmp/telemetry/receiver.log` staying empty with no events beside it is that
  case. The join below is built against that session's real event file, not
  the documented shape alone.
- **The events become the row's total.** Read the session's event file, keep the
  numbers, and join each event to its transcript response by `request_id` against
  the record's `requestId`. A matched response is priced from its event, so the
  phases above sum billed dollars rather than estimates; an unmatched event is a
  call the transcript never saw, and lands in a bucket of its own split by
  `query_source`. That field takes only `main`, `subagent` and `auxiliary`, so
  the compaction's own call is found by position — an unmatched call between
  the boundary and the last response before it, the one that wrote the most —
  and each compaction in the row gains its billed cost, where today the ledger
  can only record its size. The real file settles whether that rule holds.
- **`prices.json` stays**, as the fallback for a session with no events and as
  the cross-check on the ones it has — the events' `cost_usd` is Claude Code's
  own estimate at list price, not an invoice. A row says which source priced it.
- **`.claude/costs/CLAUDE.md` is corrected.** § "Checking the arithmetic" puts
  the calls it cannot see at "a fraction of a percent" and calls them background
  Haiku; this session measured about 8% of spend in Opus calls that read the
  whole context and write almost nothing. § "What the totals do not cover" loses
  "Each compact" once the events price it.

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
