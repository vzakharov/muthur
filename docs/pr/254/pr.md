# PR #254: feat: steno — an opt-in /go mode where Haiku applies dictated edits

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/254
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/haiku-edit-relay
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-29T04:49:06Z
- **Updated:** 2026-11-02T02:39:21Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 2

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `docs/remove-before-merging/squash-message.md`:19 — unresolved — last: @vzakharov (human) 2026-11-02T02:33:58Z — "пусть будет MUTHUR_EXPERIMENTAL_STENO" → [↓](#t01)
- **T02** `.claude/skills/go/steno.md`:35 — unresolved — last: @vzakharov (human) 2026-11-02T02:38:28Z — "вот что-то я задумался тут. если мы можем записать для хайку…" → [↓](#t02)

---

## Body

## Summary

- Adds **steno**, an experimental `/go` Step 2 mode, **off unless `MUTHUR_STENO=on`**: the delegating model dictates every edit a stretch of work needs (file, exact anchor, exact replacement) as one list, and a Haiku subagent applies it in the session's own tree, reporting what did not apply and anything that looks wrong nearby.
- The bet comes from the `haiku` evidence in #253: Haiku applies named corrections exactly and only those, and misreads anything it must restate — so it is a reliable pair of hands when nothing is left to interpret.
- **Costed in waves, not edits.** A wave (dictate → Haiku applies → review) re-reads the delegator's context twice and pays Haiku's run; editing directly re-reads it once a turn and absorbs discoveries inline. `delegation.py --forecast --turns <n> --waves <w>` prices both from the running session before dictating.
- **Forecast against fact.** Weighing a wave with `--waves` files its forecast beside its measured cost on `cost-ledger`, under `delegations/<YYYY-MM>/<agent-id>.json` — outside `sessions/`, so no total counts it twice. Later forecasts take Haiku's run as the mean of the measured waves.
- `go-delegation.py` grows the switch rather than a second hook being added; `/go` Step 2 and the G2 catalog entry name it.

## Dogfood

Two runs, both through the mode itself.

- **Wave 1** (hook switch, tests, `/go` Step 2, catalog — 16 items): all applied exactly; the review changed nothing. Haiku $0.06, the list as Opus output $0.14.
- **Wave 2** (the rename to steno — 30 items across five files, anchors quoted from greps rather than full reads): 29 applied exactly; one skipped because the Markdown formatter re-wrapped its paragraph after the previous item, which moved the line break the anchor quoted. `steno.md` now says to anchor a second item in one paragraph on a phrase within one line. Haiku also reported the skipped item's fix and confirmed no stray mentions remained.
- **Forecast against measured, wave 2** (first ledger row): forecast $0.127 for the wave, measured $0.117 — Haiku run $0.049, dictating re-read $0.033, reviewing re-read $0.035. Direct editing forecast at 5 turns × $0.033 = $0.165.
- **What changed from the first verdict.** Wave 1 was called "a draw at best" against one turn of parallel `Edit`s. That case is rare; real direct work is sequential, so at ~125k context the break-even is about 4 turns for one wave, and each wave the review spawns raises it.

The `haiku` entry in `delegation-model-capabilities.md` still waits on #253, which rewrites it.

## QA Checklist

- [ ] `steno-off` — with `MUTHUR_STENO` unset, entering `/go` delivers exactly the two delegation files, as before.
- [ ] `steno-on` — with `MUTHUR_STENO=on`, entering `/go` delivers `steno.md` as well.
- [ ] `steno-without-delegation` — with `MUTHUR_DELEGATION=off` and steno on, only `steno.md` and the capabilities file arrive.
- [ ] `hook-tests` — `python3 scripts/test_go_delegation.py` passes.
- [ ] `forecast` — in a live session, `python3 .claude/costs/delegation.py --forecast --turns 5 --waves 1` prints both prices and a verdict, the Haiku run read from the ledger.
- [ ] `wave-row` — `python3 .claude/costs/delegation.py <agent-id> --turns <n> --waves <w>` after a Haiku run files `delegations/<YYYY-MM>/<agent-id>.json` on `cost-ledger`; a second run rewrites the same file rather than adding one.
- [ ] `cost-tests` — `python3 .claude/costs/test_delegation.py` passes.
- [ ] `report-untouched` — `python3 .claude/costs/report.py` totals are unchanged by the `delegations/` rows.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `steno-off` | yes | unit test | |
| `steno-on` | yes | unit test | |
| `steno-without-delegation` | yes | unit test | |
| `hook-tests` | yes | vet | |
| `forecast` | partly | unit test for the arithmetic | reading the live transcript and the ledger is manual |
| `wave-row` | partly | unit test for the row's shape | the ledger push was run once by hand on this branch |
| `cost-tests` | yes | vet | |
| `report-untouched` | yes | no | `report.py` reads `sessions/` only |

https://claude.ai/code/session_01DaohkC8CqD2FqWtVHR6BSe

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-29T04:49:23Z — "Proposed squash body: ``` Haiku applies an exactly named edi…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-29T04:49:23Z

[https://github.com/vzakharov/muthur/pull/254#issuecomment-6488237203](https://github.com/vzakharov/muthur/pull/254#issuecomment-6488237203)

Proposed squash body:

```
Haiku applies an exactly named edit exactly as given and misreads
anything it has to restate, so it is a reliable pair of hands where
nothing is left to interpret. Steno puts that to work in /go's Step 2:
the delegating model dictates every edit a stretch of work needs --
file, exact anchor, exact replacement -- as one list, a Haiku subagent
applies it in the session's own tree and reports what did not apply and
what it noticed nearby, and the delegator reviews the diff and commits.

The mode is costed in waves, not edits: a wave (dictate, apply, review)
re-reads the delegator's context twice and pays Haiku's run, while
editing directly re-reads it once a turn and absorbs discoveries
inline. delegation.py --forecast prices both from the running session,
and weighing a wave files its forecast beside its measured cost on
cost-ledger under delegations/, which later forecasts calibrate from.

The mode is experimental and off unless MUTHUR_STENO=on.
go-delegation.py delivers .claude/skills/go/steno.md alongside the
delegation files when the switch is on, and with the capabilities file
even under MUTHUR_DELEGATION=off; /go Step 2 and the G2 catalog entry
name the switch.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:19 — unresolved — last: @vzakharov (human) 2026-11-02T02:33:58Z — "пусть будет MUTHUR_EXPERIMENTAL_STENO" → [↓](#t01)
- **T02** `.claude/skills/go/steno.md`:35 — unresolved — last: @vzakharov (human) 2026-11-02T02:38:28Z — "вот что-то я задумался тут. если мы можем записать для хайку…" → [↓](#t02)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:19 — unresolved

```diff
@@ -0,0 +1,30 @@
… 15 lines elided …
+and weighing a wave files its forecast beside its measured cost on
+cost-ledger under delegations/, which later forecasts calibrate from.
+
+The mode is experimental and off unless MUTHUR_STENO=on.
```

**@vzakharov (human)** — 2026-11-02T02:33:58Z

пусть будет MUTHUR_EXPERIMENTAL_STENO

---

<a id="t02"></a>

### `.claude/skills/go/steno.md`:35 — unresolved

```diff
@@ -0,0 +1,84 @@
… 22 lines elided …
+next. An edit's size barely matters: its text is output you pay for once either
+way.
+
+**Forecast before dictating.**
+`python3 .claude/costs/delegation.py --forecast --turns <n> --waves <w>` prices
+both from your current context: `<n>` the turns the work would take you —
+sequential `Edit`s, test runs and fixes, not the one-turn ideal of parallel
+calls — and `<w>` the waves you expect, counting one for what the review usually
+turns up. Dictate only where steno comes out cheaper.
+
+What `delegation.md` § "What qualifies" keeps with you stays yours to decide:
+steno moves your hands, never your judgement, so prose the loop executes may go
+through it once you have written every word of it into the list.
```

**@vzakharov (human)** — 2026-11-02T02:38:28Z

вот что-то я задумался тут. если мы можем записать для хайку всё за один раз, что сделать, то ведь мы и сделать это за раз (параллельными Edit-ами) тоже сможем?

может вся идея мертворожденная?

---

## Timeline (status, references, and other events)

- **2026-10-29T04:49:24Z** @vzakharov renamed from «feat: edit relay — an opt-in /go mode where Haiku applies the delegator's edit list» to «feat: edit relay — an opt-in /go mode where Haiku applies edits».
- **2026-10-29T05:27:15Z** @vzakharov renamed from «feat: edit relay — an opt-in /go mode where Haiku applies edits» to «feat: steno — an opt-in /go mode where Haiku applies dictated edits».
- **2026-11-02T02:39:21Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/254#pullrequestreview-5731528437.
