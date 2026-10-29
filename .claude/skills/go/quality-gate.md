# The Opus quality gate

The checkpoint that `/plan`, `/go`, `/handle` and `/finalize` each run where
their pointer line says. It runs only in a session on a model other than Opus,
and the work it checks is the session's own so far. The procedure is here, once;
each skill's pointer says where the checkpoint sits.

## Detect the model

Call `get_session` (`mcp__claude-code-remote__get_session`, loaded with
`ToolSearch` where it is deferred) with no id. The session is strong when
`external_metadata.last_served_model` names an Opus model, since that is the
model that did the work, fallbacks included; only where that field is absent
does `session_context.model` decide. Otherwise it is weak. Where the tool does
not exist, as in a local CLI, the model the system prompt names decides; with
neither, the session counts as weak and the gate runs.

A strong session has nothing to check here. It carries on past the checkpoint.

## The judge

Launch `Agent` with `model: "opus"`, `run_in_background: false` and no worktree:
the judge works in the session's own tree, where its fixes for C and D land. The
session blocks on its verdict, so the two never write at once.

The brief names the checkpoint and the branch, gives the base the work merges
into, and names the plan file the work implements, if any. At `/finalize`, the
sweep has already removed the plan from the tree, so the brief names the commit
that last held it, and the judge reads it with `git show`. It asks whether the
work so far passes the quality bar, and it lists the five verdicts below with
their meanings. It asks for one verdict and the reason for it, with each defect
and its correction named. It tells the judge that it may correct
`.claude/skills/go/delegation-model-capabilities.md` where the review taught
something, following `.claude/skills/go/delegation.md` § "Keeping". The judge
reads the diff with `git`, against the base, and commits whatever it edits, its
fixes and the capabilities entry alike, under the repo's commit conventions.

## The verdicts

- **A. Passes.** Continue past the checkpoint.
- **B. Fails with corrections the session can make.** Apply the corrections the
  judge named, then send the result back to the same judge with `SendMessage`.
  Its answer is the next verdict.
- **C. Fails, and the judge has fixed it.** Continue without another round.
- **D. Fails, the judge has fixed what it found, and the work is too hard for
  this model.** Relay the rest to an Opus session (§ "Relaying").
- **E. Fails, and the judge cannot fix it.** Relay at once (§ "Relaying").

A defect a previous B already named and the session's fix did not reach is never
a B again: the judge fixes it itself, as C or D, or returns E.

**Re-showing reuses the judge.** `SendMessage` continues the spawned agent with
its context intact. Only when that agent is gone, launch a fresh Opus judge with
a brief that carries every earlier verdict, its reasons, and the corrections
applied since.

## Relaying

For D and E: run `/relay park`, its argument the work the judge left open, so
the summary's Next step carries it. Park skips the relay skill's Step 3, so this
file carries it out: `@.claude/skills/relay/SKILL.md` Step 3 (its title rule and
its local-CLI branch), with `model` set to the current Opus model's ID, which
the `claude-api` skill lists, looked up at launch. Step 4's report then stands
in for park's own, and the turn ends.

## When the judge cannot be launched

If the judge cannot be launched, the gate did not run. Report that, and end the
turn. Passing silently undoes the point of the gate.
