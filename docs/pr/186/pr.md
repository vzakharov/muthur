# PR #186: feat: [attn adopters] #185 repo estimate roles, kept on cost-ledger

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/186
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/repo-estimate-roles-cwl9kz
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-13T05:22:20Z
- **Updated:** 2026-10-22T07:52:31Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 2

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/costs/sessions/2026-10/327a2b9c-9636-577f-b3af-e851b486a733.json`:14 — unresolved — last: @vzakharov (human) 2026-10-22T07:50:12Z — "prompter? адоптеры это же обычно такие же агенты" → [↓](#t01)
- **T02** `.claude/costs/estimate.py`:1 — unresolved — last: @vzakharov (human) 2026-10-22T07:51:12Z — "так, а у нас два estimate.py это нормально, ничего там у нас…" → [↓](#t02)

---

## Body

## Summary

- **A repository's own estimate roles live in `.claude/costs/rates.repo.json` on `cost-ledger`, beside the rows they rate, and nowhere else.** The `Stop` hook writes rows to the ledger from every branch, so a table read off the default branch left rows that only an unmerged branch could rate — one such `artist` row stopped `report.py --all-my-repos`. Each entry is `{"multiplier", "grade", "work"}`, booked at that one grade, so its hours land in an existing grade column.
- **Written by commands, not by editing a file:** `estimate.py role set <name> <multiplier> <grade> "<work>"` and `role drop <name>` commit and push through the same ledger append the `Stop` hook uses, so `git log cost-ledger` reads as the table's history. `role set` refuses a role `rates.json` rates; `role drop` refuses a role ledger rows book that the shared table does not rate, so every booked role stays rateable. `estimate.py set` reads the local ledger copy and fetches only on a role it does not know.
- **A collision keeps history whole:** when `rates.json` later takes up a role a ledger adds, that repository's rows keep their own multiplier, and the report, `check_estimates.py` and the estimate notice each name both rates and point at `role drop` to adopt the shared one.
- **Readers and migration:** `report.py` reads rows and table at one fetched ledger tip, and across repositories reads `refs/heads/cost-ledger:.claude/costs/rates.repo.json`. The estimate notice fetches the ledger once in a fresh container (and says so if it cannot), and names `role set` as the way to add a role. `ledger.py backfill` carries a tree file onto the ledger, stopping where the two differ; `check_estimates.py` fails while a tree copy remains.

## QA Checklist

- [ ] `role-set` — `estimate.py role set artist 0.9 senior "a persona's reflections on songs"`: `cost-ledger` on `origin` gains `.claude/costs/rates.repo.json` with that entry under the commit `chore: estimate role artist ×0.9 at senior`, and the default branch gains no file.
- [ ] `notice` — Start a fresh session in that repository: the estimate notice names `artist`, `senior`, the work and `--part <hours> senior artist`, plus the `role set` sentence.
- [ ] `fixed-grade` — `estimate.py set --part 1 middle artist "…"` is refused with "booked at `senior` only"; `--part 1 senior artist "…"` is accepted.
- [ ] `refusals` — `role set copywriter …` is refused ("rates.json rates this role already"); after a session books `artist`, `role drop artist` is refused naming that session.
- [ ] `shadowed` — Add `artist` to `rates.json` at another multiplier: `report.py`, `scripts/vet.sh` and the notice each name both rates, the report's figures keep ×0.9 for this repository's rows, and the vet run still passes.
- [ ] `migrate` — In vzakharov/life (`tutor` in the tree), `ledger.py backfill` carries the table onto `cost-ledger`; the vet run fails until `git rm .claude/costs/rates.repo.json`.
- [ ] `cross-repo` — `report.py --repo vzakharov/vovazakharov.com`, once `artist` is on its ledger via `role set`, rates its `artist` rows instead of stopping.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `role-set` | integration | ✅ | `test_estimate.py` `TheCommand` over a bare-origin clone |
| `notice` | integration | ✅ | `test_estimate_notice.py`, including the fresh-container fetch and a failed fetch |
| `fixed-grade` | unit | ✅ | `test_estimate.py` `RolesARepositoryAdds` |
| `refusals` | integration | ✅ | `test_estimate.py` `role_change` cases and `TheCommand` drop refusal |
| `shadowed` | integration | ✅ | `test_estimate.py`, `test_check_estimates.py`, `test_estimate_notice.py`; the live report run is manual |
| `migrate` | integration | ✅ | `test_estimate.py` `BackfillCarriesATreeTable`, `test_check_estimates.py` tree-file failure; the run in life is manual |
| `cross-repo` | integration | ✅ | `test_github.py` answers the roles blob only ledger-side; the live run against GitHub is manual |

Closes #185

https://claude.ai/code/session_01CL74mAK6rHiTBNBBCoocfQ

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-13T05:22:36Z — "Proposed squash body: ``` An adopter whose sessions do work…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-13T05:22:36Z

[https://github.com/vzakharov/muthur/pull/186#issuecomment-6138858286](https://github.com/vzakharov/muthur/pull/186#issuecomment-6138858286)

Proposed squash body:

```
An adopter whose sessions do work no shared estimate role captures
could only add a role by editing rates.json, which collides with every
sync of it.

A repository now keeps roles of its own in .claude/costs/rates.repo.json
on the cost-ledger branch, beside the rows they rate: each a multiplier,
one grade and a line of the work booked under it. `estimate.py role set`
and `role drop` write it there directly, the way the Stop hook writes a
row, so a role is on the ledger before any row can book it, from any
branch, merged or not. A retune re-rates every row under the role alike,
and `role drop` refuses while a row books a role nothing else rates.
Every reader, report.py across repositories included, rates rows by
the table from the same ledger.

The role is fixed-grade, so its hours land in an existing column of the
hours table. The table only adds: `role set` refuses a role rates.json
rates. Where rates.json later takes one up, that repository's rows keep
its own rate and every reader warns. The estimate notice names each
added role, its grade, its work and the exact --part.

Adopters: a repository that took this branch early carries a tree
.claude/costs/rates.repo.json, which the vet run now fails on. Run
`python3 .claude/costs/ledger.py backfill` to carry it onto
cost-ledger, then `git rm` it. This pushes to cost-ledger, so it waits
on the operator's yes.

Closes #185

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/costs/sessions/2026-10/327a2b9c-9636-577f-b3af-e851b486a733.json`:14 — unresolved — last: @vzakharov (human) 2026-10-22T07:50:12Z — "prompter? адоптеры это же обычно такие же агенты" → [↓](#t01)
- **T02** `.claude/costs/estimate.py`:1 — unresolved — last: @vzakharov (human) 2026-10-22T07:51:12Z — "так, а у нас два estimate.py это нормально, ничего там у нас…" → [↓](#t02)

<a id="t01"></a>

### `.claude/costs/sessions/2026-10/327a2b9c-9636-577f-b3af-e851b486a733.json`:14 — unresolved

```diff
@@ -0,0 +1,95 @@
… 10 lines elided …
+      {
+        "hours": 1.0,
+        "grade": "middle",
+        "role": "copywriter",
```

**@vzakharov (human)** — 2026-10-22T07:50:12Z

prompter? адоптеры это же обычно такие же агенты

---

<a id="t02"></a>

### `.claude/costs/estimate.py`:1 — unresolved

**@vzakharov (human)** — 2026-10-22T07:51:12Z

так, а у нас два estimate.py это нормально, ничего там у нас не WET?

---

## Timeline (status, references, and other events)

- **2026-10-15T10:25:58Z** @vzakharov referenced this pull request in a commit.
- **2026-10-15T10:26:12Z** @vzakharov cross-referenced this pull request from [#199 school: #198 Золтан: «Оливер Твист», гл. 5; § 9, Нидерланды; стили речи](https://github.com/vzakharov/life/pull/199).
- **2026-10-15T10:49:48Z** @vzakharov referenced this pull request in a commit.
- **2026-10-16T10:41:22Z** @vzakharov referenced this pull request in a commit.
- **2026-10-21T15:37:48Z** @vzakharov cross-referenced this pull request from [#215 feat: [attn adopters] keep a repo's estimate roles on cost-ledger](https://github.com/vzakharov/muthur/pull/215).
- **2026-10-21T16:20:22Z** @vzakharov renamed from «feat: let an adopting repository add fixed-grade estimate roles» to «feat: [attn adopters] #185 repo estimate roles, kept on cost-ledger».
- **2026-10-22T07:52:31Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/186#pullrequestreview-5610863228.
