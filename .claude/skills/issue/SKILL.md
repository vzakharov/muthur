---
description: Compatibility redirect — `/issue` split into four skills and is no longer one of them. Invoke as `/issue <what to do> #<N>` and it forwards to `/plan`; with no number it names `/propose-issue` and stops. Kept because handoff blocks and muscle memory still say `/issue`.
---

`/issue` used to read an issue and decide what happened to it. Reading is now
`@.claude/skills/take-issue/SKILL.md`, which nothing but a skill calls, and
deciding is spread across `/task`, `/plan`, `/go` and `/propose-issue`. So this
name cannot forward to one skill unconditionally — it forwards on the one thing
that distinguishes the cases, which is whether the argument carries an issue
number.

**With a `#<N>` in the argument:** load and follow
`@.claude/skills/plan/SKILL.md`, passing the argument through unchanged —
prose, number and all. Then say in one line that `/task` and `/go` take that
same argument: `/task` hands the plan-or-not call back to the agent, and `/go`
skips it.

`/plan` is the default of the three because it is where `/issue` sent work for
as long as the name meant anything, and because the deprecated name says
nothing about which reading the operator meant — so the guess should be the one
that costs a round trip rather than an unreviewed diff.

**With no number:** there is no issue to take, and the prose is an unfiled unit
of work. Name `@.claude/skills/propose-issue/SKILL.md` and stop rather than
running it — filing is the one of the four that writes to the tracker, so it is
the operator's call to make explicitly.

Do not act on the summary above — this file carries no procedure of its own
beyond the fork, and `/handle`'s Do-NOT names acting on a one-line summary of a
skill as the failure mode.

Adopting repos: the source's `.claude/skills/update-muthur/catalog.md` states
when this row is worth taking.
