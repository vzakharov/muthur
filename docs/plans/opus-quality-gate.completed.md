# Opus quality gate for weak-model sessions

## Goal

When a session runs on a model other than Opus, it asks an Opus subagent at each
loop checkpoint whether the work so far passes the quality bar. The subagent
answers with one of five verdicts, and the session acts on the verdict. The gate
is dogfooded on the session that writes it, which runs on a weak model.

The checkpoints, one per skill that closes a loop turn:

- `/plan`: after the draft is written and published, before the handoff block.
- `/go`: after Step 3's quality passes, before Step 4 fills in the PR.
- `/handle`: at the end of the lane it runs, before its turn closes.
- `/finalize`: before the PR is marked ready for review.

The subagent may also correct
`.claude/skills/go/delegation-model-capabilities.md` where the review taught
something, per `delegation.md` § "Keeping".

## Decisions

These are recommendations taken as the plan's single approach. None is a fork
the operator has to choose.

1. **Detect the model with `get_session`.** The claude-code-remote MCP tool,
   loaded through `ToolSearch`, reports `session_context.model` and
   `external_metadata.last_served_model`. A session is weak when neither names
   an Opus model. If `get_session` cannot be reached, the session counts as weak
   and the gate runs, because the failure should land on the side of checking.

2. **The judge is an `Agent` with `model: "opus"`.** It runs without a worktree,
   because it reads the session's own tree and edits nothing there except the
   capabilities file. The session blocks on its verdict, so the two never write
   at once.

3. **Five verdicts, best to worst.** The judge picks one and says why. The
   options are stated here in essence, not as wording:
   - A. Passes. Continue.
   - B. Fails with fixable corrections. The session applies the corrections it
     names, then shows the result to the judge again.
   - C. Fails, but the session has fixed it already and can continue without
     another round.
   - D. Fails, and the work is too hard for this model. The session applies the
     fixes, then relays the rest to an Opus session.
   - E. Fails, and the session cannot fix it. It relays at once.

4. **Re-showing reuses the judge.** `SendMessage` continues a spawned agent with
   its context intact (the `Agent` tool's own description), so a B verdict goes
   back to the same judge. If that agent is gone, a fresh Opus agent gets a
   brief carrying the first verdict and its reasons.

5. **Relay goes through `/relay park`.** It writes the summary and starts no
   session. The session then calls `create_session` with `model` set to the Opus
   model's ID and the prompt `/relay take <branch>`. That keeps `/relay`
   unchanged, at the cost of a model argument that `/relay` itself does not
   take.

6. **A judge that cannot be launched is a stop, not a pass.** The session
   reports that the gate did not run and ends the turn. Passing silently would
   undo the point of the gate.

7. **The shared procedure lives in one file.**
   `.claude/skills/go/quality-gate.md` holds detection, verdicts, the judge
   brief and the relay path. `go`, `plan`, `handle` and `finalize` each carry
   one pointer line at their checkpoint, the same shape `delegation.md` already
   uses.

## Steps

1. Write `.claude/skills/go/quality-gate.md` with the decisions above.
2. Add one pointer line at the checkpoint in each of `go/SKILL.md`,
   `plan/SKILL.md`, `handle/SKILL.md` and `finalize/SKILL.md`. Body edits only,
   so the skill descriptions and the staging rule do not come into play.
3. Read `handle/SKILL.md` and `finalize/SKILL.md` in full before placing the
   pointers, to find the step that closes each turn.
4. Run the vet suite and the skill catalog check, which cover the new
   cross-references.

## DRY notes

- **Shared.** The checkpoint procedure exists once, in `quality-gate.md`. The
  four skills point to it and repeat none of it.
- **Reused.** `get_session` for detection, `Agent` and `SendMessage` for the
  judge and its re-show, `/relay park` and `create_session` for the relay, and
  the `delegation.md` keeping procedure for the capabilities file.
- **Declined.** A helper script for model detection. It is one tool call, and a
  script would add a file the loop has to keep in step with the MCP tool name.
  The judge itself is a model call, so no code can stand in for it.

## Open questions

None. Each decision above carries its recommendation. If the operator wants a
different checkpoint for `/go`, the change is one pointer line in `go/SKILL.md`.
