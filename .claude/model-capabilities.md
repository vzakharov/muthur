# What the models below Opus can and cannot do

One entry per `model:` value `Agent` takes below the delegating agent's own,
kept per `go/delegation.md` § "Keeping `.claude/model-capabilities.md`" by two
writers: the session that delegated to the model, and the Opus checkpoint
reviewer (`go/review.md`) of a session on it. The lessons that hold for every
model come first.

## Across models

- **Cache reads set the floor.** Most of a delegated run's cost is cache reads,
  and at `.claude/costs/prices.json` rates Sonnet 5.5 reads its cache for what
  Opus 5.5 does. The saving is in output tokens and in the delegator's context
  staying small, so a sub-task of a few hundred lines costs more delegated than
  done in-session. Recheck when the rates change; Haiku 5.5 reads at a twentieth
  of Opus 5.5's rate, a quarter once its prompt passes 100k tokens.

## sonnet

- **Handles:** a unittest suite against a hook written as the contract, in a
  named reference's style — needed one rename the brief could not have known;
  went past the brief with sound extra cases. Reworking an existing suite
  against two changed hooks, with its fixture split into a shared module, came
  back clean with nothing to repair. Driving a short review-lane run of the loop
  itself: a review thread answered with a fix checked against the code, the
  `/go` checkpoint review run where no hook forced it, a reviewer brief of facts
  only. A plan's shape — every point of the request mapped to a part, DRY notes,
  a claim settled by a cheap probe rather than assumed. A `revise` of three
  findings across the PR body, the squash proposal and its comment, and three
  thread replies, applied whole in one round, the replies opening with the
  session's words as `CLAUDE.md` asks. Implementing a plan's remaining parts
  after a relay — a gate moved from session state to git with throwaway-repo
  tests, a reviewer launched with exactly the one line its skill gives. A batch
  of review comments on skill prose answered in one round, a renamed commit type
  followed through every hook, test, catalog entry and skill naming it. New
  TypeScript modules from a brief in parallel worktrees: a DOM pan/zoom port, a
  packing algorithm, a Myers line diff tested against `git diff`, a git-plumbing
  collector — each green on its acceptance commands, its surprises reported. A
  3,000-line port of a checker suite to another toolchain, a framework's parts
  cut and its tests re-fixtured, each checker proved on planted violations. A
  lint rule ported from another repo onto the local alias, its findings fixed as
  the rule asks. A six-part UI plan in one session — a stored-doc migration, a
  top-layer popover, a time-grouped scale — green and browser-checked.
- **Misses:** planning a reader for an undocumented record format, it drew the
  shapes from the one existing reader it opened and missed those other readers
  in the tree already handle; and it scoped a new gate by a state that holds for
  the whole skill run rather than the moment the gate guards. Rewriting a plan
  from its own recorded analysis, it widened that gate again (the analysis keyed
  it on the prompt's first line, the plan on any mention of a path) and left a
  one-line requirement with no mechanism behind it. Moving that gate's state
  from the session to git, it made the gate branch-wide (denying a flip the
  session's own cutoff never covered), and its exemptions named commits that
  land after the guarded command while missing the ones before it; adding a
  verdict, it stated the gate's state after it from one case, missing the one
  where an earlier review had already opened it. After an Opus review it edited
  the plan's text again unreviewed, judging the edit too small; and dropping a
  part of the design, it changed the plan alone, leaving the PR body, the squash
  proposal and the thread replies that promised the part saying it was still in;
  renaming a planned module, it left the old name in the PR body and the squash
  proposal. Polishing a fix it made for a review thread, it cut as a duplicate
  the very clause the operator had asked for there. At a plan's gate it took a
  "go" left as an artifact comment for the go-ahead, named the plan an elephant
  without the sections that make one, and chose a scale (log of each commit's
  age) that does the opposite of the operator's example. Moving code onto a
  shared helper, it passed its own callback where the helper calls back with the
  arguments in the other order, on a path no test ran; turning one stored value
  into a list, it missed the reverse of a state the old value reached by
  carry-over, and browser-checked a toggle without pressing it twice. Under
  strict index checks it reaches for a cast rather than reshaping the code,
  keeps dead exports a "port as is" brief covers, and runs its own typed output
  back through the boundary schema. Ask it to list every reader of the format,
  and, for a gate, every commit and session that reaches the guarded command, in
  the order the skills make them; on a rewrite, to diff the plan against the
  analysis it carries out; on dropping or renaming a part, to grep every place
  that describes the change for it; on a refactor, to test each path it moved;
  on a scale, to run the operator's own example through it; on a polish cut, to
  check it against the review threads open on those lines.
- **Brief:** naming the style reference and the run-until-green command was
  enough; ask for "anything that surprised you" — it reports useful edges.
- **Cost, by eye:** that suite, a few hundred lines, cost about twice as much
  delegated as written in-session; the rework ran to about 137k subagent tokens.
  New modules of 500–1,000 lines with tests, from a cold brief, cost about
  two-thirds of in-session (8–10 turns assumed), the review included by eye; the
  3,000-line port, about four-fifths (25 turns assumed); a 2,700-line page
  assembly, about two-thirds (22 turns assumed). Both skipped linters their base
  tree did not yet have, so their review carried a lint pass.

## haiku

Seen so far driving a session under an Opus reviewer, not yet as a subagent.

- **Handles:** a list of named corrections sent back to it, each applied as
  given, in one round.
- **Misses:** an instruction that needs interpreting: restating a nuanced spec
  in its own words, it lost who acts.
- **Brief:** quote the spec it works from — the operator's words, where the task
  is theirs — rather than paraphrasing it, and leave nothing to interpret; for a
  correction, the defect and its fix named exactly — it fixes what is named and
  does not look for the same defect elsewhere.
