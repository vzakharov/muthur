# Relay 2 — LSP tool trial: the flag alone does not surface the tool

## Standing constraints

None stated.

## The conversation

1. **Operator (relay launch):** «/relay take claude/lsp-tool-trial-dra5wk —
   ENABLE_LSP_TOOL=1 уже в окружении, дальше проверка инструмента LSP на
   Python-скриптах репо.» **Agent:** Attached (already on the branch), read
   `relay-1.md`, set an estimate. Checked: `ENABLE_LSP_TOOL=1` is in the env,
   but no `LSP` tool exists — not in the tool list, not among deferred tools,
   ToolSearch for "LSP" finds nothing. No plugins installed (`~/.claude/plugins`
   holds no LSP plugin). Tried
   `claude plugin marketplace add anthropics/claude-plugins-official && claude plugin install pyright-lsp@claude-plugins-official`
   — denied by the auto-mode classifier as "Untrusted Code Integration"; handed
   the operator a fenced message to allow it. Noted that even a user-scope
   install likely would not surface the tool in this session (tool list fixed at
   start). Proposed the durable route: project `.claude/settings.json` with
   `extraKnownMarketplaces` (the official marketplace) and
   `enabledPlugins: {"pyright-lsp@claude-plugins-official": true}`, edited via a
   staged copy (it loads every turn), then trial in a new session; or the same
   in the environment's settings for the operator alone. Asked for agreement.
   (verbatim in Last agent turn)

The operator did not reply; the session was parked by the keepalive's last wake.

2. **Operator (after the park):** «> План был такой: подключить официальный
   маркетплейс плагинов anthropics/claude-plugins-official и установить из него
   pyright-lsp. — ну мы же хотим сделать не только для себя, но и для адоптеров.
   однократная установка плагина вопроса не решит» **Agent:** Agreed: the
   one-off install was only a probe. Verified the official marketplace manifest
   (`gh api repos/anthropics/claude-plugins-official/contents/.claude-plugin/marketplace.json`)
   lists per-language LSP plugins (`pyright-lsp` → `pyright-langserver --stdio`,
   `typescript-lsp` → `typescript-language-server`, `rust-analyzer-lsp`,
   `gopls-lsp`, …); each plugin only declares a command, the binary must be on
   PATH. Proposed the adopter-shaped design: (1) muthur's
   `.claude/settings.json` carries `env.ENABLE_LSP_TOOL=1`, the marketplace in
   `extraKnownMarketplaces` and `pyright-lsp` in `enabledPlugins` (muthur's own
   scripts are Python) — whether settings `env` reaches the tool's gate is
   unverified; (2) the binary goes in `.claude/hooks/install-deps.sh`; (3) a
   stack landing gains a fourth site to wire — the language's LSP plugin — in
   CLAUDE.md § "Vetting" and `/detemplate`, so an adopter's stack picks its own
   plugin. Verification in a new session on the branch. Asked for a go.

## Intent

Vova wants agents to have a retrieval option beyond grep with the smallest blast
radius; the chosen candidate is Claude Code's built-in `LSP` tool, now being
trialled on the repo's Python scripts.

## Decisions

- **Project-level plugin over a per-session install** (proposed, not yet
  approved): the tool list is fixed at session start, so a mid-session install
  cannot be trialled here, and a project setting reaches every session with no
  environment change.

## Errors and dead ends

- `ENABLE_LSP_TOOL=1` alone yields no `LSP` tool at all (not even a "No LSP
  server available" error) on Claude Code 2.1.312 — consistent with relay-1's
  guess that the tool's gate needs a plugin-provided LSP server.
- `claude plugin marketplace add … && claude plugin install …` is blocked by the
  auto-mode classifier ([Untrusted Code Integration]); it passes only if the
  operator's own message names it.

## State

- Branch `claude/lsp-tool-trial-dra5wk`, no PR. Commits beyond `main`: only the
  relay summaries.
- No plan file. Nothing running; keepalive stopped by the park.
- Environment `env_01Xg9JSSbzPCQgWZzAGCtGhK`: `ENABLE_LSP_TOOL=1`,
  `pyright-langserver` at `/root/.local/bin/`, no LSP plugin.
- Estimate: this session 0.5 h senior developer — "establishing that the flag
  alone does not surface the LSP tool, and which plugin wiring it needs, takes
  reading an undocumented gate and the plugin model, not a routine lookup".
  Remainder handed on: wiring the plugin and the trial itself, unsized — the
  successor sets its own estimate.

## Pointers

- `.claude/settings.json` — where `extraKnownMarketplaces` / `enabledPlugins`
  would go; `.claude/rules/staging.md` — the staged-copy mechanics for it.
- `docs/remove-before-merging/relay-1.md` — the survey that chose LSP.
- This session's transcript:
  https://claude.ai/code/session_01DaohkDdJpVqGT8LWBLudag

## Next step

Wait for the operator: the adopter-shaped design in conversation item 2
(settings `env` + marketplace + `pyright-lsp`; binary in `install-deps.sh`; LSP
plugin as a fourth stack-landing site in CLAUDE.md § "Vetting" and
`/detemplate`) awaits their go. Operator's framing: «мы же хотим сделать не
только для себя, но и для адоптеров».

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

````text
Already on target branch; skip steps 2–4. Read the summary.

Привет, Вова. Эта сессия продолжает https://claude.ai/code/session_01DaohkCEmE8BrUSL3Fo7HUA. Я на ветке `claude/lsp-tool-trial-dra5wk` и коммичу и пушу только туда.

Инструмента LSP у меня нет, хотя переменная `ENABLE_LSP_TOOL=1` до сессии дошла. Его нет ни в списке моих инструментов, ни среди отложенных, поиск по «LSP» тоже ничего не находит. Поэтому до сообщения «No LSP server available» дело даже не доходит. Похоже, флаг лишь открывает дверь: инструмент появляется, только когда загружен плагин с LSP-сервером. А таких плагинов здесь нет ни одного. `pyright-langserver` при этом в образе стоит, так что не хватает только плагина-обёртки. Дверь есть, ручки нет, всё по Плоскому миру.

Я попробовал поставить плагин сам. План был такой: подключить официальный маркетплейс плагинов `anthropics/claude-plugins-official` и установить из него `pyright-lsp`. Автоматический классификатор прав остановил команду как «Untrusted Code Integration». Если хочешь пропустить её, пришли:

```
Разрешаю выполнить: claude plugin marketplace add anthropics/claude-plugins-official && claude plugin install pyright-lsp@claude-plugins-official
```

Даже если установка пройдет, LSP в этой сессии, скорее всего, так и не появится: список инструментов фиксируется при старте. Такая установка нужна только чтобы проверить, что плагин вообще встаёт. Чтобы плагин был во всех сессиях, нужно другое:

- **На уровне проекта:** в `.claude/settings.json` добавить `extraKnownMarketplaces` (тот же маркетплейс) и `enabledPlugins: {"pyright-lsp@claude-plugins-official": true}`. Тогда каждая новая сессия в репо подхватывает плагин сама, и в окружении ничего настраивать не надо. Этот файл загружается на каждом ходу, поэтому правка идёт через staged-копию.
- **Только для тебя:** то же самое в настройках окружения.

Предлагаю первый вариант, а проверять LSP на Python-скриптах уже в новой сессии. Если согласен, внесу правку в `.claude/settings.json` и передам работу дальше.
````
