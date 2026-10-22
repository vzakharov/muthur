# PR #217: feat: add /merge, routing by whether the branch is finalized

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/217
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/merge-skill-rnvj7p
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-22T10:55:37Z
- **Updated:** 2026-10-22T12:26:18Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 3

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/skills/finalize/merge.md`:22 — unresolved — last: @vzakharov (human) 2026-10-22T12:23:23Z — "у нас тут infinite loop не создаётся случайно?" → [↓](#t01)
- **T02** `.claude/skills/merge/SKILL.md`:17 — unresolved — last: @vzakharov (human) 2026-10-22T12:24:24Z — "эм, а как тут можно что-то ask? вроде аргументов нет у скилл…" → [↓](#t02)
- **T03** `.claude/skills/merge/SKILL.md`:26 — unresolved — last: @vzakharov (human) 2026-10-22T12:25:04Z — "хм, стоит ли это last rule выделить в отдельный файл, чтобы…" → [↓](#t03)

---

## Body

## Summary

- Adds a `/merge` skill as the single entry for an operator's ask to merge: an unfinalized branch runs `/finalize and merge`; a finalized one runs `/check-merge` and merges under the same step-8 gate, or syncs via `/sync-branch` and stands down when the base advanced.
- Splits ownership: `/merge` owns reading the ask and the "finalized?" test; `finalize/merge.md` keeps the gate, the merge and the stand-down, which `/merge` cites by section. `/finalize and merge` does not route through `/merge`, which would loop or judge only the run's tail.
- On the finalized path the attestation itself is part of the gate: a line short of green stands the run down, while a `no vet` attestation is judged by the gate's existing "Under `no vet`" entry, as `/finalize and merge` judges it.
- Repoints `/finalize`'s description (through a staged copy, swapped in at `/finalize`) and body, `merge.md`, and `/handle`'s held-merge hand-off at `/merge`; adds the catalog entry.

## QA Checklist

- [ ] `unfinalized` — on a draft PR with no attestation, `/merge` opens by saying it reads the ask as `/finalize and merge` and runs land prep through step 8.
- [ ] `finalized-merge` — on a finalized PR whose base has not moved and with no open feedback, `/merge` runs `/check-merge` once, reports `contained`, and squash-merges with the proposal's title and body, without re-running land prep.
- [ ] `finalized-red-attestation` — on a finalized PR whose attestation reports anything short of green, `/merge` stands down and names the attestation line.
- [ ] `finalized-no-vet` — on a docs-only PR finalized with `no vet`, base unmoved, `/merge` merges rather than standing down on the skipped vet line.
- [ ] `advanced` — on a finalized PR whose base advanced, `/merge` runs `/sync-branch`, reconciles the squash record, and stands down naming step 6; a second `/merge` then runs `/finalize and merge`.
- [ ] `landed` — on a merged or closed PR, `/merge` reports it and stops.
- [ ] `handle-held` — `/handle <branch> and merge` reports the held merge with `/merge <branch>` as the line to type.
- [ ] `merge-main` — "merge main" still routes to `/sync-branch`, not `/merge`.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `unfinalized` | manual | ❌ | Agent-procedure behavior; needs a live session on a throwaway PR |
| `finalized-merge` | manual | ❌ | Same; merges a throwaway PR |
| `finalized-red-attestation` | manual | ❌ | Hand-edit an attestation to a red vet line first |
| `finalized-no-vet` | manual | ❌ | This PR itself, if finalized `no vet` |
| `advanced` | manual | ❌ | Push a commit to the base after finalizing |
| `landed` | manual | ❌ | Run on an already-merged PR |
| `handle-held` | manual | ❌ | Read the report text |
| `merge-main` | manual | ❌ | Skill routing by description |

https://claude.ai/code/session_01Gs1h4L9m46Ti3ibh42DpiN

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-22T10:55:55Z — "Proposed squash body: ``` An operator's ask to merge had one…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-22T10:55:55Z

[https://github.com/vzakharov/muthur/pull/217#issuecomment-6339038368](https://github.com/vzakharov/muthur/pull/217#issuecomment-6339038368)

Proposed squash body:

```
An operator's ask to merge had one route, /finalize and merge, defined
only for a branch not yet finalized; a finalized branch had none short
of re-running land prep to reach a gate that only needs the base
checked. /merge is now the one name for that ask.

On an unfinalized branch it runs /finalize and merge. On a finalized
one -- ready for review, its attestation naming the head -- it runs
/check-merge once: a contained base passes through the same step-8
gate in finalize/merge.md, plus the attestation's own lines, and
squash-merges; an advanced base is synced with /sync-branch and the
run stands down, so the next /merge re-finalizes the merged head.

/merge owns reading the ask and the finalized test; merge.md keeps
the gate, the merge and the stand-down, written in /finalize's step
numbers, and /merge cites them. /finalize and merge does not route
through /merge, which would loop or judge only the run's tail.
/finalize and /handle now point a merge ask at /merge.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/skills/finalize/merge.md`:22 — unresolved — last: @vzakharov (human) 2026-10-22T12:23:23Z — "у нас тут infinite loop не создаётся случайно?" → [↓](#t01)
- **T02** `.claude/skills/merge/SKILL.md`:17 — unresolved — last: @vzakharov (human) 2026-10-22T12:24:24Z — "эм, а как тут можно что-то ask? вроде аргументов нет у скилл…" → [↓](#t02)
- **T03** `.claude/skills/merge/SKILL.md`:26 — unresolved — last: @vzakharov (human) 2026-10-22T12:25:04Z — "хм, стоит ли это last rule выделить в отдельный файл, чтобы…" → [↓](#t03)

<a id="t01"></a>

### `.claude/skills/finalize/merge.md`:22 — unresolved

```diff
@@ -19,17 +19,8 @@ forward it, and `@.claude/skills/handle/SKILL.md` § "Argument shape" holds the
… 11 lines elided …
-then run the skill with the flag. The paragraph above holds here too: an ask
-that also requests changes was written before the diff it would merge, so land
-prep runs and the merge is held.
+**An operator's ask to merge goes to `@.claude/skills/merge/SKILL.md`**, which
```

**@vzakharov (human)** — 2026-10-22T12:23:23Z

у нас тут infinite loop не создаётся случайно?

---

<a id="t02"></a>

### `.claude/skills/merge/SKILL.md`:17 — unresolved

```diff
@@ -0,0 +1,58 @@
… 13 lines elided …
+- **`no vet`** (optional): rides unchanged to whichever of `/finalize` and
+  `/sync-branch` runs below.
+
+**An ask that also requests changes holds the merge.** It was written before the
```

**@vzakharov (human)** — 2026-10-22T12:24:24Z

эм, а как тут можно что-то ask? вроде аргументов нет у скилла кроме ветки. Может это медведь оставшийся с до-переноса?

---

<a id="t03"></a>

### `.claude/skills/merge/SKILL.md`:26 — unresolved

```diff
@@ -0,0 +1,58 @@
… 22 lines elided …
+
+**Finalized means the PR is ready for review and its
+`<!-- finalize-attestation -->` comment names the current head**, give or take
+what `@.claude/skills/finalize/SKILL.md` step 7's last rule lets ride past it.
```

**@vzakharov (human)** — 2026-10-22T12:25:04Z

хм, стоит ли это last rule выделить в отдельный файл, чтобы в этом форке не грузить целый finalize? (возможно к каким-то другим вещам ниже тоже вопрос относится)

---

## Timeline (status, references, and other events)

- **2026-10-22T10:55:55Z** @vzakharov renamed from «feat: add /merge, routing a merge ask by whether the branch is finalized» to «feat: add /merge, routing by whether the branch is finalized».
- **2026-10-22T12:26:18Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/217#pullrequestreview-5614056832.
