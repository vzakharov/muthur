# Relay 1 — multi-repo sessions

## Standing constraints

None stated by the operator.

## The conversation

1. **Operator:** «в новых версиях claude code ui можно подключать сразу реп
   сразу -- и кажется это ломает какие-то из наших штучек (например один агент
   говорил про gh shim). давай исправим это. заодно догфужу и подключаю помимо
   muthur две другие репы» **Agent:** diagnosed it — a multi-repo session starts
   in `/home/user` and loads no repo's hooks (documented); probed that a hook
   written to `/home/user/.claude/settings.json` mid-session fires (hot reload)
   and that a user-level `~/.claude/settings.json` `PreToolUse` hook fires too.
   Routed via `/task` → plan, published draft PR #199 with two open questions.
2. **Operator:** «а всякие /from-branch, /handle итп, что с ними?» **Agent:**
   they assume the shell's directory is the repo (it is `/home/user`); a bare
   branch/`#N` names no repo; same-named skills collapse to one copy (muthur's
   loaded here); `/relay` successors are single-repo. Proposed a "resolve the
   target repo first" rule.
3. **Operator:** «думаю. а пока: правильно я понимаю, что подход к созданию
   "общей клодовой заглушки" -- через setup script, руками оператора?»
   **Agent:** partly — the setup script installs only a static user-level
   `SessionStart` hook that finds and runs the generator; the generator writes
   the parent settings each session; the CLAUDE.md fallback covers environments
   without it. User-level `SessionStart` at cloud start is unverified.
4. **Operator:** «> По аргументу не понять, какая репа — очень редко там номер
   пиара, чаще branch, который чаще всего уникален благодаря случайному
   суффиксу» **Agent:** agreed; `git ls-remote --heads origin <branch>` per repo
   finds the one; the only shared name is the session's own auto-branch.
5. **Operator:** «> Через setup script оператор один раз прописывает только хук,
   который запускает генератор — а откуда берётся код для генератора если в
   голом контейнере его нет?» **Agent:** from the repos themselves — they are
   cloned before `SessionStart` (a single-repo session's hooks run from the
   clone); the setup script carries only a glob lookup.
6. **Operator:** «> git ls-remote --heads origin <ветка> в каждой подключённой
   репе — можно для этого же скрипт какой-то создать, типа находит репу по
   бранчу?» **Agent:** proposed `scripts/find-repo.py <branch|#N|PR URL>`
   sharing a `scripts/lib/` session module with the generator; asked whether to
   add it to the plan.
7. **Operator:** «> Почему победил muthur, нигде не задокументировано — да, там
   типа в UI "vzakharov/muthur + ..."» **Agent:** `get_session` shows
   `session_context.sources` ordered, muthur first — the first source likely
   wins skill collisions; the order is visible only via that MCP tool, not to
   hooks/scripts.
8. **Operator:** «> Тут два пути: в каждом скилле поменять git … на git -C
   "$repo" …, — в каждом бы я точно не стал, но где-то в одном месте "если
   работаешь из мультирепо-окружения", любую комманду трактуй как ...»
   **Agent:** one always-loaded rule: `cd <repo> &&` on every Bash call (the
   shell resets to `/home/user` between turns), scripts and `@.claude/skills/…`
   resolve against the target repo.
9. **Operator:** «> Например, /finalize у vovazakharov.com знает про деплой… —
   ну мы же определим репу по ветке, и оттуда уже будем использовать скилл
   каждой?» **Agent:** yes — the loaded copy is only the entry point; once the
   target is known, read `<repo>/.claude/skills/<name>/SKILL.md` and follow it.
10. **Operator:** «> Тогда это не её скилл: агент говорит об этом и
    останавливается… — подозреваю что UI не даст такое даже запустить, сказав
    "такого скилла нет". но это не суть. обнови пжст план по текущим
    обсуждениям. открытые вопросы оставь открытыми чтобы я их не потерял»
    **Agent:** rewrote the plan (§§ 1–7), refreshed PR body, title and squash
    proposal; four open questions.
11. **Operator:** «1 а откуда запущенная в мультирепе сессия узнает про правило?
    2 - в каждую 3 ждёт обсуждения 1 4 один» **Agent:** from `CLAUDE.md`, the
    one thing verified to arrive on turn one from every repo; a rule file
    without `paths:` is unverified. Recorded 2 (cost rows in every repo) and 4
    (one PR).
12. **Operator:** «в каком виде лежали? сразу в твоём контексте, в тройном
    размере?» **Agent:** yes — all three `CLAUDE.md` + three `voice.md`, whole,
    back to back, ~89 KB / ~22–25k tokens, unmerged.
13. **Operator:** «жесть какая! 3 - да, с указателем» **Agent:** recorded 3:
    `.claude/rules/multi-repo.md` plus a `CLAUDE.md` pointer that itself names
    the `Read`, so the rule reaches turn one either way. Only question 1 left
    open.
14. **Operator:** «да нет, тут системная проблема, сколько не чисть, все равно
    это в каком-то смысле проблема N+1. Давай добавим в план кинуть issue в репу
    claudecode и можно начинать» **Agent:** added plan § 8 (upstream issue),
    flipped the plan to in-progress quoting that go-ahead, built
    `scripts/lib/session.py` and `scripts/multi-repo-hooks.py`, ran the
    generator live (it worked), then hit the context budget's pause line and
    relayed.

## Intent

Make muthur's loop work in cloud sessions with several repositories attached:
the repos' hooks run, and the branch/PR skills act on the right repo using that
repo's own copy of the skill — with no per-skill edits. Also file one upstream
issue on `anthropics/claude-code` for what no repo can fix. The operator is
dogfooding with muthur + vovazakharov.com + life attached.

## Decisions

- **Generator over per-hook changes** — `scripts/multi-repo-hooks.py` builds the
  parent's `settings.json` from each repo's own hooks; beat editing twenty
  hooks, since they already honor `CLAUDE_PROJECT_DIR`.
- **Per repo / once / skipped** — the classification lives in the generator, not
  as keys in `settings.json` (Claude Code validates that file).
- **Cost rows in every repo** (operator, Q2) — beat "primary repo only", which
  the setup-script path cannot read.
- **One PR** (operator, Q4) — hooks and skills share `scripts/lib/`.
- **Rule file plus a CLAUDE.md pointer naming the `Read`** (operator, Q3) — beat
  the whole rule in `CLAUDE.md`, which every attached repo loads in full.
- **Open, recommendation in force (Q1):** what runs the generator — the setup
  script's user-level hook plus the rule's fallback.
- **One rule instead of `git -C` in every skill** (operator's words, turn 8).
- **Terms:** "primary repo" = the session's first source (UI "muthur + …"); "the
  multi-repo rule" = `.claude/rules/multi-repo.md`; "the generator" =
  `scripts/multi-repo-hooks.py`; "N+1" = the operator's name for the per-repo
  `CLAUDE.md` duplication.

## Errors and dead ends

- The first plan draft was in Russian; muthur's human-facing prose is English
  (its PRs are), so it was rewritten.
- `gh pr list` through the proxy returns 403 (GraphQL blocked); the shim path
  (`env -u HTTPS_PROXY`) works. The shim was installed by hand early in this
  session, then by the generator.

## State

- **Branch:** `claude/multi-repo-hooks-z0ln0c` in `vzakharov/muthur` (renamed
  from the auto-branch `claude/kind-lamport-z0ln0c`, which was never pushed).
  The other two repos are untouched on their auto-branch.
- **PR:** https://github.com/vzakharov/muthur/pull/199, draft, title "feat:
  support sessions with several repositories attached"; squash proposal posted
  and tracked in `docs/remove-before-merging/squash-message.md`.
- **Plan:** `docs/plans/multi-repo-hooks.paused.md`, its `## Progress` section
  saying what is done and left.
- **Last pushed before this file:** 4da373f (pause commit).
- **Nothing running**: no CI, no subscription, no check-in.
- **Estimate:** this session 5 h senior developer (diagnosis and the generator)
  - 2 h senior architect (design and the four decisions). Remainder for the
    successor: about 4 h senior developer — tests, `find-repo.py`, the rule and
    pointer, docs and catalog, the upstream issue.

## Pointers

- `docs/plans/multi-repo-hooks.paused.md` — the plan; § 8 the upstream issue's
  content; § "Verified by hand" the evidence to cite in it.
- `scripts/multi-repo-hooks.py`, `scripts/lib/session.py`,
  `scripts/lib/github.py` (`parse_repo_url`) — built.
- `docs/adopting/web-remote.md` — gets the setup-script block.
- Live-run evidence (outside the repo): the generator wrote
  `/home/user/.claude/settings.json` with 7 SessionStart, 3 UserPromptSubmit, 4
  PreToolUse, 3 PostToolUse, 1 PermissionDenied, 3 Stop groups; the
  context-budget hook fired on the next tool call.
- The successor is a single-repo session (the gap the plan lists out of scope),
  so it cannot re-run the live check; tests use fixture roots with
  `CLAUDE_CODE_REMOTE=true` and `CLAUDE_PROJECT_DIR` set.
- Predecessor transcript:
  https://claude.ai/code/session_01A1ZPEFseUYgmqt9Gdfbjx1

## Next step

Resume the paused plan with `/go` from its Step 1 — the go-ahead was given in
this session: «Давай добавим в план кинуть issue в репу claudecode и можно
начинать». Work through `## Progress` → `### Left`, then `/polish` and `/pr`.
