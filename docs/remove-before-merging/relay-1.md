# Relay 1 — /polish floor skips base merges (parked)

## Standing constraints

None stated by the operator.

## The conversation

1. **Operator** (opening, via `/task`): "`/polish`'s scope re-reads work that
   was already polished elsewhere. Fix `.claude/skills/polish/passes.md` § "The
   floor" so a run reads only what nobody has polished. […] diff HEAD against a
   virtual merge of the floor with the base commit the branch has merged:
   `mb=$(git merge-base HEAD origin/<base>)`,
   `T=$(git merge-tree --write-tree <floor> "$mb" | head -1)`,
   `git diff "$T" HEAD` […] Mind merge-tree's exit code 1 on conflicts […] A
   second hole of the same kind, from the same adopter, for you to rule on: an
   "elephant" branch takes its bites as child PRs squash-merged into it […]
   Decide whether this fix covers it, or whether it needs a follow-up issue."
   (Condensed: the middle explains the defect and the adopter's 1108 → 1001 file
   figures.)

   **Agent:** went planless; rewrote § "The floor" with the virtual-merge recipe
   plus a `git cat-file -e "$T^{tree}"` guard (merge-tree exits 1 on a bad ref
   too); verified in a scratch repo; ruled the elephant case uncovered and filed
   issue #241 via `/propose-issue`; `/polish` subagent found nothing; opened
   draft PR #242 with squash proposal.

2. **Operator:** "во-первых, пропиши где-то никогда не открывать issue без
   спроса / во-вторых, слон сейчас даже так здесь не работает, вызывающая сессия
   работала на vzakharov/vovazakharov.com#169, где понятие слона изменено, так
   что ничто из этого к текущему состоянию muthur не относится / но раз уж
   упомянули -- создай новую сессию как раз сделать такую переделку слона.
   должна выключаться по энву, переходя в предыдущий (текущий для нынешнего
   состояния muthur) однопиарный подход."

   **Agent:** added an operator-yes gate to `/propose-issue` Step 3; removed
   elephant/#241 mentions from the PR body and squash proposal; asked whether to
   close #241; started session session_01DaohkDV4jUxEY1kwvC2knd for the
   env-toggled elephant rework (pointing it at vovazakharov.com PR 169, branch
   `claude/multi-app-sliced-design-7bn3oq`, `.claude/skills/plan/elephant.md`).

3. **Operator:** "а, создавшая сессия туда такое записала? тогда беру свои слова
   назад -- ты поступил правильно с учётом запроса"

   **Agent:** confirmed the `/task` prompt said "or whether it needs a follow-up
   issue"; offered keep / soften / revert the new rule, recommending keep.

4. **Operator:** "откатить / и ещё / > По ходу пришло предупреждение о бюджете
   контекста: около 146k токенов при пороге 141k / что-то несколько последних
   раз порог сильно упал -- он у нас как-то динамически считается?"

   **Agent:** reverted the rule; explained the priced warning line and named
   #222 as the likely cause, unverified; offered to investigate a floor for the
   priced line. (verbatim in Last agent turn)

## Intent

- Land the `/polish` floor fix (#242) as a base-merge-only change; the elephant
  case is not this repo's concern in its current state.
- No gate rule on issue creation (operator reverted it).
- Understand why the context-budget warning line has dropped lately.

## Decisions

- **Virtual-merge scope** over `git diff <floor>..HEAD`: excludes base work,
  keeps own commits and conflict resolutions. The `cat-file` tree check guards
  against merge-tree's exit 1 on unreadable refs.
- **Elephant out of scope**: muthur's elephant is single-PR; the child-PR
  elephant belongs to vovazakharov.com PR 169 and is being ported, env-toggled,
  by the separate session.
- **Issue gate reverted** at the operator's call.

## Errors and dead ends

- Issue #241 was filed on reading "or whether it needs a follow-up issue" as
  permission; the operator first objected, then accepted it as within the
  request. #241 is irrelevant to muthur now; closing it awaits the operator's
  yes.
- The last reply named the revert commit as 4f0c1a2; it is 87c8885.
- The revert commit's subject uses `revert:`, outside CLAUDE.md's prefix list;
  left as is (pushed; squash replaces it).

## State

- Branch `claude/polish-floor-skips-base-merges`, last pushed 87c8885 before
  this summary; draft PR #242 open
  (https://github.com/vzakharov/muthur/pull/242), squash proposal posted and
  tracked in `docs/remove-before-merging/squash-message.md`.
- Issue #241 open.
- Sibling session session_01DaohkDV4jUxEY1kwvC2knd running the elephant rework.
- Estimate (unchanged, nothing handed on): 2 h senior prompter — two
  load-bearing rules where a misread wording re-reads a codebase or publishes
  without asking; 1 h senior developer — the virtual-merge mechanism needs
  verifying against merge-tree's exit codes and edge cases.

## Pointers

- `.claude/skills/polish/passes.md` § "The floor" — the fix.
- `.claude/context-budget/CLAUDE.md`,
  `.claude/context-budget/hooks/priced_line.py`, `.claude/costs/lib/restart.py`
  — the priced warning line. This session's inputs: reorientation 97.7k context
  / $0.38 from its own orientation, ~0.00067 requests per token, warning
  line 140341.
- Transcript: https://claude.ai/code/session_01DaohkDkHXE5awKuUXuiNd3

## Next step

Wait for the operator. Open questions from the last reply: whether to close
#241, and whether to investigate the context-budget line ("Разбираться?").

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Now the PR body bullet, then commit.

Откатил. Теперь про порог.

Откатил: правило убрано из `/propose-issue`, а из PR #242 и предложенного сообщения для squash ушли и правило, и фраза про слона с #241 (коммит 4f0c1a2, запушен). #241 по-прежнему открыт и ждёт твоего «закрывай». Коммит я озаглавил `revert:`, а этого префикса нет в списке CLAUDE.md. Переписывать запушенное не стал, при squash заголовок всё равно заменится.

**Про порог: да, он считается динамически, и у этой сессии он вышел низким, потому что я очень быстро сориентировался.** Предупреждение срабатывает там, где передача работы новой сессии через `/relay` начинает окупаться на следующих 100k токенов. Расчёт сравнивает две суммы:

- **Работать дальше:** каждый следующий запрос заново читает весь накопленный контекст. У меня выходило около 67 запросов на каждые 100k прироста, потому что было много коротких вызовов инструментов. Чем чаще запросы, тем дороже каждый лишний токен контекста.
- **Передать работу:** новой сессии надо заново сориентироваться. Её цена берётся из того, во что обошлась ориентация этой сессии: около 98k контекста и $0.38.

Дешёвая ориентация при частых запросах сдвигает точку окупаемости почти вплотную к начальному контексту. Тут она пришлась на 140k, всего примерно на 42k выше того, с чего стартовала бы новая сессия. Без цены порог был бы фиксированным, 300k.

**Почему стало заметно в последние разы:** скорее всего из-за #222 от 26 октября. С тех пор агент сам отмечает конец ориентации через `oriented.py`, а раньше её конец определялся иначе. Если агент отмечает рано, ориентация выходит дешёвой и порог падает. Сам я это не проверял: старые сессии с новыми не сравнивал. Подтвердить можно, пересчитав порог для нескольких сессий до и после #222.

Если низкий порог мешает, есть готовые переключатели в переменных окружения облачной среды: `MUTHUR_CONTEXT_BUDGET_WARN` задаёт порог вручную, а `MUTHUR_CONTEXT_BUDGET_LINES=fixed` возвращает фиксированные 300k/400k. Могу вместо этого разобраться по существу. Похоже, расчёт не учитывает, что новая сессия после `/relay` получает готовую сводку, а не ориентируется с нуля. Тогда ему стоит иметь нижнюю границу для порога, а не брать дешёвую ориентацию как есть. Разбираться?
```
