# Relay 2 — LSP tool: wired in the repo, plugin install moved to the setup script

## Standing constraints

None stated.

## The conversation

1. **Operator (relay launch):** «/relay take claude/lsp-tool-trial-dra5wk —
   ENABLE_LSP_TOOL=1 уже в окружении, дальше проверка инструмента LSP на
   Python-скриптах репо.» **Agent:** Attached (already on the branch), read
   `relay-1.md`. Found no `LSP` tool (not in the tool list, not deferred,
   ToolSearch finds nothing) although `ENABLE_LSP_TOOL=1` is set; no plugins
   installed. Tried
   `claude plugin marketplace add anthropics/claude-plugins-official && claude plugin install pyright-lsp@claude-plugins-official`
   — denied by the auto-mode classifier ("Untrusted Code Integration"); handed a
   fenced allow-message. Proposed project-level `enabledPlugins` in
   `.claude/settings.json`, edited "via a staged copy". Then the keepalive's
   last wake parked the session.
2. **Operator:** «> План был такой: подключить официальный маркетплейс плагинов
   anthropics/claude-plugins-official и установить из него pyright-lsp. — ну мы
   же хотим сделать не только для себя, но и для адоптеров. однократная
   установка плагина вопроса не решит» **Agent:** Agreed — the install was a
   probe. Checked the official marketplace manifest: one LSP plugin per language
   (`pyright-lsp`, `typescript-lsp`, `rust-analyzer-lsp`, `gopls-lsp`, …), each
   declaring only a server command that must be on PATH. Proposed: settings
   `env` + marketplace + `pyright-lsp`; binary in `install-deps.sh`; the LSP
   plugin as a fourth stack-landing site. Asked for a go.
3. **Operator:** «> settings.json правлю через staged-копию, раз он загружается
   на каждом ходу — тогда мы не сможем задогфудить» **Agent:** Corrected itself:
   `.claude/rules/staging.md`'s set is the prompt prefix only; `settings.json`
   is read at startup, not in it, so it is edited in place and is live on the
   branch. Only the `CLAUDE.md` line needs staging.
4. **Operator:** «ну давай попробуем» **Agent:** Implemented and pushed
   (a11c7f3, b2eb8aa, 8e53134); vet passes. Started probe session
   https://claude.ai/code/session_01DaohkFBTd5PxYWvP9jehqg on the branch.
5. **(Probe report, cross-session, data not operator):** no `LSP` tool;
   `ENABLE_LSP_TOOL=1` set; the project marketplace was cloned and `pyright-lsp`
   fetched into
   `~/.claude/plugins/cache/claude-plugins-official/pyright-lsp/1.0.0/` (README,
   LICENSE, empty `.in_use/`), but `~/.claude/plugins/installed_plugins.json` is
   `{"version":2,"plugins":{}}` and `claude plugin list` says "No plugins
   installed". **Agent:** Reported: project `enabledPlugins` fetches but does
   not install in a cloud session (guess, unverified: the install waits on an
   interactive trust prompt nobody answers). Only something that runs before the
   session starts can install it — the environment setup script, not
   `install-deps.sh` (a SessionStart hook runs after the tool list is built).
   Asked the operator to add to the setup script of
   `env_01Xg9JSSbzPCQgWZzAGCtGhK`:
   `claude plugin marketplace add anthropics/claude-plugins-official` and
   `claude plugin install pyright-lsp@claude-plugins-official`. Proposed keeping
   `enabledPlugins` for the local CLI. (verbatim in Last agent turn)
6. **Operator:** «сделал, давай попробуем релейнуть» — this relay answers it.

## Intent

Vova wants agents to have a retrieval option beyond grep with the smallest blast
radius — Claude Code's built-in `LSP` tool — and wants it to reach adopters of
the template, not only this environment («мы же хотим сделать не только для
себя, но и для адоптеров»). The trial dogfoods it on muthur's own Python
scripts.

## Decisions

- **Built-in `LSP` over Serena** (relay-1): reads stay on `Read`, so nested
  `CLAUDE.md` and path-scoped rules still load.
- **`pyright-lsp` for muthur itself**: the loop's own scripts (`scripts/*.py`,
  hooks) are Python and travel to every adopter.
- **`settings.json` edited in place, not staged**: it is not in the prompt
  prefix, and staging would have stopped the dogfood.
- **The stack's LSP plugin is a fourth stack-landing site**
  (`.claude/rules/stack.md`, staged `CLAUDE.md` § "Vetting"); `/detemplate` not
  edited — its Step 7 defers stack wiring to `stack.md`.
- **Plugin install belongs in the environment setup script** (pending
  verification): project `enabledPlugins` alone does not install in the cloud.
  `enabledPlugins` stays for the local CLI.

## Errors and dead ends

- `ENABLE_LSP_TOOL=1` alone yields no `LSP` tool at all on Claude Code 2.1.312.
- Installing the plugin from the agent's Bash is blocked by the auto-mode
  classifier, and could not help the running session anyway.
- Project-level `extraKnownMarketplaces` + `enabledPlugins` in a cloud session:
  marketplace cloned, plugin cached, not installed → no tool.
- The agent first claimed `settings.json` needed a staged copy; wrong, the
  operator caught it.

## State

- Branch `claude/lsp-tool-trial-dra5wk`, no PR, no plan file. Commits beyond
  `main`: relay summaries; a11c7f3 (settings `env`/`extraKnownMarketplaces`/
  `enabledPlugins`, `install-deps.sh` installs `pyright` via `uv tool` where
  absent, `stack.md` site 4); b2eb8aa (stage `CLAUDE.md`); 8e53134 (staged
  `CLAUDE.md` § "Vetting" says four sites; G4 catalog entries for
  `settings.json` and `install-deps.sh`).
- `.claude/staged/CLAUDE.md.staged` is staged; `/finalize` swaps it in.
- The operator says they added the two `claude plugin …` lines to the setup
  script of `env_01Xg9JSSbzPCQgWZzAGCtGhK` — not verified by the agent.
- Probe session `session_01DaohkFBTd5PxYWvP9jehqg` finished its report; it holds
  no work.
- Estimate: this session 1.5 h senior developer — "proving where an LSP plugin
  must be installed for cloud sessions took reading an undocumented gate, wiring
  settings, install-deps and the stack contract, and a live probe that disproved
  project-level install". Remainder handed on: verifying the setup-script
  install, trying the tool, documenting the setup-script lines for adopters,
  `/polish`, `/pr` — unsized, the successor sets its own estimate.

## Pointers

- `.claude/settings.json` — `env`, `extraKnownMarketplaces`, `enabledPlugins`.
- `.claude/hooks/install-deps.sh` — the `pyright-langserver` install.
- `.claude/rules/stack.md` — site 4 (the LSP plugin); its text says
  `enabledPlugins` is what gives the tool, which the probe disproved for cloud
  sessions — to be corrected once the setup-script route is verified.
- `docs/adopting/web-remote.md` § "Hand the operator a setup script" — where the
  two `claude plugin …` lines go for adopters; `/detemplate` Step 6 hands that
  script over.
- `.claude/skills/update-muthur/catalog/g4-remote-plumbing.md` — the catalog
  entries touched.
- `docs/remove-before-merging/relay-1.md` — the survey that chose LSP.
- Re-fetch the marketplace manifest:
  `gh api repos/anthropics/claude-plugins-official/contents/.claude-plugin/marketplace.json --jq .content | base64 -d`
- Transcripts: this session
  https://claude.ai/code/session_01DaohkDdJpVqGT8LWBLudag; the probe
  https://claude.ai/code/session_01DaohkFBTd5PxYWvP9jehqg.

## Next step

Check whether the `LSP` tool is present now that the setup script installs
`pyright-lsp` (`claude plugin list`, ToolSearch "LSP"). If it is: try it on
`scripts/*.py` (goToDefinition on an import from `scripts/lib/`, findReferences,
hover, documentSymbol) and report to Vova; then put the two setup-script lines
in `docs/adopting/web-remote.md` § "Hand the operator a setup script", correct
`stack.md` site 4 and the G4 catalog entry to say the setup script installs the
plugin, and continue `/go`'s tail (`/polish`, then `/pr`). If it is not:
diagnose (does `installed_plugins.json` list it? was the setup script's snapshot
rebuilt?) and report. Operator's words: «сделал, давай попробуем релейнуть».

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

````text
Инструмента `LSP` в новой сессии так и нет. Причина в том, что плагин скачался, но не установился. Настройки проекта в репо до сессии дошли, флаг выставлен, маркетплейс склонирован. Даже `pyright-lsp` попал в кэш, `~/.claude/plugins/cache/…/pyright-lsp/1.0.0/`. Но записи об установке нет (`installed_plugins.json` пустой), `claude plugin list` выдаёт «No plugins installed». Флагу нечем было включиться.

Почему установка не доходит до конца, точно не знаю. Предполагаю, что Claude Code показывает пользователю вопрос «этот проект просит плагины, ставить?», а в облачной сессии задать его некому. Это объясняло бы, почему скачивание прошло, а установка нет.

Обойти это можно только тем, что выполняется до старта сессии, а это setup-скрипт окружения. Хук `install-deps.sh` не годится: он срабатывает уже после того, как список инструментов собран. Добавь, пожалуйста, в setup-скрипт окружения `env_01Xg9JSSbzPCQgWZzAGCtGhK`:

```
claude plugin marketplace add anthropics/claude-plugins-official
claude plugin install pyright-lsp@claude-plugins-official
```

Сам я этого сделать не могу: setup-скрипт меняется только в настройках окружения в вебе. Потом снова запущу пробную сессию.

Если LSP после этого заработает, для адоптеров нужно будет вот что:

- Эти две строки войдут в setup-скрипт, который `/detemplate` выдаёт адоптеру, и в четвёртый пункт `stack.md` про плагин.
- `enabledPlugins` в `settings.json` я бы оставил. В локальном CLI, где человек может ответить на вопрос об установке, проект сам предложит плагин.

Сводку `relay-2.md` я обновил и запушил.
````
