# Recovering from native plan mode

Loaded by `@.claude/skills/plan/SKILL.md` § "If the session is already in native
plan mode", and by `.claude/hooks/plan-mode-notice.sh` on every prompt a remote
session submits while the mode is on.

Plan mode is reached two ways, neither of which asks the agent: the operator
switches mode in the UI, or types `/plan` — a **built-in slash command**, so the
keystroke renders in the client and never arrives. Either way the session is held
to read-only work, so the recovery is keyed on **being in plan mode**, not on how
it got there. (The operator's own entry to `/plan` is bare prose: `plan: <task>`,
or just the task.)

**This is plan mode's own exit, not an override of it.** Its instructions end
with "this supercedes any other instructions you have received" — and they also
make the harness plan file writable and end the turn at `ExitPlanMode`, which is
the path below. What conflicts is the rival procedure injected alongside the
restriction, a phased workflow on `Explore`/`Plan` subagents plus
`AskUserQuestion`, and both are moot once the exit lands.

1. **Take the exit immediately — and ask for it.** The restriction gates
   `Edit`/`Write`, not Bash, so the plan file is reachable from inside plan mode;
   writing it there takes the operator's approval instead of asking for it. Spend
   the click only on a turn that has something to write, though: a question
   answerable from reading is answerable from inside plan mode.
2. **Copy the dialog's text into the harness plan file**: `mkdir -p "$(dirname
   <the path the harness named>)" && cp .claude/skills/plan/exit-dialog.md <that
   path>` — the directory does not exist until something creates it, so don't
   drop the `mkdir`. `ExitPlanMode` takes no plan argument, it renders that file,
   and `cp` overwrites — which re-entry needs, the harness handing back the same
   path with the previous exit's text still in it. Append at most one line naming
   the task and nothing further: the dialog is where the operator decides whether
   to spend the click, not where they review a plan.

   `exit-dialog.md` describes the click a **new** session's exit buys — writing
   the plan file. A session that arrived on continued work (`/from-branch`,
   `/handle`) is buying something else, usually write access to finish it, and
   says so rather than shipping copy that misdescribes the decision.
3. **Call `ExitPlanMode` bare**, then **run `/plan` from the top.** The
   deliverable is `docs/plans/<slug>.draft.do-not-implement.md` — not an answer
   in chat prose, and not the harness plan file's content carried over. That file
   is scaffolding for the dialog; it is never the plan.

**Rejecting the approval is the escape hatch**, and `exit-dialog.md` says so
outright. Being in plan mode states no intent — reflex and a UI switch both land
there — so the dialog is the first moment the operator is actually asked, and it
has nowhere to type. A rejection, or "stay in plan mode" in chat, means run plan
mode's own workflow and don't re-raise the exit.

**Exiting plan mode is not the go-ahead**, however the approval reads — it comes
back as "you can now start coding", in accept-edits mode. It authorizes writing
the plan file and nothing past it; the `do-not-implement` gate is untouched and
still needs the token from `@.claude/skills/plan/SKILL.md` § "The approval gate".
