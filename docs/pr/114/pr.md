# PR #114: feat: offer adopters muthur updates at session start

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/114
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/muthur-self-update-0izdlm
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-25T23:59:35Z
- **Updated:** 2026-09-26T00:55:17Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **Why:** a sync 20–30 commits behind is miserable to run in one go, so adopters' sessions offer the update when there's something to pull, and the lag stays small.
- **Nudge:** a new `SessionStart` entry (startup only, 30s timeout) runs `scripts/muthur-sync.sh nudge`. It fetches the trunk and reads its watermark. When the source has moved past it, the nudge prints the commit titles, the changed files marked `here` / `not here`, the `adopted` keys, and the rules for the offer: a ride-along for a commit or two, a new session for more, and nothing investigated before the operator says yes. It says nothing in the template itself, in an unhydrated fork, in a repo that's up to date, or while a fresh lock is held. When it can't run, it prints one line and the session still starts.
- **Lock:** `muthur-sync.sh claim` pushes a `muthur-sync-lock-<lastSyncedSha>` branch to the adopter's origin with an empty-expect `--force-with-lease`, so of two racing claims exactly one lands. The agent claims just before making the offer. If the lock is taken (exit 3), it drops the offer without mentioning it. If the operator says no, `muthur-sync.sh release` deletes the lock, leased on its SHA. A claim the session already holds succeeds again, matched on the `Claimed-By` and `Session` trailers. A lock over 24h old is reported with those trailers, and `--takeover` replaces it only on the operator's say-so. The lock is named after the trunk's watermark, so when a sync lands the next one gets a new name and nothing has to be deleted.
- **`/update-muthur`:** a new § "Arguments" defines `claimed` (skip the claim: the session that made the offer holds it) and `ride-along` (the sync is part of the task already running, so it skips Step 3a). Step 1 claims the lock. Step 2 runs `muthur-sync.sh clone`, whose credential helper keeps `$GH_TOKEN` off disk. Step 3a hands the candidates to `/task`, which can split the work into an elephant or a pizza. Step 7 bumps the watermark to the sync's boundary. § "Offered at session start" covers both shapes of the offer. The script gets no catalog row of its own: the `/update-muthur` row carries it, and #116 applies that rule to the whole catalog. `scripts/test_muthur_sync.py` (23 cases) runs under `check-muthur.sh`.

## QA Checklist

- [ ] `silent-exits`: in the template itself, an unhydrated fork, and an up-to-date adopter, a new session shows no nudge
- [ ] `lag-nudge`: an adopter a few commits behind sees titles, `here` / `not here` files and its `adopted` keys, capped at 40 lines
- [ ] `no-dig`: before the operator answers the offer, the agent runs no clone and no `git show`
- [ ] `claim-before-offer`: the agent claims just before offering, and when the claim exits 3 it says nothing about the sync
- [ ] `claim-race`: of two concurrent `claim`s, exactly one exits 0 and the other exits 3 and names the holder
- [ ] `reclaim`: a second `claim` from the session holding the lock exits 0 and leaves the lock unchanged
- [ ] `release`: after a no, `release` deletes this session's lock and refuses one held by someone else
- [ ] `stale-lock`: a lock older than 24h makes the nudge print its `Claimed-By` and `Session`
- [ ] `ride-along`: on a yes mid-task, `/update-muthur ride-along` runs after the task's commits and does not route through `/task`
- [ ] `new-session`: on a yes, a cloud session is spawned with `/update-muthur claimed`
- [ ] `boundary`: a split sync bumps `lastSyncedSha` to its slice's last source commit
- [ ] `vet`: `./scripts/vet.sh` green, including `scripts/test_muthur_sync.py`

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `silent-exits` | integration | ✅ | `SilentTest` in `test_muthur_sync.py`, including a sync that landed after the clone's last fetch |
| `lag-nudge` | integration | ✅ | `LagTest`: output, exclusions, cap, branch behind the trunk, unreachable source |
| `no-dig` | manual-only | — | agent behavior; read a real adopter session |
| `claim-before-offer` | manual-only | — | agent behavior; the script half is `LockTest.test_second_claim_is_refused` |
| `claim-race` | integration | ✅ | `LockTest.test_concurrent_claims`, from two clones at once |
| `reclaim` | integration | ✅ | `LockTest.test_reclaim_by_the_holder`, plus another session of the same operator refused |
| `release` | integration | ✅ | `ReleaseTest`: frees the lock, keeps someone else's, nothing to release |
| `stale-lock` | integration | ✅ | `GIT_COMMITTER_DATE` on the claim commit |
| `ride-along` | manual-only | — | skill procedure; needs an adopter a commit behind |
| `new-session` | manual-only | — | needs `create_session` in a cloud session on an adopter |
| `boundary` | manual-only | — | skill procedure; check on the first split sync |
| `vet` | integration | — | not run this round; `/finalize` runs it |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01JRUMXLF7TjRQNxmGzV5zzo

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-25T23:59:50Z — "Proposed squash title/body: ``` feat: offer adopters muthur…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-25T23:59:50Z

[https://github.com/vzakharov/muthur/pull/114#issuecomment-5841275681](https://github.com/vzakharov/muthur/pull/114#issuecomment-5841275681)

Proposed squash title/body:

```
feat: offer adopters muthur updates at session start (pr #114)
```

```
A sync twenty or thirty commits behind is miserable to run in one go,
so an adopter's sessions offer the update as soon as there is one.

A SessionStart nudge compares the trunk's watermark with the source's
HEAD. When it has moved, the nudge prints the commit titles, the changed
files marked by whether they exist here, and the adopted keys, and tells
the agent to offer an update at a natural moment: carried along with the
task at hand for a commit or two, as a new session for more. The agent
investigates nothing until the operator says yes.

The lock is a muthur-sync-lock-<lastSyncedSha> branch on the adopter's
origin, pushed with an empty-expect lease so exactly one of two racing
sessions wins. The agent claims it just before offering, so a sync
another session holds is never offered, and releases it on a no. A lock
over a day old is reported with its holder and session. Keyed on the
trunk's watermark, it is freed by the sync landing.

/update-muthur claims that lock and hands its candidate set to /task,
which can split a long lag across sessions; run as `ride-along` inside
another task, it stays part of that task instead. Each slice bumps the
watermark to its own boundary in the source rather than always to HEAD.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

_4 resolved threads omitted; re-run with `--include-resolved` to export them._

- **T01** `.claude/skills/update-muthur/SKILL.md`:178 — unresolved — last: @vzakharov (human) 2026-09-26T00:55:16Z — "не, верни тогда как было. ну окажется что кто-то уже заклейм…" → [↓](#t01)

<a id="t01"></a>

### `.claude/skills/update-muthur/SKILL.md`:178 — unresolved

```diff
@@ -155,63 +157,48 @@ chain is what makes it load-bearing.
… 7 lines elided …
 is still a placeholder — there is no baseline to diff against, and guessing one
 would either re-port work already here or skip work that isn't.
 
+Then claim the lock with `scripts/muthur-sync.sh claim`, so no parallel session
```

**@vzakharov (human)** — 2026-09-26T00:41:55Z

зачем мы хотим клеймить до того как даже зададим вопрос? можно типа перед тем как задать -- клеймишь, занята? ок, забили, едем дальше. нет -- задаём вопрос.

**@vzakharov (agent)** — 2026-09-26T00:52:42Z

Было наоборот: сначала вопрос, клейм только после «да». Поэтому сессия могла предложить синк, который уже держит другая, и потом забрать предложение назад. Сделал по-твоему (c38d565): клейм прямо перед тем, как предложить; exit 3 — молча не предлагаем; «нет» — `muthur-sync.sh release`, который удаляет только свой лок (с lease на его SHA, так что takeover посередине не пострадает). Повторный `claim` из той же сессии теперь проходит, поэтому Step 1 после предложения ничего не ломает. Цена записана в § "Offered at session start": если на предложение так и не ответили, лок висит сутки до stale, и всё это время nudge у остальных молчит.

**@vzakharov (human)** — 2026-09-26T00:55:16Z

не, верни тогда как было. ну окажется что кто-то уже заклеймил, скажет, зиняйте бананов нема

---

## Timeline (status, references, and other events)

- **2026-09-26T00:45:24Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/114#pullrequestreview-5323814970.
- **2026-09-26T00:50:11Z** @vzakharov cross-referenced this pull request from [#116 Fold tool rows into their skills' catalog rows](https://github.com/vzakharov/muthur/issues/116).
- **2026-09-26T00:51:51Z** @vzakharov renamed from «feat: adopters update muthur themselves» to «feat: offer adopters muthur updates at session start».
