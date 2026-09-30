# PR #123: feat: cap CLAUDE.md with hysteresis at 25.5k/24.5k characters

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/123
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/claude-md-size-cap-vn0pdj
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-30T15:33:26Z
- **Updated:** 2026-09-30T16:44:43Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **vet fails when the CLAUDE.md a branch will land passes 25,500 characters. A branch that took it past that point has to land it at 24,500 or under.** This is `scripts/check-claude-md-size.sh`. With a single cap, every session would trim back to just under the line, and the next session would start right at it again. The 1,000-character gap means one trim makes room for many additions.
- **Whether the branch went over is read from its history, so nothing is stored.** The check looks at every commit since the branch split from origin's default branch, plus the worktree. A base that is already over counts as crossed on the branch's first commit. With no base to compare against, only the ceiling is checked, and the output says so.
- **What gets measured is the file the branch will land.** That is the staged copy (`.claude/staged/CLAUDE.md.staged`) in any commit that has one, and CLAUDE.md otherwise. So a staged trim of an oversized file passes before `/finalize` swaps it in, and a staged copy that grew past the ceiling fails.
- **The failure message and `.claude/rules/staging.md` both say to hand the trim to a subagent.** The trim is never what the PR is for, and its cut-and-remeasure loop would use up the session's context. Imports are not counted, the count is characters rather than bytes, and there is no env override.

## QA Checklist

- [ ] `ok` — on this branch, `scripts/check-claude-md-size.sh` prints `ok — CLAUDE.md is 23609/25500 chars` and exits 0.
- [ ] `ceiling` — in a scratch clone, grow CLAUDE.md past 25,500 and commit: the check exits 1, names the commit, says `lands at 24500 or under`, and says to hand the trim to a subagent.
- [ ] `hysteresis` — in the same clone, trim to 25,000 and commit: it still fails and says how much more to cut. Trim to 24,500: it passes and says `back under 24500`.
- [ ] `staged` — `scripts/staged.sh stage CLAUDE.md` and grow the copy past the ceiling: the check fails on the copy although the real file fits.
- [ ] `vet-line` — `./scripts/vet.sh` prints the `check-claude-md-size:` line between `staged.sh check` and `check-muthur.sh`.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `ok` | unit | ✅ | `test_growth_up_to_the_ceiling_passes`; the real repo is exercised by every vet run |
| `ceiling` | unit | ✅ | `test_a_file_over_the_ceiling_fails_and_names_the_target`, `test_an_uncommitted_file_over_the_ceiling_fails` |
| `hysteresis` | unit | ✅ | `test_trimming_back_under_the_ceiling_alone_still_fails`, `test_trimming_to_the_target_passes`, `test_a_crossing_on_the_base_is_not_this_branchs` |
| `staged` | unit | ✅ | `test_a_staged_copy_over_the_ceiling_fails_though_the_real_file_fits`, `test_a_staged_trim_passes_though_the_real_file_is_over`, `test_the_swap_commit_measures_the_real_file_again` |
| `vet-line` | manual-only | — | Wiring in `vet.sh`, visible in its output |

https://claude.ai/code/session_01GXYBayCsJLcxyatvbENoSC

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-30T15:33:44Z — "Proposed squash title/body: ``` feat: cap CLAUDE.md with hys…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-30T15:33:44Z

[https://github.com/vzakharov/muthur/pull/123#issuecomment-5914494358](https://github.com/vzakharov/muthur/pull/123#issuecomment-5914494358)

Proposed squash title/body:

```
feat: cap CLAUDE.md with hysteresis at 25.5k/24.5k characters (pr #123)
```

```
Every character of the root CLAUDE.md is paid on every turn of every
session, and nothing pushed back on its growth: each addition passed its
own test while the total drifted up. Across the repos built on this
template it had reached 24-61k characters before hand trims.

vet now fails when the CLAUDE.md the branch will land passes 25,500
characters, and a branch that took it past that must land it at 24,500
or under. A single cap would be trimmed back to just under itself every
session; the gap makes one trim buy room for many additions. "Crossed"
is read off the branch's own commits since its merge-base, so no state
is kept. The landing file is the staged copy where there is one, so a
staged trim of an oversized file passes before /finalize swaps it in.

Imports are not counted, the count is characters rather than bytes, and
there is no env override. The failure message and the staging rule send
the trim to a subagent: it is never the PR's own work, and its
cut-and-remeasure loop would spend the session's context.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:21 — unresolved — last: @vzakharov (human) 2026-09-30T16:43:14Z — "означает ли это, что агент может потянуться за workaround'ом…" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:22 — unresolved — last: @vzakharov (human) 2026-09-30T16:43:53Z — "я бы сказал что адоптеры могут сами выбрать другой размер дл…" → [↓](#t02)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:21 — unresolved

```diff
@@ -0,0 +1,31 @@
… 17 lines elided …
+is kept. The landing file is the staged copy where there is one, so a
+staged trim of an oversized file passes before /finalize swaps it in.
+
+Imports are not counted, the count is characters rather than bytes, and
```

**@vzakharov (human)** — 2026-09-30T16:43:14Z

означает ли это, что агент может потянуться за workaround'ом, в котором он будет просто перемещать куски в автоимпорты?

если да, то -- крамольная мысль -- можно ли оценивать размер этой затравки по тому, что *реально* подаётся в контекст (например в логах транскрипта), а не по этому файлу? пока проверь, но изменений не делай.

---

<a id="t02"></a>

### `docs/remove-before-merging/squash-message.md`:22 — unresolved

```diff
@@ -0,0 +1,31 @@
… 18 lines elided …
+staged trim of an oversized file passes before /finalize swaps it in.
+
+Imports are not counted, the count is characters rather than bytes, and
+there is no env override. The failure message and the staging rule send
```

**@vzakharov (human)** — 2026-09-30T16:43:53Z

я бы сказал что адоптеры могут сами выбрать другой размер для скрипта, если у них другое представление об оптимальном размере

---

## Timeline (status, references, and other events)

- **2026-09-30T15:40:11Z** @vzakharov renamed from «feat: cap the CLAUDE.md a branch lands at 25k characters» to «feat: cap CLAUDE.md with hysteresis at 25.5k/24.5k characters».
- **2026-09-30T16:44:43Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/123#pullrequestreview-5369247524.
