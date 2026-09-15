# PR #79: feat: extract /go's quality passes into /polish

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/79
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/polish-skill-jzaozq
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-15T10:45:15Z
- **Updated:** 2026-09-15T12:57:39Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **`/polish` is the new home of the two mandatory passes** — `/dry` then `/tend-prose`. They lived only inside `/go` Step 3, so work that reached a PR by any other route (a task asked for and done directly, a branch another session wrote) got them only when the operator named both by hand.
- **It owns the scope, which neither pass could resolve on its own.** Both bottom out at unpushed work, which falls through to "nothing to review" on an already-pushed branch; the composite fetches the base and hands `git diff origin/<base>...HEAD` to both. Running it on its own diff caught the stale-ref case: against an unfetched `origin/main` the range covered 19 files where the branch had touched 8.
- **A floor keeps the second run off ground the first one cleared.** A branch is polished at `/go` and again at `/finalize`, and the second pass was re-reading the whole branch. Every commit a `/polish` run makes now opens with `polish:` (`polish(<guidance>):` for a focused run, which the lookup skips), and the newest such commit is where the next run starts; a run that finds nothing commits empty, since that is exactly the run whose floor the next one needs. It needs no invalidation rule — the search is bounded by the branch, so a commit a rebase dropped cannot come back as the answer — and what narrows is what gets reviewed rather than what it is compared against: `/dry` still reads the earlier commits as context. `/polish full` covers the one failure the mechanism cannot see: a floor left by a run that stopped early, or by a standard that has since moved.
- **`polish:` is a new branch-local commit type**, documented in CLAUDE.md § "Git conventions". The run's edits are `refactor:` or `docs:` by nature, which says nothing about who made them; and the squash gives the branch one hand-written subject, so the extension reaches no trunk.
- **Three call sites**: `/go` Step 3 (unchanged in effect, now by reference), `/finalize` ahead of its numbered steps — land prep being the funnel every branch reaches — and the operator directly, which is the entry the other two exist to make unnecessary and routinely don't.
- **`/finalize`'s `and merge` predicate names the passes as part of what an uneventful run may contain.** Polish edits rewrite prose and fold duplication without changing what the code does; a gate that fired on them would fire on nearly every branch that reached land prep without `/go`. A fold that does alter behavior is no longer a polish edit and stands the merge down like any other.

The `/finalize` call is unnumbered on purpose — its step numbers are cited from five other skills, so inserting a Step 1 would have been a wide mechanical renumber with a stale citation as its likeliest outcome.

## QA Checklist

- [ ] `polish-standalone` — in a session that made a change without `/go`, say "polish this" and confirm `/polish` runs both passes over the branch diff rather than reporting nothing to review.
- [ ] `polish-scope-stale` — on a branch whose `origin/<base>` is behind, confirm the run fetches first and scopes to the branch's own files.
- [ ] `polish-floor` — polish a branch, commit more work, polish again; confirm the passes' commits open with `polish:` and that the second run reads only the new commits.
- [ ] `polish-floor-reset` — confirm a focused run marks itself `polish(<guidance>):` and is skipped by the lookup, that a run finding nothing still leaves an empty `polish:` commit, and that `/polish full` ignores an existing floor.
- [ ] `polish-push` — invoke `/polish` bare on a branch and confirm the run's commits reach the remote without a caller pushing for it.
- [ ] `go-step-3` — run `/go` on a task and confirm Step 3 loads `/polish` rather than the two passes inline, and that the plan file still flips to `*.completed.md` afterwards.
- [ ] `finalize-first` — run `/finalize` on a branch that never saw `/go` and confirm the passes run before the vet suite.
- [ ] `finalize-merge-gate` — run `/finalize and merge` on a branch where `/polish` changes prose only, and confirm the gate does **not** stand down on that alone.
- [ ] `catalog` — `./scripts/vet.sh` is green, i.e. `/polish` has exactly one catalog row and no `@`-reference dangles.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `polish-standalone` | no | no | Agent-behavior check; only a live session exercises it. |
| `polish-scope-stale` | partially | no | The `git fetch` + `git diff origin/<base>...HEAD` pair is scriptable; whether the agent runs it is not. |
| `polish-floor` | partially | no | The `git log`/`awk` lookup is scriptable; whether the agent honours it is not. |
| `polish-floor-reset` | no | no | Same. |
| `polish-push` | no | no | Same. |
| `go-step-3` | no | no | Same. |
| `finalize-first` | no | no | Same. |
| `finalize-merge-gate` | no | no | Judgment clause in a stand-down list — prose, not code. |
| `catalog` | yes | yes | `scripts/check-skill-catalog.sh`, inside `scripts/vet.sh`. |

---

## Comments

### Comment by @vzakharov (agent) on 2026-09-15T10:45:39Z

[https://github.com/vzakharov/muthur/pull/79#issuecomment-5678908530](https://github.com/vzakharov/muthur/pull/79#issuecomment-5678908530)

Proposed squash title/body:

```
feat: extract /go's quality passes into /polish (pr #79)
```

```
The two mandatory quality passes, /dry then /tend-prose, lived only
inside /go Step 3. Work that reached a PR by any other route — a task
asked for and done directly, a branch another session wrote — got them
only when the operator named both by hand.

/polish is their home: the pair, the order, and the scope. Scope is the
part neither pass could resolve alone, since both bottom out at unpushed
work and so fall through to "nothing to review" on a branch already
pushed. The composite fetches the base and hands the branch's net diff
against it to both, floored at the newest `polish:` commit — a branch is
polished at /go and again at /finalize, and the second run has no
business re-reading what the first one cleared. A run that finds nothing
commits empty, since that is the run whose floor the next one needs, and
what the floor narrows is what gets reviewed, not what it is compared
against. `polish:` is a branch-local commit type the squash never
carries to the trunk. The run pushes what it commits: invoked by the
operator it has no caller behind it to do so.

Three call sites reach it. /go Step 3 loads it in place of the two
passes it used to name; /finalize runs it ahead of its numbered steps,
land prep being the funnel every branch reaches whatever route its work
took; and the operator invokes it over work that took neither. That last
entry is the one the other two exist to make unnecessary and routinely
don't. /finalize's `and merge` predicate names the passes among what an
uneventful run may contain: they rewrite prose and fold duplication
without changing what the code does, and a fold that does is no longer
a polish edit.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

### `.claude/skills/polish/SKILL.md`:1 — resolved

**@vzakharov (human)** — 2026-09-15T11:17:24Z

давай добавим ещё watermark (возможно в remove-before-merging), чтобы скилл не проверял то, что уже проверялось (т.е. смотрел именно на дифф)

**@vzakharov (agent)** — 2026-09-15T11:28:57Z

Сделано в c89515c — `/polish` теперь пишет строку в `docs/remove-before-merging/polished.md`, а следующий прогон берёт `<watermark>..HEAD` вместо полного диапазона от базы. Пол возвращается к базе в трёх случаях: файла/строки нет, `HEAD` не потомок записанного коммита (ребейз, аменд, ресет), или явный `/polish full`.

Два ограничения, которые я вписал рядом, чтобы ватермарк не глушил находки: строку пишет только полный прогон (у прогона с фокусом чистый результат ничего не говорит про дефекты, которые он не искал), и сужается **предмет ревью, а не база сравнения** — `/dry` по-прежнему читает более ранние коммиты как контекст, иначе дубль между новым кодом и уже отполированным становится невидимым.

Обкатал на самой ветке: первая строка уже лежит в файле (db0e247), и её сметает та же уборка `docs/remove-before-merging/` на шаге 6.

**@vzakharov (agent)** — 2026-09-15T11:36:08Z

Переделал в 928ae8b — файла нет, ватермарк уехал в трейлер коммита: каждый коммит прогона несёт `Polished: full` (или `Polished: <guidance>` у прогона с фокусом, который лукап пропускает), а пол — это `git log origin/<base>..HEAD --grep='^Polished: full$' -1`.

Заодно ушли три правила, которые держались за файл: проверка на предка (поиск и так ограничен веткой, так что коммит после ребейза просто не находится), правило «пропусти коммит ватермарка внутри следующего диапазона» (такого коммита больше нет) и зависимость от уборки `docs/remove-before-merging/` на шаге 6.

Цена — прогон, который ничего не изменил, не оставляет коммита и потому не оставляет пола: следующий перечитает уже чистое. Дешевле, чем трекнутый артефакт с обслуживающей его механикой.

**@vzakharov (agent)** — 2026-09-15T12:41:47Z

Финальная форма — 028597c: не трейлер, а префикс сабджекта `polish: <что изменили>` (`polish(<guidance>):` у прогона с фокусом, лукап его пропускает). Видно в `git log --oneline`, чего трейлер не давал, а лукап матчит именно сабджект, а не всё сообщение:

```bash
git log origin/<base>..HEAD --format='%H %s' | awk '$2 == "polish:" { print $1; exit }'
```

Тип локален для ветки и легитимен ровно по причине, которую назвал оператор: сквош даёт ветке один написанный руками сабджект, так что до трунка `polish:` не доезжает. Записал это в CLAUDE.md § «Git conventions».

Прогон, который ничего не изменил, теперь коммитит пустой коммит вместо того, чтобы не оставлять следа, — это ровно тот прогон, чей пол нужен следующему.

---

### `.claude/skills/finalize/SKILL.md`:33 — resolved

```diff
@@ -28,6 +28,10 @@ description: Finalize (a.k.a. "prep merge") — land prep: verify there's a draf
 
 Either way, **step 7's attestation comment is the record.** A reviewer cannot see from the diff what was run; if it isn't written down it did not happen as far as anyone else is concerned.
 
+**First, the quality passes.** Before step 1, load and follow `@.claude/skills/polish/SKILL.md` over this branch. Land prep is the funnel every branch reaches whatever route its work took, so this is where a branch written without `/go` in front of it still gets the passes — and the last point at which changing the diff is cheap, since the vet run, the base merge, the squash message and the attestation's SHA are all statements about a diff that has stopped moving.
+
+It carries no step number because the numbers below are cited from other skills and stay put; it runs first regardless. **`no vet` does not skip it** — a docs-only diff is the case `/tend-prose` exists for.
```

**@vzakharov (human)** — 2026-09-15T11:18:24Z

and `/dry` too has at least a certain relation to prose

**@vzakharov (agent)** — 2026-09-15T11:29:08Z

Верно — переписал в c89515c: «a docs-only diff is squarely what both passes are for: `/tend-prose` by construction, and `/dry` because a constraint stated in two places is a duplication like any other». Правило CLAUDE.md про «одно место — дом, второе — указатель» ровно это и есть, только над прозой.

---

### `.claude/skills/finalize/SKILL.md`:115 — resolved

```diff
@@ -108,6 +112,7 @@ Steps (stop on first unresolved failure):
    **Stand down if any of this happened**, at whichever step it happened:
 
    - **Pre-check** — `HEAD` was detached, or there was no PR and you created one. A PR opened and merged inside one turn was never a reviewable object. (A PR you flipped back to draft is fine — that is the ordinary re-finalize.)
+   - **The quality passes** — `/polish` changed anything. An edit there is a judgment about the diff, made after the operator last looked at it, and it is the ordinary outcome on a branch that never went through `/go`. Finding nothing is what clears this.
```

**@vzakharov (human)** — 2026-09-15T11:19:33Z

нет, давай это не будем включать. "полировочные" изменения по определению не меняют работу кода.

**@vzakharov (agent)** — 2026-09-15T11:29:09Z

Убрал в c89515c.

Одна связанная правка, иначе пункт вернулся бы сам собой: предикат гейта — «эффект прогона = уборка шага 3 + то, что переписал автофикс тула» — формально не пропускал правки пассов, так что агент встал бы на нём даже без пункта в списке. Теперь пассы названы внутри предиката, с той границей, которую задаёт твоя формулировка: правка, которая всё-таки меняет поведение кода, — уже не полировка и мерж останавливает.

---

### `.claude/skills/polish/SKILL.md`:44 — unresolved

```diff
@@ -35,9 +39,35 @@ git diff origin/<base>...HEAD                     # the branch's net change
 
 `<base>` is the repo's default branch wherever that lookup has no answer — no PR yet, no `gh`, no GitHub at all. Nothing here needs the PR except the name of the branch this work merges into.
 
-That range plus anything uncommitted is the scope.
+That range plus anything uncommitted is the scope, unless the floor below moves up.
+
+## The floor: the last polish commit
```

**@vzakharov (human)** — 2026-09-15T12:56:47Z

also need to account for a situation when it's the *first-ever* polish commit on the branch (we have no "polish:" commits on main, but it also should have be foolproof against the case that we ever do, e.g. we should NOT compare against a polish: that existed on main at some point)

(maybe you already did and I missed it.)

---

### `.claude/skills/polish/SKILL.md`:81 — unresolved

```diff
@@ -48,6 +78,6 @@ That range plus anything uncommitted is the scope.
 
 ## Do NOT
 
-- Run the vet suite, push, touch the PR, or flip a plan file — every caller owns its own land prep, and `/go` flips its plan file once this returns.
+- Run the vet suite, touch the PR, or flip a plan file — every caller owns its own land prep, and `/go` flips its plan file once this returns. The push above is not in this list.
```

**@vzakharov (human)** — 2026-09-15T12:57:23Z

> The push above is not in this list.

polar bear?

---

## Timeline (status, references, and other events)

- **2026-09-15T11:22:01Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/79#pullrequestreview-5209251676.
- **2026-09-15T12:57:39Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/79#pullrequestreview-5210218242.
