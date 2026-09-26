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
- **The capture is on.** `.claude/costs/hooks/start-telemetry-receiver.sh`
  starts `telemetry_receiver.py` on `127.0.0.1:4318` at `SessionStart`, and
  `.claude/settings.json`'s `env` points the log export at it. Events land in
  `tmp/telemetry/<session-id>.jsonl`, stripped to numbers and the named fields;
  `.claude/costs/CLAUDE.md` § "Telemetry" says nothing reads them yet.
  `NO_PROXY` is not in the block: a settings value replaces the environment's
  list, which here already exempts `127.0.0.1`.

## Rest of the elephant

The telemetry side, coarse. The first bite leaves events landing on disk; what
is left is reading them.

- **Check the capture works**, in the first session started with the variables
  set: events in `tmp/telemetry/` after its first turn. An environment whose
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

## This bite

**The capture moves to the environment's settings.** Claude Code ignores
OpenTelemetry exporter variables in a repository's `.claude/settings.json`
(code.claude.com/docs/en/env-vars § "Variables Claude Code ignores in env"), so
the first bite's `env` block can never turn the export on: it is honored only in
user settings, managed settings and the process environment, and a cloud
environment's variables are the last.

- **The `env` block goes** from `.claude/settings.json`.
- **`start-telemetry-receiver.sh` reads the variables it is started beside.**
  Set to the receiver's endpoint → start it, as now. Unset or pointing elsewhere
  → start nothing and print a notice to stdout, which `SessionStart` folds into
  the context the way `.claude/hooks/gh-shim.sh` reports a missing `gh`: that
  the ledger is priced from the transcript alone, the variables to add, and
  where — the environment's settings, as variables, picked up by the next
  session. A session whose telemetry is off on purpose
  (`CLAUDE_CODE_ENABLE_TELEMETRY` unset and nothing else of it set) gets the
  same notice, since nothing tells the two apart.
- **`ADOPTING.md` gains the variables** beside § "Hand the operator a setup
  script", with the same route to the environment's settings; the catalog's
  `.claude/costs/` row, `/detemplate`'s and `/spinoff`'s reports point at it
  where they mention the ledger.
- **`.claude/costs/CLAUDE.md` § "Telemetry"** says where the variables live and
  why not in the repository.
- **Tests:** the hook's two paths, over a stub `python3` on `PATH` rather than a
  real listener.

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
