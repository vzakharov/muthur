# PR #160: feat: report.py --all-repos, one cost report across all your repos

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/160
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/costs-siblings-8f5s0a
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-07T06:50:17Z
- **Updated:** 2026-10-07T08:55:46Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 2

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/costs/lib/github.py`:1 — unresolved — last: @vzakharov (human) 2026-10-07T08:56:28Z — "DRY относительно других гитхаб-штук, которые у нас есть?" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:4 — unresolved — last: @vzakharov (human) 2026-10-07T08:58:13Z — "давай сделаем --all-my-repos" → [↓](#t02)

---

## Body

## Summary

- `python3 .claude/costs/report.py --all-repos` finds every repo the `gh` user owns, collaborates on or reaches through an organization, keeps those whose default branch carries `.claude/costs/sessions/`, and sums their ledgers in one report: a `repo` table, then the usual tables with each branch labelled `owner/name:branch`. `--repo owner/name` (repeatable) is the alternative that reads only the named repos; the two flags are mutually exclusive, and `--month` and `--json` work with either. No clone is needed, so it runs the same locally, in a cloud session or in a routine.
- A repo qualifies by its ledger, not by the muthur watermark: the ledger is opt-in for adopters, so a watermark alone has nothing to count. Watermark-only repos are named in one line so a missing repo has a visible reason.
- `lib/github.py` does the reading through `gh api graphql`: a listing paged 40 repos at a time with 5xx retries, then month trees in aliased batches. A session id found in two repos (a fork) is counted once and named; a GraphQL error, a truncated row, or a `--repo` with no ledger stops the run with exit 1. `reshape` is split out of `read_row`, so remote rows are parsed in the current shape and never written.
- While a cross-repo run reads, it says what it is doing on stderr — the listing page, the ledgers found, the month trees read, a 5xx retry — as one line rewritten in place on a terminal and cleared before the report, so tens of seconds of reading no longer look like a hang.
- Every report, this repo's or across repos, gains a table of a period's estimated hours by role and grade — plain hours, a row per role and a column per grade, with totals. It is in `--json` as `hours`.
- `--month`, `--week` and `--day` each take a named period (`2026-10`, `2026-W41`, `2026-10-07`) or `cur` / `prev`, and narrow the whole report, hours table included, to the sessions that started in it; a week reads both months it may touch. Without one, the hours cover the current UTC month. `lib/period.py` and `lib/hours.py` keep `totals.py` and `report.py` under ~400 lines.
- Live on the operator's token: 7 ledger repos, two under other organizations, in about 32 s. Without either flag the report prints what it printed before plus the hours table.

Plan: `docs/plans/costs-siblings.completed.md`.

## QA Checklist

- [ ] `discover` — `report.py --all-repos` lists the ledger repos visible to `gh`, including ones under other organizations, and prints a `repo` table over them.
- [ ] `watermark-only` — a repo with the muthur watermark and no ledger is named in the "muthur, no ledger" line and contributes nothing.
- [ ] `narrow` — `--repo owner/name` (twice) reads only those two repos; combining it with `--all-repos` is refused; `--month YYYY-MM` reads only that month.
- [ ] `dupes` — a fork carrying its source's rows is counted once, with both repos named.
- [ ] `errors-loud` — a GraphQL error, a truncated row or a `--repo` without a ledger stops the run with the message; a 502 page is retried.
- [ ] `single-repo` — `report.py` without the flags prints what it printed before, plus the hours table.
- [ ] `status` — `report.py --all-repos` in a terminal shows one changing status line while it reads and clears it before the report; piped, each step is a `costs:` line on stderr and `--json` on stdout stays parseable.
- [ ] `hours` — the hours table covers the current month by default and the chosen period otherwise, its cells summing to the totals on both edges.
- [ ] `periods` — `--week cur`, `--week prev`, `--day prev`, `--month prev` and a named week spanning two months each narrow every table to that period; a malformed value or two period flags together is refused.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `discover` | yes | yes | `test_github.py`, fake transport with pagination; run live in the session |
| `watermark-only` | yes | yes | `test_github.py` |
| `narrow` | yes | partly | `test_github.py` covers named repos and the month filter; the flag exclusion is argparse's, checked by hand |
| `dupes` | yes | yes | `test_github.py` |
| `errors-loud` | yes | yes | `test_github.py`; exit 1 checked live against a missing repo |
| `single-repo` | yes | partly | `test_totals.py` covers the absent-`repo_of` path; output diffed by hand against the base before the hours table landed |
| `status` | partly | partly | `test_github.py` checks each step and the retry are reported; the terminal rewrite checked by hand under `script` |
| `hours` | yes | yes | `test_totals.py`: role and grade sums, rate-table order, the period filter |
| `periods` | yes | yes | `test_period.py`: edges, `cur`/`prev`, a week across two months, undated rows; run live in the session |

https://claude.ai/code/session_016f4jGaUJSdxY4GPMppVMnM
https://claude.ai/code/session_01R4hTJ7dd89fFhJ32NzFtXG

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-07T06:50:25Z — "Proposed squash title/body: ``` feat: report.py --all-repos,…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-07T06:50:25Z

[https://github.com/vzakharov/muthur/pull/160#issuecomment-6032616432](https://github.com/vzakharov/muthur/pull/160#issuecomment-6032616432)

Proposed squash title/body:

```
feat: report.py --all-repos, one cost report across all your repos (pr #160)
```

```
The cost ledger's totals stopped at the repository they were read in,
so seeing the work across all of an operator's repos meant running the
report in each and adding the numbers by hand.

`report.py --all-repos` lists every repository the `gh` user owns,
collaborates on or reaches through an organization, keeps those whose
default branch carries a ledger, and prints the usual tables over all
of them plus a per-repo table; `--repo owner/name` reads just the named
ones instead. It reads each trunk through GitHub's GraphQL API, so it
needs no clone and runs the same on a laptop, in a cloud session or in
a routine. The ledger, not the muthur watermark, qualifies a repo;
adopters that opted out of it are named in one line.

A session id found in two repos is counted once, and a GitHub error, a
truncated row or a named repo without a ledger stops the run rather
than leaving a total short. Rows are reshaped in memory only, the parse
split out of `read_row` so the single-repo report keeps rewriting its
own rows as before. While it reads, it says on stderr what it is doing,
so tens of seconds of listing do not look like a hang.

Every report also prints a period's estimated hours by role and grade,
in plain hours. `--month`, `--week` and `--day`, each named or `cur` /
`prev`, narrow the whole report to the sessions that started in that
period; without one, the hours cover the current month.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/costs/lib/github.py`:1 — unresolved — last: @vzakharov (human) 2026-10-07T08:56:28Z — "DRY относительно других гитхаб-штук, которые у нас есть?" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:4 — unresolved — last: @vzakharov (human) 2026-10-07T08:58:13Z — "давай сделаем --all-my-repos" → [↓](#t02)

<a id="t01"></a>

### `.claude/costs/lib/github.py`:1 — unresolved

**@vzakharov (human)** — 2026-10-07T08:56:28Z

DRY относительно других гитхаб-штук, которые у нас есть?

---

<a id="t02"></a>

### `docs/remove-before-merging/squash-message.md`:4 — unresolved

```diff
@@ -0,0 +1,38 @@
+Proposed squash title/body:
+
+```
+feat: report.py --all-repos, one cost report across all your repos (pr #160)
```

**@vzakharov (human)** — 2026-10-07T08:58:13Z

давай сделаем --all-my-repos

---

## Timeline (status, references, and other events)

- **2026-10-07T07:05:32Z** @vzakharov renamed from «feat: report.py --siblings, one cost report across local clones» to «feat: report.py --github, one cost report across all your repos».
- **2026-10-07T08:07:15Z** @vzakharov renamed from «feat: report.py --github, one cost report across all your repos» to «feat: report.py --all-repos, one cost report across all your repos».
- **2026-10-07T08:58:33Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/160#pullrequestreview-5439944220.
