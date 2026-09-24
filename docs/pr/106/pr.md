# PR #106: fix: keep the tree clean while the cost row is written

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/106
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/cost-row-clean-tree-5fcj6n
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-24T02:11:15Z
- **Updated:** 2026-09-24T10:17:51Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- The harness's Stop check reports "uncommitted changes" at turn end when the only change is this session's cost row. The main cause is not the race #105 describes — pricing already runs while the tree is clean — but the naming prompt, which had the agent rewrite the tracked row in place and leave it for the Stop hook to commit. On that turn the check failed every time; a second repo reproduced it the same way.
- The row's `name` field is gone, with `session_cost.py --name` and the `prompt-session-name.sh` hook that asked for it. `branch` and `prs` already group the rows. `report.py` rewrites any row still carrying a key the shape no longer writes and names each rewrite on stderr, so the first report in each repository clears the old names.
- The Stop hook commits the row by plumbing, in a throwaway index, and pushes the commit before moving the branch. The tree now differs from `HEAD` for two sub-millisecond steps, instead of for the whole add, signed commit and push.
- When a hand run did leave the row dirty, the hook's verdict says so — "the check was counting the row, it is pushed now, just stop" — alongside the check's own exit 2, so it adds no turn.
- Measured here, with the real harness check looping over one ledger run: the old hook drew 48 refusals in 203 checks (42 "unpushed", 6 "uncommitted"); the new one drew 0 in 218.

## QA Checklist

- [ ] `stop-commit` — end a turn: a `chore: session cost …` commit is on `origin`, the local branch is level with it, and the tree is clean.
- [ ] `no-change` — end a second turn with nothing new priced: no new commit.
- [ ] `staged-work` — stage an unrelated change and end the turn: it is still staged afterwards, and the cost commit touches only the row.
- [ ] `left-dirty` — rewrite the row by hand (a plain `session_cost.py` run) and end the turn: the check's complaint is followed by the hook's line saying the row is now committed and pushed.
- [ ] `push-fails` — with `origin` unreachable, the hook reports the row as committed but not pushed.
- [ ] `old-rows` — `python3 .claude/costs/report.py` over rows that carry a `name`: each is named on stderr and rewritten without it, and a second run is silent.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `stop-commit` | integration | ✅ | `test_a_row_is_committed_and_pushed_leaving_the_tree_clean`, plus `test_the_tree_is_clean_and_level_while_the_push_is_in_flight` (a `pre-receive` probe) and `test_the_row_is_signed_where_commits_are` |
| `no-change` | integration | ✅ | `test_a_row_that_has_not_changed_is_not_committed_again` |
| `staged-work` | integration | ✅ | `test_work_the_agent_has_staged_stays_staged_and_out_of_the_commit` |
| `left-dirty` | integration | ✅ | `test_a_row_left_dirty_is_named_to_the_agent_where_a_check_read_it`, `…_committed_silently_where_no_check_ran`, `test_a_refired_stop_never_blocks` |
| `push-fails` | integration | ✅ | `test_a_failed_push_is_reported_as_committed_but_not_pushed` |
| `old-rows` | unit | ✅ | `test_a_row_carrying_a_retired_key_is_rewritten_without_it`, `test_a_row_in_the_current_shape_is_left_untouched` |

Closes #105

https://claude.ai/code/session_018Uy7EfiYGHHdXHNX84dMvB

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-24T02:11:30Z — "Proposed squash title/body: ``` fix: #105 keep the tree clea…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-24T02:11:30Z

[https://github.com/vzakharov/muthur/pull/106#issuecomment-5806226550](https://github.com/vzakharov/muthur/pull/106#issuecomment-5806226550)

Proposed squash title/body:

```
fix: #105 keep the tree clean while the cost row is written (pr #106)
```

```
The harness's Stop check kept refusing turn ends over the session's
cost row. Pricing was never the window: the row is priced off the tree
and renamed in. The naming prompt was, because it had the agent rewrite
the tracked row in place and leave it for the Stop hook, so the check
saw it dirty every time; the add, signed commit and push were a smaller
window behind it.

The row's `name` field is gone, along with `--name` and the prompt that
asked for it: `branch` and `prs` already group the rows. report.py
rewrites any row still carrying a key the shape no longer writes, so
the first report in each repository clears the old names. The hook now
commits the row by plumbing in a throwaway index, pushes the commit,
and only then moves the branch and puts the file in place, so the tree
differs from HEAD for two sub-millisecond steps and is never ahead of
origin.

When a hand run did leave the row dirty, the hook's verdict says the
check was counting it and that it is now pushed, riding the check's own
exit 2 rather than adding a turn.

Fixes #105

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:4 — unresolved — last: @vzakharov (human) 2026-09-24T10:17:48Z — "давай фреймить как "убрать name", а объяснение зачем и почем…" → [↓](#t01)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:4 — unresolved

```diff
@@ -1,31 +1,31 @@
… 1 line elided …
 
 ```
-feat: #100 stage edits to always-loaded files, swap at /finalize (pr #102)
+fix: #105 keep the tree clean while the cost row is written (pr #106)
```

**@vzakharov (human)** — 2026-09-24T10:17:48Z

давай фреймить как "убрать name", а объяснение зачем и почему это в принципе не больно уже в дескрипшне

---

## Timeline (status, references, and other events)

- **2026-09-24T10:17:51Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/106#pullrequestreview-5303023971.
