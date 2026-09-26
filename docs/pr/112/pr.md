# PR #112: feat: measure orientation and billed spend in the session ledger

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/112
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/orientation-cost-phs3oc
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-25T22:53:03Z
- **Updated:** 2026-09-26T01:18:40Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- Each cost row records what the session spent **before it started acting**: tokens, dollars and context size up to its first `Edit`/`Write`/`NotebookEdit` inside the repository, `AskUserQuestion`/`ExitPlanMode`, or its own `end_turn`. Writes into `tmp/`, the scratchpad or outside the repo don't count, and neither does a subagent's `end_turn`; a subagent's edit does. `report.py` averages it across rows, by what ended the phase and by opening command.
- Every compaction boundary opens its own re-orientation, cut off at the next boundary, and records its size, its summary's length, and the re-reads it forced: exact repeats of a pre-boundary `Read`/`Grep`/`Glob`/`Bash`, estimated in tokens and dollars from the cache write they arrived in. The point of the number is deciding between a fresh session and a compact.
- The measure takes what the pricer's one scan already collects, so `message.id` dedup keeps a single home. `Rates`/`Tally` move to `lib/tally.py` to avoid an import cycle. Rows from before the fields parse and are skipped by the summary.
- **Telemetry capture is ready, and the environment switches it on.** A `SessionStart` hook starts a stdlib OTLP/HTTP-JSON receiver on `127.0.0.1:4318` when Claude Code's exporter variables point there; `api_request` events land in `tmp/telemetry/<session-id>.jsonl`, stripped to numbers plus `request_id`/`model`/`speed`/`query_source`/timestamp. Claude Code ignores those variables in a repository's `.claude/settings.json`, so they go in the environment's settings, and the hook prints a notice listing them until they are set. `ADOPTING.md`, `/detemplate`, `/spinoff` and the catalog row point at that list. Claude Code strips `OTEL_*` from every process it spawns, so the hook reads them from the `claude` process's own environment through `/proc`; checked live, events reach disk.
- **The row now includes the calls the transcript never records.** The pricing scan joins the events to its responses by request id. On a live session the table and the events priced all 45 matched responses identically, so a matched response keeps its table price and the row warns past 1% drift; the unmatched calls (Opus `prompt_suggestion` calls there, compactions per Claude Code's code) go into `total`, `byRate` and a new `telemetry.unseen` by `query_source`, and each compaction gains `billedUsd`. No event file leaves `telemetry: null`. The row's shape moves from `lib/pricing.py` to `lib/rows.py`.
- The operator's voice entry gains one line: a message with no language of its own gets a Russian reply.
- Planned as an elephant: three bites done (orientation, capture, billed spend). Left: `report.py` showing the unseen calls, and a position fallback should a real compaction arrive untagged. Plan: `docs/plans/orientation-cost.paused.md`.

## QA Checklist

- [ ] `row`: `python3 .claude/costs/session_cost.py --transcript <a transcript with an Edit> --out tmp/row.json` gives a row whose `orientation` has `endedBy: "Edit"`, a repo-relative `endedOn`, and a `spend` smaller than `total`.
- [ ] `answer-only`: a transcript whose first turn only answers gives `endedBy: "end_turn"`.
- [ ] `subagent`: a subagent's edit timestamped before the session's own ends orientation there.
- [ ] `compact`: a session that compacted twice carries two `compactions` entries, each with `compactedFrom`, `summaryChars` and its own `reorientation`.
- [ ] `reread`: a file `Read` before a compact and again after it shows up in that compaction's `rereads`; one edited in between does not.
- [ ] `report`: `python3 .claude/costs/report.py` prints the orientation section ("measured on N of M rows"), and the old rows under `sessions/2026-09/` parse without being rewritten.
- [ ] `receiver`: the receiver keeps only the numbers and named fields of an `api_request`, and drops the email and ids.
- [ ] `capture`: with the variables from the hook's notice set in the environment, a fresh session holds its event file in `tmp/telemetry/` after the first turn, and `receiver.log` is empty.
- [ ] `notice`: a session started without them opens on the hook's notice naming what is unset, and no receiver is listening.
- [ ] `billed`: `session_cost.py --transcript <this session's transcript> --out tmp/row.json` gives a `telemetry` whose `matched` responses agree on both prices and whose `unseen` holds the calls absent from the transcript, added into `total`.
- [ ] `compact-billed`: a session that compacted with the receiver running shows `billedUsd` on that compaction.
- [ ] `no-telemetry`: a row from a session without events carries `telemetry: null` and the same total as before.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `row` | unit | yes | `WhereOrientationEnds.test_leaves_the_acting_response_out_of_the_spend` |
| `answer-only` | unit | yes | `test_is_not_ended_by_a_subagent_s_end_turn_or_a_write_into_tmp` |
| `subagent` | unit | yes | `test_ends_at_a_subagent_s_edit_that_comes_before_the_session_s_own` |
| `compact` | unit | yes | `WhatEachCompactionCost.test_opens_a_re_orientation_at_each_boundary` |
| `reread` | unit | yes | `test_charges_a_re_read_to_the_latest_boundary_before_it`, `test_counts_no_re_read_of_a_file_written_since_it_was_read` |
| `report` | unit | yes | `WhatOrientationAverages`; old rows checked by hand (no git change after a report run) |
| `receiver` | unit | yes | `test_telemetry.py`, over a payload in Claude Code's documented shape, not a recorded one |
| `capture` | manual | yes | checked in session_01DRQDTXV7hb5HfZmSydb3FD, receiver started by the hook from inside the session |
| `notice` | unit | yes | `WhenTheHookStartsTheReceiver` |
| `billed` | unit | yes | `test_billed.py` `WhatTheEventsAdd`; checked by hand on a live session (45 matched, 2 unseen) |
| `compact-billed` | unit | partly | `test_prices_each_compaction_from_the_compact_call_nearest_it`; no real compaction has reached an event file yet |
| `no-telemetry` | unit | yes | `WithoutEvents` |

https://claude.ai/code/session_01GzP5MvWCb57dKoUqT9Qbiq
https://claude.ai/code/session_01Ggo4zc9XyUQxLEt7gCmgpD
https://claude.ai/code/session_01MEfgE9U79c5zyP9fg6irTQ
https://claude.ai/code/session_01DRQDTXV7hb5HfZmSydb3FD

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-25T22:53:19Z — "Proposed squash title/body: ``` feat: measure orientation an…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-25T22:53:19Z

[https://github.com/vzakharov/muthur/pull/112#issuecomment-5840752435](https://github.com/vzakharov/muthur/pull/112#issuecomment-5840752435)

Proposed squash title/body:

```
feat: measure orientation and billed spend in the session ledger (pr #112)
```

```
Whether a fresh session or a compact is the cheaper way to shed context
turns on what an agent spends getting its bearings before it acts, and
the ledger priced sessions only as a whole, from the transcript alone,
which misses every call it does not record.

Each cost row now records its orientation: the tokens, dollars and
context size spent before the session's first Edit, Write or
NotebookEdit inside the repository, its first AskUserQuestion or
ExitPlanMode, or its own first end_turn. Scratch writes into tmp/ do
not end it, subagent responses before that point count toward it, and
the acting response itself does not. Every compaction boundary restarts
the measure and estimates the holes the summary left: calls after the
boundary that repeat one made before it.

Claude Code's OpenTelemetry api_request events, captured by a local
receiver that keeps only their numbers and request ids, are joined to
the transcript's responses by request id. Where both exist they agree
with prices.json, so a response keeps its table price and the row warns
if the two drift. The calls the transcript never recorded, prompt
suggestions and compactions among them, join the total at the event's
price, bucketed by source, and each compaction gets its billed cost. A
session without events is priced as before. Claude Code ignores its
exporter variables in a repository's settings.json and strips them from
the processes it spawns, so the environment's settings carry them and
the start hook reads them from the claude process, listing what is
unset.

report.py averages orientation and compactions across the rows that
carry them, by what ended the phase and by opening command. Older rows
stay without the fields. Bash edits are not seen. A session's first cost
commit reads "session cost (new)", telling new sessions from continued
ones in the log.

The operator's voice entry also asks for Russian replies to messages
that carry no language of their own.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/costs/hooks/start-telemetry-receiver.sh`:73 — unresolved — last: @vzakharov (human) 2026-09-26T01:13:22Z — "агент же скажет, какие именно переменные прописать? давай то…" → [↓](#t01)
- **T02** `.claude/skills/detemplate/SKILL.md`:262 — unresolved — last: @vzakharov (human) 2026-09-26T01:16:00Z — "про что это? последнее предложение выглядит медведем" → [↓](#t02)
- **T03** `docs/remove-before-merging/squash-message.md`:40 — unresolved — last: @vzakharov (human) 2026-09-26T01:17:08Z — "не, ну на уровне muthur это явно лишнее для включения в опис…" → [↓](#t03)

<a id="t01"></a>

### `.claude/costs/hooks/start-telemetry-receiver.sh`:73 — unresolved

```diff
@@ -13,8 +16,71 @@ need_command python3 "no telemetry is being captured"
… 55 lines elided …
+This session's row is priced from its transcript alone, which misses the calls the
+transcript never records.
+
+Agent: relay this to the operator once. Claude Code ignores these variables in
```

**@vzakharov (human)** — 2026-09-26T01:13:22Z

агент же скажет, какие именно переменные прописать? давай только так, пусть говорит в самом конце сессии, типа там после finalize, и в режиме "кстати, ...", потому что это очень редко когда критичный вопрос

---

<a id="t02"></a>

### `.claude/skills/detemplate/SKILL.md`:262 — unresolved

```diff
@@ -255,7 +255,13 @@ is — each records a trap that actually bit:
… 1 line elided …
    absent.
 
-Say plainly in the report that this is the one step you could not apply yourself.
+**Where the ledger was kept, the same settings take its telemetry variables** —
+as environment variables beside the script, the list being the one
+`.claude/costs/hooks/start-telemetry-receiver.sh` prints. Claude Code ignores
+them in a repository's `.claude/settings.json`, so no file of the fork can set
+them, and until they are set every session opens on that hook's notice.
```

**@vzakharov (human)** — 2026-09-26T01:16:00Z

про что это? последнее предложение выглядит медведем

---

<a id="t03"></a>

### `docs/remove-before-merging/squash-message.md`:40 — unresolved

```diff
@@ -20,17 +20,25 @@ the measure and estimates the holes the summary left: calls after the
… 22 lines elided …
 carry them, by what ended the phase and by opening command. Older rows
 stay without the fields. Bash edits are not seen.
 
+The operator's voice entry also asks for Russian replies to messages
+that carry no language of their own.
```

**@vzakharov (human)** — 2026-09-26T01:17:08Z

не, ну на уровне muthur это явно лишнее для включения в описание коммита

---

## Timeline (status, references, and other events)

- **2026-09-26T00:05:35Z** @vzakharov cross-referenced this pull request from [#115 feat: order an elephant plan's sections as the work runs](https://github.com/vzakharov/muthur/pull/115).
- **2026-09-26T00:23:13Z** @vzakharov renamed from «feat: measure orientation cost in the session ledger» to «feat: measure orientation and billed spend in the session ledger».
- **2026-09-26T01:18:40Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/112#pullrequestreview-5323948821.
