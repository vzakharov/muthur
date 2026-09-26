# PR #114: feat: adopters update muthur themselves

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/114
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/muthur-self-update-0izdlm
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-25T23:59:35Z
- **Updated:** 2026-09-26T00:45:24Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **Why:** a sync 20–30 commits behind is miserable to run in one go, so adopters' sessions keep the lag small without being asked.
- **Nudge:** a new `SessionStart` entry (startup only, 30s timeout) runs `scripts/muthur-sync.sh nudge`. It fetches the trunk and reads its watermark. When the source has moved past it, the nudge prints the commit titles, the changed files marked `here` / `not here`, the `adopted` keys, and the rules for the offer: a ride-along for a commit or two, a new session for more, and nothing investigated before the operator says yes. It says nothing in the template itself, in an unhydrated fork, in a repo that's up to date, and while a fresh lock is held. When it can't run, it prints one line and the session still starts.
- **Lock:** `muthur-sync.sh claim` pushes a `muthur-sync-lock-<lastSyncedSha>` branch to the adopter's origin with an empty-expect `--force-with-lease`, so of two racing claims exactly one lands. The loser exits 3 and names the holder. A lock over 24h old is reported with its `Claimed-By` and `Session` link, and `--takeover` replaces it only on the operator's say-so. The name is keyed on the trunk's watermark, so a landed sync frees it and nothing has to be deleted.
- **`/update-muthur` becomes a task:** Step 1 claims the lock, unless invoked as `/update-muthur claimed`. Step 2 runs `muthur-sync.sh clone`, whose credential helper keeps `$GH_TOKEN` off disk. New Step 3a hands the candidates to `/task`, which can split the work into an elephant or a pizza. Step 7 bumps the watermark to the sync's boundary. The new § "Offered at session start" covers the ride-along and new-session shapes. The catalog gains a row for the script, and `scripts/test_muthur_sync.py` (18 cases) runs under `check-muthur.sh`.

## QA Checklist

- [ ] `silent-exits` — in the template itself, an unhydrated fork, and an up-to-date adopter, a new session shows no nudge
- [ ] `lag-nudge` — an adopter a few commits behind sees titles, `here` / `not here` files and its `adopted` keys, capped at 40 lines
- [ ] `no-dig` — before the operator answers the offer, the agent runs no clone, no `git show` and no claim
- [ ] `claim-race` — two concurrent `claim`s: exactly one exits 0, the other exits 3 and names the holder
- [ ] `stale-lock` — a lock older than 24h makes the nudge print its `Claimed-By` and `Session`
- [ ] `new-session` — on yes, a cloud session spawns `/update-muthur claimed` after claiming
- [ ] `boundary` — a split sync bumps `lastSyncedSha` to its slice's last source commit
- [ ] `vet` — `./scripts/vet.sh` green, including `scripts/test_muthur_sync.py`

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `silent-exits` | yes | yes | `SilentTest` in `test_muthur_sync.py`, including a sync that landed after the clone's last fetch |
| `lag-nudge` | yes | yes | `LagTest`: output, exclusions, cap, branch behind the trunk, unreachable source |
| `no-dig` | no | — | agent behavior; read a real adopter session |
| `claim-race` | yes | yes | `LockTest.test_concurrent_claims`, from two clones at once |
| `stale-lock` | yes | yes | `GIT_COMMITTER_DATE` on the claim commit |
| `new-session` | no | — | needs `create_session` in a cloud session on an adopter |
| `boundary` | no | — | skill procedure; check on the first split sync |
| `vet` | yes | yes | green on 8413488 |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01LW3YMBbyJ6axgYAshf5Zrr

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-25T23:59:50Z — "Proposed squash title/body: ``` feat: adopters update muthur…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-25T23:59:50Z

[https://github.com/vzakharov/muthur/pull/114#issuecomment-5841275681](https://github.com/vzakharov/muthur/pull/114#issuecomment-5841275681)

Proposed squash title/body:

```
feat: adopters update muthur themselves (pr #114)
```

```
A sync twenty or thirty commits behind is miserable to run in one go,
so an adopter's sessions now keep the lag small without being asked.

A SessionStart nudge compares the trunk's watermark with the source's
HEAD. When it has moved, the nudge prints the commit titles, the changed
files marked by whether they exist here, and the adopted keys, and tells
the agent to offer an update at a natural moment: carried along with the
task at hand for a commit or two, as a new session for more. The agent
investigates nothing until the operator says yes.

The claim is a muthur-sync-lock-<lastSyncedSha> branch on the adopter's
origin, pushed with an empty-expect lease so exactly one of two racing
sessions wins. It is silent under a day old and names its holder and
session after that. Keyed on the trunk's watermark, it is freed by the
sync landing, with nothing to delete.

/update-muthur claims that lock and hands its candidate set to /task,
which can split a long lag across sessions. Each slice bumps the
watermark to its own boundary in the source rather than always to HEAD.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:4 — unresolved — last: @vzakharov (human) 2026-09-26T00:37:14Z — "ну, они и так это делали, muthur за них этого не делал :) на…" → [↓](#t01)
- **T02** `.claude/skills/update-muthur/catalog.md`:94 — unresolved — last: @vzakharov (human) 2026-09-26T00:40:21Z — "договаривались не включать строчки для пунктов, не являющихс…" → [↓](#t02)
- **T03** `.claude/skills/update-muthur/SKILL.md`:166 — unresolved — last: @vzakharov (human) 2026-09-26T00:41:55Z — "зачем мы хотим клеймить до того как даже зададим вопрос? мож…" → [↓](#t03)
- **T04** `.claude/skills/update-muthur/SKILL.md`:199 — unresolved — last: @vzakharov (human) 2026-09-26T00:42:40Z — "а это всё почему удалили (если оправданно -- я только за)?" → [↓](#t04)
- **T05** `.claude/skills/update-muthur/SKILL.md`:344 — unresolved — last: @vzakharov (human) 2026-09-26T00:44:29Z — "а сам update-muthur понимает, что может быть частью чего-то…" → [↓](#t05)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:4 — unresolved

```diff
@@ -0,0 +1,33 @@
+Proposed squash title/body:
+
+```
+feat: adopters update muthur themselves (pr #114)
```

**@vzakharov (human)** — 2026-09-26T00:37:14Z

ну, они и так это делали, muthur за них этого не делал :) надо как-то перефразировать понятнее ('auto' updates?)

---

<a id="t02"></a>

### `.claude/skills/update-muthur/catalog.md`:94 — unresolved

```diff
@@ -90,7 +90,8 @@ enforces it the same way.
… 2 lines elided …
 | --- | --- | --- | --- | --- |
-| `/update-muthur` | Pull the agent infrastructure forward from the repo you adopted it from: diff since the watermark, triage commit by commit, port what applies. Carries `watermark.json` — which re…
+| `/update-muthur` | Pull the agent infrastructure forward from the repo you adopted it from: diff since the watermark, triage commit by commit, port what applies — claiming a lock first, and handing…
+| `scripts/muthur-sync.sh` | The sync's shared mechanics. `nudge`, run at session start, offers an update when the source has moved past the trunk's watermark, and is silent otherwise; `claim` takes the `muthur-sync-lock-<lastSyncedSha>` branch on your origin, so parallel sessions never sync the same range twice; `clone` is the source clone `/update-muthur` Step 2 runs. A nudge that cannot run says so in one line and lets the session start. | `bash`, `jq`, `gh`, git transport to the source repo and to origin; `.claude/settings.json` wiring (G4) | `scripts/lib/gh-repo.sh` (G2) | adopt — **with `/update-muthur`** |
```

**@vzakharov (human)** — 2026-09-26T00:40:21Z

договаривались не включать строчки для пунктов, не являющихся самостоятельными (самостоятельный тут update-muthur, это один из его инструментов). если адоптер не хочет брать какой-то инструмент, он просто прописывает это в комменте в watermark

перепроверь есть ли уже issue на подчистить весь каталог таким образом; если нет заведём давай

---

<a id="t03"></a>

### `.claude/skills/update-muthur/SKILL.md`:166 — unresolved

```diff
@@ -155,63 +157,48 @@ chain is what makes it load-bearing.
… 7 lines elided …
 is still a placeholder — there is no baseline to diff against, and guessing one
 would either re-port work already here or skip work that isn't.
 
+Then claim the lock with `scripts/muthur-sync.sh claim`, so no parallel session
```

**@vzakharov (human)** — 2026-09-26T00:41:55Z

зачем мы хотим клеймить до того как даже зададим вопрос? можно типа перед тем как задать -- клеймишь, занята? ок, забили, едем дальше. нет -- задаём вопрос.

---

<a id="t04"></a>

### `.claude/skills/update-muthur/SKILL.md`:199 — unresolved

```diff
@@ -155,63 +157,48 @@ chain is what makes it load-bearing.
… 30 lines elided …
+scripts/muthur-sync.sh clone tmp/muthur-source
 ```
 
-**One recipe, whatever the source's visibility.** The credential helper is a
-no-op against a public repo rather than an error, and the lazy blob fetches still
-resolve, so there is no public/private branch to take here — verified, not
-assumed.
-
-The blobless partial clone carries **full history** for a fraction of the
-transfer, so any `git log <sha>..HEAD` resolves.
-
-**`-c` after `clone`, not `git -c` before it.** The two spellings look
-interchangeable and are not: `clone -c` writes the helper into the new repo's
-config, where the lazy blob fetches a later `git show` triggers can still find
-it, while `git -c … clone` applies it to the clone alone. Under the second, the
-log works and the first diff dies on `could not read Username`. The token does
-land in `<scratchpad>/up/.git/config` in the clear, which is the other reason the
-clone belongs in the scratchpad rather than anywhere under the repo.
-
-**Do not reach for `--depth` or `--shallow-since` instead.** A shallow clone that
-doesn't reach back past `lastSyncedSha` fails with a bare "unknown revision",
-which reads like a bad SHA rather than a truncated clone. (`ADOPTING.md`'s
-first-contact clone *is* shallow — correct there, where only the working tree
-matters, and wrong here.)
```

**@vzakharov (human)** — 2026-09-26T00:42:40Z

а это всё почему удалили (если оправданно -- я только за)?

---

<a id="t05"></a>

### `.claude/skills/update-muthur/SKILL.md`:344 — unresolved

```diff
@@ -315,6 +325,29 @@ Provenance needs no prose. `watermark.json`'s `lastSyncedSha`, committed in Step
… 14 lines elided …
+in the gap, then one of two shapes:
+
+- **Ride-along** — a lag of a commit or two touching files here, offered once
+  the session is already making a change on its branch. Run `/update-muthur
+  claimed` in this session, on this branch, after the task's own commits. The
+  sync's commits ride that task's PR, and its triage table goes in that PR's
```

**@vzakharov (human)** — 2026-09-26T00:44:29Z

а сам update-muthur понимает, что может быть частью чего-то большего? возникает небольшая коллизия: мы говорим ему что он таск, при этом он может быть частью другого таска. можно иметь ещё один режим "/update-muthur <smth>", в котором он понимает, что он НЕ task (в отличие от того добавления которое мы сверху сделали которое говорит что да)

---

## Timeline (status, references, and other events)

- **2026-09-26T00:45:24Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/114#pullrequestreview-5323814970.
