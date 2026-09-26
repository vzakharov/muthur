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
  to numbers and the named fields.
- **The capture is checked live.** Claude Code strips `OTEL_*` from what it
  spawns, so the hook reads them from the `claude` process through `/proc`;
  with that, events reached `tmp/telemetry/` in a session whose environment
  set the variables. Every main-thread call there arrived with
  `query_source: "sdk"`.
- **The events are in the row** (`lib/billed.py`, joined inside the one scan
  by request id). On a live session the table and the events priced all 45
  matched responses alike, so a matched response keeps its table price and the
  row warns past 1% drift; the calls no response matches — Opus
  `prompt_suggestion` calls there — go into `total`, `byRate` and
  `telemetry.unseen` by `query_source`, and a compaction's `billedUsd` is the
  `compact` call nearest its boundary. No event file leaves `telemetry` null.
  The row's shape moved into `lib/rows.py`.
- **`report.py` shows the unseen calls** (`TelemetrySummary` on `Totals`): how
  many rows were priced with events and their spend, then the unseen calls by
  `query_source` as `Bucket`s, each with its share of that spend.
- **The receiver survives a mid-session checkout.** The hook also runs at
  `PostToolUse`, silent there, and starts a receiver that is missing: a session
  that checks out a branch carrying it registers the hook with `SessionStart`
  already past. `ADOPTING.md` says why an adopting session captures nothing and
  how to start the receiver by hand.
- **A compaction is priced live.** A manual compact of a 185k-token context
  arrived tagged `compact`, 6 ms before its boundary, and the row gave it
  `billedUsd` 0.168 — so no position fallback for an untagged one is built.

## What the events are still to cover

- **Events emitted after the last `Stop`.** The row is written at `Stop`, and
  the exporter flushes once a second, so the tail of a session's last turn can
  miss its row.

## DRY notes

- **No second walk for the join.** The scan already keeps each response's
  `requestId`; matching events to responses reads the event file and that list,
  never the transcript again.
- **An unseen call is a `Tally`**, the event's `cost_usd` in it, so `total`,
  `byRate` and the `unseen` buckets sum it with the `add` every other tally
  uses.
- **The row's shape has one home**, `lib/rows.py`, beside the code that writes
  and reads it; `lib/billed.py` imports nothing from `lib/pricing.py`, so the
  two cannot cycle.
- **The receiver stays apart** from the pricing code: they share only the
  field names it writes and the join reads.
