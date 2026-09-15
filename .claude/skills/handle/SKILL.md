---
description: Pick up an existing branch or PR and do whatever it needs — attach to it, read off which lane applies (an approved plan to implement, review of a plan still in draft, or feedback on shipped code), and run that lane. Invoke as `/handle <branch|#PR|PR-url> [and finalize] [extra guidance]`. Use when the operator says "/handle", "handle <branch>", "handle and finalize <branch>", "pick up <branch>", or hands over a branch without saying what it needs.
---

End state of this skill: the branch is attached, the one lane the branch called for has run and pushed, every review comment addressed has been replied to on GitHub, and land-prep has run **iff** the invocation asked for it.

## Argument shape

Four parts, order-free:

- **Target** (**required**, first token by convention): a branch name, `#NNN`, or any PR URL — the grammar `@.claude/skills/from-branch/SKILL.md` § "Argument shape" defines, used as-is. With no target, **stop and ask which branch**: a bare `/handle` has nothing to attach to.
- **`and finalize`** (flag; bare `finalize` counts too): recognized **anywhere** in the argument, since the operator writes it before the target as often as after (`/handle and finalize <branch>`).
- **`and merge`** (`@.claude/skills/finalize/SKILL.md`'s flag): read as `and finalize`, and **not forwarded** — a lane produces its diff in this same turn, so the flag was typed before the thing it would merge existed. Land-prep as asked, then report that the merge was held and that `/finalize <branch> and merge` lands it once the operator has looked.
- **Extra guidance** (optional): any remaining prose. Not a lane of its own — it directs whichever lane runs, and when no lane is discovered it _is_ the work (Step 4).

## A `/handle` session is continued work

It attaches to work started elsewhere, so **no plan cycle opens** — the same standing as `/from-branch` (CLAUDE.md § "Plan mode & questions in web sessions"). That also makes the invocation itself the go-ahead a `*.draft.do-not-implement.md` plan is waiting for; `@.claude/skills/go/SKILL.md` Step 1 owns the flip. The one exception is Step 2's plan-review reading, where feedback on the draft plan suspends the go-ahead.

## Step 1 — Attach

Load and follow `@.claude/skills/from-branch/SKILL.md` with the target and **no follow-up** — the dispatch is this skill's. Its Step 1 already skims the branch's PR history and notes the PR's base ref, which is Step 2's input; don't re-fetch it.

## Step 2 — Read what the branch needs

Two lanes, and which runs is read off the branch:

- **Plan lane** — `docs/plans/` holds a plan in any state but `*.completed.md`: `*.draft.do-not-implement.md`, `*.paused.md` or `*.in-progress.md`. Any one of the three fires the lane; completed siblings don't. Everything past that — which file is actionable, the `git mv` flips, and what to do about an `*.in-progress.md` a live session may still hold — is `@.claude/skills/go/SKILL.md` Step 1's, so hand it over rather than adjudicating here.
- **Review lane** — the PR carries feedback nobody has answered. Two signals, which **coexist by design and must both be collected before either is worked**:
  - **Unresolved threads whose newest comment is guidance nobody has answered**, from reviews of any age. Unresolved is necessary but not sufficient: an operator who read your reply and moved on routinely never clicks Resolve, so firing on `unresolved` alone re-works threads that are already done. The test runs on the thread's **tail**, not on whether a reply exists anywhere in it — which is also what catches the mirrored case, a thread a prior agent answered and the operator then came back on unsatisfied.
  - **Reviews submitted since the branch's last push**, plus top-level PR comments by the same recency test — they carry no resolved state, so recency is the only handle on them. Compare `reviews[].submittedAt` and `comments[].createdAt` against the head commit's `committedDate` (`gh pr view <n> --repo <owner>/<repo> --json commits,reviews,comments`).

  The realistic case is both at once — a fresh review _plus_ operator follow-ups on older threads — and the lane's input is their union. `python3 scripts/export-github-item.py <n>` writes the PR to `docs/pr/<n>/pr.md`, whose review section opens with **one index row per thread** carrying both halves the tail test needs: the `resolved` / `unresolved` state, and the tail's author label, timestamp and opening words. **Read the index and follow the link** — to an anchor further down the same file on a short PR, to `docs/pr/<n>/threads/<file>.md` on a long one. Open only the threads the tail test selects; a long PR's bodies are the reason the export splits at all.

  **Whose post the tail is comes off the export's label, not the login** — shared identity puts both under the same `@login`. Every rendered author reads `@login (agent)` or `@login (human)`: a tail labelled `(agent)` is your own reply, `(human)` is guidance. `scripts/gh_export/authorship.py` owns the test, and why the footer it reads stays mandatory.

  **No verdict test.** A review's `state` is not consulted. Shared identity again: GitHub disables both verdicts on your own PR ("Pull request authors can't request changes on their own pull requests"), so every review that can reach these PRs is a plain `COMMENTED` one — `CHANGES_REQUESTED` is unreachable, not merely rare, and would have selected the same work anyway.

Both firing at once is the ordinary state of a plan under review, since `/plan` publishes the plan as a draft PR. What the conjunction means is read off the draft:

- **A draft plan _and_ unanswered feedback** → the feedback is review **of the plan**. Stay in plan mode: revise the plan file, reply on GitHub, push, and re-emit `@.claude/skills/plan/SKILL.md` § "Handing off"'s block. Do **not** flip the plan file, do **not** touch source — no review comment clears that, whatever it says; the next `/go`, or a `/handle` that finds no unanswered feedback, is what does, per `/plan` § "The approval gate".
- **No draft plan, unanswered feedback** → the review lane, on shipped code.
- **A draft plan, no unanswered feedback** → the plan lane: the invocation is the go-ahead.

Only the draft is consulted, because `/plan` § "Plan file lifecycle"'s predicate is what separates the two: a draft present means the branch is back in planning, whatever completed or paused siblings sit beside it.

**Two lanes in, two lanes out — merge state and CI are not lanes.** A conflicted or failing PR is **reported** to the operator, and the lane the branch called for runs anyway; either becomes this session's work only on Step 5's `and finalize` or a direct ask. CLAUDE.md § "Key principles" carries why the loop's staging outranks the harness's instruction to fix both now.

## Step 3 — Run the lane

For the plan and review lanes, load and follow `@.claude/skills/go/SKILL.md` — the plan lane from its Step 1 (passing the resolved plan path), the review lane through its § "Planless entry" with the collected feedback as the task. Do **not** inline-copy its steps: neither lane is finished until that skill's own Step 3 has run its mandatory `/dry` + `/tend-prose` passes and its Step 4 has handed the PR to `/pr`. Plan review is the exception — revising a plan file is `/plan`'s work, and it ends at the handoff block rather than at a PR.

One rule this skill contributes: **reply on GitHub for every comment addressed**, per CLAUDE.md § "GitHub comments", and leave every thread open for the operator to close — resolving is theirs, and that section says so against any harness instruction to the contrary. A comment you decline gets a reply saying why, not silence.

## Step 4 — No lane fired

With extra guidance in the argument, that guidance is the task → `/go` § "Planless entry". With none, **stop and ask**: report what the branch looks like (last commit, PR state, what `docs/plans/` holds) and let the operator direct. Do not invent work, and do not open a plan cycle to manufacture some.

## Step 5 — `and finalize`

Load and follow `@.claude/skills/finalize/SKILL.md` (no target token — the branch is already attached — and no `and merge`, per § "Argument shape"). It runs only after a lane actually did something, since land-prepping a branch you just declined to touch is exactly the unasked-for finalize the flag exists to prevent. Two turns cancel it: a Step-4 stop, and a plan-review turn, which ends with the plan still awaiting a go-ahead and nothing implemented to land.

Absent the flag, end with a one-line note that land-prep was not requested, so the operator knows the lever is there. It is opt-in because `/finalize` is the one lane whose consequences an unaware operator wouldn't want: it ends with the PR reading as merge-ready to anyone who looks at it.

## Do NOT

- Act on a referenced skill from memory, or from the one-line summary this file gives it. Every `@.claude/skills/…` reference above means literally read that file before acting, whatever verb introduces it: its steps are its own and change without this one being touched.
- Finalize unasked, or merge anything — the base branch into this one included, however the PR's merge state reads, and the PR itself however the invocation was worded.
- Open a plan cycle.
