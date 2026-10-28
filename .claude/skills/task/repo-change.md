# A skill that changes the repo is a task

A skill whose run leaves work in this repo — files it writes, a sweep it
applies, a record it commits — runs as the work of
`@.claude/skills/task/SKILL.md` in every part its invocation leaves unsaid.
`/task` makes its plan-or-not call as for any task, and `/go`'s tail, `/polish`
then `/pr`, lands it. That tail is the point: a skill that commits and pushes on
its own skips both, and the operator gets a diff no pass has read and no PR to
review it in.

**A skill names its deviations from that route, and only those** — landing on a
PR that already exists rather than opening one, say, or always writing a plan
and handing it off. A deviation adjusts a step and leaves the rest of the route
in force.

The loop's own skills (`/go`, `/polish`, `/pr`, `/finalize`, `/relay`,
`/sync-branch` and the like) are the route itself.
