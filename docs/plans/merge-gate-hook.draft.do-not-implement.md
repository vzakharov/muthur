> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# Merge gate: a bare `/merge` lands a finalized PR without waking the agent

## Goal

When the operator types exactly `/merge` and the branch's PR passes every
mechanical condition of the `/merge` gate, a hook squash-merges it and blocks
the prompt with `✅ Merged #<n> into <base> at <sha>`. No model request is made,
so the operator does not have to open GitHub, and the cache is never re-written
for a click. If any condition fails, or anything errors, the hook steps aside:
the prompt reaches the agent, which runs `/merge` and applies judgement.

Operator's decisions (session, 2026-10-28): the trigger is a bare `/merge` only;
a decline passes the prompt to the agent without bothering the operator.

## What the probe established

These were checked on `claude` 2.1.312 with a throwaway project in the
scratchpad, logging both events:

- **`UserPromptSubmit` runs first and finishes before `UserPromptExpansion`
  starts**, even with a 2 s sleep in the submit hook. A submit-side `block`
  means the expansion never fires.
- **The expansion event for a bare `/merge` carries `command_name: "merge"` and
  `command_args: ""`**, plus the common fields (`session_id`, `transcript_path`,
  `scratchpad_dir`, `prompt`).
- **A `decision: "block"` there makes no API request** (`total_cost_usd: 0`,
  `num_turns: 0`). `hookSpecificOutput.suppressOriginalPrompt: true` drops the
  `Original prompt: /merge` tail from the message.
- Hooks registered for one event run in parallel, per
  code.claude.com/docs/en/hooks. The design does not depend on this, because the
  two hooks it has to order sit on different events.

## Design

### Where it lives

The layout copies the cold-cache guard: `.claude/merge-gate/` holding
`hooks/merge_gate.py` (stdlib only, Python 3.9+), `test_merge_gate.py`, and a
`CLAUDE.md` that carries the contract. Registration in `.claude/settings.json`:

- **`UserPromptExpansion`, matcher `merge`, `timeout: 120`**: the gate. A merge
  plus the feedback export takes longer than the 30 s default.
- **`UserPromptSubmit`**: the after-merge note (§ "After a merge"). It only adds
  context, so running in parallel with the other submit hooks is harmless.

The gate acts only when `command_name == "merge"` and `command_args.strip()` is
empty. Any argument, such as `/merge #12` or `/merge no vet`, goes to the agent.

### The checks

**Every fact comes from GitHub, never from the local checkout**: a container
that woke for this prompt may hold a stale tree. The PR is the open one whose
head is `git branch --show-current`. Checks run cheapest first, and the first
failure declines:

1. **Exactly one open PR from the branch, not a draft.**
2. **The attestation is a full one with every line green.** The PR's last
   `<!-- finalize-attestation <sha> -->` comment (`finalized.MARKER`) names a
   SHA. Its heading is `### Attestation`; a `### Attestation — none required`
   declines, because checking the `no vet` precondition is judgement. Each of
   the three list lines carries one of the values `attest.md`'s template allows:
   - vet: `**green**`, with a trailing parenthetical allowed;
   - CI: `**green` followed by a run link, or
     `**nothing runs on a PR in this repo**`;
   - CI-only buckets: `**dispatched and passed`,
     `**not dispatched: the diff doesn't reach them**`, or
     `**/test-on-gh is an unhydrated stub**`.

   Any other value declines, which covers a red line and a recorded two-shot
   stop. Prose below the list, such as the "Verified ≠ marker" explanation, is
   not parsed: `/merge` already treats a trailing `Verified` SHA as nothing to
   stand down on.

3. **The head is past the attested SHA only by ledger rows.** GitHub's
   `compare/<sha>...<head>` reports `ahead` or `identical`, and every file in it
   is under `.claude/costs/sessions/` (`ledger_branch.PREFIX`).
4. **The base has not advanced.** `compare/<base>...<head>` reports
   `behind_by == 0`, the same fact `/check-merge`'s `contained` reads.
5. **GitHub says mergeable.** `mergeable == MERGEABLE` and
   `mergeStateStatus == CLEAN`. Every check run and status context on the head
   has completed with `success`, `neutral` or `skipped`. An empty rollup passes
   only when the attestation's CI line says nothing runs on a PR. A Claude
   Approvals check, where one runs, is one of these runs.
6. **No feedback is waiting for an answer.** The `## Awaiting an answer` verdict
   from `scripts/gh_export` is `none`. It is computed in memory, so nothing is
   written into the tree, and the harness's Stop check never sees an untracked
   `docs/pr/`.
7. **The squash record reads back cleanly.** There is a comment headed
   `Proposed squash body:` or `Proposed squash title/body:`. Its last fenced
   block is the body, and the body ends on its `Co-authored-by:` line. The PR
   title fits `<type>: … ` within 72 characters, and any title block equals
   `<PR title> (#<n>)`. This is `merge.md` § "Merging"'s read-back, done in
   code. A squash reconcile is not needed: checks 3 and 4 mean the branch has
   not moved since `/finalize` reconciled the record.

Then the merge runs:
`gh pr merge <n> --squash --subject "<title> (#<n>)" --body-file <tmp> --match-head-commit <head>`.
`--match-head-commit` closes the window between checking and merging, in which
someone could push. There is no `--admin` and no `--auto`. If GitHub refuses the
merge, the gate declines like any other failed check.

### Declining

**A decline passes the prompt through and tells the agent why.** It produces no
block, and its `additionalContext` reads, for example: "The merge gate declined
a bare `/merge`: check 4, base advanced 1faba97..0345136". The operator never
sees it. It gives `/merge` a head start, and it shows which check fires in
practice.

The same path takes an exception in the gate. This is not a swallowed error: the
error is handed to the agent as context, and `/merge` then does the work the
gate could not.

### After a merge

The gate blocks with the merged line and `suppressOriginalPrompt`, and writes
`tmp/merge-gate/<session>.json` (`pr`, `base`, `sha`). A blocked prompt never
reaches the model, so the next turn would otherwise start unaware that the PR
had landed. The next **operator** prompt, meaning one not carrying the
keepalive's `Cache keepalive` mark, makes the submit half add one line of
context ("Before this prompt, the merge gate squash-merged #<n> into <base> at
<sha>; the PR is no longer a place to do work"). It then deletes the record.

### The cold-cache guard

Submit runs before expansion, so without a change the cold-cache guard would
stop `/merge` before the gate ever ran. That would hit the very prompt most
often sent after a long gap, the operator back from review. So:

- **`cold_cache.py` lets a bare `/merge` through at submit while
  `.claude/merge-gate/hooks/merge_gate.py` exists.** A repository that removes
  the gate gets the guard back on `/merge` without editing anything.
- **On a decline, the gate runs the guard itself.** It loads `cold_cache.py` by
  path, the way the ledger's lib is reached, calls its `on_prompt` with the
  expansion event, and blocks with the guard's stop when the guard would. A
  declined `/merge` on a cold cache therefore gets the same price stop as any
  other prompt, and the guard's `!` resends `/merge` to the agent. A merged one
  re-caches nothing and needs no stop.

### The keepalive

A watcher started before the merge still wakes later and parks a session whose
PR has landed, spending a full-context summary on nothing. While
`tmp/merge-gate/<session>.json` exists, `keepalive.py`'s wake context therefore
asks for one line ("PR merged; nothing to keep warm"), with no watcher and no
`/relay park`.

### `/merge`'s side

Add one line to the body of `.claude/skills/merge/SKILL.md`: a bare `/merge`
that reaches the skill is one the gate declined, and the decline reason is in
context. The description stays as it is, so nothing needs staging.

## Wiring

- `scripts/vet.sh`: add `merge-gate` to the opt-in loop's directory list, and to
  its header comment.
- Catalog: a group entry under `.claude/skills/update-muthur/catalog/` beside
  `g9-cold-cache.md`, listed in `catalog.md`, so `/detemplate` and
  `/update-muthur` know the gate is a separate opt-in.
- `install-deps.sh` and the environment setup script are unchanged: the gate
  adds no dependency.

## Tests

The tests mock `gh` and the GitHub client at the boundary: `lib.github.Client`
takes a transport. They cover:

- each of the seven checks declining on its own, with its reason in the context;
- a full pass that runs `gh pr merge` with the exact subject, body file and
  `--match-head-commit`;
- a refused merge, which declines;
- an argument, which is a no-op;
- the attestation parser against every alternative in `attest.md`'s fenced
  templates, read from that file, so the template and the parser cannot drift
  apart unnoticed;
- the cold-cache handoff in both directions: a pass at submit, and a stop on a
  declined `/merge` with a cold cache;
- the after-merge note delivered once, and not consumed by a keepalive wake;
- the keepalive's wake context while a merge record exists.

## DRY notes

- **Reused, not reimplemented:**
  - `finalized.MARKER` and `ledger_branch.PREFIX` (the attestation marker and
    the rows' path);
  - `lib.github.Client`, for GitHub access and the injectable transport;
  - `cold_cache.on_prompt`, for the stop on a decline: one guard and one price,
    not a copy;
  - `gh_export`, for the feedback verdict.
- **One small extraction:** the awaiting rows move out of `awaiting_section`
  into an `awaiting_rows()` that the section renders. That way the gate counts
  rows rather than parsing the heading's text. The section's output does not
  change, so `test_export_awaiting.py` pins it.
- **`finalized.holds()` is not reused.** It asks the local git, and the gate has
  to ask GitHub, for the stale-tree reason above. Both run the same predicate
  over different sources, on 4 lines each. A source-agnostic abstraction would
  cost more than the duplicated lines.
- **Mirrored on purpose:** the attestation's allowed values live as prose in
  `attest.md` and as patterns in the gate. The test that reads `attest.md`'s
  template is what keeps them as one contract. The squash read-back lives as
  prose in `merge.md` § "Merging" and as code in the gate. The gate's
  `CLAUDE.md` names `merge.md` as the home, so a change there reaches the gate.

## Open questions

Each one has a recommendation, and the plan above is written with it in force.

1. **Should the decline reason go to the agent as context?**
   - (a, recommended) Yes. The operator never sees it either way.
   - (b) No, a fully silent pass-through.
2. **Should the keepalive skip the park after a merge?**
   - (a, recommended) Yes, at the cost of one more file read in `keepalive.py`.
   - (b) Leave it: the next wake parks a merged session.
3. **A `no vet` attestation:**
   - (a, recommended) Decline, and let the agent check the precondition.
   - (b) Merge on it as on a full one.
4. **`/test-on-gh is an unhydrated stub` on the buckets line:**
   - (a, recommended) Passes. Every attestation in this repo carries it, and
     `/merge` merges on it in practice.
   - (b) Declines, by the letter of "undispatched for any other reason".
