# PR #257: fix: the Opus review of weaker sessions reads its own procedure

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/257
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/checkpoint-reviewer-procedure-wcfux3
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-30T10:05:34Z
- **Updated:** 2026-11-02T02:06:33Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 8

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (the export committed at cb4f1ff). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/skills/go/checkpoint-review.md`:75 — unresolved — last: @vzakharov (human) 2026-11-02T01:49:27Z — "уточнить что run на Opus, а то "Opus successor" begs the que…" → [↓](#t01)
- **T02** `.claude/skills/go/review.md`:16 — unresolved — last: @vzakharov (human) 2026-11-02T01:51:46Z — "давай учитывать только оснонвую часть префикса (в данном слу…" → [↓](#t02)
- **T03** `.claude/skills/go/review.md`:27 — unresolved — last: @vzakharov (human) 2026-11-02T01:52:51Z — "ну вообще это непонятная ситуация -- с чего его тогда запуст…" → [↓](#t03)
- **T04** `.claude/skills/go/review.md`:40 — unresolved — last: @vzakharov (human) 2026-11-02T01:53:55Z — "не всегда план существует" → [↓](#t04)
- **T05** `.claude/skills/go/review.md`:55 — unresolved — last: @vzakharov (human) 2026-11-02T01:54:40Z — "почему and а не or?" → [↓](#t05)
- **T06** `.claude/skills/go/review.md`:60 — unresolved — last: @vzakharov (human) 2026-11-02T01:55:06Z — "почему?" → [↓](#t06)
- **T07** `.claude/skills/go/review.md`:87 — unresolved — last: @vzakharov (human) 2026-11-02T01:56:14Z — "это hand-waving -- мы не знаем что стоит больше; скорее здес…" → [↓](#t07)
- **T08** `.claude/skills/go/review.md`:91 — unresolved — last: @vzakharov (human) 2026-11-02T01:57:03Z — "а нужен ли нам `...-relay` именно как scope для префикса? по…" → [↓](#t08)

---

## Body

## Summary

- The Opus review of a weaker session's work no longer takes a brief from that session. `.claude/skills/go/checkpoint-review.md` (delivered by the hook to Sonnet/Haiku sessions only, as on `main`) launches an Opus subagent with one line, ``Proceed per `.claude/skills/go/review.md` ``, and `review.md` is the reviewer's whole procedure: scope, what to check, verdicts, the commit. `/polish` is back to `main`'s two passes on the session's own model.
- Verdicts are recorded in git: `pass`, `fixed` and `fixed-relay` end in a `review(<verdict>):` commit, `revise` and `relay` make none. On `revise` the session fixes and sends the **same** reviewer a look-again message by `SendMessage`, so it keeps its findings and counts its looks (the third cannot `revise`).
- `scripts/floor.py` is the one floor lookup: the newest branch commit of the given types, diffed from with base merges kept below the line. `/polish` (from `polish:`), the reviewer (from `review(...)`) and the hook all use it, so each sees the other's commits since its own last run.
- `.claude/hooks/checkpoint-review.py` gates the closing step of an entered cutoff (`git mv` out of the draft name, to `*.completed.md`, `gh pr ready`) on a passing `review(...)` commit with only working artifacts changed since; the cost-row copies under `.claude/costs/sessions/` count as working artifacts, since a hook adds one to every commit.
- `scripts/session-qa.py` prints a session's questions and answers for the reviewer to read when the records disagree with git; the helpers it shares with `relay-last-reply.py` move to `scripts/lib/session_transcript.py`. `delegation-model-capabilities.md` moves to `.claude/model-capabilities.md`, since the reviewer keeps it too.
- Dogfooded: an Opus subagent launched with the one line reviewed the branch, fixed the cost-row gate bug itself, and answered `revise` on this body and the squash proposal being stale.

## QA Checklist

- [ ] `review-procedure` — `go/review.md` and `go/checkpoint-review.md` match the design the operator settled: review only below Opus, one-line launch, same reviewer on `revise`, verdict commits.
- [ ] `floor` — `python3 scripts/floor.py 'polish:'` and `python3 scripts/floor.py 'review(pass):' 'review(fixed):' 'review(fixed-relay):'` print the right floor and `from` ref on this branch.
- [ ] `closing-gate` — on a Sonnet session the closing command is open after a `review(pass):` commit, stays open after a cost-row-only commit, and shuts after a later code or plan-text commit.
- [ ] `qa-script` — `python3 scripts/session-qa.py` on a real session prints its questions and answers, and `--since <commit>` filters them.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `review-procedure` | no | no | review of prose |
| `floor` | yes | yes | `scripts/test_floor.py` |
| `closing-gate` | yes | yes | `scripts/test_checkpoint_review.py` |
| `qa-script` | yes | yes | `scripts/test_session_qa.py` |

https://claude.ai/code/session_01DaohkFcprjdSKSRhqhU46L

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-30T10:06:02Z — "Proposed squash body: ``` A session below Opus wrote the Opu…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-30T10:06:02Z

[https://github.com/vzakharov/muthur/pull/257#issuecomment-6520121242](https://github.com/vzakharov/muthur/pull/257#issuecomment-6520121242)

Proposed squash body:

```
A session below Opus wrote the Opus reviewer's brief itself, so what the
reviewer knew of the request, the run and the diff was whatever the
weaker model chose to put in. Now the session launches the reviewer
with one line naming .claude/skills/go/review.md, the reviewer's whole
procedure, and passes on nothing of its own. /polish stays on the
session's model; the review follows it, below Opus only.

The verdict lives in git: pass, fixed and fixed-relay end in a
review(<verdict>): commit, which the checkpoint hook requires before a
cutoff's closing step, with only working artifacts changed since. On
revise the session fixes and asks the same reviewer to look again by
SendMessage, so it keeps its findings and counts its looks.

scripts/floor.py is the one floor lookup /polish, the reviewer and the
hook share: the newest commit of the given types, with base merges kept
below it, so each sees the other's work since its own last run.
scripts/session-qa.py prints a session's questions and answers for the
reviewer; the transcript helpers it shares with relay-last-reply.py
move to scripts/lib/session_transcript.py, and the model capabilities
file moves to .claude/model-capabilities.md.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

_8 resolved threads omitted; re-run with `--include-resolved` to export them._

- **T01** `.claude/skills/go/checkpoint-review.md`:75 — unresolved — last: @vzakharov (human) 2026-11-02T01:49:27Z — "уточнить что run на Opus, а то "Opus successor" begs the que…" → [↓](#t01)
- **T02** `.claude/skills/go/review.md`:16 — unresolved — last: @vzakharov (human) 2026-11-02T01:51:46Z — "давай учитывать только оснонвую часть префикса (в данном слу…" → [↓](#t02)
- **T03** `.claude/skills/go/review.md`:27 — unresolved — last: @vzakharov (human) 2026-11-02T01:52:51Z — "ну вообще это непонятная ситуация -- с чего его тогда запуст…" → [↓](#t03)
- **T04** `.claude/skills/go/review.md`:40 — unresolved — last: @vzakharov (human) 2026-11-02T01:53:55Z — "не всегда план существует" → [↓](#t04)
- **T05** `.claude/skills/go/review.md`:55 — unresolved — last: @vzakharov (human) 2026-11-02T01:54:40Z — "почему and а не or?" → [↓](#t05)
- **T06** `.claude/skills/go/review.md`:60 — unresolved — last: @vzakharov (human) 2026-11-02T01:55:06Z — "почему?" → [↓](#t06)
- **T07** `.claude/skills/go/review.md`:87 — unresolved — last: @vzakharov (human) 2026-11-02T01:56:14Z — "это hand-waving -- мы не знаем что стоит больше; скорее здес…" → [↓](#t07)
- **T08** `.claude/skills/go/review.md`:91 — unresolved — last: @vzakharov (human) 2026-11-02T01:57:03Z — "а нужен ли нам `...-relay` именно как scope для префикса? по…" → [↓](#t08)

<a id="t01"></a>

### `.claude/skills/go/checkpoint-review.md`:75 — unresolved

```diff
@@ -14,101 +20,64 @@ mid-session changes that. `.claude/hooks/checkpoint-review.py` decides it, from
… 137 lines elided …
+  does a new one start, from the launch line; it reviews the same scope afresh.
+  The gate stays shut until a look answers otherwise.
+- **`fixed-relay`** — the reviewer fixed what it found, and the work is beyond
+  the session's model. Finish the skill's remaining steps, then run `/relay`
+  (`@.claude/skills/relay/SKILL.md`) with no argument, so the Opus successor
+  takes the operator's next message.
```

**@vzakharov (human)** — 2026-11-02T01:49:27Z

уточнить что run на Opus, а то "Opus successor" begs the question

---

<a id="t02"></a>

### `.claude/skills/go/review.md`:16 — unresolved

```diff
@@ -0,0 +1,118 @@
… 12 lines elided …
+## Scope: the branch since the last review
+
+```bash
+python3 scripts/floor.py 'review(pass):' 'review(fixed):' 'review(fixed-relay):'
```

**@vzakharov (human)** — 2026-11-02T01:51:46Z

давай учитывать только оснонвую часть префикса (в  данном случае же не важно, какой `(...)` был для этого). Если для полиша важно, то сделать опциональным аргументом

---

<a id="t03"></a>

### `.claude/skills/go/review.md`:27 — unresolved

```diff
@@ -0,0 +1,118 @@
… 22 lines elided …
+reads its own, a staged copy by its diff against the real file. The commits
+below the floor and the rest of the tree stay readable as context.
+
+A scope with nothing in it has nothing to review: say so and answer `pass`
+without a commit, since the floor already stands.
```

**@vzakharov (human)** — 2026-11-02T01:52:51Z

ну вообще это непонятная ситуация -- с чего его тогда запустили; нужно сообщить запускающему агенту что что-то не так

---

<a id="t04"></a>

### `.claude/skills/go/review.md`:40 — unresolved

```diff
@@ -0,0 +1,118 @@
… 35 lines elided …
+body, squash proposal, thread replies, its last messages — matches what the diff
+does.
+
+**The request** comes from the plan's verbatim `## Request` section in
+`docs/plans/`, the PR and the issue it links, and any relay summary under
```

**@vzakharov (human)** — 2026-11-02T01:53:55Z

не всегда план существует

---

<a id="t05"></a>

### `.claude/skills/go/review.md`:55 — unresolved

```diff
@@ -0,0 +1,118 @@
… 51 lines elided …
+before any floor. In a session whose transcript the script cannot find, there is
+no conversation to read: say so and work from the records.
+
+**Fix what is cheaper to do than to describe, and what you cannot describe in a
```

**@vzakharov (human)** — 2026-11-02T01:54:40Z

почему and а не or?

---

<a id="t06"></a>

### `.claude/skills/go/review.md`:60 — unresolved

```diff
@@ -0,0 +1,118 @@
… 55 lines elided …
+form the session's model follows.** Judge the second from the entry for that
+model in `.claude/model-capabilities.md`, its **Misses** above all, and from
+what the review just saw. Answer `revise` only for what is describable that way.
+You never touch the PR, so a stale PR body, squash proposal comment or thread
+reply is always a `revise` finding.
```

**@vzakharov (human)** — 2026-11-02T01:55:06Z

почему?

---

<a id="t07"></a>

### `.claude/skills/go/review.md`:87 — unresolved

```diff
@@ -0,0 +1,118 @@
… 82 lines elided …
+
+**A look again** reads the session's commits since your last look against your
+findings, and anything else they changed as fresh work. The third look cannot
+answer `revise`: it fixes the rest or answers `relay`, since telling the session
+what to do a third time costs more than doing it.
```

**@vzakharov (human)** — 2026-11-02T01:56:14Z

это hand-waving -- мы не знаем что стоит больше; скорее здесь про avoid spiraling

---

<a id="t08"></a>

### `.claude/skills/go/review.md`:91 — unresolved

```diff
@@ -0,0 +1,118 @@
… 87 lines elided …
+
+## The commit
+
+**`pass`, `fixed` and `fixed-relay` end the run in a commit whose subject opens
```

**@vzakharov (human)** — 2026-11-02T01:57:03Z

а нужен ли нам `...-relay` именно как scope для префикса? по сути и то и то fixed? к слову now that I'm asking it, а зачем нам вообще скоуп нужен?

---

## Timeline (status, references, and other events)

- **2026-10-30T11:10:02Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/257#pullrequestreview-5711259351.
- **2026-10-30T11:19:43Z** @vzakharov renamed from «feat: the Opus checkpoint reviewer reads its own procedure» to «fix: the Opus review of weaker sessions runs inside /polish».
- **2026-11-01T16:55:45Z** @vzakharov renamed from «fix: the Opus review of weaker sessions runs inside /polish» to «fix: the Opus review of weaker sessions reads its own procedure».
- **2026-11-02T02:06:33Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/257#pullrequestreview-5731328406.
