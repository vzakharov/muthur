# The Opus quality gate

The checkpoint that `/plan`, `/go`, `/handle` and `/finalize` each run where
their pointer line says. It runs only in a session on a model other than Opus,
and the work it checks is the session's own so far. The procedure is here, once;
each skill's pointer says where the checkpoint sits.

## Detect the model

Load `get_session` with `ToolSearch`
(`select:mcp__claude-code-remote__get_session`) and call it with no id. The
session is strong when `session_context.model` or
`external_metadata.last_served_model` names an Opus model. Otherwise it is weak.
If the tool cannot be reached, the session is weak: a failure to tell lands on
the side of checking.

A strong session has nothing to check here. It carries on past the checkpoint.

## The judge

Launch `Agent` with `model: "opus"` and no worktree. The judge reads the
session's own tree and edits nothing there except the capabilities file. The
session blocks on its verdict, so the two never write at once.

The brief names the checkpoint and the branch, and gives the base the work
merges into. It asks whether the work so far passes the quality bar, and it
lists the five verdicts below with their meanings. It asks for one verdict and
the reason for it, with each defect and its correction named. It tells the judge
that it may correct `.claude/skills/go/delegation-model-capabilities.md` where
the review taught something, following `.claude/skills/go/delegation.md` §
"Keeping". The judge reads the diff with `git`, against the base, and does not
edit source.

## The verdicts

- **A. Passes.** Continue past the checkpoint.
- **B. Fails with fixable corrections.** Apply the corrections the judge named,
  then send the result back to the same judge with `SendMessage`. Its answer is
  the next verdict.
- **C. Fails, and the session has fixed it already.** Continue without another
  round.
- **D. Fails, and the work is too hard for this model.** Apply the fixes the
  judge named, then relay the rest to an Opus session (§ "Relaying").
- **E. Fails, and the session cannot fix it.** Relay at once (§ "Relaying").

A B that comes back as B again, after its corrections were applied, is an E.
Each round a judge sends back adds the same fix to the same work, so a second B
on the same defect means the fix did not reach it.

**Re-showing reuses the judge.** `SendMessage` continues the spawned agent with
its context intact. Only when that agent is gone, launch a fresh Opus judge with
a brief that carries the first verdict, its reasons, and the corrections applied
since.

## Relaying

For D and E: run `/relay park`, which writes the summary and starts no session.
Then call `create_session` from the claude-code-remote tools with:

- `model` set to the current Opus model's ID, which the `claude-api` skill
  lists. The ID is not written into the repository.
- `source_url` the `origin` URL, and `source_revision` the branch.
- the prompt `/relay take <branch> — <what now>`, the line the relay skill's
  Step 3 gives, with `<what now>` in plain words.

Confirm with `get_session` that the new session did not fail at start. Report
its link and end the turn.

## When the judge cannot be launched

If the judge cannot be launched, the gate did not run. Report that, and end the
turn. Passing silently undoes the point of the gate.
