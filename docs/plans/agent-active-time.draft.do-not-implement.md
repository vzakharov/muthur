> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# Agent active time and the speedup over the human estimate

## Goal

Each cost row records how long the agent actually worked — wall-clock, from the
moment a turn starts until the reply reaches the operator, plus the time a
background task of its own keeps running, with any silence past 20 minutes cut
to 20 — and how many senior-hours of the session's estimate each of those hours
bought. `report.py` shows the same ratio beside the dollars per senior-hour,
over the rows that carry both.

The request, as given (session prompt):

1. start counting on a hook when work begins;
2. stop counting on a hook when the agent answers the operator;
3. the ledger computes and shows how many times faster than the human estimate
   (all of the session's human hours summed);
4. the report shows the same where it already counts;
5. the cache keepalive watcher is excluded; other background tasks are not.

Settled at review: parallel work counts as wall-clock; a silence past 20 minutes
counts as 20 ("the agent went for a smoke"); the keepalive's parking wake counts
from the wake to the park; the ratio weighs the estimate by grade (and role), as
the ledger's senior-hours do.

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

**Excluded:** the keepalive watcher's own interval, and the turns its renewal
wakes start — a one-line reply that exists only to keep the cache warm. **The
wake that parks counts**, from the wake to the end of its `/relay park`: writing
the summary is real work on the session, whatever woke it. It is told apart from
a renewal by running the `relay` skill.

**Wall-clock, not agent-seconds.** Three parallel subagents running ten minutes
are ten minutes. Summing them would make fanning out look slower, which is the
opposite of what the ratio is for.

**A silence past 20 minutes counts as 20.** Within the union, every record the
session writes — in the main transcript or any subagent's — is a sign of life,
and a gap between two consecutive ones longer than `IDLE_CAP` (20 minutes, a
constant in `lib/active.py`) contributes only `IDLE_CAP`. That is what "the
agent went for a smoke" costs: a turn stuck on a permission prompt overnight, or
a background task that hung, adds 20 minutes rather than the night. It is
arithmetic over timestamps already read at `Stop`, so it needs no timer and no
extra task.

The cost of that rule: **a background command that runs silent for longer is cut
too.** A 2-hour test suite launched with `run_in_background` writes nothing to
the transcript until its notice, so it counts as 20 minutes. A background
_agent_ is unaffected, since its own transcript records every step.

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

Subagent transcripts (`<session-id>/subagents/*.jsonl`) are read for their
timestamps only, as signs of life for the idle cap: a background agent's
interval itself is its launch and its notice, both in the main file, and a
foreground agent runs inside its turn.

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
- **`speedup`** — the estimate's senior-hours (`estimate_model.senior_hours`:
  each part's hours × its role's and grade's multipliers) divided by
  `activeSeconds / 3600`; rounded to one decimal. Null without an estimate or
  without active time. It reads as senior-developer hours per agent hour: for an
  estimate that is all senior developer it is exactly how many times faster, and
  a junior's 10 hours count as the 4 senior-hours the ledger already prices them
  at.

`speedup` is a write-time snapshot, as a row's dollars are under its
`pricesAsOf`. Every path that writes a row — the `Stop` hook and
`estimate.py set --session` alike — computes it from the estimate the row
carries at that moment and the rate table then in force: `rates.json` plus the
`rates.repo.json` the hook has just fetched with the ledger. The report never
reads it back: it re-rates from the parts under the current table, as it does
the dollars per senior-hour, so a retuned multiplier moves the whole history
alike. Its presence does not count as a key `reshape` dropped.

## The report

`Rate` gains `timed_sessions`, `timed_senior_hours`, `active_hours` and
`speedup`, counted over the rows that carry both an estimate and `activeSeconds`
— a ratio of sums, as the dollars are, so one five-minute session cannot swamp a
month. Each per-senior-hour table (all, by month, week, day, model) prints the
speedup and how many sessions it covers, since older rows have an estimate and
no clock and the two counts differ. `--json` carries the same fields.

## Files

- `.claude/costs/lib/active.py` (new) — interval derivation: turns, background
  tasks, keepalive exclusion and its parking wake, union, idle cap.
- `.claude/costs/lib/pricing.py` — `summarise_transcript` fills `activeSeconds`.
- `.claude/costs/lib/rows.py` — the two fields.
- `.claude/costs/session_cost.py`, `.claude/costs/estimate.py` — compute
  `speedup` under the rate table they already load.
- `.claude/costs/lib/totals.py`, `.claude/costs/report.py` — the `Rate` fields
  and the column.
- `.claude/keepalive/hooks/keepalive.py` — imports the watcher's task
  description from `lib/active.py` instead of owning it.
- `.claude/costs/CLAUDE.md` — a § "Active time" stating the definition and what
  it misses; `.claude/keepalive/CLAUDE.md` — a line that its time is excluded.
- Tests: `test_active.py` (fixtures from the live sample: plain turns, an
  interrupt, a background Bash, a background agent overlapping a turn, a
  `TaskStop`, a keepalive renewal and a parking wake, a gap past the idle cap
  with and without a subagent writing through it); additions to `test_totals.py`
  and the row round-trip tests.

## What it misses

- **A permission prompt's wait counts as work, up to the idle cap.** Outside
  auto mode, the time a tool call waits for the operator's approval is inside
  the turn, and the transcript does not separate it from the call's run time.
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
- **The estimate's weight** is `estimate_model.senior_hours` under
  `estimate_model.checked`, the pair the report's dollars per senior-hour
  already use, in the row writers and the report alike — no second weighting.
- **One `speedup` helper** in `lib/rows.py` (estimate, active seconds, rates →
  ratio or null) serves both row writers; the report divides its own sums, since
  a ratio of sums is not a sum of ratios.

## Rejected at review

Plain hours (every part an hour whatever its grade) lost to the grade-weighted
senior-hours the ledger already uses everywhere else. Summed agent-seconds for
parallel work lost to wall-clock. Excluding the keepalive's parking wake lost to
counting it, since the park writes the session's summary.
