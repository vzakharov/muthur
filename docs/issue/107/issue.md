# Issue #107: Routing ladder misses a session that starts as a question and turns into changes

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/107
- **Author:** @vzakharov (agent)
- **Created:** 2026-09-24T17:45:35Z
- **Updated:** 2026-09-24T17:45:35Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Gap

`CLAUDE.md` § "Plan mode & questions in web sessions" routes a session **once**, on its opening prompt: row 1 (asks for a change) → `/task`, row 2 (asks for no change) → answer it. The only other state it names is *continued work*, which it defines as "once you've prepared a plan this way and started implementing".

That leaves a third path unrouted: **a session that opens as row 2 and turns into row 1 partway through.** The opening prompt is a question, so it is answered. Then the operator's follow-ups start asking for changes to the repo, one reply at a time. None of them is an opening prompt, so the ladder never fires again. And there is no plan behind the work, so the "continued work" bullet doesn't describe it either. The agent just keeps working in chat: it commits and pushes, but `/task`'s plan-or-not call never happens, `/go`'s quality passes (`/polish`) never run, and `/pr` never opens a PR. The operator finds out when they ask where the PR is.

## Observed

In a downstream repo (vzakharov/life), a session opened with "create a branch, I'll upload my dental X-rays — .dcm, do you know it? anything to convert it with?". It was read as row 2 plus a trivial branch. Over the next ~15 turns it grew into a study directory: a build script, a committed report, a README, and a published viewer. There were two commits and no PR, and `/polish` never ran until the operator asked for both.

## Proposed rule

**The first turn that asks for a change to the repo is a routing point, wherever it falls in the session.** If the session has not been routed to `/task` yet, and isn't attached to a plan or a branch via `/from-branch` or `/handle`, that turn gets the same treatment an opening prompt in row 1 would: `/task`, which makes the plan-or-not call against the work as it now stands. From then on it is continued work.

Where this belongs: it's the ladder's own rule, so it goes in that section. The natural spot is beside the "only new sessions, not continued work" bullet, which it narrows: continued work starts at the first routing, not at the first commit.

Two details a fix should settle:
- **What counts as the switch.** The test is the one the ladder already uses, the expected deliverable, applied per turn. A request whose answer lands as a file in the repo is the switch. An answer that happens to leave something in `tmp/` is not.
- **Mid-stream `/task` usually picks "no plan".** By then the scope is typically obvious from the conversation, so the cost is small. What the routing buys is `/go`'s planless lane with its mandatory tail (`/polish`, then `/pr`), not a plan file.

---

