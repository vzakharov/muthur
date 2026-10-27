> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# Agent active time and the speedup over the human estimate

## Goal

Each cost row records how long the agent actually worked — wall-clock, from the
moment a turn starts until the reply reaches the operator, plus the time a
background task of its own keeps running — and how many times faster that is
than the session's human-hour estimate. `report.py` shows the same ratio beside
the dollars per senior-hour, over the rows that carry both.

The request, as given (session prompt):

1. start counting on a hook when work begins;
2. stop counting on a hook when the agent answers the operator;
3. the ledger computes and shows how many times faster than the human estimate
   (all of the session's human hours summed);
4. the report shows the same where it already counts;
5. the cache keepalive watcher is excluded; other background tasks are not.

## What counts as active time

The **union** of these intervals, so overlapping ones count once:

- **A turn** — from the record that starts it (an operator prompt, or a
  background task's completion notice that wakes an idle session) to its last
  record: the `end_turn` response, or, for a turn the operator interrupted, the
  last record before the next turn starts.
- **A background task** — a `run_in_background` Bash call or a background
  `Agent` — from the tool call that launched it to its completion notice. A task
  whose end is never seen (stopped with `TaskStop`, killed by a container
  restart) closes at the earliest of: its `TaskStop`, the restart notice that
  lists it, or the session's last counted record. The row warns when any task
  closed that way, since its interval is then a floor.

**Excluded:** the keepalive watcher's own interval, and every turn its wake
starts — the one-line renewal and the `/relay park` the last wake runs alike.
Both are cache housekeeping, not the task.

**Wall-clock, not agent-seconds.** Three parallel subagents running ten minutes
are ten minutes. Summing them would make fanning out look slower, which is the
opposite of what the ratio is for.

## Where the clock comes from: the transcript, read by the `Stop` hook

The two hooks the request names already bracket every turn in the transcript:
`UserPromptSubmit` fires as the prompt record is written, and `Stop` fires right
after the `end_turn` response. Every record carries a timestamp. So the `Stop`
hook — which already rebuilds the row from the whole transcript every turn —
derives the intervals from those timestamps, and no hook keeps a running clock
of its own.

A clock kept in hook state (a start mark in `tmp/` on `UserPromptSubmit`, a
delta added on `Stop`) would be wrong in ways the transcript is not:

- **A resume in a fresh container starts with an empty `tmp/`**, losing any open
  mark and the running total; the transcript is reloaded whole.
- **`Stop` does not fire on an interrupted turn**, so its mark stays open and
  swallows the operator's idle time until the next prompt.
- **A background task ends with no hook at all** — only a notice in the
  transcript says when.
- **The row is rewritten from the whole transcript every run**
  (`session_cost.py`'s contract), so a derived figure repairs itself on the next
  turn; an accumulated one carries its first error forever.

Subagent transcripts (`<session-id>/subagents/*.jsonl`) need not be read for the
clock: a background agent's interval is its launch and its notice, both in the
main file, and a foreground agent runs inside its turn.

**First implementation step: capture the record shapes from a live sample.**
This session's transcript has no background task or interrupt in it, so the
exact shape of a completion notice (the `queue-operation` enqueue and the `user`
record it becomes, with its `origin`/`turnOrigin`), of a `TaskStop`, and of an
interrupted turn is confirmed on a real transcript in `tmp/` before the parser
is written, and becomes the test fixtures.

## The row

Two fields, beside `estimate` at the top of the row:

- **`activeSeconds`** — the union above, rounded to the second. Null on a row
  written before the field existed.
- **`speedup`** — the estimate's hours, every part summed as plain hours
  whatever its role and grade, divided by `activeSeconds / 3600`; rounded to one
  decimal. Null without an estimate or without active time.

`speedup` is computed in `row_text`, the one serializer, so every path that
writes a row — the `Stop` hook and `estimate.py set --session` alike — writes it
from the estimate the row carries at that moment, and nothing can leave it
stale. The parser treats it as derived: it is recomputed on read, never trusted,
and its presence does not count as a key `reshape` dropped.

## The report

`Rate` gains `human_hours`, `active_hours` and `speedup`, counted over the rows
that carry both an estimate and `activeSeconds` — a ratio of sums, as the
dollars are, so one five-minute session cannot swamp a month. Each
per-senior-hour table (all, by month, week, day, model) prints the speedup and
how many sessions it covers, since older rows have an estimate and no clock and
the two counts differ. `--json` carries the same fields.

## Files

- `.claude/costs/lib/active.py` (new) — interval derivation: turns, background
  tasks, keepalive exclusion, union.
- `.claude/costs/lib/pricing.py` — `summarise_transcript` fills `activeSeconds`.
- `.claude/costs/lib/rows.py` — the two fields; `speedup` in `row_text`.
- `.claude/costs/lib/estimate_model.py` — plain-hours sum of an estimate, if
  `lib/hours.py` has none to reuse.
- `.claude/costs/lib/totals.py`, `.claude/costs/report.py` — the `Rate` fields
  and the column.
- `.claude/keepalive/hooks/keepalive.py` — imports the watcher's task
  description from `lib/active.py` instead of owning it.
- `.claude/costs/CLAUDE.md` — a § "Active time" stating the definition and what
  it misses; `.claude/keepalive/CLAUDE.md` — a line that its time is excluded.
- Tests: `test_active.py` (fixtures from the live sample: plain turns, an
  interrupt, a background Bash, a background agent overlapping a turn, a
  `TaskStop`, keepalive wakes and park); additions to `test_totals.py` and the
  row round-trip tests.

## What it misses

- **A permission prompt's wait counts as work.** Outside auto mode, the time a
  tool call waits for the operator's approval is inside the turn, and the
  transcript does not separate it from the call's run time.
- **Hooks' own run time** before the prompt record or after `end_turn` is
  outside the clock — seconds, but the `Stop` hook's ledger push is the largest.
- **The ratio is only as good as the estimate**, which the same model sets
  (`.claude/costs/CLAUDE.md` § "Human-hour estimates").

## DRY notes

- **Timestamps** parse through `lib/restart.py`'s `epoch`, not a second parser.
- **Record reading** goes through `lib/transcript.py`'s `TranscriptSources` and
  `lib/shape.py`'s null-safe readers, as the rest of the ledger does.
- **The keepalive's task description** has one home, moved into `lib/active.py`:
  `keepalive.py` already imports from the costs lib (`lib.restart`), so this
  keeps the dependency pointing one way rather than making the ledger import a
  hook.
- **Turn boundaries are not shared with `lib/orientation.py`.** Orientation ends
  at the first act inside a turn and works on priced responses; the clock needs
  the turn's start record and its last record of any kind, including
  notifications that are no response at all. A shared "turn" abstraction would
  have to carry both readings and serve neither better.
- **Plain hours of an estimate**: `lib/hours.py` already totals plain hours per
  role and grade for the report; the per-estimate sum is taken from there if it
  exposes one, and otherwise added once beside `senior_hours` in
  `estimate_model.py` for both callers.
