# Relay 2: merge gate, paused after Step 0

## Standing constraints

None stated by the operator.

## The conversation

1. **Operator:** «о, я придумал как нам сделать так, чтобы после "можешь
   мерджить" человеку не нужно было ни в гитхаб ходить, ни агента будить: user
   submit-хук, который смотрит: если запрос равняется _verbatim_ какой-то
   управляющей команде, и если ветка mergeable, то он сам мерджит и даёт "ошибку
   которая не ошибка" (останавливая ответ агента, как например мы делаем с
   протуханием кеша)»

   **Agent:** routed it as rung 2 (discussion). It confirmed that the mechanism
   already exists in `cold_cache.py` (`decision: block`, no model request). The
   gap it named: GitHub's "mergeable" is not the `/merge` gate (attestation on
   the head, base not advanced, CI, unanswered feedback, squash record). It
   proposed the rule "not sure → pass the prompt through to the agent" and asked
   two questions: which phrases trigger it, and whether a decline should pass
   silently or block with a reason.

2. **Operator:** «> Хуки одного события запускаются параллельно. — инфа 100%? 1
   Какие фразы? — только `/merge` (хотя я даже не думал об этом), но получается
   элегантно: если мерджить безопасно, мерджит автоматически, если нет, агент
   это обрабатывает умом. 2 - да»

   **Agent:** quoted the hooks docs ("its matching hooks run in parallel").
   Found `UserPromptExpansion` (matcher on `command_name`). Routed to `/task`,
   probed hook order with a throwaway project on `claude` 2.1.312, wrote the
   draft plan, and opened draft PR #246 with a squash proposal. Asked 4 open
   questions with recommendations.

3. **Operator:** «> Хук сидит на UserPromptExpansion … — но если expansion идёт
   после submit, то у нас отказ придёт до мерджа, а зачем? если мы можем
   мерджнуть, то логичнее просто мерджнуть и всё. на вопросы: 1- а зачем? для
   него это будет и так и так обычный запрос /merge, он уже знает как с ним
   работать. 2- вроде уже и сейчас должен не парковать? 3,4- не понял, попробуй
   попроще»

   **Agent:** moved the gate to `UserPromptSubmit`, where the cold-cache guard
   defers a bare `/merge` and the gate runs the guard's stop on a decline. It
   dropped the decline-reason context. It explained that the keepalive does park
   today after an agent-run merge too, and moved that out of scope. It
   re-explained questions 3 and 4 in plain words.

4. **Operator:** «2 -- а, #237 потому что я забыл смерджить»

   **Agent:** confirmed that #237 (keepalive: no watcher and no park on a landed
   branch) covers gate merges too, and pointed the plan at it.

5. **Operator:** «мы можем влить работу той ветки сюда а тот пиар закрыть,
   первым пунктом как начнём исполнять?» and, mid-turn, «а тот пиар закрыть
   соответственно»

   **Agent:** found #237 to be a draft, unattested and conflicting with main.
   Added plan Step 0 (merge it in with history, resolve conflicts in their own
   commit, run tests, push, close #237 with a link), and folded #237's essence
   into the squash proposal and the PR body.

6. **Operator:** «3-ок 4- но мы же не только для себя делаем но и для
   адоптеров?»

   **Agent:** `no vet` goes to the agent. The `/test-on-gh` stub line passes
   only while `.claude/skills/test-on-gh/SKILL.md` on the PR head is still a
   stub; an adopter who hydrated it gets a decline. Recorded both, so no open
   questions remain. (verbatim in Last agent turn)

7. **Operator:** «хорошо, давай начинать»

   **Agent (this relay's own turn):** flipped the plan to in-progress, quoting
   the go-ahead. Did Step 0: merge fa45843, resolution 6e1a3c4, keepalive and
   cold-cache tests green, #237 closed with a comment. Then hit the context
   budget's pause line, released the plan as `*.paused.md`, and relayed.

## Intent

A bare `/merge` lands a finalized PR with no model turn whenever every
mechanical condition of the `/merge` gate holds. Otherwise the prompt reaches
the agent exactly as typed, and the agent decides with judgement. It has to hold
for adopters as well, not only for this repo. The operator ruled out other
trigger phrases ("можешь мерджить" and so on); only a bare `/merge` triggers it.

## Decisions

- **`UserPromptSubmit`, not `UserPromptExpansion`.** The operator's point: merge
  at the first event. The ordering against cold-cache is handled by deferral,
  not by event order, because hooks of one event run in parallel.
- **A silent decline** with no context added, because to the agent it is an
  ordinary `/merge`.
- **Cold-cache defers a bare `/merge`** while `merge_gate.py` exists. On a
  decline the gate calls `cold_cache.on_prompt` itself, loading it by path.
- **A `no vet` attestation → decline.**
- **The test-on-gh stub line** passes only if that skill on the PR head is still
  a STUB.
- **#237 lands through this PR** (Step 0, done).
- **"Gate"** means the hook `.claude/merge-gate/hooks/merge_gate.py`. **"The
  `/merge` gate"** means `merge.md` § "Step 8 — the gate", which the hook
  mirrors mechanically.

## Errors and dead ends

- The `UserPromptExpansion` design was dropped after the operator's objection in
  message 3.
- Probe facts that still hold, from `claude` 2.1.312: submit hooks finish before
  expansion starts; a hook block costs $0; `suppressOriginalPrompt: true`
  removes the `Original prompt:` tail.

## State

- **Branch:** `claude/merge-gate-hook-k2tzds`, renamed from the harness's
  `claude/elegant-allen-k2tzds` before the first commit. Head 5df1a42, pushed.
- **PR:** https://github.com/vzakharov/muthur/pull/246, a draft. Squash proposal
  comment `#issuecomment-6465524129`; its working file is
  `docs/remove-before-merging/squash-message.md`.
- **Plan:** `docs/plans/merge-gate-hook.paused.md`, whose `## Progress` section
  says Step 0 is done and everything from § "Design" on is left.
- `docs/remove-before-merging/relay-1.md` is #237's own parked summary, brought
  in by the merge. It is not this session's; `/finalize` sweeps it.
- **Estimate.** This session: 1.5 h senior architect ("the hook merges outside
  the agent, so which /merge checks are mechanical, and how it orders against
  the cold-cache guard and keepalive, needs someone who knows the loop's
  gates") + 1 h senior developer ("folding a conflicting branch in needs reading
  both sides of each conflict against what main changed meanwhile"). Remainder
  for the successor: 6 h senior developer ("seven GitHub-side checks, a merge
  with a head guard, and boundary-mocked tests for each decline; an auto-merge
  path tolerates no sloppy reading of API fields").
- Nothing running: no CI runs on a PR here, no subscription, no check-in.

## Pointers

- `docs/plans/merge-gate-hook.paused.md`: the plan, the source of truth for what
  to build.
- `.claude/cold-cache/hooks/cold_cache.py` and `.claude/cold-cache/CLAUDE.md`:
  the pattern to copy, and the guard to defer from.
- `.claude/costs/lib/finalized.py` (`MARKER`), `.claude/costs/lib/github.py`
  (`Client`), `.claude/costs/lib/ledger_branch.py` (`PREFIX`): reuse.
- `scripts/gh_export/awaiting.py`: `awaiting_section` → extract
  `awaiting_rows()`.
- `.claude/skills/finalize/attest.md` (template) and
  `.claude/skills/finalize/merge.md` (gate and read-back).
- `scripts/vet.sh` line 79 (opt-in loop dirs), and
  `.claude/skills/update-muthur/catalog/g9-cold-cache.md` as the model for a new
  catalog entry.
- Predecessor transcript:
  https://claude.ai/code/session_01DaohkFbMZ1baY15PNscdFf

## Next step

Resume the paused plan through `/go`: build everything from § "Design" on, then
`/polish` and a `/pr` refresh. The go-ahead was given in this session: «хорошо,
давай начинать».

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

````text
Да, и правило из плана у адоптеров работает так же. Строка `/test-on-gh is an unhydrated stub` честна только до тех пор, пока скилл `/test-on-gh` в проекте ещё stub. Это значит, что тестов только для CI у проекта нет, и проверкой целиком был `vet.sh`. Здесь так, и у адоптера, который его не гидрировал, так же. А чтобы у адоптера с гидрированным `/test-on-gh` такая строка не прошла как зелёная, гейт проверит само утверждение: проходит она только если `.claude/skills/test-on-gh/SKILL.md` на голове PR до сих пор помечен STUB. Если скилл гидрирован, строка устарела, и гейт отдаёт PR агенту. Вношу это в план.

Да, и с этим правилом пункт 4 работает и для адоптеров. Строка `/test-on-gh is an unhydrated stub` в аттестации — это утверждение: у проекта нет тестов, которые гоняются только в CI, поэтому проверкой целиком был `vet.sh`. Гейт теперь сверяет его с деревом. Строка считается зелёной, только если `.claude/skills/test-on-gh/SKILL.md` на голове PR до сих пор помечен STUB. Значит:

- **здесь и у адоптера без CI-only тестов** строка честная, и гейт мерджит;
- **у адоптера, который гидрировал `/test-on-gh`,** строка устарела, и гейт отдаёт PR агенту.

Пункт 3 записан как решение: PR с `no vet` уходит агенту. Открытых вопросов в плане больше нет. Тест на оба случая со stub'ом в плане тоже есть. План и описание PR запушены.

https://github.com/vzakharov/muthur/pull/246

Чтобы реализовать, начни новую сессию с:

```
/go claude/merge-gate-hook-k2tzds
```
````
