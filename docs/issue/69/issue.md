# Issue #69: feat: sweep the skills for minority-entry sections worth moving to a colocated file

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/69
- **Author:** @vzakharov (agent)
- **Created:** 2026-09-11T13:34:44Z
- **Updated:** 2026-09-11T13:34:44Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## The pattern

PR #68 moved `/plan`'s `plan or go` decision out of `SKILL.md` into a colocated `plan-or-go.md`. The section only ever fires when the operator's prompt literally carries those words, but it was loaded by every planning session — so `SKILL.md` now keeps three lines of routing (the entry exists, two questions pick between three outcomes, load the sidecar iff those words are present) and the page sits beside it.

The same shape almost certainly recurs. Skills already load lazily as whole units, so the win is **inside** a frequently-loaded skill: a section that handles one invocation form, one flag, or one failure mode, while every other run pays for it.

## The criterion

Extract a section when all three hold:

1. **It fires on a recognizable trigger** — a literal phrase in the prompt, a flag, a mode, a branch state — so the resident pointer can state the condition precisely enough that an agent knows whether to load it.
2. **The trigger is the minority case.** Not "sometimes" — most runs of that skill must not fire it.
3. **What stays behind is a real pointer, not a stub.** The resident lines must carry enough that a session which does *not* fire the trigger needs nothing else, including any guard that keeps them from firing it unprompted. For `plan or go` that guard is "absent the words nothing changes" — the pointer is what creates the temptation, so the pointer answers it.

Do **not** extract when the section is load-bearing on every run (`/pr` § "Modes", `/go` § "Step 1"), or when the trigger is only recognizable after reading the section you would be extracting.

## The counter-force

A pointer that fails to fire is a **silent skip** — the agent follows the surviving prose and never learns what they missed. This is the exact failure `scripts/check-skill-catalog.sh` assertion 1 exists to prevent, and it currently only matches `@.claude/skills/<name>/SKILL.md`: a reference to a colocated non-`SKILL.md` file is unchecked. Widening that pattern is part of this work, not a follow-up — the sweep multiplies the number of such references.

## Candidate sites

Measured as `## heading [lines]` over the current tree. Each needs the criterion applied, and rejecting one is a valid outcome worth recording in the PR.

| Site | Lines | Trigger | Note |
|---|---|---|---|
| `/plan` § "If the session is already in native plan mode" | 18 of 135 | the session is in plan mode | Strongest analogue; `exit-dialog.md` already sits beside it |
| `/go` § "Argument shape" — the canary block | ~15 of 99 | a handoff block pasted into the wrong session | Split it: the token-vs-prose classifier fires every run, the canary does not |
| `/issue` Step 3 — the split machinery | ~52 of 140 | the issue is split-worthy | Four sub-sections that a non-split issue never reads |
| `/squash-message` Step 2 — working-file selection | ~101 of 324 | a swept-then-restored file, a ready-vs-draft PR | Much of it branches on states most runs are not in |
| `/from-branch` § "Argument shape" + § "Failure modes" | 26 of 125 | a target that does not resolve cleanly | Check whether the resident half survives the cut |
| `/tend-prose` — the four lens sections | 143 of 319 | `/tend-prose <lens>` runs one | **Inverted**: the default full sweep needs all four, so a per-lens split may cost more than it saves. Verify before assuming |

## Acceptance

- Each site above is either extracted or explicitly declined, with the reason recorded.
- `scripts/check-skill-catalog.sh` asserts that **every** `@.claude/skills/**/*.md` reference resolves, not just `SKILL.md` ones.
- Every extraction leaves a resident pointer that names the trigger condition and carries whatever a non-triggering session needs.
- `.claude/skills/update-muthur/catalog.md` rows stay correct. Precedent from #68: a sidecar that travels with its skill gets no row of its own (`exit-dialog.md`, `analyst-rules.md`); `voice.md` and `operators.md` have rows because CLAUDE.md imports them and an adopter decides on them separately.

---


