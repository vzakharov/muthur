# Relay 1 — review board redesign (parked)

## 1. Standing constraints

Names of the client project are redacted below as `[…]`, because the constraint
itself forbids them in this repo. The opening prompt said, verbatim apart from
that redaction:

> «Если нужно, подключи репозиторий через add_repo с доступом read. […] —
> рабочий репозиторий по клиентскому проекту, поэтому из него бери только
> устройство страницы: никаких имён, путей, текстов и данных проекта в muthur.»

- The full opening prompt (with the reference repo, branch and artifact link) is
  in this session's transcript — see Pointers. **Never copy it into a committed
  file.**
- **Committing on this branch:** `.claude/costs/hooks/stage-cost-row.sh` stages
  this session's cost row on every `git commit`, and that row carries the
  opening prompt with the client names. Every commit command in a session that
  still has that opening prompt must name `.claude/costs/sessions` (e.g. a
  trailing `# .claude/costs/sessions` comment) so the hook skips it. A successor
  session has its own clean opening prompt, so this applies only if the operator
  returns to _this_ session.

## 2. The conversation

**Operator (opening prompt, `/task`, names redacted):** Rebuild `/review-board`
after the reference page «[…]» from [the reference repo] — "Нынешний
review-board очень много весит и, честно говоря, не очень удобен (Вова,
15.11.2026)". What Вова liked about the reference: rows are parts of the change,
not files (one sentence, a status, a list of "what changed and why" with
commits); files with diffs fold inside a part, noise removed before display; one
summary line on top with date and pinned-SHA GitHub links; the agent writes the
data and the builder validates it and fails (unclaimed file, unknown commit,
status contradicting files); a light page with a theme toggle. Task: generalize
to any PR, to part of a PR (since last review, since the last commit Вова saw, a
commit range), parts chosen by meaning. Keep line comments reaching Claude and
the sticky PR comment link — "Если что-то из этого в новом виде не нужно или
мешает, скажи прямо." Start by reading the current skill and the reference and
naming what exactly is heavy and inconvenient; plan decision is `/task`'s;
questions to Вова as numbered prose in a draft PR.

**Agent:** Chose plan-and-hand-off (`/task` outcome 1). Diagnosis: the PR #269
board was 1.19 MB — 877 KB embedded full text of every revision of every changed
file at every commit, 304 KB JS (board engine, highlight.js, markdown-it, zod);
files on a pannable field with no reading order; ~8k lines of TS. The reference
is 750 KB but has 766 bytes of script — static. Wrote the plan, opened draft PR
#275, posted the squash proposal, asked five numbered questions (status meaning,
source of "seen", fallback if shell anchors fail, syntax highlighting, keeping
the FSD/MASD lint chain), each with a recommendation the plan already follows.

**Operator:** "так, приватные данные нигде не упомянуты? если да, переписывай
историю"

**Agent:** Found the leak in the cost-ledger row (its `openingPrompt` field),
not in the plan/PR. Rewrote the branch without the row file and force-pushed
(old SHAs `823c95f`, `29cf733` stay fetchable on GitHub by SHA for a while). Did
**not** rewrite `cost-ledger` commit `d221b8f`, because the Stop hook re-writes
the row from the transcript every turn. Proposed: (1, recommended) a separate
small PR adding a manual session-title override to the cost ledger, then retitle
this session and rewrite `d221b8f`; (2) redact the local transcript, only on
Вова's explicit yes. (verbatim in Last agent turn)

## 3. Intent

A lighter, more usable review board: a static, part-by-part page over a whole PR
or a range of it, agent-written parts validated against git, comments to Claude
and the sticky link kept. And no client-project data in muthur, anywhere —
including history.

## 4. Decisions

- **Plan gated on Вова** rather than implemented: an 8k-line rewrite with real
  forks (Step 3 of `/task`).
- **One PR, no split** — the page and the skills are useless apart.
- **TS in `.claude/artifacts/`**, not the reference's Python builder: one
  toolchain.
- **"Part"** = a unit of the change by meaning; the data file is
  `docs/remove-before-merging/review-parts.json`, replacing `review-focus.json`.
- **Cost-ledger leak:** branch rewritten; ledger rewrite deferred until the
  source of the row is fixed (options in § 2's last reply).

## 5. Errors and dead ends

- The cost hook staged the private row into both plan commits; caught only on
  Вова's question.

## 6. State

- Branch `claude/review-board-redesign`, head `45cd2e2`, pushed.
- PR #275, open, draft: https://github.com/vzakharov/muthur/pull/275
- Plan: `docs/plans/review-board-redesign.draft.do-not-implement.md` (draft, no
  go-ahead given).
- Squash proposal comment posted; working file
  `docs/remove-before-merging/squash-message.md`.
- `origin/cost-ledger` tip `d221b8f` still carries this session's row with the
  client names in `openingPrompt` (path
  `sessions/2026-11/claude/review-board-redesign/1/e8bc6be1-ca2e-5886-b1ea-5271b041d025.json`).
  Later Stop hooks of this session add commits with the same field.
- Estimate: this session 2.5 h senior architect — "reading an 8k-line app and a
  foreign reference to name what makes it heavy, then shaping a data contract
  and builder checks, is design work a senior does before anyone codes".
  Remainder for the implementing session: 14 h senior developer — "a new builder
  with git range resolution, validation that fails loudly, static rendering and
  comment anchoring replaces an 8k-line app; the anchoring needs a spike against
  the artifact runtime"; 3 h senior prompter — "the skill and its callers in /pr
  and /finalize carry a new agent-written data contract whose rules decide how
  well parts are cut".

### Watches

(none — no artifact was published)

## 7. Pointers

- The plan file above, and `.claude/skills/review-board/SKILL.md`,
  `.claude/artifacts/src/review-board/` (the app being replaced).
- `.claude/costs/lib/identity.py` `prompt_text_of`, `.claude/costs/CLAUDE.md` §
  "What names a session" — where the opening prompt enters a row.
- Transcript: https://claude.ai/code/session_01RAikusW5cAsY4SHbVTGxb7

## 8. Next step

Wait for the operator. Two threads are open:

1. The leak cleanup — Вова's "переписывай историю" is done for the branch; the
   `cost-ledger` rewrite waits on his pick between the two options in the last
   reply.
2. The plan — `/go claude/review-board-redesign` once Вова gives the go-ahead,
   with any answers to the five questions folded in first.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs. The
client-project names in it are redacted as `[…]` per § 1 — the only edit.

````text
Ветку почистил, но на ветке `cost-ledger` первый промпт сессии всё ещё лежит, и чистить её сейчас бессмысленно: в конце этого же хода хук запишет его туда снова.

**Где нашлось.** В плане, PR, описании и комментариях имён, путей и данных […] нет, это я проверил поиском. Утекло через учёт стоимости сессий: хук каждый раз записывает строку о сессии, а в ней первые ~150 символов первого промпта. У этой сессии там «[…]» и «[…]». Эта строка оказалась в двух местах.

**Наша ветка — переписана.** Оба коммита пересобраны без файла со строкой, ветка перезалита с `--force-with-lease`. Теперь в ветке поиск по именам клиентского проекта и ссылке на артефакт ничего не находит. Но старые коммиты (`823c95f`, `29cf733`) GitHub ещё какое-то время отдаёт по SHA через историю PR #275. Совсем их убрать может только поддержка GitHub.

**Ветка `cost-ledger` — не переписана.** Там строка сидит в коммите `d221b8f`. Это сейчас последний коммит ветки, так что заменить его легко. Причина ждать в том, что хук пишет строку туда в конце каждого хода и берёт промпт заново из лога сессии. Способа задать сессии другое название в учёте сейчас нет.

Чтобы утечка не повторялась, вижу два пути:

1. **(рекомендую)** Добавить в учёт стоимости способ задать название сессии вручную. Отдельным маленьким PR, не в этом. После этого задам этой сессии нейтральное название и перепишу `d221b8f`. Заодно это закроет ту же дыру для любой будущей сессии, которая начинается с клиентского промпта.
2. Исправить имена прямо в локальном логе сессии, из которого хук берёт промпт, и потом переписать `d221b8f`. Это быстро, но означает править лог сессии задним числом, поэтому без твоего прямого «да» делать не буду.

План и вопросы к нему остались прежними: https://github.com/vzakharov/muthur/pull/275

Чтобы реализовать план, начни новую сессию с:

```
/go claude/review-board-redesign
```
````
