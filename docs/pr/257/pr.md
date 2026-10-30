# PR #257: feat: the Opus checkpoint reviewer reads its own procedure

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/257
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/checkpoint-reviewer-procedure-wcfux3
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-30T10:05:34Z
- **Updated:** 2026-10-30T11:10:03Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 8

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `docs/remove-before-merging/squash-message.md`:1 — unresolved — last: @vzakharov (human) 2026-10-30T10:56:36Z — "это fix:" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:18 — unresolved — last: @vzakharov (human) 2026-10-30T10:58:07Z — "у нас бывает хук на запуск скилла (когда агент создаёт подаг…" → [↓](#t02)
- **T03** `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:49 — unresolved — last: @vzakharov (human) 2026-10-30T11:00:01Z — "опять же, мы не можем программно отказывать в запуске подаге…" → [↓](#t03)
- **T04** `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:53 — unresolved — last: @vzakharov (human) 2026-10-30T11:05:41Z — "хм, не понял, о чём это. Я предполагал что у нас будет как в…" → [↓](#t04)
- **T05** `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:69 — unresolved — last: @vzakharov (human) 2026-10-30T11:06:40Z — "на самом деле я это сам сказал и сам теперь сомневаюсь. Можн…" → [↓](#t05)
- **T06** `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:74 — unresolved — last: @vzakharov (human) 2026-10-30T11:08:35Z — "cheaper to do или если нет уверенности, что описать можно в…" → [↓](#t06)
- **T07** `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:145 — unresolved — last: @vzakharov (human) 2026-10-30T11:09:22Z — "а, то, с чего я начал" → [↓](#t07)
- **T08** `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:198 — unresolved — last: @vzakharov (human) 2026-10-30T11:10:00Z — "ну вот нет: to the extent possible должно быть воспроизведен…" → [↓](#t08)

---

## Body

## Summary

- The Opus checkpoint reviewer stops depending on the brief a Sonnet or Haiku session writes: it reads its whole procedure from `.claude/skills/go/checkpoint-reviewer.md` and derives the request, the last cutoff and the parent's log itself.
- The session launches it with one prompt, ``Proceed per `.claude/skills/go/checkpoint-reviewer.md` ``, and the hook denies an Opus `Agent` prompt that names the checkpoint review without being that line, or that line sent to a model other than Opus.
- `scripts/session-qa.py` extracts the parent's questions and answers (and its cutoff entries, with the head commit then) from the transcript; the transcript helpers it shares with `relay-last-reply.py` move to `scripts/lib/transcript.py`.
- This PR is a plan so far (`docs/plans/checkpoint-reviewer-procedure.*.md`). It is reviewed by Opus under the old procedure, and the implementation becomes the first review run under the new one.

## QA Checklist

- [ ] `plan-read` — the plan covers all of the request's points 1-3 and the dogfood.
- [ ] `qa-script` — after implementation, `python3 scripts/session-qa.py --cutoffs` on a real session lists its `/plan`, `/go`, `/finalize` entries.
- [ ] `launch-gate` — after implementation, a Sonnet session's Opus `Agent` call with a prompt other than the one line is denied while a review is pending.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `plan-read` | no | no | review of prose |
| `qa-script` | yes | yes (planned) | `scripts/test_session_qa.py` |
| `launch-gate` | yes | yes (planned) | `scripts/test_checkpoint_review.py` |

https://claude.ai/code/session_01RAikutax5eGF92PkSppyCn

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-30T10:06:02Z — "Proposed squash body: ``` A session below Opus wrote the Opu…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-30T10:06:02Z

[https://github.com/vzakharov/muthur/pull/257#issuecomment-6520121242](https://github.com/vzakharov/muthur/pull/257#issuecomment-6520121242)

Proposed squash body:

```
A session below Opus wrote the Opus checkpoint reviewer's brief itself,
so what the reviewer knew of the request, the run and the diff was
whatever the weaker model chose to put in. The reviewer now reads its
procedure from checkpoint-reviewer.md and derives all of that itself.

The session launches it with one prompt, naming that file, and the
checkpoint-review hook denies an Opus Agent prompt that names the review
without being that line, or that line sent to another model. The
reviewer finds the last /plan, /go or /finalize
entry in the parent's transcript, reads the parent's full log, checks
the work against CLAUDE.md, the skill and every operator message, and
answers with a verdict. checkpoint-review.md keeps only the session's
side: who runs it, the launch and what to do on each verdict.

scripts/session-qa.py extracts the parent's questions, answers and skill
entries, each with the head commit then, from the transcript; the
transcript helpers it shares with relay-last-reply.py move to
scripts/lib/transcript.py.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:1 — unresolved — last: @vzakharov (human) 2026-10-30T10:56:36Z — "это fix:" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:18 — unresolved — last: @vzakharov (human) 2026-10-30T10:58:07Z — "у нас бывает хук на запуск скилла (когда агент создаёт подаг…" → [↓](#t02)
- **T03** `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:49 — unresolved — last: @vzakharov (human) 2026-10-30T11:00:01Z — "опять же, мы не можем программно отказывать в запуске подаге…" → [↓](#t03)
- **T04** `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:53 — unresolved — last: @vzakharov (human) 2026-10-30T11:05:41Z — "хм, не понял, о чём это. Я предполагал что у нас будет как в…" → [↓](#t04)
- **T05** `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:69 — unresolved — last: @vzakharov (human) 2026-10-30T11:06:40Z — "на самом деле я это сам сказал и сам теперь сомневаюсь. Можн…" → [↓](#t05)
- **T06** `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:74 — unresolved — last: @vzakharov (human) 2026-10-30T11:08:35Z — "cheaper to do или если нет уверенности, что описать можно в…" → [↓](#t06)
- **T07** `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:145 — unresolved — last: @vzakharov (human) 2026-10-30T11:09:22Z — "а, то, с чего я начал" → [↓](#t07)
- **T08** `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:198 — unresolved — last: @vzakharov (human) 2026-10-30T11:10:00Z — "ну вот нет: to the extent possible должно быть воспроизведен…" → [↓](#t08)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:1 — unresolved

**@vzakharov (human)** — 2026-10-30T10:56:36Z

это fix:

---

<a id="t02"></a>

### `docs/remove-before-merging/squash-message.md`:18 — unresolved

```diff
@@ -0,0 +1,28 @@
… 14 lines elided …
+answers with a verdict. checkpoint-review.md keeps only the session's
+side: who runs it, the launch and what to do on each verdict.
+
+scripts/session-qa.py extracts the parent's questions, answers and skill
```

**@vzakharov (human)** — 2026-10-30T10:58:07Z

у нас бывает хук на запуск скилла (когда агент создаёт подагента-ревьюера)? тогда можно это делать программно без необходимости гонять опус туда-сюда вообще

---

<a id="t03"></a>

### `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:49 — unresolved

```diff
@@ -0,0 +1,246 @@
… 42 lines elided …
+
+Written to the Opus subagent, self-contained. Its steps:
+
+1. **Take nothing from the launch prompt.** The prompt is the one line
+   `Proceed per \`.claude/skills/go/checkpoint-reviewer.md\``; anything else in
+   it is the launching session's opinion and is not input. Said once, at the
+   top, with why.
```

**@vzakharov (human)** — 2026-10-30T11:00:01Z

опять же, мы не можем программно отказывать в запуске подагента, если там есть что-то кроме этого текста?

---

<a id="t04"></a>

### `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:53 — unresolved

```diff
@@ -0,0 +1,246 @@
… 46 lines elided …
+   `Proceed per \`.claude/skills/go/checkpoint-reviewer.md\``; anything else in
+   it is the launching session's opinion and is not input. Said once, at the
+   top, with why.
+2. **The last cutoff.** Run `python3 scripts/session-qa.py --cutoffs`: it lists
+   each entry into `/plan`, `/go` or `/finalize` in the parent's transcript with
+   its route (`Skill` call, `Read` of the `SKILL.md`, typed command), timestamp
+   and the head commit then. **The reviewer picks the cutoff, the script does
```

**@vzakharov (human)** — 2026-10-30T11:05:41Z

хм, не понял, о чём это. Я предполагал что у нас будет как в polish: будет отдельный вид коммитного префикса, от которого будет смотреть опус.

к слову, крамольная мысль.. а что если нам просто завернуть всё это в polish? т.е. а) polish всегда делает опус, б) последним шагом он проверяет не конкретные вещи (как в dry/tend-prose), а всё вместе (но желательно не читая весь дифф ещё раз, конечно).

тогда много из механики схлопывается, остаётся лишь точно так же поправить скилл polish -- чтобы агенты вызывали их с минимум текста (типа просто `/polish <some token arg>`, а всё остальное подагент уже смотрел в соответствующем ранбуке.

---

<a id="t05"></a>

### `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:69 — unresolved

```diff
@@ -0,0 +1,246 @@
… 59 lines elided …
+   `git diff origin/<base>...HEAD` (the branch around it), `<base>` being the
+   PR's `baseRefName` (`gh pr view`), else the repository's default branch; the
+   plan file under `docs/plans/` and the PR are found from the branch.
+3. **The parent's full log.** Run `python3 scripts/session-qa.py`: every
+   operator message verbatim, mid-turn ones included, and every assistant text
+   reply, in order, with the cutoff markers. Read all of it, not the tail — a
+   later operator message amends an earlier one. `--tools` adds one line per
+   tool call when what the session did matters, not only what it said. For a
+   record the script does not cover, `.claude/costs/CLAUDE.md` § "Reading a
+   transcript" is where the format is written down.
```

**@vzakharov (human)** — 2026-10-30T11:06:40Z

на самом деле я это сам сказал и сам теперь сомневаюсь. Можно сказать *можешь* смотреть в транскрипт, но требовать -- с учётом того что процедура теперь ясна -- может и не надо? просто пусть поступает по своему deliberation. (Белых медведей не оставляй когда будешь убирать)

---

<a id="t06"></a>

### `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:74 — unresolved

```diff
@@ -0,0 +1,246 @@
… 70 lines elided …
+   skill that ran, every message of the operator's (not the plan's reading of
+   the first one), and the plan where there is one. Also: does what the session
+   told the operator match the diff.
+5. **Fix** what is cheaper to do than to describe; commit under the repo's
```

**@vzakharov (human)** — 2026-10-30T11:08:35Z

cheaper to do или если нет уверенности, что описать можно в таком виде, что более слабая модель поймёт (исходя из того что мы знаем о её слабостях so far, как общих из model-delegation-capabilities*, так и выясненных сейчас)

*сам этот файл надо тоже переименовать и перенести, так как он теперь, получается, относится не только к delegation.

---

<a id="t07"></a>

### `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:145 — unresolved

```diff
@@ -0,0 +1,246 @@
… 141 lines elided …
+them. Errors become a raised `TranscriptError` that each script turns into its
+own failure.
+
+### 5. The hook enforces the one-line launch
```

**@vzakharov (human)** — 2026-10-30T11:09:22Z

а, то, с чего я начал

---

<a id="t08"></a>

### `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`:198 — unresolved

```diff
@@ -0,0 +1,246 @@
… 192 lines elided …
+
+## Dogfood
+
+1. **This plan** goes through the checkpoint review as the _old_ procedure
+   requires, since the new one does not exist yet; the reviewer's verdict and
+   what its brief lacked go in the PR.
```

**@vzakharov (human)** — 2026-10-30T11:10:00Z

ну вот нет: to the extent possible должно быть воспроизведено, типа

"Proceed with the reviewer role per <plan.md>, as if it was already implemented"

---

## Timeline (status, references, and other events)

- **2026-10-30T11:10:02Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/257#pullrequestreview-5711259351.
