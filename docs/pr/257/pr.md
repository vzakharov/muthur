# PR #257: fix: the Opus review of weaker sessions reads its own procedure

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/257
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/checkpoint-reviewer-procedure-wcfux3
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-30T10:05:34Z
- **Updated:** 2026-11-01T17:52:07Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: none

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (the export committed at 14eba09). Resolved threads never count; an `(agent)` tail is a reply already given._

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

## Timeline (status, references, and other events)

- **2026-10-30T11:10:02Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/257#pullrequestreview-5711259351.
- **2026-10-30T11:19:43Z** @vzakharov renamed from «feat: the Opus checkpoint reviewer reads its own procedure» to «fix: the Opus review of weaker sessions runs inside /polish».
- **2026-11-01T16:55:45Z** @vzakharov renamed from «fix: the Opus review of weaker sessions runs inside /polish» to «fix: the Opus review of weaker sessions reads its own procedure».
- **** @vzakharov reviewed (PENDING): https://github.com/vzakharov/muthur/pull/257#pullrequestreview-5731328406.
