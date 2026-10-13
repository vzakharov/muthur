# Relay 1 — Markdown tables to lists or sections (#189, pr #190)

## 1. Standing constraints

None stated by the operator beyond the repo's own conventions.

## 2. The conversation

1. **Operator:** "Replace Markdown tables with lists or sections #189"
   **Agent:** Routed via `/task` (rung 1); took the issue export, went planless
   (the issue was already a spec), renamed the branch, converted all 34 tables
   (issue said 30), turned the catalog into one list item per entry and
   `check-skill-catalog.sh` into a list-item parser, added
   `.claude/rules/markdown.md` and `scripts/check-markdown-tables.sh` wired into
   vet, ran `/polish`, opened draft PR #190 with a squash proposal.
2. **Operator:** "скорее это refactor:?"
   **Agent:** Argued for keeping `feat:` because of the new vet guard and the
   catalog format contract; offered to switch on the word `refactor`.
3. **Operator:** "ну то что vet падает это скорее chore (но в общем refactor), т.е.
   считай это типа линтерным правилом. единственное что нужно убедиться что у
   адоптеров не будет соблазна тоже падать -- ИХ таблицы могут быть их выбором"
   **Agent:** Retitled PR and squash to `refactor:`; made the rule and check
   `never` (check behind `check-muthur.sh`, a never-vendored banner in the rule,
   carve-outs in ADOPTING.md and `/detemplate`). Flagged that `/update-muthur`
   could still offer the file to an adopter who took `.claude/rules/` whole.
4. **Operator:** "> Добавляю запись never в каталог, исключение при копировании и
   баннер в сам файл правила — never -- слишком сильно"
   **Agent:** Reworked it as `adopt — opt-in: ask` in G1: the rule is asked like
   any opt-in, `scripts/check-markdown-tables.sh` travels "with" it, vet runs
   the check only while `.claude/rules/markdown.md` exists (a no deletes the
   rule and the line goes quiet), banner and special carve-outs removed,
   ADOPTING.md gained the general "a declined opt-in's path stays out even
   inside a copied directory". Also fixed the check missing one-column tables
   (`|---|`), with a test.
5. **Operator:** "спасибо, давай мерджить"
   **Agent:** Read it as `/finalize and merge`. Ran the staged swap (CLAUDE.md,
   commit 73b4993) and hit the 300k context pause before the quality passes;
   relayed.

## 3. Intent

Land #189: no Markdown tables outside code fences in this repo, the catalog
in list form, and a guard against new tables — framed as a lint-like house
style (`refactor:`), never imposed on adopters (their tables are their call;
asked as an opt-in, not forbidden and not `never`).

## 4. Decisions

- **Planless** — the issue already specified every conversion shape.
- **Commit type `refactor:`** — the operator's call: the vet failure is a
  lint rule, not a feature. (Branch commits say `feat:`; the squash title is
  what matters.)
- **`opt-in: ask`, not `never`, not plain adopt** — `never` was "too strong";
  adopters decide. The vet line is keyed on the rule file's presence, so
  declining = deleting the rule.
- **Rungs** — CLAUDE.md's routing ladder is a numbered list; its items are
  "rungs" (was "rows"), also in `.claude/hooks/prompt-route-notice.sh`.
- **Entry / field** — catalog vocabulary replacing row / column. Ledger "rows"
  under `.claude/costs/` keep the word.
- **Working artifacts skipped by the check** (`docs/issue/`, `docs/pr/`,
  `docs/plans/`, `docs/remove-before-merging/`) — exports are GitHub text
  verbatim, and `/audit-github-backlog` writes machine-parsed summary tables
  into `docs/plans/backlog-audit/`.
- **`/qa-checklist`'s table stays, fenced** — PR bodies are read rendered.
- **`staged_view()` duplicated** in `check-skill-catalog.sh` and
  `check-markdown-tables.sh`, deliberately (reasoning in commit d109e8a).

## 5. Errors and dead ends

- The `never` approach (commit before af1c3ec) — rejected by the operator.
- First table regex missed one-column tables; fixed in af1c3ec.

## 6. State

- Branch `claude/markdown-no-tables-xfkjzm`, head 73b4993 (pushed).
- PR https://github.com/vzakharov/muthur/pull/190 — draft, open, base `main`,
  title `refactor: replace Markdown tables with lists or sections`.
- No plan file. Squash proposal tracked at
  `docs/remove-before-merging/squash-message.md`, posted as PR comment
  6152447972 (title `refactor: #189 … (pr #190)`).
- Staged swap done (73b4993); nothing left under `.claude/staged/`.
- Last polish commit d109e8a — the `/polish` floor; scope since then is
  `git diff d109e8a..HEAD` (the refactor retitle, the never → opt-in rework,
  the squash refresh and the swap).
- No workflow runs on PRs (`.github/workflows/` absent): the attestation is the
  only record.
- `origin/main` has advanced to 6631e06 "feat: [attn adopters] prefix muthur's
  env variables with MUTHUR_ (pr #188)" since the branch was cut — finalize
  step 2 brings it in; read it for interaction (it renames env vars, possibly
  in files this branch touched, e.g. vet.sh, ADOPTING.md, catalog entries).
- Estimate: this session 4 h middle editor + 1.5 h middle developer. Remainder
  handed on: 0.5 h middle developer — "land prep: quality passes over the
  opt-in rework, base merge against an advanced main, attestation and merge".

## 7. Pointers

- `docs/issue/189/issue.md` — the issue (swept at finalize step 3).
- `.claude/rules/markdown.md`, `scripts/check-markdown-tables.sh`,
  `scripts/test_markdown_tables.py`, `scripts/vet.sh` (keyed line),
  `.claude/skills/update-muthur/catalog/g1-prose-principles.md` (the opt-in
  entry), `ADOPTING.md` (opt-in copy sentence).
- Predecessor transcript: https://claude.ai/code/session_01CerKJCFopZBHQNfbGYmGCy

## 8. Next step

finalize and merge
