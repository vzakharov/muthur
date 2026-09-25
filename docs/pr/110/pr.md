# PR #110: feat: elephant and pizza, two ways to split work across sessions

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/110
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/elephant-and-pizza-04z3ht
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-25T07:47:24Z
- **Updated:** 2026-09-25T22:28:41Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **Two shapes for work that doesn't fit one session**, named in the plan with a recommendation and picked by the operator at review (`plan/SKILL.md` § "Splitting work across sessions"). **Elephant**, the default: a bite per session in one PR. **Pizza**: the existing carve into issues, which now takes a reason — self-contained slices, a gain worth locking in before a riskier stretch, or a part other work needs.
- **`plan/elephant.md`** — the plan is the current contract with no progress diary: `## Rest of the elephant`, coarse and in whatever form suits the job (its presence marks the shape), and `## This bite` in detail, open only while a bite is. A stop mid-bite renames it `## Rest of the bite` with the built parts struck. The session claiming the plan takes the bite — whatever bite the plan already holds first and as written, then as much of the elephant as fits, erring small. A bite leaves `vet` green, lands whole, fits before the budget's warning line, one per session.
- **`/go`** writes the bite right after the flip, asking `/task`'s questions of it, and pauses either at the bite's end (section deleted — the built work is on record in the commits and this body — then `/polish`, `/pr`, stop) or mid-bite on the budget notice (renamed to `## Rest of the bite`, built parts struck, no polish). It no longer holds the plan as a frozen snapshot. The budget hook's "nearly done" reads the open bite.
- **Fix:** `check-repo-identity.sh` skips the cost ledger's session rows, whose quoted opening prompts can name sibling repositories — this session's own prompt failed `vet` on it.

## QA Checklist

- [ ] `vet` — `./scripts/vet.sh` exits 0.
- [ ] `hook-bite` — both context-budget notices name the open bite (`test_nearly_done_judges_an_elephants_open_bite`).
- [ ] `identity-ledger` — a session row whose opening prompt names another `vzakharov/…` repo no longer fails `check-repo-identity.sh`.
- [ ] `plan-split` — `/plan` on work beyond one session names elephant or pizza with a recommendation, and a pizza states which of the three reasons holds.
- [ ] `elephant-run` — `/go` on a paused elephant writes `## This bite` before building, builds only that, deletes the section, runs `/polish` and `/pr`, leaves the plan `*.paused.md` and hands off.
- [ ] `budget-midbite` — a pause notice mid-bite renames `## This bite` to `## Rest of the bite`, strikes the built parts, keeps the rest as written, and pauses without `/polish`; the next session takes that rest first.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `vet` | e2e | ✅ | the script itself |
| `hook-bite` | unit | ✅ | `test_context_budget.py` |
| `identity-ledger` | integration | ❌ | seen live on this branch; no fixture test |
| `plan-split` | manual-only | — | agent behaviour under the skill text |
| `elephant-run` | manual-only | — | needs a real multi-session run |
| `budget-midbite` | manual-only | — | needs a session crossing 300k |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01U7MeUVPqtRDgMQ4kjiHQcb

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
plan is kept as the current contract with no progress diary: the rest
of the elephant, coarse and in whatever form suits it, and the open
bite in detail. The session claiming the plan takes the bite: any bite
already in the plan first and as written, then as much of the elephant
as fits. It pauses at the bite's end with /polish and /pr, or mid-bite
on the context budget notice, which leaves the bite's rest for the next
session and whose nearly-done judgment now reads the open bite.

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

_2 resolved threads omitted; re-run with `--include-resolved` to export them._

- **T01** `.claude/skills/go/SKILL.md`:88 — unresolved — last: @vzakharov (human) 2026-09-25T22:28:41Z — "что-то мне не очень нравится такой подход. Агент, берущий но…" → [↓](#t01)

<a id="t01"></a>

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

**@vzakharov (agent)** — 2026-09-25T22:25:16Z

В самом плане — никто, и так задумано: план описывает только то, что впереди, без дневника прогресса. Сделанное записано в коммитах ветки и в теле PR, которое Step 4 (`/pr`) пересобирает по всему диффу. Но в тексте `/go` это было неочевидно, так что дописал это прямо в пункт про удаление раздела. f1181d3

**@vzakharov (human)** — 2026-09-25T22:28:41Z

что-то мне не очень нравится такой подход. Агент, берущий новый кусок, должен понимать (пусть на высоком уровне) что сделано до него. PR-ы и прочая археология -- это именно археология (для тех кто смотрит завтра), а те кто в поту сегодня должны иметь всё на руках сразу.

---

## Timeline (status, references, and other events)

- **2026-09-25T22:22:14Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/110#pullrequestreview-5323229659.
