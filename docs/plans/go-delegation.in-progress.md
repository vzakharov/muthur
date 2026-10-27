# `/go` delegates clear sub-tasks to weaker models in worktrees

## The ask

In `/go`'s execution step, the Opus agent running it spots sub-tasks it judges
clear and judgement-free, hands each to a subagent on a weaker model working in
its own git worktree, and reviews — and where needed fixes — the result before
merging it into the branch. It keeps a file of what each model can and cannot
do: read before the session's first delegation, corrected as it learns, a
compressed summary of at most 100 lines.

An environment variable switches all of it off, and "off" means `/go` behaves as
if delegation had never been written — not "delegation is forbidden". So the
procedure lives in a file beside the skill, and `SKILL.md` carries only a
conditional pointer to it; a hook delivers the file when the skill loads, so the
agent spends no round trip fetching it.

## Shape

### 1. The switch — `MUTHUR_DELEGATION=off`

Follows the repo's existing opt-out convention (`MUTHUR_CACHE_KEEPALIVE=off`,
`MUTHUR_COLD_CACHE_GUARD=off`) rather than bare presence, so an empty or
leftover variable does not silently change behaviour. Unset → delegation on.

### 2. `.claude/skills/go/delegation.md` — the procedure

Self-contained, loaded only when the switch is not off. Covers:

- **What qualifies.** A sub-task whose spec fits in a brief with no judgement
  left to make: the files, the shape of the change and the acceptance check are
  all nameable up front (a test file for a written contract, a mechanical rename
  across files, a script whose interface is fixed). Anything touching design,
  prose the loop executes, authorization code, or a call the plan left open
  stays with the Opus agent.
- **Picking the model** against `models.md`, cheapest that the notes say handles
  the kind of work; no note → try the cheaper one on a small piece.
- **Launching.** `Agent` with `model:` and `isolation: "worktree"`; the brief
  states goal, files, constraints from CLAUDE.md that bite (no suppressions,
  Read/Edit/Write, no narrating comments), the acceptance check, and "commit in
  the worktree, do not push". Independent sub-tasks launch in parallel.
- **Reviewing before merge.** Read the worktree branch's diff against the
  feature branch as if it were a PR from a stranger; run the acceptance check;
  fix what is wrong — in the worktree before merging, or as a follow-up commit
  naming what was fixed. Land with `git merge --squash <worktree-branch>` and
  one commit whose body names the model that wrote it, so the operator reads a
  linear history; then remove the worktree and its branch. Never push the
  worktree branch.
- **When it goes badly.** A result that needs more fixing than writing it would
  have taken is discarded and done in-session — and that is a note for
  `models.md`.
- **Updating `models.md`** after each review that taught something: rewrite the
  model's entry in place rather than appending, keep it ≤ 100 lines, commit it
  with the work.

### 3. `.claude/skills/go/models.md` — the capability notes

A compressed per-model summary (`### <model>` → can / can't / brief tips),
seeded with the two models `Agent` accepts below Opus (`sonnet`, `haiku`) and no
observations yet beyond a one-line prior each. Committed, so notes learned on
one branch reach every later session once it lands. The 100-line cap is enforced
by `scripts/vet.sh` (a line keyed on the file existing, so an adopter who
deletes the feature has nothing left for it to find).

### 4. `SKILL.md` — one conditional pointer

In Step 2, one sentence: unless `MUTHUR_DELEGATION` is `off`, follow
`delegation.md` (and `models.md`) — already in context when the hook delivered
them, otherwise `Read` them. Body-only edit, so in place, no staging.

### 5. The hook — `.claude/hooks/go-delegation.py`

Prints `delegation.md` and `models.md` as additional context the first time
`/go`'s body enters a session, and nothing when the switch is off. `/go` is
entered three ways, so three registrations of the one script in
`.claude/settings.json`:

- `PostToolUse` on `Skill` with `skill` = `go` or `implement`;
- `PostToolUse` on `Read` of `.claude/skills/go/SKILL.md` (`/task`, `/handle`,
  `/from-branch … go` reach it this way);
- `UserPromptSubmit` whose prompt starts with `/go` or `/implement` (a typed
  slash command expands without a tool call).

A per-session marker under the system temp dir keeps a second entry in the same
session silent. Tested by `scripts/test_go_delegation.py` (the switch, each
entry shape, the dedupe, non-matching events), which `check-muthur.sh` already
runs as a `scripts/test_*.py`.

### 6. Catalog

Entries for the three new files in
`.claude/skills/update-muthur/catalog/g2-pr-loop.md`, beside `/go`'s own.

### Dogfooding

This branch's own implementation uses it: the hook's test file (a contract the
plan fixes) goes to a `sonnet` subagent in a worktree, reviewed and merged per
`delegation.md`, and what that teaches seeds `models.md`.

## DRY notes

- **Shared:** one hook script serves all three entry shapes; the event-shape
  parsing differs only in where the skill name / path / prompt sits, so it is
  one function per shape feeding one emitter.
- **Reused:** the `MUTHUR_*=off` convention and the `scripts/test_*.py`
  discovery in `check-muthur.sh`; `.claude/hooks/lib.sh` is shell and this hook
  is Python (JSON in, JSON out), so nothing there applies.
- **Not extracted:** a generic "inject a skill's sidecar on load" hook. One
  skill wants it today; a second user would show which parts are actually
  shared.
- **Duplicated on purpose:** none — the pointer in `SKILL.md` names the files
  rather than restating any of `delegation.md`.

## Open questions (recommendations in force)

1. **Switch semantics.** a) `MUTHUR_DELEGATION=off` _(recommended — matches
   every other switch here)_; b) any non-empty value, as literally asked.
2. **Where `models.md` lives.** a) beside the skill, committed _(recommended —
   learning outlives the session and the branch)_; b) gitignored under `tmp/`,
   per machine.
