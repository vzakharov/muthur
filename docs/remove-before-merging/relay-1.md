# Relay 1 — comparing the Haiku/Sonnet/Opus runs of the Opus quality gate

## 1. Standing constraints

- "всё что правишь правь уже после того как перенесёшь, чтобы я увидел дифф от
  исходного тоже" — done; keep editing the moved notes as further commits, never
  rewrite their first commit.
- "здесь оставь только правки delegation-model-capabilities" — muthur#253
  carries only that file (plus working files /finalize sweeps).
- `delegation-model-capabilities.md` describes models as subagents an Opus
  delegator hands work to, not as a session's own driver ("там должно
  описываться именно для опуса, передающего дешёвым подагентам, а не наоборот").

## 2. The conversation

**Operator 1:**

> Сравни реализацию одной и той же задачи тремя моделями (haiku/sonnet/opus
> соответственно): https://claude.ai/code/session_01DaohkE1kSi2cgf98P77S8p
> (+продолжившая её https://claude.ai/code/session_01DaohkFFsYGnqzYXF4juG6D),
> https://claude.ai/code/session_01DaohkE7bS8WQiGsVZMXfjw,
> https://claude.ai/code/session_01DaohkDGvyPHkmGezpudcWA
>
> интересует сравнение: 1- собственно результата -- то, что получилось на выходе
> 2- процесса, в том числе самого догфуда (в случае с первыми двумя) -- то,
> _как_ модель шла к результату 3- костов: оправдал ли (в данном конкретном
> случае) в принципе себя подход "делать дешёвой, проверять дорогой"
>
> интересуют также неожиданности (было ли что-то, с чем более дешёвая модель
> справилась лучше дорогой)
>
> ну и рекомендация -- какую из сессий/пиаров продолжать (и в каком режиме),
> какие закрыть
>
> `.claude/skills/go/delegation-model-capabilities.md` надо синтезировать из
> соответствующих пиаров, плюс добавить что обнаружишь сам

Mid-turn additions: "а, забыл, в сравнения ещё wall time"; and, quoting the
agent's "без плана — правка одного файла": "нужен подробный анализ тоже
(мерджить ли его в конце решим потом)".

**Agent:** routed via /task (planless), read the three PRs (#250 Haiku, #252
Sonnet, #251 Opus), transcripts and usage; wrote a detailed comparison and a
capabilities synthesis; ran /polish and /pr (muthur#253). Findings: Haiku
inverted verdicts 3–4 (who fixes) and its Opus judge passed it because Haiku's
brief carried the plan, not the ask; Sonnet+review ≈ Opus quality at 73% cost,
+23% time; recommendation: continue #251, port from #252, close #250/#252.

**Operator 2:**

> спасибо;
>
> во-первых, пжст перенеси (ну точнее пересоздай) бранч и пиар в
> vzakharov/vovazakharov.com; какие-то выводы-статьи, если будут, будут писаться
> там (стоило начать эту сессию оттуда тоже, но уж как есть). здесь оставь
> только правки delegation-model-capabilities
>
> по твоему сообщению, мельком (весь отчёт пока не читал)
>
> > Haiku перевернул вердикты 3 и 4.
>
> наверное, стоило в первоначальной постановке задачи сказать "при постановке
> задачи подагенту включи моё исходное сообщение буквально". Сейчас прогоню ещё
> раз в таком виде, заодно посмотрим насколько ошибки воспроизводимы
>
> > и нет выключателя, которого ты не просил.
>
> я при беглом просмотре записал это как раз в "неожиданное лучше" у Соннета
>
> > Haiku срелеил сразу после плана, на ~187k контекста
>
> у него были сложности с релеем, что-то там не сработало, ты это увидел?
>
> > Haiku + ревью номинально −57%, но результат придётся переделывать, так что
> > не окупилось
>
> я сейчас запросил того (первого) хайку релейнуть в опус чтобы тот проверил и
> исправил работу; посмотри что стало с костами (ну и результатом тоже) в этом
> режиме (хотя это уже отход от первоначальной постановки эксперимента,
> конечно): https://claude.ai/code/session_01DaohkCAUm4oyGqC2bhM7vZ
>
> и ещё пройдись по delegation-model-capabilities и посмотри что из того что ты
> там написал там does not belong (там должно описываться именно для опуса,
> передающего дешёвым подагентам, а не наоборот).
>
> всё что правишь правь уже после того как перенесёшь, чтобы я увидел дифф от
> исходного тоже.

**Agent:** moved the notes verbatim to vovazakharov.com#230
(`writing/notes/weak-driver-opus-gate.md`), then edited them: switch counted as
a Sonnet plus; relay troubles (relay-last-reply.py fails by contract on a
first-turn relay, /relay doesn't cover it; the verbatim ask in Haiku's
relay-1.md corrupted by a stray `>`, made worse by the Opus fixer; the second
relay's script blocked by auto mode); new § 4 on the Haiku→Opus fix-up (chain
$3.73 = 89% of Opus-only, ~2× time; Opus fixed verdict semantics but left the
ask out of the judge brief); a re-run checklist. In muthur removed the
comparison and trimmed the capabilities file to the `haiku` delegation lessons
only; refreshed #253 body, title and squash proposal. (verbatim in Last agent
turn)

**Operator 3:**

> а вот ещё странно, что ни хайку ни соннет не отдали сам план на ревью опусу,
> хотя в оригинальном запросе прямо перечислялся /plan как порог

**Agent:** neither gated its plan because the gate did not exist in the skills
while the plan was written, and both plans deferred dogfooding to /go (Sonnet's
own rule skips the /plan gate in /task outcome 3); for Haiku the plan was where
the misreading entered, the cheapest place to catch it. Added this as item 0 of
«Неожиданности» in the notes (3331d35 in vovazakharov.com), then relayed for the
context budget — this relay's own turn.

## 3. Intent

Vova is running an experiment: does "a cheap model builds, Opus verifies" pay
off in this agent loop? He wants evidence for posts (written in
vovazakharov.com) and a capabilities file in muthur that helps Opus delegate to
cheaper subagents. He plans to re-run the same task with "include my original
message verbatim when briefing the subagent" to test reproducibility.

## 4. Decisions

- **Notes live in vovazakharov.com `writing/notes/`** (evidence for a post not
  yet drafted, per `writing/CLAUDE.md`), in Russian as written; translation only
  if a post goes English.
- **Capabilities file = delegation only.** Driver observations (cost vs
  Opus-only, loop-prose misses, reviewer-brief lesson) removed; the `haiku`
  entry keeps transferable traits and says it was seen driving a session, not
  yet as a subagent. The `sonnet` entry equals main.
- **A dropped Sonnet "miss"**: the Opus reviewer's claim that a weaker session
  can't know the Opus model id is false here (system prompt lists all ids).
- **Recommendation**: continue #251 (Opus) via /handle, porting from #252 the
  gate-before-plan-flip, the verbatim-ask brief and "reviewer prefers revise";
  close #250 and #252.

## 5. Errors and dead ends

- First commit's `Claude-Session` trailer was mistyped and amended before push.
- Running `vet.sh` from other branches' worktrees fails `check-estimates` on
  this session's own row — an artifact of where it ran, not of those branches.

## 6. State

- **muthur**: branch `claude/model-capabilities-from-gate-runs-z0qwbt`, draft
  https://github.com/vzakharov/muthur/pull/253 ("feat: record what Haiku needs
  in a brief, for delegation"), squash proposal posted and tracked in
  `docs/remove-before-merging/squash-message.md`.
- **vovazakharov.com**: branch `claude/weak-driver-gate-notes-z0qwbt`, draft
  https://github.com/vzakharov/vovazakharov.com/pull/230, head 3331d35, squash
  proposal posted and tracked. Its PR body predates the § 4 and item-0 additions
  but stays accurate. That repo must be attached (`add_repo`) and cloned to
  `/home/user/vovazakharov.com` in a new session.
- No plan files. Nothing running besides this session's keepalive. Estimate: 4 h
  senior analyst + 1 h senior prompter, all done here; no remainder.

## 7. Pointers

- Notes: `writing/notes/weak-driver-opus-gate.md` in vovazakharov.com.
- Capabilities: `.claude/skills/go/delegation-model-capabilities.md`.
- Sessions studied: Haiku 01DaohkE1kSi2cgf98P77S8p → 01DaohkFFsYGnqzYXF4juG6D →
  Opus fix-up 01DaohkCAUm4oyGqC2bhM7vZ; Sonnet 01DaohkE7bS8WQiGsVZMXfjw; Opus
  01DaohkDGvyPHkmGezpudcWA (`list_events` with `kinds: ["result"]` gives cost
  and timing).
- This session: https://claude.ai/code/session_01DaohkDXkx4zjTwnmDQ5HeC

## 8. Next step

Wait for the operator. Likely next: the re-run's sessions to compare against
these notes, or merging #253 / #230.

## 9. Last agent turn

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Ветка и PR в vovazakharov.com есть: https://github.com/vzakharov/vovazakharov.com/pull/230, файл перенесён как был. Теперь убираю его из muthur.

Добавляю squash-предложение в PR в vovazakharov.com. `content:` не публикующий тип, так что мердж ничего не задеплоит.

Вова, переезд сделан: заметки теперь в https://github.com/vzakharov/vovazakharov.com/pull/230, файл `writing/notes/weak-driver-opus-gate.md`. Первый коммит там — файл как был, второй — мои правки, так что дифф от исходного виден. В muthur в https://github.com/vzakharov/muthur/pull/253 осталась только правка `delegation-model-capabilities.md`; PR я переименовал под новое содержание. Заметки остались на русском, хотя всё, что в той репе пишется для людей, идёт на английском. Если пост будет на английском, переведу.

**Выключатель.** Ты прав, это плюс Sonnet: он повторяет уже существующий `MUTHUR_DELEGATION`. Перенёс его в «неожиданно лучше» у Sonnet.

**Релей Haiku.** Одну проблему я видел и в первой версии упомянул, вторую пропустил.
- **Видел:** `relay-last-reply.py` упал с «no turn before this one wrote any text». Причина: релей случился в первом и единственном ходе сессии, а скрипт по своему контракту дописывает ответ *предыдущего* хода и без него падает. `/relay` ничего не говорит о релее в первом ходе, так что это дыра в muthur, а не ошибка Haiku. Haiku поступил правильно: пометил раздел пустым и ничего не стал пересказывать.
- **Пропустил:** в сводке релея испорчена дословная цитата твоей просьбы. В неё затесался лишний `>`, и от него же упал prettier в `vet.sh`. Смысл цитаты цел. Opus-сессия потом «переформатировала, чтобы vet прошёл», и стало хуже: вложенной цитатой стал весь остаток просьбы.
- При втором релее (в Opus) этот скрипт не запустился вовсе: его остановил auto mode.

**Режим «Haiku делает, Opus проверяет и правит».**
- **Цена.** Вся цепочка Haiku стоила $3.73 и заняла ~15.5 минут работы против $4.17 и 7.5 минут у одного Opus. Это 89% денег и вдвое больше времени. Sonnet с ревью обошёлся дешевле ($3.06).
- **Что Opus исправил.** Он сам нашёл ту же причину, что и я: судья сверял работу с планом, а не с твоим сообщением. Исправил вердикты C и D по смыслу, определение модели и ещё несколько мест.
- **Что осталось.** Твоего сообщения в брифе судьи по-прежнему нет: причину он назвал, но в процедуру исправление не внёс. Гейт в `/finalize` он не перенёс, а залатал повторным vet.
- **Итог:** на этой задаче такой режим свёлся к «сделай на Opus, только медленнее».

**`delegation-model-capabilities.md`.**
- **Убрал:** всё, что описывало модель в роли ведущей сессии под Opus-ревьюером: стоимость против Opus, промахи Sonnet, урок про бриф ревьюеру. Последний про обратное направление: там бриф пишет слабая модель для Opus. Запись `sonnet` вернулась к версии из `main`.
- **Оставил:** запись `haiku` с тем, что пригодится Opus, когда он отдаёт задачу Haiku. Названные правки Haiku вносит точно и только их. Пересказанную своими словами задачу понимает неверно, поэтому в брифе её надо цитировать дословно. В записи прямо сказано, что Haiku пока видели только ведущей сессии, не подагентом.

**Повторный прогон.** Твоя добавка «включи моё сообщение буквально» исправит слепоту судьи, но не чтение Haiku: план Haiku пишет раньше, чем появляется любой подагент. Поэтому главное, что покажет прогон, — поймает ли судья ошибку чтения, если та повторится. Список того, что ещё смотреть, — в заметках, в конце.
```
