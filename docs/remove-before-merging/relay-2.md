# Relay 2 — cold-cache stop copy, parked for dogfooding

`relay-1.md` holds the session up to its first park (the original critique, the
first rework, the "why is reorienting dearer yet cheaper" explanation). This
summary repeats what still matters and covers everything after.

## Standing constraints

None stated by the operator.

## The conversation

Turns covered by `relay-1.md`, condensed: the operator criticised the cold-cache
stop's message (why offer a dearer reorientation; dearer up front yet cheaper
per request reads as a contradiction; say what you save over the next 100k, and
only when > 0). The agent reworked it onto one saving over 100k
(`fresh_saving_over`) and opened draft PR #220; then explained that
reorientation is priced by its path (many requests), not its resulting context.

1. **Operator** (after the first park):

   > хотя да, давай
   >
   > > Сводить ли 100k в одну константу. да
   >
   > > Останавливать ли промпт, когда новая сессия невыгодна нет

   ("хотя да, давай" answered the offer to reword the reorientation clause.)
   Mid-turn they pasted a live alert from this session: "Prompt cache expired:
   72.4 h since the last response, 196k tokens to re-cache. Carrying on
   re-caches them for ~$1.19. A new session pays ~$0.88 to reorient … saves
   ~$0.96 (~23%) over the next 100k tokens of work …".

   **Agent:** moved the 100k slice into `SLICE` in
   `.claude/costs/lib/restart.py` (cold-cache hook and `priced_line.py` read it;
   the context-budget bash hook no longer passes it); reworded the clause; kept
   "no stop when a fresh session doesn't pay".

2. **Operator:**

   > давай адаптируем копию, а то каша какая-то, плюс почему б в тестах не
   > грузить проверяемые текстовые значения хелперами, а не прописывать вручную?
   > Копия:
   >
   > 🪫 PROMPT CACHE EXPIRED Continuing costs $1.19 (196k tokens), reorienting
   > in a new session costs ~$0.88, and saves ~23% over the next 100k tokens of
   > work. Consider starting a new session, or send any message to continue
   > here. A bare "!" will do.

   Then mid-turn: "... costs
   $1.19 (196k tokens) to re-cache, reorienting ...";
   "так, но бывают же ситуации когда reorienting дороже, и тем не менее
   экономия?"; "тогда надо — reorienting ~$Y,
   but breaks even after the next Zk tokens of work?"; "btw у нас расчёты
   затраты, реориентация, breakeven и всё это -- DRY между авторелеем и
   стоппером холодного кеша? или там разные расчёты?"; "ты прости но я всё ещё
   думаю как лучше формулировать :)".

   **Agent:** adopted the copy; split the text into helpers (`priced_offer`,
   `estimated_offer`, `unpriced_offer`, `stop_text`) that the tests build their
   expected strings from, so tests pin figures, not copy; added
   `fresh_break_even`. Answered DRY: one model, `restart.py`, shared by both
   hooks (`_switch_over`, `SLICE`, reorientation sources); only the inputs
   differ (relay: summary turn + reorientation vs nothing; cold cache:
   reorientation vs re-cache), and the two solvers answer different questions
   (`line_for`: the context where a relay starts paying; `fresh_break_even`: the
   work after which a fresh session has paid back its extra).

3. **Operator:** "а 23% это от чего?" — **Agent:** of carrying on's total over
   the next 100k (re-cache + reading the context on ~40 requests + writing the
   new tokens): $0.96 of ~$4.17.

4. **Operator:** "и вопрос, мы говорим ТОЛЬКО если за 100к будет экономия, или
   возможно что и стоит дороже, и через 100 к будет дороже?" — **Agent:** only
   when it saves over 100k (above `MUTHUR_COLD_CACHE_MARGIN`, 10% of the
   re-cache, and a re-cache of at least $0.30); otherwise no stop; so a shown
   break-even is always under 100k. Unpriced models are the exception.

5. **Operator:** "а 100k tokens -- разумеется, имеется в виду 100k
   дополнительных токенов инпута, не вообще с учётом всех тулов туда-сюда?" —
   **Agent:** 100k is context growth (messages, outputs, tool results), billed
   input is far more, since ~37–40 requests each re-read the context; what is
   the same both ways (writing the new tokens, output) cancels out of the
   comparison.

6. **Operator:**

   > что если: 1- если продолжить здесь, потратите столько-то на следующие 100к
   > контекста (тут сумма нагрева кеша + следующих 100к, разбивку не пишем) 2-
   > если создать новую, потратите столько-то (реориентация + 100к контекста
   > там, опять же без разбивки), то есть на X% меньше
   >
   > дальше тот же текст с "Consider..."

   Mid-turn: "хотя хочется сделать ещё (если реориентация дороже), что 'до
   стольки-то токенов конекста начать новую сессию будет всё-таки дешевле,
   поэтому оцените примерно оставшийся объём работы' -- но как-то это умудриться
   запихнуть в несколько слов".

   **Agent:** gave both totals (`Saving.carry` added), and, where the
   reorientation is dearer, "(for under ~Zk tokens of work, continuing here is
   cheaper)" — noting the operator's direction was inverted.

7. **Operator:** "да но тогда мы не пишем, сколько экономим здесь на 100к" —
   **Agent:** the 100k saving was still there as "21% less"; offered "up to
   $0.12 cheaper" in the parenthesis, asked which was meant.

8. **Operator:**

   > а, звучит двусмысленно, непонятно было что "a new session costs" тоже
   > относится к "over the next 100 tokens of context)
   >
   > (draft) 🪫 PROMPT CACHE EXPIRED. Over the next 100k of context, continuing
   > here costs ~$3.53, vs over the next 100k tokens of context. The same amount
   > of work in a new session costs ~$2.80 (for under ~14k tokens of work,
   > continuing here is cheaper). Consider starting a new session, or send any
   > message to continue here. A bare "!" will do.
   >
   > проценты думаю все равно мало чем полезны -- 20% от 20 долларов и 5
   > долларов это две большие разницы, как говорят в Одессе; важны абсолютные
   > сбережения

   Mid-turn, the final copy: "🪫 PROMPT CACHE EXPIRED. Over the next 100k of
   context, continuing here costs ~$3.53. The same amount of work in a new
   session costs ~$2.80 (for under ~14k tokens of work, continuing here is
   cheaper). Consider starting a new session, or send any message to continue
   here. A bare "!" will do."

   **Agent:** implemented it verbatim, percentages removed; pushed 3e2edc0.

9. **Operator:** "дам сессии протухнуть, потом задогфудим, посмотрю сообщение и
   если всё ок начну finalize в новой сессии. спасибо!" — **Agent:** stopped the
   keepalive, gave `/finalize claude/cold-cache-fresh-session-saving-286i3o`,
   noted `relay-1.md` was stale.

10. **Operator:** "не, ну релей подправь таки, если сообщение будет не ок мне
    нужно будет его править" — answered by this relay. (verbatim in Last agent
    turn)

## Intent

A cold-cache stop the operator can read at a glance: two dollar totals over the
same 100k of context, no breakdown, no percentages, a break-even note only where
reorienting is dearer, and no stop at all when a new session doesn't pay. They
will dogfood it on this session once its cache expires, then finalize — or tweak
the copy first.

## Decisions

- **Copy is the operator's, verbatim**: `priced_offer()` in
  `.claude/cold-cache/hooks/cold_cache.py`. Idle time, price source and the "if
  everything is on the branch" condition were dropped with it.
- **Absolute dollars, no percentages** — the operator's call (see turn 8).
- **No stop when a fresh session doesn't pay** (≤ 0 or under
  `MUTHUR_COLD_CACHE_MARGIN` of the re-cache) — operator: "нет" to stopping.
- **`SLICE` lives in `restart.py`**, shared by both hooks — operator: "да".
- **Tests build expected text from the hook's helpers** (`hook.stop_text`,
  `hook.priced_offer`, …), pinning figures only — operator's ask.
- **Terms**: "carry" = continuing in this session; "fresh" = a new session;
  "break-even" = the work (context growth) after which a dearer reorientation
  has paid back its extra; "100k of context" = context growth, not billed input.

## Errors and dead ends

- An intermediate "reorienting costs ~$Y, but breaks even after Zk" line and a
  "costs more, but carries less" line were both superseded by the two-totals
  copy.
- The operator's first break-even wording had the direction inverted (a dearer
  fresh session wins only past the break-even, not before it).

## State

- Branch `claude/cold-cache-fresh-session-saving-286i3o`, pushed; PR
  https://github.com/vzakharov/muthur/pull/220 — draft, open, mergeable, no CI
  checks reported. Last code commit 3e2edc0.
- Squash proposal: comment 6364814035 on the PR, working file
  `docs/remove-before-merging/squash-message.md` — current.
- `/go` done; `/finalize` not run. No plan file. No keepalive, no PR
  subscription, no check-ins.
- Estimate (whole task, this session): 3 h senior developer "the change
  re-derives a cost comparison and a break-even point inside the pricing model
  two hooks share, rebuilds the hook fixtures to price a realistic session, and
  moves a constant across a bash-python boundary" + 1.5 h middle copywriter "the
  stop message went through several operator rounds to make two totals and a
  break-even read unambiguously in one line". Nothing handed on beyond
  `/finalize`.

## Pointers

- `.claude/cold-cache/hooks/cold_cache.py` — `priced_offer`, `estimated_offer`,
  `unpriced_offer`, `stop_text`, `reason`, `outclassed`.
- `.claude/cold-cache/CLAUDE.md` — the guard's contract.
- `.claude/costs/lib/restart.py` — `SLICE`, `Saving`, `_switch_over`,
  `saving_over`, `fresh_saving_over`, `fresh_break_even`.
- `.claude/cold-cache/test_cold_cache.py` (`DEFAULT_OFFER`, figures pinned per
  case), `.claude/costs/test_restart.py`.
- To see each variant's text without a cold cache: build a `HookCase` session as
  the tests do and call `prompt()` (the tests' scenarios: default session;
  `fresh_sessions(60_000, 1.19)`; a resume with `fresh_sessions(60_000, 0.30)`).
- Predecessor transcript:
  https://claude.ai/code/session_01KPAD1wtwmQpeuHTJQZzihd

## Next step

Wait for the operator. They will dogfood the stop on their own session, then
either ask for a copy change ("если сообщение будет не ок мне нужно будет его
править") — edit `priced_offer`/`stop_text`, re-pin the test figures if they
changed, update `.claude/cold-cache/CLAUDE.md` and the squash proposal if the
contract moved — or run `finalize`.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages,
usually unneeded but harmless; the reply proper is usually its last
paragraphs.

````text
Пусть остывает, Вова: убираю keepalive, иначе он не даст кешу протухнуть.

Keepalive остановлен, ветка запушена целиком.

Через час кеш протухнет, и следующий твой промпт в этой сессии наткнётся на новый стоп с настоящими цифрами. Если цифры сойдутся, новую сессию начни с:

```
/finalize claude/cold-cache-fresh-session-saving-286i3o
```

Одна деталь: на ветке лежит `docs/remove-before-merging/relay-1.md` со старым «Next step» (ждать решений по копии). `/finalize` его всё равно сметёт, а запускать `/relay take` для финализации не нужно.

Удачного догфудинга!
````
