# Relay 1 — Opus quality gate, plan done, implementation pending

## 1. Standing constraints

- None stated by the operator beyond the repo's CLAUDE.md. Operator is Vova
  Zakharov (@vzakharov); address in Russian with «ты», name «Вова».
- No model identifiers in anything pushed (CLAUDE.md § "Model identity"). Two
  were scrubbed from the plan in commits 3a0363b, b51a958 and 827452b. Do not
  reintroduce them in plan, code, PR or squash text.

## 2. The conversation

Operator (verbatim, the only operator message of the session):

> давай если сессия запущена на слабой модели (не Опусе), она после каждой
> отсечки лупа (/plan, если есть; /go; любые последующие /go и /handle;
> /finalize) создаёт подагента на Опусе с вопросом: "на твой, проходит ли
> проверку качества то, что я сделал", с вариантами ответа (в порядке от всё
> хорошо до всё плохо) да / нет, внеси такие-то правки [указывая не > verbatim,
>
> > а по сути] и покажи мне ещё раз (не знаю, правда, можно ли писать подагенту
> > который уже отчитался -- в противном случае придётся создавать нового) /
> > нет, я исправил, можешь продолжать работать дальше / нет, я исправил, работа
> > сложновата для тебя, поэтому после этих правок релей в новую сессию на Опусе
> > / нет, я не могу исправить по тем или иным причинам (например, ограничение
> > возможностей подагентов как таковых), релей сразу. подагент также может
> > править
> > https://github.com/vzakharov/muthur/blob/main/.claude/skills/go/delegation-model-capabilities.md
> > по результатам. тут сразу же и догфудим

Agent reply, condensed: routed the prompt to `/task` (rung 1, a change to the
codebase). `/task` Step 1 said plan (several skills, order matters); Step 2
wrote the draft; Step 3 said no operator gate (no fork without a
recommendation), so the next step is `/go` Step 1, which flips the draft. The
draft was published as PR #250 via `/pr`, then the squash proposal was posted.
The session stopped before `/go` because the context budget notice left no room
for the implementation.

Agent-side mistakes worth knowing: a Bash `cat` was blocked by a hook and the
call was rerun with Read; a commit `3a0363b` landed with a message that did not
match its content (only a cost-ledger row was in it; the plan edit had failed),
so it was not rewritten (no force-push), and a correction followed.

## 3. Intent

Weak-model sessions (any model that is not Opus) get a quality check from an
Opus subagent at each loop checkpoint: `/plan`, each `/go`, each `/handle`, and
`/finalize`. The subagent returns one of five verdicts, best to worst: A pass; B
fix-and-show-again; C already fixed, continue; D fixed but too hard for this
model, relay to Opus; E cannot fix, relay now. The subagent may also edit
`.claude/skills/go/delegation-model-capabilities.md`. The operator wants this
dogfooded on the session that builds it.

Ruled out by the operator's words: nothing explicitly. The operator left open
whether a judge agent can be messaged again after it reported; the plan answers
that from the Agent tool's own description (SendMessage continues a spawned
agent).

## 4. Decisions

Each is a recommendation already written into the plan
(`docs/plans/opus-quality-gate.draft.do-not-implement.md`, read it in full):

- Detection via `get_session` (`session_context.model`,
  `external_metadata.last_served_model`). A session that cannot tell counts as
  weak, so the gate runs.
- Judge = `Agent` with `model: "opus"`, no worktree, sequential (the session
  blocks on the verdict).
- Re-show goes to the same judge via `SendMessage`; fresh Opus agent only if the
  first is gone.
- Relay = `/relay park`, then `create_session` with the Opus model's ID as
  `model` and the prompt `/relay take <branch>`. The ID is looked up at
  implementation time, not written into the repo.
- Judge launch failure stops the turn, never a silent pass.
- Shared procedure in one new file `.claude/skills/go/quality-gate.md`; go,
  plan, handle and finalize get one pointer line each at their checkpoint. Body
  edits only, so no staging of SKILL.md descriptions is needed.

Rejected: placing the procedure in each skill (duplication); a helper script for
detection (one tool call, not worth code).

## 5. Errors and dead ends

- `Edit` of the plan failed once because the formatter hook had re-wrapped the
  line. Fix: Read first, then Edit. The formatter rewraps `.md` on every edit,
  so Read again before any later Edit of the plan.
- A bad commit message, see section 2.

## 6. State

- Branch `claude/opus-quality-gate-867zbu`, renamed from
  `claude/serene-bell-867zbu` before any PR existed. Pushed, tracking origin.
- Last pushed commit
  `827452b docs: state the Opus judge and relay model without model IDs`. Tree
  clean except what this relay commits.
- PR #250, draft, base `main`, title
  `feat: gate weak-model sessions on an Opus quality check`. Squash proposal
  comment posted
  (https://github.com/vzakharov/muthur/pull/250#issuecomment-6486816268).
- Plan file: `docs/plans/opus-quality-gate.draft.do-not-implement.md`. Its name
  is still `draft`, so no implementation has begun; the operator's go-ahead is
  the `/task` prompt quoted in section 2.
- Nothing running. No keepalive watcher was started; this session is handing
  off.
- Estimate set this session: 3 h middle developer + 1 h senior architect (3.12
  senior-hours). The reasons are in the ledger row. No remainder to hand on
  separately.

## 7. Pointers

- Plan: `docs/plans/opus-quality-gate.draft.do-not-implement.md`.
- Files the plan touches: `.claude/skills/go/SKILL.md`,
  `.claude/skills/plan/SKILL.md`, `.claude/skills/handle/SKILL.md`,
  `.claude/skills/finalize/SKILL.md`, and the new
  `.claude/skills/go/quality-gate.md`. Read `handle/SKILL.md` and
  `finalize/SKILL.md` in full before placing pointers; this session did not.
- Delegation model notes: `.claude/skills/go/delegation.md`,
  `.claude/skills/go/delegation-model-capabilities.md`.
- This session's transcript:
  https://claude.ai/code/session_01DaohkE1kSi2cgf98P77S8p

## 8. Next step

Operator's most recent request, verbatim (section 2): implement the gate as the
plan describes, dogfooded in the session that does it.

Concretely, in the successor:

1. `/go` Step 1: `git mv` the draft to `*.in-progress.md`, delete the line-1
   banner, commit quoting the operator's `/task` prompt as the go-ahead.
2. Implement steps 1–4 of the plan. Read `handle/SKILL.md` and
   `finalize/SKILL.md` in full first to find each closing step.
3. Run `./scripts/vet.sh` only at `/finalize`, not per commit, and the skill
   catalog check.
4. Then `/polish` and `/pr` per `/go` Step 3–4 (the PR exists, so refresh).
5. The gate itself runs at the end of that `/go` (it is a weak-model session if
   it runs on a non-Opus model). Follow the verdict it returns.

## 9. Last agent turn

Not appended. `scripts/relay-last-reply.py` failed at the handoff with "no turn
before this one wrote any text" in the session transcript, so this section is
empty rather than retold. The successor should not treat it as a missing reply:
section 2 holds the agent's account of this session.
