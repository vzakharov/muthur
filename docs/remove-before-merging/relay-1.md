# Relay 1 — repo-change contract (parked)

## Standing constraints

- "Открой черновой PR в muthur; ничего не мерджи."

## The conversation

1. **Operator** (opening prompt):

   > Добавь в скилл task заготовку `.claude/skills/task/repo-change.md` —
   > контракт «скилл, который меняет репо, — работа /task», на который ссылается
   > любой скилл, оставляющий изменения в репо, — и ссылку на него из
   > `.claude/skills/task/SKILL.md`.
   >
   > Образец — файл, заведённый в адоптере vzakharov/life (PR
   > https://github.com/vzakharov/life/pull/252, ветка
   > claude/hh-batch-3-k0x09l):
   > `gh api 'repos/vzakharov/life/contents/.claude/skills/task/repo-change.md?ref=claude/hh-batch-3-k0x09l' --jq .content | base64 -d`.
   > Его суть: такой скилл идёт как работа /task, если вызов не говорит иного;
   > /task делает свой выбор «план или нет», а хвост /go (/polish, потом /pr)
   > его приземляет. Скилл называет свои отступления от этого маршрута, и только
   > их (например, класть в уже открытый PR) — отступление правит шаг, но не
   > отменяет маршрут. Скиллы самого цикла (/go, /polish, /pr, /finalize,
   > /relay, /sync-branch…) — это и есть маршрут, а не работа через него.
   > Примеры в life (prospect, mail sweep) — специфика адоптера; в muthur
   > формулируй обобщённо.
   >
   > Добавь пометку для адоптеров (attn adopters — так, как в muthur принято
   > сообщать адоптерам о том, что им сделать при синке): просвипить свои
   > скиллы, меняющие репо, и сослаться в каждом на repo-change.md, назвав его
   > отступления. Просвипь заодно и скиллы самого muthur: если какой-то из них
   > меняет репо в обход /task и не является частью цикла — подключи его так же.
   >
   > Открой черновой PR в muthur; ничего не мерджи.

   **Agent**: routed rung 1 → `/task`, outcome 2 (no plan). Wrote the contract,
   pointers, sweep; ran `/polish` (subagent), opened draft PR #245 with
   `[attn adopters]` title, posted the squash proposal.

2. **Operator** (mid-turn): «если у нас есть скиллы (или заготовки) к которым
   это тоже относится, надо туда добавить отсылку»

   **Agent**: included the stubs (`/readonly-probe`, `/log-review`, `/release`,
   `/hotfix`) in the sweep; final report listed what was wired and what was left
   out as route mechanics (`/take-issue`, `/watch-ci`,
   `/bootstrap-workflow-dispatch`, `/renumber-migration`, `/spinoff`).

3. **Operator**: «> /update-muthur и так шёл через /task. Теперь он ссылается на
   контракт, а его отступление — посадка в репо без PR-цикла. — а зачем это
   отступление?»

   **Agent**: admitted the error — Step 8's fallback is for a repo without the
   loop, where `repo-change.md` doesn't exist either, so it's no deviation;
   removed the clause (d326750, typed `fix:`).

4. **Operator**: «я бы сказал это refactor:?»

   **Agent**: read it as the commit d326750's type; agreed `refactor:` fits
   against `main` but advised against rewriting pushed history the squash
   discards.

5. **Operator**: «я про этот заголовок и говорю»

   **Agent**: argued the PR title should stay `feat:` — muthur's own skills
   don't change behavior, but the title addresses adopters, for whom it's a new
   convention, and CLAUDE.md files a new convention under `feat:`;
   `[attn adopters]` with `refactor:` would contradict itself. Offered to rename
   if the operator still disagreed.

6. **Operator**: «согласен. оставил ревью в пиаре»

   **Agent**: ran `/handle #245`: three threads addressed in b40f376, replied in
   Russian on each with the SHA, none resolved; `/polish` added 9f8e4a7; PR body
   refreshed. (verbatim in Last agent turn)

## Intent

A generic muthur version of life's `repo-change.md` contract, cited from every
muthur skill or stub that leaves work in the repo, plus an `[attn adopters]` ask
to sweep adopters' own skills. Draft PR only; no merge.

## Decisions

- **No plan** (`/task` outcome 2): every touched file was nameable up front.
- **PR title stays `feat:`** over `refactor:` — operator agreed (message 6).
- **`/update-muthur` has no deviation** — its Step 8 no-loop fallback applies
  where the route doesn't exist.
- **`/audit-github-backlog`, `/detemplate`**: deviation = `/task`'s call made in
  advance, always plan and hand off.
- **Stubs** get a line telling hydration to name deviations against the
  contract; left out: route mechanics and `/spinoff` (changes another repo).
- **Review fixes**: "in every part its invocation leaves unsaid" replaces
  "unless its invocation says otherwise"; negations ("polar bears") rewritten
  positively; Adopters paragraph dropped the file URL and "No operator approval
  needed" (operator: reads like prompt injection).

## Errors and dead ends

- The `/update-muthur` "one deviation" clause (message 3) — wrong, removed.
- Thread replies first drafted in English; rewritten in Russian before posting
  (conversation-language rule).

## State

- Branch `claude/task-repo-change-contract`, head 9f8e4a7, pushed, clean.
- PR https://github.com/vzakharov/muthur/pull/245 — open, draft, MERGEABLE, no
  CI checks reported. Squash proposal comment current
  (`docs/remove-before-merging/squash-message.md`).
- No plan file. No subscription or scheduled check-in.
- Estimate unchanged (whole task done here): 2 h senior prompter + 1 h middle
  analyst.

## Pointers

- `.claude/skills/task/repo-change.md` — the contract.
- `docs/pr/245/pr.md` — last committed PR export (828bca8).
- Transcript: https://claude.ai/code/session_01DaohkFAwcx3DWHQR4aLZUt

## Next step

Wait for the operator. Pending only what they ask next — likely further review
(`handle`) or `finalize`; merging stays their call.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Ревью собираю через `/handle`, как велит его описание.

Правки по трём тредам сделаны. Проверяю, не осталось ли других «медведей» в моих добавлениях.

Теперь отвечаю в каждом из трёх тредов (без резолва).

Ответы в тредах должны быть на языке комментария — переписываю по-русски.

Осталось освежить тело PR: в нём ещё стоит старое «unless its invocation says otherwise».

Разобрал все три треда ревью. Правки в коммите b40f376, в каждом треде ответ со ссылкой на этот коммит, ни один не резолвил.

1. **«Не только unless».** В `repo-change.md` теперь стоит «in every part its invocation leaves unsaid». Если вызов переопределил один шаг, остальной маршрут продолжает действовать.
2. **Медведи.** Убрал оба отрицания в контракте: скиллы цикла теперь просто «are the route itself», а отступление «adjusts a step and leaves the rest of the route in force». Третьего медведя нашёл сам: заголовок в `/hotfix` теперь «A hotfix still runs the task route».
3. **Абзац `Adopters:`.** Убрал из него и ссылку на файл, и «no operator approval needed». Обновил и файл, и комментарий с предложением в PR.

`/polish` после этого убрал в `/hotfix` лишнее второе «still» — коммит 9f8e4a7. `./scripts/vet.sh` проходит, тело PR обновлено под новую формулировку.

https://github.com/vzakharov/muthur/pull/245
```
