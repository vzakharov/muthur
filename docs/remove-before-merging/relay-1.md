# Relay 1 — cold-cache stop prices a fresh session by its saving over 100k

## Standing constraints

None stated by the operator.

## The conversation

1. **Operator** (with a screenshot of the cold-cache hook's block, whose text
   read: "Prompt cache expired: 80 min since the last response, 132k tokens to
   re-cache. Carry on: ~$0.67 to re-cache. A new session, if everything the work
   needs is already on the branch and nothing decided since lives only in this
   conversation: ~$0.78 to reorient, priced from this session's own orientation,
   and each request after reads ~118k instead of ~132k. This message was not
   sent: send ! alone to carry on with it as written, send anything else to
   carry on with that instead, or start a new session on the branch."):

   > не оч удачное сообщение, если честно. 1- если reorient дороже, то вообще
   > зачем предлагать? 2- как может быть reorient дороже, но при этом each next
   > costs less? 3- вместо сколько токенов читает, нужно, как в случае с релеем,
   > писать, сколько сэкономишь на следующих 100к токенах (и писать только если
   > это самое сэкономишь >0)

   **Agent:** routed via `/task` → planless `/go`. Reworked the hook so the
   fresh session is priced by one saving over the next 100k tokens (reorient vs
   re-cache up front, smaller context per request after); a fresh session that
   saves nothing or under `MUTHUR_COLD_CACHE_MARGIN` of the re-cache lets the
   prompt pass with no stop. Ran `/polish`, opened draft PR #220, posted the
   squash proposal. Estimated the operator's screenshot case at a ~$0.1–0.2
   saving (by hand, assumed request rate), likely under the margin, so it would
   now probably not be stopped. Put two calls to the operator: (1) whether to
   unify the 100k slice, written in three places (`finish=100000` in
   `.claude/context-budget/hooks/post-tool-context-budget.sh`, `SLICE` in
   `.claude/cold-cache/hooks/cold_cache.py`, `FINISH` in
   `.claude/costs/test_restart.py`) — recommended leaving it or a separate PR;
   (2) whether to keep stopping even when a fresh session does not pay, just to
   show the re-cache price — currently it passes silently, as before.

2. **Operator:**

   > > A new session pays ~$1.19 to reorient … but carries less on every request
   > > after
   >
   > ну вот это я и не понимаю. Если мы за X>Y реориентились, значит у нас там
   > больше токенов, значит последующее сообщение в X должно быть дороже?

   **Agent:** explained that the reorientation price is the cost of the path
   (10–20 requests writing files to cache, re-reading the growing prefix, output
   tokens), not of the resulting context size, which is smaller since a fresh
   session reads only what it needs; moving-to-a-smaller-flat analogy. Offered
   to reword the message so it does not invite the question, e.g. "A new session
   takes ~$1.19 of reading to reorient, but ends up with a smaller context, so
   …" — awaiting a yes. (verbatim in Last agent turn)

## Intent

The operator wants the cold-cache stop's message to be a single, honest
comparison they don't have to compute themselves: offer a new session only when
it actually saves money, and say how much over the next 100k tokens, as the
relay notice does.

## Decisions

- **No stop at all when the fresh session doesn't pay**, rather than a stop
  offering only "carry on" — this keeps the guard's existing rule that a stop
  with no real choice passes (`outclassed()`). The operator has not confirmed;
  it is question (2) above.
- **`MUTHUR_COLD_CACHE_MARGIN` redefined**: the saving over 100k must reach
  `margin` (default 0.10) of the re-cache, instead of the old "10% better on
  both up-front cost and context".
- **`restart.py`**: `saving_over` (relay) and `fresh_saving_over` share
  `_switch_over`; `Saving.relay` renamed `up_front`.
- **Hook tests** build a session at 37 requests per 100k (`session()` helper,
  `WORKED_RATE` from `test_restart.py`), since a two-response transcript prices
  ~1 request per 100k and no fresh session pays off at that rate.

## Errors and dead ends

None worth noting; the first test run failed only because the old two-response
fixture no longer stopped under the new rule.

## State

- Branch `claude/cold-cache-fresh-session-saving-286i3o`, pushed, head 4fe6321.
- PR https://github.com/vzakharov/muthur/pull/220 — draft, open, mergeable, no
  CI checks reported. Squash proposal posted as a comment; working file
  `docs/remove-before-merging/squash-message.md`.
- `/go` complete (implementation, `/polish`, `/pr`); `/finalize` not run.
- No plan file (planless). No PR subscription, no scheduled check-ins.
- Estimate (unchanged, the whole task was done here): 2 h senior developer "the
  change re-derives a cost comparison inside a shared pricing model, and the
  hook fixtures need rebuilding to price a realistic session" + 0.5 h middle
  copywriter "the stop message has to make one figure carry an up-front cost and
  a per-request gain without asking the reader to add them".

## Pointers

- `.claude/cold-cache/hooks/cold_cache.py` — `reason()` builds the message,
  `outclassed()` decides whether to stop.
- `.claude/cold-cache/CLAUDE.md` — the guard's contract.
- `.claude/costs/lib/restart.py` — `_switch_over`, `saving_over`,
  `fresh_saving_over`, `verdict`.
- `.claude/cold-cache/test_cold_cache.py`, `.claude/costs/test_restart.py`.
- Predecessor transcript:
  https://claude.ai/code/session_01KPAD1wtwmQpeuHTJQZzihd

## Next step

Wait for the operator. Pending from them: a yes/no on rewording the message's
reorientation clause (last offer), and the two open calls from turn 1 (unify the
100k slice; stop or pass when a fresh session does not pay). With those settled,
`/finalize`.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages,
usually unneeded but harmless; the reply proper is usually its last
paragraphs.

```text
Вова, X — это цена дороги к контексту, а не его размер. Поэтому новая сессия может заплатить больше и при этом остаться с меньшим контекстом.

- **Перекеш в текущей сессии — это один запрос.** Все 132k токенов, уже лежащих в разговоре, разом пишутся в кеш, и всё.
- **Реориентация — это 10–20 запросов подряд.** Новая сессия читает CLAUDE.md, план, файлы, и каждый прочитанный кусок пишется в кеш по ставке записи, самой дорогой из входных. Каждый следующий запрос заново читает всё накопленное. Плюс она тратит выходные токены на рассуждения, а они дороже входных. Всё это вместе и есть $1.19.
- **На выходе у неё всего 60k контекста.** Она прочла только нужное, а не всю историю разговора. Значит, каждый следующий запрос тащит 60k, а не 174k, и именно на этом она отыгрывает переплату.

Это как переезд в квартиру поменьше: сам переезд стоит дороже месячной аренды, зато потом каждый месяц платишь меньше. Цифра «сэкономит ~$0.72 на следующих 100k» как раз говорит, отбился ли переезд за этот срок.

Твоя логика «дороже — значит токенов больше» верна для одного запроса. Реориентация же оплачивает целую цепочку запросов, и её цена растёт с их числом и с объёмом записанного, а не с итоговым размером контекста.

Если сообщение хука само наводит на этот вопрос, его можно переписать, например: «A new session takes ~$1.19 of reading to reorient, but ends up with a smaller context, so …». Сказать «да» — и поправлю в этом же ПР.

Пока жду твоего ответа, держу кеш тёплым. Если правка не нужна, ПР ждёт `/finalize`.
```
