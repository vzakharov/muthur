# PR #94: feat: port the API-rate session cost ledger, opt-in for adopters

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/94
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/session-costs-sekrye
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-23T08:04:05Z
- **Updated:** 2026-09-23T09:51:20Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **Ports vzakharov/vovazakharov.com@d84f30a's session cost ledger** into `.claude/costs/` as stdlib Python (≥3.9), so muthur gets it without gaining a Node stack. Each session is priced from its own transcript at Claude API rates. The pricing rules carry over unchanged: records are deduplicated by `message.id`, rates go by `(model, speed)`, cache writes are billed by TTL, subagent files are included, and a pair with no price raises an error instead of counting as free. Rows keep the source's camelCase keys, so the two ledgers read each other's rows.
- **Wired on in muthur itself.** A `Stop` hook commits and pushes the session's row at the end of every turn, after waiting out the harness's own git check. A `UserPromptSubmit` hook asks the agent to name the session once. `scripts/vet.sh` runs the ledger's tests by path. The contract doc is `.claude/costs/CLAUDE.md`, which loads when a session reads anything in that directory. The source's temporary wait log is dropped.
- **`prices.json` adds `claude-opus-5-5`** (standard and fast), taken from the bundled API pricing reference. It isn't in the source's table, and this session runs on that model, so without the rows the ledger would have stopped at its unpriced-pair error.
- **Adopters opt in explicitly.** The catalog gets group G7 with a single row, `.claude/costs/`. `ADOPTING.md` Step 2, `/detemplate` Step 1 and `/update-muthur` Step 4a each ask the operator and cite that row. `/update-muthur` never syncs `sessions/` (it's an invariant), `/spinoff` never seeds it, and `/finalize` treats a commit that only adds a row as leaving the attested head unchanged.

## QA Checklist

- [ ] `tests` — `./scripts/vet.sh` runs `.claude/costs/test_pricing.py` and `test_totals.py` by path and passes.
- [ ] `real-row` — a session in this repo ends a turn, and `.claude/costs/sessions/<YYYY-MM>/<id>.json` is committed and pushed as `chore: session cost row`. Where the transcript has `cost-state` records, the row's total is at least 98% of the `claudeCodeTotalUsd` it records.
- [ ] `name-prompt` — the next prompt carries the request to name the session. After `session_cost.py --name`, the request stops.
- [ ] `report` — `python3 .claude/costs/report.py` prints the month/week/day/branch tables and the rate table's age. `--json` prints the same totals.
- [ ] `cross-rows` — rows written by the TypeScript ledger at vovazakharov.com parse in `report.py`.
- [ ] `trunk` — on `main`, the `Stop` hook commits nothing.
- [ ] `catalog` — `scripts/check-skill-catalog.sh` passes with the G7 row.
- [ ] `opt-in-prose` — `ADOPTING.md` Steps 2 and 4, `/detemplate` Step 1 and `/update-muthur` Step 4a each ask about the ledger and cite the row. `/update-muthur` and `/spinoff` exclude `.claude/costs/sessions/`.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `tests` | yes | yes | the ported unit tests, plus row round-trip cases |
| `real-row` | no | partly | the hook was driven by hand in this session and committed its row. This container's transcripts carry no `cost-state` records, so the floor check had nothing to compare |
| `name-prompt` | no | partly | the hook was driven by hand; it asked, then went quiet once the name was set |
| `report` | yes | partly | the totals logic is unit-tested; the printing was checked by hand |
| `cross-rows` | yes | no | checked by hand against the source's three rows; not committed as a test |
| `trunk` | yes | no | checked by hand in a throwaway worktree on `main` |
| `catalog` | yes | yes | vet runs it |
| `opt-in-prose` | no | no | read the diff |

https://claude.ai/code/session_01WQUsbFXexHVXcGKiHKsxcq

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-23T08:04:23Z — "Proposed squash title/body: ``` feat: port the API-rate sess…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-23T08:04:23Z

[https://github.com/vzakharov/muthur/pull/94#issuecomment-5791279427](https://github.com/vzakharov/muthur/pull/94#issuecomment-5791279427)

Proposed squash title/body:

```
feat: port the API-rate session cost ledger, opt-in for adopters (pr #94)
```

```
A subscription price hides what the agent loop actually costs, and the
ledger vzakharov/vovazakharov.com grew in its PR #71 prices each
session from its own transcript at Claude API rates. This brings it to
muthur, where every adopter can have it.

It is a stdlib-Python port living wholly under .claude/costs/: the
pricer, a report summing rows by month, week, day and branch, a Stop
hook that commits and pushes the session's row to the branch after
every turn, and a prompt hook asking the agent to name the session
once. Python rather than the original TypeScript keeps muthur free of
a stack, and rows keep the source's keys, so either ledger reads the
other's. The rate table adds claude-opus-5-5. Muthur runs the ledger
on itself; its tests join the vet run, and .claude/costs/CLAUDE.md
carries its contract.

The ledger costs a commit and a push per turn on every branch, so it
is never taken by inference. The catalog carries it as one row in its
own group, and ADOPTING.md, /detemplate and /update-muthur each ask
the operator, citing that row. A repo's rows are its own spend:
/update-muthur and /spinoff never carry .claude/costs/sessions/, and
/finalize's attestation is not unsettled by a row-only commit after
it.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:11 — unresolved — last: @vzakharov (human) 2026-09-23T09:51:08Z — "не нужно археологию (откуда портировано), нужно что делаем.…" → [↓](#t01)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:11 — unresolved

```diff
@@ -0,0 +1,36 @@
+Proposed squash title/body:
+
+```
+feat: port the API-rate session cost ledger, opt-in for adopters (pr #94)
+```
+
+```
+A subscription price hides what the agent loop actually costs, and the
+ledger vzakharov/vovazakharov.com grew in its PR #71 prices each
+session from its own transcript at Claude API rates. This brings it to
+muthur, where every adopter can have it.
```

**@vzakharov (human)** — 2026-09-23T09:51:08Z

не нужно археологию (откуда портировано), нужно что делаем. соответственно если где-то в докстрингах тоже упоминается источник, тоже убрать

---

## Timeline (status, references, and other events)

- **2026-09-23T09:51:20Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/94#pullrequestreview-5289400293.
