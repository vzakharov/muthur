# Delegating sub-tasks to weaker models

In `/go`'s Step 2, hand a sub-task you judge clear to a cheaper model working in
its own worktree, and review what it produces before it reaches the branch. The
point is spending your own context and tokens on the parts that need judgement.

## What qualifies

A sub-task qualifies when its brief leaves nothing to decide: the files, the
shape of the change and the check that proves it done are all nameable before it
starts. A test suite for a contract already written, a mechanical change across
many files, a script whose interface is fixed, a data file in a known format.

It stays with you when any of these hold:

- it carries a design call, or a fork the plan left open;
- it is prose the loop executes — skills, rules, `CLAUDE.md` — or prose a person
  reads to decide something;
- it is authorization or permission code;
- writing the brief would take about as long as doing it, or the brief would
  have to explain most of the conversation;
- it is too small for the saving to beat the brief and the review — § "Weighing
  the cost" below, and what the model's entry says it cost last time.

Delegating is a judgement, never a quota: a task with nothing that qualifies is
done in-session without comment.

## Picking the model

`delegation-model-capabilities.md` beside this file is the summary of what each
model has handled. Read it before the session's first delegation — the hook's
delivery counts as that read — and pick the cheapest model whose entry covers
this kind of work. A model with no entry for it gets a small, easily checked
piece first.

## Launching

`Agent` with `model:` set and `isolation: "worktree"`, so it works on its own
copy. That copy starts from the default branch, not yours: commit what it needs
to build on, and have the brief's first step be `git merge --ff-only <sha>` onto
that commit. Independent sub-tasks launch together, in the background, while you
carry on with work that does not touch their files. The brief is all it knows:

- the goal and the files, including which ones to read first as the contract or
  the style reference;
- the acceptance check, stated as a command it runs until it passes;
- the `CLAUDE.md` rules the work could break — no lint suppressions,
  `Read`/`Edit`/`Write` over shell edits, comments that state the contract
  rather than narrate the change;
- that it commits in the worktree and never pushes;
- that a defect it finds outside its files is reported in its final message, not
  fixed.

## Reviewing and merging

Its result is a stranger's PR. Read `git diff HEAD...<its branch>` whole, run
the acceptance check yourself, and hold it to the standard of your own commits.
Review from your own tree — `git diff`, `git show <its branch>:<path>` — never a
`Read` under `.claude/worktrees/`, which loads that copy's whole skill listing
into your context. Fix what is wrong — a follow-up message to the same agent for
a slip in its own brief, your own edit for anything else.

Land it with `git merge --squash <its branch>` and one commit whose body names
the model that wrote it and what the review changed, so the operator reads a
linear history; then `git worktree remove` it and delete its branch. Its branch
is never pushed.

A result needing more repair than the sub-task would have cost to write is
discarded and done in-session.

## Weighing the cost

After each delegation, put what it cost beside what doing it yourself would have
cost. `python3 .claude/costs/delegation.py <agent-id> --turns <n>` prints both
at `.claude/costs/prices.json` rates, `<n>` being the turns you would have taken
— the one figure that is your judgement, since a stronger model often needs
fewer than the subagent did. It also prints what each later turn of yours
re-reads either way; multiply by the turns the session has left. Your review is
in neither figure, so charge it to the delegation by eye.

Where the script is not in the tree, weigh the same terms by eye: the subagent's
turns re-reading a context growing toward its `subagent_tokens`, against its
output at your rate plus your context re-read on each turn you would have taken.

The verdict goes into the model's entry in `delegation-model-capabilities.md`,
and what it teaches about every model into that file's § "Across models". Say
which turn count you assumed wherever you report it.

## Keeping `delegation-model-capabilities.md`

After a review that taught something — a kind of work the model handled cleanly,
a mistake it made, a brief wording that prevented one, what it cost against
doing it in-session — rewrite that model's entry in place and commit it with the
work it came from. An Opus reviewer keeps the same file the same way after a
checkpoint review (`checkpoint-review.md` beside this file). It is a compressed
summary, not a log: fold the new observation into what the entry already says,
replace what it contradicts, and drop detail that no longer changes which model
you pick or how you brief it. Stay under 100 lines; `scripts/vet.sh` fails it
past that.

**An entry names the kind of work, never the task.** "A unittest suite against a
hook" holds in any repo; a branch, file, PR or case count does not, and every
repo that adopted this loop folds the file into its own on each sync
(`@.claude/skills/update-muthur/SKILL.md` § "Step 5 — Apply by intent, not by
patch").
