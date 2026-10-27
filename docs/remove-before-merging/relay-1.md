# Relay 1 — cost rows filed by branch (parked)

## Standing constraints

None stated beyond the repository's own rules.

## The conversation

1. **Operator:** «давай вести косты не голыми джсонами, а в структуре
   `папка/<полный/путь-ветки>`; забэкфилить тоже где возможно (там где ветки
   указаны; где нет -- оставить как есть или засунуть в общую "безветочную"
   ветку)»
   - **Agent:** routed it as rung 1 → `/task`, and started reading
     `.claude/costs/` and the `cost-ledger` branch.
2. **Operator (mid-turn):** «и давай совать uuid.json в подпапку с порядковым
   номером сессии для этой ветки (если это программно вычисляемо)»
3. **Operator (mid-turn), quoting the agent's «Сейчас проверю, у скольких
   записей это поле заполнено»:** «это полезно но не очень, потому что речь идёт
   и про адоптеров тоже, а про них мы ничего не знаем»
   - **Agent:** agreed. The backfill must be a migration in code that runs in
     any adopter's repository with no prior knowledge of its rows.
4. **Operator (mid-turn), quoting «работы на день»:** «как же это умиляет :)»
   - **Agent:** renamed the branch to `claude/cost-rows-by-branch-qyu06w`, wrote
     the draft plan, and opened draft PR #236 with a squash proposal. The reply
     explained the design, answered the banter (the day is a team member's day,
     the gate's unit), and put three questions with recommendations: 1 drop the
     month folder, 2 branchless rows under `.no-branch/`, 3 plain integers.
5. **Operator:** «> Поэтому у адоптера всё мигрирует само на первом Stop после
   /update-muthur — а это не будет каждый раз отнимать 100500 времени?»
   - **Agent:** no. Only the one-time migration is real work. The steady-state
     check reads names only (`ls-tree --name-only`), measured at 3 ms on 202
     rows, against 9 ms to read every row, and it adds no network round trip.
     Committed that requirement to the plan.
6. **Operator:** «1 оставить но считать по месяцу самой первой сессии на ветке
   (то есть никто никуда не уедет если я правильно понимаю) / 2 по месяцам +
   .no-branch / 3 пусть будут обычные, переживём»
   - **Agent:** collapsed the plan onto those answers and updated the PR body
     and the squash proposal (verbatim in Last agent turn).

## Intent

File each cost-ledger row by branch with a per-branch session ordinal, and
migrate every existing row, in this repository's ledger and in any adopter's,
through code that knows nothing about their rows. Branchless rows go into a
shared bucket rather than being dropped.

## Decisions

- **Layout:**
  `.claude/costs/sessions/<YYYY-MM>/<full/branch/path>/<N>/<uuid>.json`.
  - `<YYYY-MM>` is the month of the branch's **first** session. It is fixed once
    the branch has a directory, so a branch never splits across months.
  - `<N>` is a 1-based plain integer: one past the highest `<N>` held, never the
    count.
  - Branchless rows go in `<own month>/.no-branch/<N>/`. Git forbids a ref
    component that starts with a dot, so no real branch collides with it.
  - Beaten: dropping the month level, and zero-padding `<N>`.
- **The ledger assigns the month and the ordinal**, because only the ledger sees
  every session on a branch.
- **A row moves only when its session changes branch**, for example on an
  auto-branch rename or a `/from-branch` attach. The operator's «никто никуда не
  уедет» holds apart from that.
- **Re-filing pass = the migration.** It runs inside `append` on every ledger
  write. It is self-healing: duplicates, ordinal collisions, one branch under
  two months, and old-layout rows from stale branches. Its steady-state check
  reads names only.
- **`--month` filtering moves from directories to each row's start time**,
  because a later session sits under its branch's first month.
- **`github.py`** lists the rows recursively over REST
  (`git/trees/... ?recursive=1`), because GraphQL lists one tree level at a
  time.

## Errors and dead ends

- Counting how many ledger rows carry `branch` was judged by the operator to be
  of little use, since adopters' ledgers are unknown. The migration must not
  assume anything about them.

## State

- Branch `claude/cost-rows-by-branch-qyu06w`; draft PR
  https://github.com/vzakharov/muthur/pull/236; last pushed commit before this
  file: `290ffc4` (a cost row, after `5398b6c`, the plan collapse).
- Plan: `docs/plans/cost-rows-by-branch.draft.do-not-implement.md`. Still a
  draft: no go-ahead has been given.
- Squash proposal tracked at `docs/remove-before-merging/squash-message.md`,
  posted as a comment on #236.
- No CI watch, PR subscription or check-in scheduled.
- Estimate revised to this session's planning work: 2 h senior architect. The
  remainder handed on is the implementation: 8 h senior developer — "re-filing
  has to stay correct under concurrent pushes, stale branches still writing the
  old layout, and adopters' unknown ledgers; a middle would miss the race and
  the dedup cases".

## Pointers

- `docs/plans/cost-rows-by-branch.draft.do-not-implement.md` — the full plan,
  file by file, with DRY notes and costs.
- `.claude/costs/CLAUDE.md` — the ledger's contracts. The layout line and §
  "Where rows live" change with this work.
- `.claude/costs/lib/ledger_branch.py`, `lib/rows.py`, `session_cost.py`,
  `ledger.py`, `hooks/stop-session-cost.sh`, `lib/github.py`, `report.py`,
  `lib/restart.py`, `estimate.py` — the code the plan touches.
- The ledger's current rows:
  `git fetch origin cost-ledger && git ls-tree -r --name-only origin/cost-ledger`.
- Predecessor transcript:
  https://claude.ai/code/session_01DaohkDWGQssqe2LoriZfN8

## Next step

Wait for the operator. The plan awaits their review and go-ahead, which a
`/go claude/cost-rows-by-branch-qyu06w` gives. On that, flip the plan per
`.claude/skills/go/SKILL.md` Step 1 and implement it.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages,
usually unneeded but harmless; the reply proper is usually its last
paragraphs.

````text
Squash-предложение тоже говорит о пути, обновляю его.

PR-описание всё ещё показывает путь без месяца, правлю его.

Да, ты правильно понял: строка, которая уже легла, больше не двигается. Месяц ветке назначается один раз, по её первой сессии, и все следующие сессии идут туда же. Строка переезжает только в одном случае: когда её сессия сама сменила ветку. Чаще всего так бывает при переименовании авто-ветки: первые `Stop` успевают записаться под `claude/nifty-maxwell-…`, и после `branch-rename` строка уезжает под новое имя с новым `N`.

Записал все три ответа в план:
- путь `sessions/<YYYY-MM>/<ветка>/<N>/<uuid>.json`, где месяц — это месяц первой сессии ветки;
- строки без ветки лежат в `sessions/<свой месяц>/.no-branch/<N>/`;
- `N` — обычные числа.

У первого ответа два следствия, оба теперь в плане:
- **`main` навсегда останется в месяце своей первой сессии**, и `N` там уйдёт в сотни. Любая долгоживущая ветка ведёт себя так же. Ветка, которую удалили и потом создали заново с тем же именем, продолжит старую нумерацию. На суммы это не влияет.
- **Фильтр `--month` больше нельзя строить по папкам.** Октябрьская сессия на сентябрьской ветке лежит в `2026-09/`, поэтому период считается по времени старта самой строки. Для строк из леджера отчёт уже так и делает. В QA-чеклист добавил пункт, который это проверяет.

PR-описание и squash-предложение обновлены.

PR: https://github.com/vzakharov/muthur/pull/236

Чтобы реализовать — начни новую сессию с:

```
/go claude/cost-rows-by-branch-qyu06w
```
````
