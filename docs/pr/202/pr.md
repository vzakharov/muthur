# PR #202: feat: [attn adopters] keep the cost ledger on its own branch

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/202
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/cost-ledger-branch-pz4s1a
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-15T17:55:01Z
- **Updated:** 2026-10-15T20:20:44Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 4

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `docs/remove-before-merging/squash-message.md`:6 — unresolved — last: @vzakharov (human) 2026-10-15T18:56:10Z — "18% как пример на этой репе, у других разумеется сумма может…" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:19 — unresolved — last: @vzakharov (human) 2026-10-15T18:56:50Z — "в смысле from main? мы УЖЕ удалили их с мейн, не дожидаясь м…" → [↓](#t02)
- **T03** `.claude/skills/update-muthur/SKILL.md`:150 — unresolved — last: @vzakharov (human) 2026-10-15T20:19:05Z — "это не медведь ли? кому бы пришло в голову брать не-main вет…" → [↓](#t03)
- **T04** `.claude/staged/.claude/skills/finalize/SKILL.md.staged`:1 — unresolved — last: @vzakharov (human) 2026-10-15T20:20:16Z — "не великоват ли? можно здесь как с некоторыми другими скилла…" → [↓](#t04)

---

## Body

## Summary

- The `Stop` hook commits every session's cost row to an orphan `cost-ledger` branch on `origin`, the source of truth. Abandoned branches, the merge turn, turns after finalize and sessions on `main` all count now. A push that loses the tip to another session re-reads it and rebuilds, so a race loses no row.
- Until the PR is finalized, the hook also commits a display copy to the feature branch, so the cost shows in the diff. "Finalized" is read off the `/finalize` attestation comment (its marker now carries the full SHA), cached in `tmp/costs/finalized/<branch>`, and dropped by any later work commit. `/finalize revoke` withdraws an attestation.
- `report.py`, `--all-my-repos`, `check_estimates.py` and `estimate.py --session` read the ledger together with the default branch's tree, one row per session, the later copy winning, so a repo that has not migrated still counts.
- **[attn adopters]** `main` no longer carries rows: `ledger.py backfill` carried 141 sessions from every branch and PR head into `cost-ledger` (every id `main` held among them), and `.claude/costs/sessions/` is removed. `/finalize` reruns the backfill and sweeps the display copies. Each adopter runs the same backfill and removal in its port.

## QA Checklist

- [ ] `ledger-write` — end a turn on a feature branch; `git ls-tree -r origin/cost-ledger` shows this session's row, and the feature branch carries the same row
- [ ] `no-ledger-yet` — in a repo with no `cost-ledger`, end a turn; the branch is created as an orphan holding one row
- [ ] `race` — two sessions end turns at once; `cost-ledger` holds both rows
- [ ] `finalized` — after `/finalize` posts the attestation, end another turn; the row updates on `cost-ledger` only, and `tmp/costs/finalized/<branch>` holds the attested SHA
- [ ] `unfinalize-implicit` — commit a source change after finalize, end a turn; the display copy reappears on the branch
- [ ] `main` — end a turn on `main`; the row lands on `cost-ledger` and `main` gets no commit
- [ ] `report-union` — `python3 .claude/costs/report.py` on this branch counts 142+ sessions with `.claude/costs/sessions/` gone from the tree
- [ ] `all-repos` — `report.py --all-my-repos` counts a repo whose rows are on `cost-ledger` only, and a repo that never migrated
- [ ] `backfill` — `python3 .claude/costs/ledger.py backfill` prints "nothing to carry" on a second run
- [ ] `sweep` — `/finalize` on this PR carries the branch's display copies into `cost-ledger`, then removes `.claude/costs/sessions/` from the branch
- [ ] `revoke` — `/finalize revoke` marks the attestation revoked and puts the PR back to draft; the next turn's row lands on the branch again

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `ledger-write` | integration | ✅ | `test_stop_hook.py` `test_an_unfinalized_branch_carries_a_copy` |
| `no-ledger-yet` | integration | ✅ | `test_the_first_row_roots_the_ledger` |
| `race` | integration | ✅ | `test_a_writer_that_takes_the_tip_first_loses_no_row` |
| `finalized` | integration | ✅ | `test_a_branch_attested_on_github_carries_none_and_the_yes_is_cached`, `test_a_cached_attestation_needs_no_github`, `test_finalized.py` |
| `unfinalize-implicit` | integration | ✅ | `test_a_work_commit_after_the_attestation_brings_the_copy_back` |
| `main` | integration | ✅ | `test_the_trunk_s_row_goes_to_the_ledger_alone` |
| `report-union` | integration | ❌ | `report.py` over a `Clone` with rows on both sides; checked live: 142 sessions |
| `all-repos` | unit | ✅ | `test_github.py` `TheTwoSides` |
| `backfill` | integration | ❌ | `Clone` with rows on several refs, run twice; checked live on this repo |
| `sweep` | manual-only | — | skill prose; runs at `/finalize` on this PR |
| `revoke` | manual-only | — | skill prose; run on a throwaway PR |

https://claude.ai/code/session_01FW5tLJjzXFv3VMwuyUby3W

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-15T17:55:15Z — "Proposed squash body: ``` Rows reached the ledger only by me…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-15T17:55:15Z

[https://github.com/vzakharov/muthur/pull/202#issuecomment-6198698041](https://github.com/vzakharov/muthur/pull/202#issuecomment-6198698041)

Proposed squash body:

```
Rows reached the ledger only by merging into main, so the report missed
abandoned branches, the turn that merges, turns after finalize and
sessions run on main itself: about 18% of the spend when measured.

The Stop hook now commits every row to an orphan `cost-ledger` branch,
which is the source of truth. It retries a racing push on the new tip,
and blocks the stop once if the push still fails. Until the PR is
finalized, the hook also commits a display copy to the feature branch,
so cost stays visible in the diff. Finalized means the attestation
comment names a SHA, which `/finalize` now writes into its marker. The
hook reads that SHA once, caches it under `tmp/`, and treats any later
commit outside `.claude/costs/sessions/` as an unfinalize.

`ledger.py backfill` copies every row any ref holds into the ledger,
the latest per session winning. This repository ran it and dropped
`.claude/costs/sessions/` from main. `/finalize` runs it over the
branch before sweeping the display copies, and `/finalize revoke`
withdraws an attestation. The readers union `cost-ledger` with the
default branch's tree, so a repository that has not migrated yet still
counts.

Adopters: in the port's PR, run `python3 .claude/costs/ledger.py
backfill`, check that the ledger holds every session your main does,
then `git rm -r .claude/costs/sessions`. The backfill pushes a new
branch to your origin, so ask your operator first. A `report.py` older
than this change undercounts a migrated repository, so run
`--all-my-repos` from an updated checkout.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:6 — unresolved — last: @vzakharov (human) 2026-10-15T18:56:10Z — "18% как пример на этой репе, у других разумеется сумма может…" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:19 — unresolved — last: @vzakharov (human) 2026-10-15T18:56:50Z — "в смысле from main? мы УЖЕ удалили их с мейн, не дожидаясь м…" → [↓](#t02)
- **T03** `.claude/skills/update-muthur/SKILL.md`:150 — unresolved — last: @vzakharov (human) 2026-10-15T20:19:05Z — "это не медведь ли? кому бы пришло в голову брать не-main вет…" → [↓](#t03)
- **T04** `.claude/staged/.claude/skills/finalize/SKILL.md.staged`:1 — unresolved — last: @vzakharov (human) 2026-10-15T20:20:16Z — "не великоват ли? можно здесь как с некоторыми другими скилла…" → [↓](#t04)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:6 — unresolved

```diff
@@ -0,0 +1,37 @@
… 2 lines elided …
+```
+Rows reached the ledger only by merging into main, so the report missed
+abandoned branches, the turn that merges, turns after finalize and
+sessions run on main itself: about 18% of the spend when measured.
```

**@vzakharov (human)** — 2026-10-15T18:56:10Z

18% как пример на этой репе, у других разумеется сумма может быть другой

---

<a id="t02"></a>

### `docs/remove-before-merging/squash-message.md`:19 — unresolved

```diff
@@ -0,0 +1,37 @@
… 14 lines elided …
+commit outside `.claude/costs/sessions/` as an unfinalize.
+
+`ledger.py backfill` copies every row any ref holds into the ledger,
+the latest per session winning. This repository ran it and dropped
+`.claude/costs/sessions/` from main. `/finalize` runs it over the
```

**@vzakharov (human)** — 2026-10-15T18:56:50Z

в смысле from main? мы УЖЕ удалили их с мейн, не дожидаясь мерджа?

---

<a id="t03"></a>

### `.claude/skills/update-muthur/SKILL.md`:150 — unresolved

```diff
@@ -142,11 +142,12 @@ Exclude it unconditionally, whatever `adopted` says.
 
 ### Never sync the source's cost rows
 
-`.claude/costs/sessions/` is the source's own ledger — what _its_ sessions cost
-— and the one path in `.claude/costs/` that is data rather than machinery. A
-sync that ported it would add the source's spend to this repo's totals, and no
-later report could tell the two apart. Exclude it unconditionally too, whether
-or not this repo runs the ledger.
+A source's rows live on its `cost-ledger` branch, which no sync reads. A source
+that has not moved them there yet still carries them in
+`.claude/costs/sessions/`, the one path in `.claude/costs/` that is data rather
+than machinery: porting it would add the source's spend to this repo's totals,
+and no later report could tell the two apart. Exclude it unconditionally too,
+whether or not this repo runs the ledger.
```

**@vzakharov (human)** — 2026-10-15T20:19:05Z

это не медведь ли? кому бы пришло в голову брать не-main ветку?

---

<a id="t04"></a>

### `.claude/staged/.claude/skills/finalize/SKILL.md.staged`:1 — unresolved

**@vzakharov (human)** — 2026-10-15T20:20:16Z

не великоват ли? можно здесь как с некоторыми другими скиллами разделить по принципу "сразу -- то что нужно всем; то что нужно лишь в отдельных случаях -- в соседние md-шки"?

---

## Timeline (status, references, and other events)

- **2026-10-15T18:03:32Z** @vzakharov renamed from «feat: keep the cost ledger on its own branch» to «feat: [attn adopters] keep the cost ledger on its own branch».
- **2026-10-15T20:20:44Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/202#pullrequestreview-5538367941.
