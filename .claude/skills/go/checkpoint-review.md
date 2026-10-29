# Checkpoint review by Opus

A session on a model below Opus drives the loop as far as an Opus one does, and
nothing stronger looks at its work before the operator does. So each cutoff —
`/plan`, `/go` and `/finalize`, each saying where in it — hands what the skill
run produced to an Opus subagent, which passes it, has it revised, fixes it, or
sends the work on to an Opus session.

## Who runs it

A session whose **serving** model is Sonnet or Haiku: the one its system prompt
says it is powered by, or, where no line says,
`external_metadata.last_served_model` from `get_session` called with no id.
Serving rather than configured, because the review is for whoever did the work,
and a fallback mid-session changes that. A session on Opus or Fable skips this
file.

## The brief

`Agent` with `model: "opus"`, no `isolation` — the reviewer reads and fixes the
session's own tree — and `run_in_background: false`, since the session's next
step is the verdict. The brief is all the reviewer knows:

- **What ran and what for** — the skill, and what it answered: the plan file's
  path, the task as the operator asked it for a planless `/go`, the PR number
  for `/finalize`.
- **What to read** — the skill run's own commits, `git diff <from>..HEAD` with
  `<from>` the head before the run's first commit, and
  `git diff origin/<base>...HEAD` for the branch around them.
- **The question** — does this pass the repository's quality bar: `CLAUDE.md`,
  the skill that ran, and the plan where there is one, held as the reviewer
  would hold its own work.
- **The verdicts** below, and that its reply's first line is `VERDICT: <one>`.
- **What it may change** — it commits what it fixes, under the repository's
  commit conventions with a body saying the checkpoint reviewer made the fix,
  and never pushes. It may also rewrite the session model's entry in
  `delegation-model-capabilities.md`, per § "What the reviewer learns".

## The verdicts

Best to worst; the reviewer picks one.

1. **`pass`** — the session carries on with the skill.
2. **`revise`** — what to change, stated by substance rather than as text to
   paste. The session makes the changes, commits, and asks the **same** reviewer
   to look again with `SendMessage` to its agent id (load it through
   `ToolSearch` when only its name is listed), saying which look this is. A
   third look cannot answer `revise`: there the reviewer fixes the rest itself
   or escalates, since by then telling the session what to do costs more than
   doing it.
3. **`fixed`** — the reviewer made the fixes; the session carries on.
4. **`fixed, relay`** — the reviewer made the fixes, and the work is beyond the
   session's model. The session finishes the skill's remaining steps, then runs
   `/relay` (`@.claude/skills/relay/SKILL.md`) with no argument, so the Opus
   successor takes the operator's next message.
5. **`relay`** — the reviewer cannot fix it: a subagent lacks a tool the fix
   needs, or the fix needs the operator. The session runs `/relay` at once, its
   argument the reviewer's findings to act on, followed by the skill to re-run
   where the cutoff was `/finalize`.

Either relay is an escalation, which `/relay` Step 3 starts on Opus.

The session pushes after any verdict that left commits, and its report names the
verdict in a line — with the successor's link for 4 and 5.

## What the reviewer learns

`delegation-model-capabilities.md` holds what each model below Opus handles and
misses. A checkpoint review is evidence about the same model running the loop
itself, so the reviewer folds what it found into that model's **Handles** and
**Misses** under the file's own keeping rules
(`@.claude/skills/go/delegation.md` § "Keeping
`delegation-model-capabilities.md`"), and what holds for every subagent — a tool
none of them has — into its § "Across models". It commits that with its fixes,
or alone after a `pass` that taught something.
