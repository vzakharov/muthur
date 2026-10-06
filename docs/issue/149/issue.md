# Issue #149: /go: a turn blocked on an operator decision should pause the plan

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/149
- **Author:** @vzakharov (agent)
- **Created:** 2026-10-06T09:57:09Z
- **Updated:** 2026-10-06T09:57:09Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

`/go`'s "Stopping partway releases the plan" names two triggers: the operator asking to stop, and the context budget hook. A turn that ends on a question to the operator is neither, so the plan stays `*.in-progress.md` across it.

That is a claim nobody is holding. If the session dies there, or the operator answers in a fresh one, the next session's Step 1 stops on someone else's `in-progress` plan.

It happened on vzakharov/vovazakharov.com#104: a review round ended on a question about the `filed:` date, the plan stayed `in-progress`, and the operator asked why.

**Proposal:** add a third trigger. A turn that ends blocked on an operator decision releases the plan to `*.paused.md`, with the open question recorded in it. The answer then resumes it like any other paused plan, in this session or another.

---

