> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# Opus checkpoint review for sessions on a weaker model

## Task, as asked

> если сессия запущена на слабой модели (не Опусе), она после каждой отсечки
> лупа (/plan, если есть; /go; любые последующие /go и /handle; /finalize)
> создаёт подагента на _Опусе_ с вопросом: "на твой, проходит ли проверку
> качества то, что я сделал", с вариантами ответа (в порядке от всё хорошо до
> всё плохо) да / нет, внеси такие-то правки [указывая не verbatim, а по сути] и
> покажи мне ещё раз […] / нет, я исправил, можешь продолжать работать дальше /
> нет, я исправил, работа сложновата для тебя, поэтому после этих правок релей в
> новую сессию на Опусе / нет, я не могу исправить по тем или иным причинам
> (например, ограничение возможностей подагентов как таковых), релей сразу
>
> подагент также может править
> .claude/skills/go/delegation-model-capabilities.md по результатам

The operator's open question — can a subagent that already reported be written
to again — has an answer: yes. `SendMessage` with the agent's id continues it
with its context intact (the `Agent` tool documents this), so the "show me
again" round goes back to the same reviewer rather than a fresh one.

## Shape

One new procedure file, `.claude/skills/go/checkpoint-review.md`, and a
one-paragraph pointer to it at each cutoff. The file owns everything; the
pointers own only _where_ in their skill it runs.

### Who runs it

A session whose serving model is below Opus — Sonnet or Haiku. The agent reads
its model from its system prompt's model line; where that line is missing, from
`get_session`'s `external_metadata.last_served_model`. Serving model, not
configured model: the review exists because of who did the work, and a fallback
mid-session changes that.

### Where it runs

- **`/plan`** — after § "Publishing the plan", before § "Handing off": the
  reviewer reads the plan file and the PR it was published on. Its fixes are
  plan revisions, and `/pr` refreshes the body.
- **`/go`** — at the end of Step 3, after the plan flips to `*.completed.md` and
  before Step 4's `/pr`, so the PR body describes the reviewed diff. This covers
  `/handle` too: its plan and review lanes run `/go`, and its plan-review lane
  runs `/plan`, so it needs no pointer of its own.
- **`/finalize`** — after the quality passes, before Step 1's vet run. Every
  step from 1 on is a statement about a diff that has stopped moving (the vet
  run, the base merge, the squash body, the attested SHA, the `and merge` gate),
  so a reviewer fix after any of them would invalidate it; before the vet run,
  the vet run covers the reviewer's fixes too.

One review per skill run: a `/handle` that runs `/go` gets `/go`'s review, not a
second one at `/handle`'s end. `/handle … and finalize` gets two — `/go`'s and
`/finalize`'s — since `/finalize`'s is the last look before land.

### The review

`Agent` with `model: "opus"`, no worktree isolation — it reviews and fixes the
session's own tree — run in the foreground, since the session's next step
depends on the verdict. The brief names:

- which skill just ran and what it was for (the plan file, or the task for a
  planless `/go`, or the PR for `/finalize`);
- the range to review: the skill run's own commits
  (`git diff <sha-at-entry>..HEAD`), plus the branch's whole diff against its
  base for context;
- the question, in the operator's framing: does what was done pass this
  repository's quality bar — `CLAUDE.md`, the skill that ran, and the plan;
- the five verdicts, and that its reply's first line names exactly one;
- that it commits what it fixes (semantic prefix, the body saying the checkpoint
  reviewer made it) and never pushes;
- that it may rewrite the session model's entry in
  `delegation-model-capabilities.md` (below).

The verdicts, best to worst:

1. **`pass`** — carry on.
2. **`revise`** — a list of what to change, stated by substance rather than as
   replacement text. The session makes the changes, commits, and sends the same
   reviewer `show again` through `SendMessage`. The reviewer may not answer
   `revise` a third time: on that look it fixes the rest itself or escalates —
   two rounds is where telling a weaker model what to do costs more than doing
   it.
3. **`fixed`** — the reviewer fixed it; carry on.
4. **`fixed, relay`** — the reviewer fixed it, and the work is beyond the
   session's model: once the skill's remaining steps finish, the session hands
   over through `/relay` to a session on Opus instead of continuing.
5. **`relay`** — the reviewer could not fix it — a subagent lacks a tool the fix
   needs, or it needs the operator — so the session relays to Opus now, the
   reviewer's findings carried into the summary's Next step.

The session pushes after any verdict that left commits, and its report to the
operator names the verdict in a line — and, for 4 and 5, links the successor.

### Escalation through `/relay`

`/relay` Step 3 inherits the model by omitting it. It gains one exception: a
handoff the checkpoint review escalated passes `model` set to the current Opus
model id (the system prompt's Environment section names it), so the successor
runs on Opus. The successor's first message is the summary's Next step — for
verdict 4 what the skill would have done next, for verdict 5 the reviewer's
findings to fix.

### The capabilities file

`delegation-model-capabilities.md` keeps one entry per model below the
delegator's own, built from delegated sub-tasks. A checkpoint review is evidence
about the same models running the loop themselves, so the reviewer folds what it
found into the session model's **Handles** / **Misses** under the file's
existing keeping rules (kind of work, never the task; compress, don't log; under
100 lines), and anything true of every subagent — a tool none of them has — into
§ "Across models". The file's header line and `delegation.md` § "Keeping …" gain
a clause naming the checkpoint as the second source.

## Steps

1. Write `.claude/skills/go/checkpoint-review.md` — who runs it, the brief, the
   five verdicts and what the session does on each, the `SendMessage` round and
   its cap, the push and report.
2. Add the pointer paragraph to `/plan` (before § "Handing off"), `/go` (end of
   Step 3), `/finalize` (after "Then, the quality passes"). Body-only edits, no
   `description:` change, so nothing is staged.
3. `/relay` Step 3: the escalation exception to "model inherited".
4. `delegation-model-capabilities.md` header and `delegation.md` § "Keeping …":
   the checkpoint as a second source.
5. Catalog: an entry for `checkpoint-review.md` in
   `.claude/skills/update-muthur/catalog/g2-pr-loop.md`, beside the delegation
   files.

## DRY notes

- **Reused:** `/relay` for escalation — no second handoff mechanism, one
  exception in its Step 3; `delegation-model-capabilities.md` and its keeping
  rules for what the reviewer learns, rather than a second notes file;
  `SendMessage` for the re-review round.
- **Shared, not duplicated:** the procedure lives once; the three skills carry a
  pointer each, saying only where it runs in that skill — the placement is the
  one thing that differs per skill, so it is the one thing stated there.
- **Not extracted:** a hook delivering the file only on weaker models (the way
  `go-delegation.py` delivers delegation). The pointers cost an Opus session
  three short paragraphs it skips, and a hook would need the serving model,
  which no hook payload reliably carries mid-session — net-negative.

## Open questions

1. **Which models count as weaker.** Recommendation, in force above: Sonnet and
   Haiku. A Fable session would otherwise send its work to a model it may
   outrank; say so if Fable should be reviewed too.
2. **The `revise` cap of two rounds.** In force above; say a number if two is
   wrong.
