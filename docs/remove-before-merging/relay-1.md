# Relay 1 — hook state follows the session's starting worktree

## Standing constraints

- The operator, mid-turn: «не упоминай "&lt;downstream&gt;" нигде» — the
  original names the downstream repository; it is redacted here because quoting
  it would break the rule itself. Never write that repository's name in any
  file, commit, PR text or comment in muthur. Call it "a downstream".
- From the opening prompt, verbatim: "Read ONLY these files — the rest of that
  repo is a private employer's material and none of it may enter muthur".

## The conversation

1. **Operator** (`/task`, condensed past its opening; the downstream's name is
   redacted as `<downstream>`): "Upstream a downstream fix: per-session hook
   state should follow the worktree the session _started_ in, on top of
   `.claude/hooks/dispatch.sh` (#276)." Why: `dispatch.sh` picks the checkout
   from the event payload's `cwd`, which follows a `cd` and on a delegate's tool
   call (Agent with `isolation: "worktree"`) names the delegate's worktree. So
   the cost row, keepalive state and estimate notice landed in that worktree's
   `tmp/`. _Condensed:_ the downstream resolves the root from the transcript's
   first `cwd` and swaps in that worktree's toplevel when it shares the git
   common dir. It does this in `session_state.py` (`checkout`, `started_in`,
   `rev_parse`, `OPENING`), in `lib.sh` (`project_root`), in `keepalive.py`
   (only the worktree parts: `checkout` in `main`, `start_line` naming the own
   checkout's watcher) and in `test_estimate_notice.py` (worktree tests). Read
   via a git clone over `$GH_TOKEN`, those files only. Asked for: re-express it
   in muthur's terms after #276, add a delegate test through `dispatch.sh`
   (event `cwd` in worktree B, transcript starting in A → state lands in A),
   land it through the loop to a draft PR, and have the commit/squash tell
   adopters that a downstream carrying its own copy replaces it on sync.
   - **Agent:** an interim line confirming the name would appear nowhere, then
     implemented it in `dispatch.sh` alone (see Decisions). Ran `/polish` and
     `/pr`, which opened draft PR #278 with the squash proposal and review
     board. Removed the clone from `tmp/`. (verbatim in Last agent turn)
2. **Operator** (mid-turn, during 1): «не упоминай "&lt;downstream&gt;" нигде» —
   see Standing constraints.

## Intent

Upstream the fix so a delegate's worktree never takes the session's hook state,
in muthur's own shape, with no trace of the downstream's name or any other
content from it.

## Decisions

- **Fix lives in `dispatch.sh` only**, not across the four downstream files.
  Every hook in `settings.json` is dispatched since #276, so choosing the
  checkout there gives `session_state.py`, `lib.sh` and the keepalive the right
  `CLAUDE_PROJECT_DIR` for free. The keepalive's `HOOK` is already the
  dispatched copy, so `start_line` needs no change. Beat: porting the four-file
  version, which would put three copies of one rule in the tree.
- **Fallbacks:** no transcript file → the payload's `cwd`. A transcript whose
  first 50 records (`OPENING`) carry no `cwd` → the anchor. This follows the
  downstream's `started_in`.
- **Known trade-off, told to the operator:** a session opened in the main
  checkout that moves into a worktree mid-session keeps its hooks in the main
  checkout. The downstream behaves the same way.

## Errors and dead ends

None.

## State

- Branch `worktree-dispatch-started-in`, head `67de1e5`, pushed, tree clean.
- PR #278, open, draft: https://github.com/vzakharov/muthur/pull/278. Squash
  proposal posted; working file `docs/remove-before-merging/squash-message.md`.
  Review focus at `docs/remove-before-merging/review-focus.json`.
- No plan file (planless). `/finalize` and `scripts/vet.sh` not run yet.
- Estimate kept whole (the work is done; nothing is handed on): 3 h senior
  developer "hook dispatch is cross-cutting shell plumbing where a wrong root
  silently loses session state; needs git-worktree fixtures and a judgement on
  where the fix belongs" + 0.5 h middle editor "the catalog entry and dispatcher
  contract must stay exact for adopters".

### Watches

https://claude.ai/artifact/6SjDUEaF1zaz9aQuekvZf1

## Pointers

- `.claude/hooks/dispatch.sh`: `started_in` and the header comment.
- `scripts/test_dispatch.py`: three new tests, including the delegate case.
- `.claude/skills/update-muthur/catalog/g4-remote-plumbing.md`: the dispatcher's
  catalog entry.
- This session: https://claude.ai/code/session_016Z4TKpmsU5nLQXCVVeoCti

## Next step

Wait for the operator. `/finalize` is the natural next step once they ask.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Вова, принял: «<downstream>» (redacted per the standing constraint) не появится ни в коде, ни в коммитах, ни в PR — только «a downstream». Сейчас переношу фикс в muthur.

Now the dispatcher edit.

Закоммитил фикс; теперь хвост цикла — `/polish`, затем `/pr`.

Polish done and pushed. Now `/pr`.

Черновик PR открыт (#278); дописываю предложение для squash и публикую его.

Step 7: `MUTHUR_AUTO_REVIEW_BOARD` is on, so the review board goes next.

Публикую доску ревью и вешаю ссылку в PR.

Вова, PR открыт черновиком: хуки теперь берут чекаут из того места, где сессия **началась**, поэтому делегат в своём worktree больше не уносит туда состояние сессии.

https://github.com/vzakharov/muthur/pull/278

**Как это устроено.** Делал напрямую, без плана: правка в одном файле плюс тест. Скажи `plan`, если нужен план. Твой рецепт трогал четыре файла (`session_state.py`, `lib.sh`, `keepalive.py`, тест estimate notice). В muthur после #276 все хуки из `settings.json` и так запускаются через `dispatch.sh`, поэтому вся логика поместилась туда. Диспетчер читает первый `cwd` из первых 50 записей транскрипта. Если транскрипта ещё нет, берётся `cwd` события. Если транскрипт есть, но `cwd` в нём не нашлось, хук запускается из `CLAUDE_PROJECT_DIR`. Остальные три файла получают правильный `CLAUDE_PROJECT_DIR` и сами ничего не вычисляют. По той же причине `start_line` в keepalive уже указывает на watcher из «своего» чекаута. Одна логика вместо трёх копий, которые со временем разъехались бы, как носки в стиральной машине.

**Тесты.** В `scripts/test_dispatch.py` три новых теста:
- **делегат:** `cwd` события в worktree B, транскрипт начат в A. Хук запускается из A, его состояние пишется в `tmp/` основного чекаута A, а в B папка `tmp/` вообще не появляется;
- **сессия, начатая в worktree:** после `cd` в основной чекаут она остаётся в своём worktree;
- **транскрипт без `cwd`:** хук запускается из якоря.

Все 12 тестов проходят. На старом `dispatch.sh` три новых падают.

**Для адоптеров.** В сообщении коммита и в предложенном squash-сообщении есть абзац: downstream со своей копией этого фикса в `session_state.py`/`lib.sh`/`keepalive.py` при синке получит версии из upstream, а работу сделает диспетчер. «<downstream>» (redacted per the standing constraint) нигде не упоминается. Склонированный репозиторий я удалил из `tmp/`.

**Чего фикс не делает.** Если сессия открыта в основном чекауте и потом перешла в worktree уже по ходу работы, хуки останутся в основном чекауте. «Где началась» и «где сейчас работает» тут расходятся. В твоём downstream-рецепте это поведение такое же.

`/polish` поправил только тест: все три теста теперь идут через общий хелпер `dispatch()`. Отдельный `/finalize` с `vet.sh` я не запускал, это следующий шаг.

Доска ревью (я подписан на комментарии с неё): https://claude.ai/artifact/6SjDUEaF1zaz9aQuekvZf1
```
