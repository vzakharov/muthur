# PR #137: feat: human-hour estimates on the session cost rows

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/137
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/human-hour-estimates-832s9l
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-04T05:39:27Z
- **Updated:** 2026-10-04T08:20:35Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- Every session's cost row gains a revisable **human-hour estimate**: the task split into parts, each the hours one **role** (developer, designer, editor, copywriter, architect, …) at one **grade** (`junior` / `middle` / `senior` / `staff`) would spend on it, plus one comment of at most 280 characters saying why the task is that size.
- `.claude/costs/rates.json` holds a multiplier per role and per grade; a part is worth hours × role × grade junior-hours, a junior-hour being an hour of the cheapest role at the lowest grade. Applied at read time, so retuning a multiplier re-rates the whole history.
- A row carries one estimate, not a revision list: a revision replaces it and git keeps the history. It goes down on a relay (the remainder moves to the successor) and up on scope creep; a prompt hook keeps the current figure in front of the agent so revisions actually happen.
- `report.py` gains API dollars per junior-hour by month, ISO week, day and model — the figure that answers "did the same amount of work start costing more?".
- The estimate sizes the task, never the agent's pace: booking its own detours as extra hours would hide exactly the regression the figure is meant to show.

## QA Checklist

- [ ] `set` — `python3 .claude/costs/estimate.py set "…" --part 2 senior developer --part 1 middle copywriter` writes `tmp/estimates/<session-id>.json`; an unknown role or grade, negative hours, no parts or a 281-character comment is refused.
- [ ] `row` — after a turn ends, the session's row under `.claude/costs/sessions/` carries `estimate` with its parts and comment.
- [ ] `carry` — with `tmp/estimates/` deleted, the next row write keeps the estimate the previous row had.
- [ ] `other-session` — `estimate.py set … --session <id>` edits that session's committed row in place.
- [ ] `notice` — a prompt in a session with no estimate shows the instruction; once set, it shows the current figure.
- [ ] `report` — `python3 .claude/costs/report.py` prints dollars per junior-hour by month, week, day and model, and how many rows carry no estimate.
- [ ] `relay` — `/relay` lowers this session's estimate to the work done and records the remainder; `/relay take` sets the successor's to it.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `set` | yes | yes | `test_estimate.py` `TheCommand`, `WhatAnEstimateMayHold` |
| `row` | partly | partly | parse round-trip tested; the Stop-time fold is seen on this PR's own rows |
| `carry` | yes | partly | `WhichCopyWins` covers the pick; the `session_cost.py` wiring is not driven end to end |
| `other-session` | yes | yes | `TheCommand` |
| `notice` | partly | no | hook output read by hand |
| `report` | yes | yes | `TheReportsRatio` |
| `relay` | no | partly | exercised by this PR's own relay |

https://claude.ai/code/session_01637Cbn1ie9ZHp359TP13QU
https://claude.ai/code/session_01TupPLyPvBC3TKNzbq8ko4u

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-04T05:39:40Z — "Proposed squash title/body: ``` feat: human-hour estimates o…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-04T05:39:40Z

[https://github.com/vzakharov/muthur/pull/137#issuecomment-5977001448](https://github.com/vzakharov/muthur/pull/137#issuecomment-5977001448)

Proposed squash title/body:

```
feat: human-hour estimates on the session cost rows (pr #137)
```

```
The cost ledger knew what each session would have cost at API rates
and nothing about how much work that bought, so a costly week could
not be told from a wasteful one, nor a model regression from a harder
backlog.

Every session's row now carries an estimate of its work: the task
split into parts, each the hours one role (developer, designer,
editor, …) at one grade (junior to staff) would spend on it, with one
comment of at most 280 characters saying why. A revision replaces the
estimate, so it goes down on a relay, which hands the remainder to the
successor, and up when the task itself grows; it measures the task,
never the agent's own detours. `.claude/costs/estimate.py` sets it,
the Stop hook folds it into the row, and a prompt hook keeps the
current figure in front of the agent.

`rates.json` turns each part into junior-hours at read time, by a
role and a grade multiplier, so a retuned multiplier re-rates the
whole history alike. `report.py` reports API dollars per junior-hour
by month, ISO week, day and model, the figure that shows whether the
same amount of work started costing more.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

_5 resolved threads omitted; re-run with `--include-resolved` to export them._

- **T01** `.claude/costs/rates.json`:8 — unresolved — last: @vzakharov (human) 2026-10-04T08:19:52Z — "предлагаю всё-таки девелопера взять за 1, а соответственно т…" → [↓](#t01)
- **T02** `.claude/costs/rates.json`:14 — unresolved — last: @vzakharov (human) 2026-10-04T08:20:10Z — "и тут, знаешь, давай тоже сениора возьмём за 1, и в отчётах…" → [↓](#t02)

<a id="t01"></a>

### `.claude/costs/rates.json`:8 — unresolved

```diff
@@ -0,0 +1,17 @@
… 4 lines elided …
+    "qa": 1.2,
+    "designer": 1.3,
+    "analyst": 1.4,
+    "developer": 1.5,
```

**@vzakharov (human)** — 2026-10-04T08:19:52Z

предлагаю всё-таки девелопера взять за 1, а соответственно тех кто дешевле сделать < 1

---

<a id="t02"></a>

### `.claude/costs/rates.json`:14 — unresolved

```diff
@@ -0,0 +1,17 @@
… 10 lines elided …
+  "grades": {
+    "junior": 1,
+    "middle": 1.6,
+    "senior": 2.5,
```

**@vzakharov (human)** — 2026-10-04T08:20:10Z

и тут, знаешь, давай тоже сениора возьмём за 1, и в отчётах соответственно per senior-hour

---

## Timeline (status, references, and other events)

- **2026-10-04T05:47:29Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/137#pullrequestreview-5404497527.
- **2026-10-04T08:20:35Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/137#pullrequestreview-5405021725.
