# PR #251: feat: Opus checkpoint review for sessions on a weaker model

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/251
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/opus-checkpoint-review-p4nmuv
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-29T03:10:45Z
- **Updated:** 2026-10-29T14:49:52Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 1

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/hooks/checkpoint-review.py`:3 — unresolved — last: @vzakharov (human) 2026-10-29T14:46:57Z — "потому что /handle тоже вызывает /go, так?" → [↓](#t01)

---

## Body

## Summary

- A session running on a model below Opus (Sonnet, Haiku) gets an Opus subagent's quality review at each loop cutoff: after `/plan` publishes, at the end of `/go`'s quality passes and before its plan is marked completed (which covers `/handle`'s lanes), and in `/finalize` before the vet run. The brief always carries the operator's request verbatim, and facts rather than the session's opinion of its work.
- A hook enforces it, not the weaker model's own judgement: `.claude/hooks/checkpoint-review.py` reads the serving model off the transcript's latest reply; on Sonnet or Haiku it delivers the procedure on entering `/plan`, `/go` or `/finalize`, and denies the command closing that cutoff (the draft flip, the `*.completed.md` flip, `gh pr ready`) until the session records the verdict with `checkpoint-review.py verdict <session> <skill> <verdict>`. `MUTHUR_CHECKPOINT_REVIEW=off` turns it off; the skill-entry detection it shares with `go-delegation.py` moves to `skill_entry.py`.
- The reviewer answers with one of five verdicts, best to worst: `pass`; `revise` (what to change, by substance — the session fixes it and sends the same reviewer "show again" through `SendMessage`, at most twice); `fixed`, kept for what is cheaper to fix than describe, since the reviewer bills at Opus rates; `fixed-relay` (the work is beyond the session's model, so it relays to an Opus session once the skill finishes); `relay` (the reviewer can't fix it, so the session relays now with the findings).
- `/relay` starts an escalated successor on Opus, and the reviewer folds what it learns about the session's model into `delegation-model-capabilities.md`.

## QA Checklist

- [ ] `weak-go` — In a session on Sonnet or Haiku, run a small `/go`; the procedure arrives as hook context, an Opus subagent is launched with the review brief before the plan's `*.completed.md` flip, and the turn's report names its verdict.
- [ ] `gate` — In that session, attempt the `*.completed.md` flip before recording a verdict: the hook denies it with the verdict command in its reason; after a `pass` it goes through, after a `revise` it stays denied.
- [ ] `revise-round` — When the reviewer answers `revise`, the follow-up goes to the same agent via `SendMessage`, not a new `Agent` call.
- [ ] `escalate` — A `fixed-relay` or `relay` verdict ends with `/relay` starting a successor whose `get_session` shows an Opus model; after `relay` in `/go` the plan is `*.paused.md`.
- [ ] `opus-skip` — In a session on Opus, no procedure is delivered and nothing is denied.
- [ ] `hook-tests` — `python3 scripts/test_checkpoint_review.py` and `python3 scripts/test_go_delegation.py` pass.
- [ ] `vet` — `./scripts/vet.sh` passes: the catalog check finds the hook and helper entries, and the capabilities file stays under 100 lines.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `weak-go` | manual | ❌ | Needs a live session on a weaker model |
| `gate` | unit | ✅ | `scripts/test_checkpoint_review.py` drives the deny and verdict paths; a live run confirms the harness honours the deny |
| `revise-round` | manual | ❌ | Read the transcript for the `SendMessage` call |
| `escalate` | manual | ❌ | `get_session` on the successor |
| `opus-skip` | unit | ✅ | `scripts/test_checkpoint_review.py` (silence on Opus and Fable) |
| `hook-tests` | unit | ✅ | Run by `scripts/check-muthur.sh` |
| `vet` | unit | ✅ | `scripts/check-skill-catalog.sh` and the 100-line check in `scripts/vet.sh` |

https://claude.ai/code/session_01DaohkDGvyPHkmGezpudcWA
https://claude.ai/code/session_01DaohkErDzQLANWgn2tnDGB

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-29T03:11:00Z — "Proposed squash body: ``` A session running on Sonnet or Hai…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-29T03:11:00Z

[https://github.com/vzakharov/muthur/pull/251#issuecomment-6486830300](https://github.com/vzakharov/muthur/pull/251#issuecomment-6486830300)

Proposed squash body:

```
A session running on Sonnet or Haiku drives the loop as far as an Opus
one does, with nobody stronger checking its work before the operator
sees it. Each loop cutoff now hands that work to an Opus subagent for
review: after /plan publishes, at the end of /go's quality passes and
before its plan is marked completed (which covers /handle's lanes),
and in /finalize before the vet run, so every later step vouches for
the reviewed diff. The brief always carries the operator's request
verbatim and facts rather than the session's view of its work.

A hook enforces it rather than the weaker model's own judgement.
.claude/hooks/checkpoint-review.py reads the serving model off the
transcript; on Sonnet or Haiku it delivers the procedure on entering
/plan, /go or /finalize and denies the step that closes that cutoff
(the draft flip, the *.completed.md flip, gh pr ready) until the
session records the review's verdict with the hook's verdict command.
MUTHUR_CHECKPOINT_REVIEW=off turns it off. The skill-entry detection
it shares with go-delegation.py lives in skill_entry.py.

The reviewer answers with one of five verdicts, best to worst: pass;
revise, stating what to change by substance, after which the session
fixes it and asks the same reviewer to look again through SendMessage,
at most twice; fixed, kept for what is cheaper to fix than describe,
since the reviewer bills at Opus rates; fixed-relay, where the work is
beyond the session's model and it hands over to an Opus session once
the skill finishes; and relay, where the reviewer cannot fix it and
the session hands over at once with the findings as the next step.

/relay starts that successor on Opus instead of inheriting the model.
The reviewer folds what it learns about the session's model into
delegation-model-capabilities.md, under the file's keeping rules.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/hooks/checkpoint-review.py`:3 — unresolved — last: @vzakharov (human) 2026-10-29T14:46:57Z — "потому что /handle тоже вызывает /go, так?" → [↓](#t01)

<a id="t01"></a>

### `.claude/hooks/checkpoint-review.py`:3 — unresolved

```diff
@@ -0,0 +1,231 @@
+#!/usr/bin/env python3
+"""Hold a session on a model below Opus to `checkpoint-review.md` at each cutoff
+of `/plan`, `/go` and `/finalize`.
```

**@vzakharov (human)** — 2026-10-29T14:46:57Z

потому что /handle тоже вызывает /go, так?

---

## Timeline (status, references, and other events)

- **2026-10-29T03:46:02Z** @vzakharov cross-referenced this pull request from [#253 feat: record what Haiku needs in a brief, for delegation](https://github.com/vzakharov/muthur/pull/253).
- **2026-10-29T04:02:08Z** @vzakharov cross-referenced this pull request from [#230 content: notes comparing Haiku, Sonnet and Opus on one agent-loop change](https://github.com/vzakharov/vovazakharov.com/pull/230).
- **2026-10-29T04:22:25Z** @vzakharov cross-referenced this pull request from [#250 feat: gate weak-model sessions on an Opus quality check](https://github.com/vzakharov/muthur/pull/250).
- **2026-10-29T04:22:27Z** @vzakharov cross-referenced this pull request from [#252 feat: an Opus quality gate for sessions on a weaker model](https://github.com/vzakharov/muthur/pull/252).
- **2026-10-29T14:49:52Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/251#pullrequestreview-5699696890.
