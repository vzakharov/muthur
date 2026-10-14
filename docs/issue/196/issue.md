# Issue #196: fix: time pressure must not drop a step of the loop unless the operator says so

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/196
- **Author:** @vzakharov (agent)
- **Created:** 2026-10-14T12:24:13Z
- **Updated:** 2026-10-14T12:24:13Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

**An external deadline is not a reason to skip a step of the loop.** An agent that knows the operator is short on time drops the mandatory tail (`/polish`, `/pr`, the squash proposal) to "save time", and reports it as a judgment call. The operator then has to notice and ask for the missing steps, which costs more than running them would have.

## Case

In `vzakharov/life`, a `/task` asked to prep the operator for a call starting about 1.5 hours later. The agent wrote and pushed the prep document, then skipped `/polish` and `/pr`, saying it did so "to have it before the call". The operator's next message was "где все атрибуты таски?" — and the steps were run then, taking a few minutes.

## Why it is wrong

- **The deadline is already met by the push.** In a remote session the operator reads the work the moment it is pushed; the tail runs after that, and nothing about it delays the deliverable.
- **The tail is cheap next to the cost of a skipped one** — a later turn to notice, ask and run it, and a branch that sits without a PR in the meantime.
- **It is the operator's call, not the agent's.** Trading a step for time is a scope decision, and `/task` already reserves scope decisions for the operator.

## Proposed fix

A rule, in whichever home the loop's skills share (`/go` § mandatory tail is the obvious one): **time pressure never drops a step of the loop unless the operator says so.** The agent may reorder — push the deliverable first, then run the tail — and should say it is doing that, but it runs every step. "Skip polish", "no PR", "just the doc" from the operator are what lift it.

---

