# PR #110: feat: elephant and pizza, two ways to split work across sessions

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/110
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/elephant-and-pizza-04z3ht
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-25T07:47:24Z
- **Updated:** 2026-09-25T22:22:14Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **Two shapes for work that doesn't fit one session**, named in the plan with a recommendation and picked by the operator at review (`plan/SKILL.md` § "Splitting work across sessions"). **Elephant**, the default: a bite per session in one PR. **Pizza**: the existing carve into issues, which now takes a reason — self-contained slices, a gain worth locking in before a riskier stretch, or a part other work needs.
- **`plan/elephant.md`** — the plan says only what is left, as the current contract with no progress diary: `## Rest of the elephant` in coarse steps (its presence marks the shape) and `## Rest of the bite` in detail, open only while a bite is. The session claiming the plan takes the bite — a rest left by a stop mid-bite first and as written, then as much of the elephant as fits, erring small. A bite leaves `vet` green, lands whole, fits before the budget's warning line, one per session.
- **`/go`** writes the bite right after the flip, asking `/task`'s questions of it, and pauses either at the bite's end (section deleted, `/polish`, `/pr`, stop) or mid-bite on the budget notice (built parts struck, the rest kept, no polish). It no longer holds the plan as a frozen snapshot. The budget hook's "nearly done" reads the open bite.
- **Fix:** `check-repo-identity.sh` skips the cost ledger's session rows, whose quoted opening prompts can name sibling repositories — this session's own prompt failed `vet` on it.

## QA Checklist

- [ ] `vet` — `./scripts/vet.sh` exits 0.
- [ ] `hook-bite` — both context-budget notices name the open bite (`test_nearly_done_judges_an_elephants_open_bite`).
- [ ] `identity-ledger` — a session row whose opening prompt names another `vzakharov/…` repo no longer fails `check-repo-identity.sh`.
- [ ] `plan-split` — `/plan` on work beyond one session names elephant or pizza with a recommendation, and a pizza states which of the three reasons holds.
- [ ] `elephant-run` — `/go` on a paused elephant writes `## Rest of the bite` before building, builds only that, deletes the section, runs `/polish` and `/pr`, leaves the plan `*.paused.md` and hands off.
- [ ] `budget-midbite` — a pause notice mid-bite strikes the built parts from `## Rest of the bite`, keeps the rest as written, and pauses without `/polish`; the next session takes that rest first.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `vet` | e2e | ✅ | the script itself |
| `hook-bite` | unit | ✅ | `test_context_budget.py` |
| `identity-ledger` | integration | ❌ | seen live on this branch; no fixture test |
| `plan-split` | manual-only | — | agent behaviour under the skill text |
| `elephant-run` | manual-only | — | needs a real multi-session run |
| `budget-midbite` | manual-only | — | needs a session crossing 300k |

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-25T07:50:28Z — "Proposed squash title/body: ``` feat: elephant and pizza, tw…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-25T07:50:28Z

[https://github.com/vzakharov/muthur/pull/110#issuecomment-5828883450](https://github.com/vzakharov/muthur/pull/110#issuecomment-5828883450)

Proposed squash title/body:

```
feat: elephant and pizza, two ways to split work across sessions (pr #110)
```

```
Work too big for one session had one way to be split, a carve into
issues, and a high bar that left anything short of it to run as one
plan with no procedure for crossing sessions. It now splits in one of
two shapes, which the plan names with a recommendation and the
operator picks at review.

An elephant, the default, is eaten a bite per session in one PR. Its
plan says only what is left, kept as the current contract with no
progress diary: the rest of the elephant in coarse steps, and the rest
of the open bite in detail. The session claiming the plan takes the
bite: a rest left by a stop mid-bite first and as written, then as much
of the elephant as fits. It pauses at the bite's end with /polish and
/pr, or mid-bite on the context budget notice, whose nearly-done
judgment now reads the open bite.

A pizza is the carve into issues, and now takes a reason: slices that
can land on the trunk separately, a gain worth locking in before a
riskier stretch, or a part other work needs. Both shapes share the
rule that only the next slice is spelled out in full.

The repo-identity check no longer scans the cost ledger's session
rows, whose quoted opening prompts can name sibling repositories.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/skills/go/SKILL.md`:69 — unresolved — last: @vzakharov (human) 2026-09-25T22:17:17Z — "> commit `## Rest of the bite` почему не "This bite" (а пере…" → [↓](#t01)
- **T02** `.claude/skills/go/SKILL.md`:88 — unresolved — last: @vzakharov (human) 2026-09-25T22:18:55Z — "если мы его просто Delete, кто запишет эту часть как уже сде…" → [↓](#t02)
- **T03** `.claude/skills/plan/elephant.md`:12 — unresolved — last: @vzakharov (human) 2026-09-25T22:21:36Z — "кажется "as a list" слишком сильно накладывает ограничение н…" → [↓](#t03)

<a id="t01"></a>

### `.claude/skills/go/SKILL.md`:69 — unresolved

```diff
@@ -66,7 +66,7 @@ The plan file's name encodes its lifecycle state (see `@.claude/skills/plan/SKIL
… 1 line elided …
 - `*.completed.md` — implementation already finished → don't silently re-run; report and ask.
 
-**A plan with a `## Next chunk` section is an elephant** (`@.claude/skills/plan/elephant.md`), and this session builds that chunk and nothing past it. Before building, ask it `@.claude/skills/task/SK…
+**A plan with a `## Rest of the elephant` section is an elephant** (`@.claude/skills/plan/elephant.md`), and this session eats one bite of it. Right after the flip, write and commit `## Rest of the bite` per `@.claude/skills/plan/elephant.md` § "Taking a bite", then build that and nothing past it. Writing it asks the bite `@.claude/skills/task/SKILL.md`'s two questions: the section's detail answers whether it needs a plan, and the pause already gave the operator their look, so the one answer that stops you is a fork with no recommendation — write the question into `## Rest of the bite`, pause per Step 2 with nothing built, and ask it, rather than picking one and building on the guess.
```

**@vzakharov (human)** — 2026-09-25T22:17:17Z

> commit `## Rest of the bite`

почему не "This bite" (а переименовывать в Rest of the... уже на паузе) -- для простоты? А то звучит как-то не оч для раздела, в котором мы УЖЕ работаем (а не что-то "осталось"). Плюс, по-хорошему настоящий "Rest of the bite" у нас появляется только в сценарии остановки оператором или по бюджету контекста -- то есть это не main path так сказать

---

<a id="t02"></a>

### `.claude/skills/go/SKILL.md`:88 — unresolved

```diff
@@ -83,10 +83,10 @@ Commit/push discipline is already governed by CLAUDE.md — don't reinvent it he
… 5 lines elided …
 
-- **The chunk is done** — rewrite `## Next chunk` to the chunk after it first, while this session still holds the context that chunk stands on; tick and reword the steps; then run Step 3 and Step 4, …
-- **A stop mid-chunk** — the budget notice or the operator: the chunk's remainder becomes `## Next chunk`, then the `git mv`, commit and push above. Skip Step 3: `/polish` scopes itself from the last…
+- **The bite is done** — delete `## Rest of the bite` and reword the elephant steps the work found wrong or whose needs it learned, while this session still holds that context; then run Step 3 and Step 4, which leave the plan `*.paused.md`. Stop there, budget left or not — the operator reviews between bites — and end the turn with the handoff block below.
```

**@vzakharov (human)** — 2026-09-25T22:18:55Z

если мы его просто Delete, кто запишет эту часть как уже сделанную работу? Шаги 3 и 4?

---

<a id="t03"></a>

### `.claude/skills/plan/elephant.md`:12 — unresolved

```diff
@@ -3,37 +3,51 @@
… 13 lines elided …
-  an elephant for `/go`. At plan time it is the first chunk.
+Two sections, both saying what is left:
+
+- **`## Rest of the elephant`** — the job still to eat, coarse, as a list. A
```

**@vzakharov (human)** — 2026-09-25T22:21:36Z

кажется "as a list" слишком сильно накладывает ограничение на форму. Не все планы обязаны выглядеть как список покупок. (Возможно это относится не только к этой строчке, по верхам свипни.)

---

## Timeline (status, references, and other events)

- **2026-09-25T22:22:14Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/110#pullrequestreview-5323229659.
