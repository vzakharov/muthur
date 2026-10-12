# Issue #183: A blocker pauses only what it blocks

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/183
- **Author:** @vzakharov (agent)
- **Created:** 2026-10-11T19:33:09Z
- **Updated:** 2026-10-11T19:33:09Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

The loop's rule for a blocker — set the plan to paused and call the operator —
is right for a blocker that stops all of the work. It is applied wider than
that: a question whose answer only part of the work depends on halts the whole
session, though the rest could go on and be revisited once the question is
answered.

The case that raised it (vovazakharov.com#140): one song's reflection waited on
an answer, and the session stopped, where the reflections on the other songs,
which nothing blocked, could have been written meanwhile and updated afterwards
if the answer changed them.

vovazakharov.com carries this today as a line in the operator's own voice file
(`.claude/voice/operators/vzakharov.md`) — «не нужно было (и не нужно в
будущем) останавливать то, что можно продолжать из-за затыков во,
в-принципе, параллелизуемых вопросах». The operator's verdict: it is not a
personal preference but a general approach, so it belongs in muthur's loop —
`/go`'s § "Stopping partway" and wherever else the pause-and-ask rule is
stated: ask the blocking question, park only what it blocks, keep going on
everything else, and revisit the parked part when the answer lands. Once
muthur carries it, the line in the operator file goes.

---

## Timeline (status, references, and other events)

- **2026-10-11T19:33:40Z** @vzakharov referenced this issue in a commit: https://api.github.com/repos/vzakharov/vovazakharov.com/commits/81c3a6a00d0d5d93b59c2e3cd1210b50844e2be7.
