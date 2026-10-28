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

Operator's decisions (session, 2026-10-28):

- the trigger is a bare `/merge` only;
- a decline passes the prompt to the agent silently, with no context added,
  since to the agent it is an ordinary `/merge` either way;
- the gate sits on `UserPromptSubmit`, the first event a prompt reaches, so a
  mergeable PR is merged before anything else gets a say.

A probe on `claude` 2.1.312 confirmed that a hook's `decision: "block"` makes no
API request (`total_cost_usd: 0`, `num_turns: 0`). It also confirmed that
`hookSpecificOutput.suppressOriginalPrompt: true` drops the
`Original prompt: /merge` tail from the block message.

## Design

### Where it lives

The layout copies the cold-cache guard: `.claude/merge-gate/` holding
`hooks/merge_gate.py` (stdlib only, Python 3.9+), `test_merge_gate.py`, and a
`CLAUDE.md` that carries the contract. It is registered in
`.claude/settings.json` under `UserPromptSubmit` with `timeout: 120`, because a
merge plus the feedback export takes longer than the 30 s default.

The gate acts only when `prompt.strip() == "/merge"`. Any argument, such as
`/merge #12` or `/merge no vet`, goes to the agent.

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

**A decline prints nothing, so the prompt reaches the agent as typed.** The same
path takes an exception in the gate, whose traceback goes to stderr. This is not
a swallowed error, because the gate is an optional fast path in front of
`/merge`. The agent's `/merge` re-checks everything the gate checked and runs
into the same failure, which it reports.

### After a merge

The gate blocks with the merged line and `suppressOriginalPrompt`, and writes
`tmp/merge-gate/<session>.json` (`pr`, `base`, `sha`). A blocked prompt never
reaches the model, so the next turn would otherwise start unaware that the PR
had landed. The next prompt that does not carry the keepalive's
`Cache keepalive` mark makes the gate add one line of context ("Before this
prompt, the merge gate squash-merged #<n> into <base> at <sha>; the PR is no
longer a place to do work"). It then deletes the record.

### The cold-cache guard

Hooks of one event run in parallel (code.claude.com/docs/en/hooks), so the
cold-cache guard cannot know whether the gate merged. If both acted on a bare
`/merge`, a merged prompt could come back with a price stop beside it. So the
gate owns both outcomes:

- **`cold_cache.py` passes a bare `/merge` while
  `.claude/merge-gate/hooks/merge_gate.py` exists.** A repository that removes
  the gate gets the guard back on `/merge` without editing anything.
- **On a decline, the gate runs the guard itself.** It loads `cold_cache.py` by
  path, the way the ledger's lib is reached, calls its `on_prompt` with the same
  event, and blocks with the guard's stop when the guard would. A declined
  `/merge` on a cold cache therefore gets the same price stop as any other
  prompt, and the guard's `!` resends `/merge` to the agent. A merged one
  re-caches nothing and needs no stop.

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

- each of the seven checks declining on its own, with no output;
- a full pass that runs `gh pr merge` with the exact subject, body file and
  `--match-head-commit`;
- a refused merge, which declines;
- an argument, which is a no-op;
- the attestation parser against every alternative in `attest.md`'s fenced
  templates, read from that file, so the template and the parser cannot drift
  apart unnoticed;
- the cold-cache handoff in both directions: the guard passes a bare `/merge`,
  and the gate returns the guard's stop on a decline with a cold cache;
- the after-merge note delivered once, and not consumed by a keepalive wake.

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

## Out of scope

**The keepalive parking a session whose PR has landed** is
vzakharov/muthur#237's. Its wake finds no live watcher, asks `gh pr view`, and
skips the park on a merged PR, which covers a gate merge as it covers an
agent-run `/merge`. The gate needs nothing of its own for it.

## Open questions

Each one has a recommendation, and the plan above is written with it in force.

1. **A PR finalized with `/finalize no vet`**, the mode for changes with no code
   to check, where the vet run is skipped. `/merge` asks the agent to confirm
   that skipping was right for this diff, which is a judgement.
   - (a, recommended) The gate leaves these PRs to the agent.
   - (b) The gate trusts the mode and merges.
2. **The attestation line
   `CI-only buckets — /test-on-gh is an unhydrated stub`.** It means the project
   has no CI-only tests set up, and every attestation in this repo carries it.
   Read literally, `/merge` stands down on any bucket left undispatched for a
   reason other than "the diff doesn't reach it", which would leave the gate
   never merging here.
   - (a, recommended) The line counts as green.
   - (b) The line declines.
