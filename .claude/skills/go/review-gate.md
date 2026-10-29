# The Opus quality gate

A session served by a model below Opus does not vouch for its own work. At each
cutoff of the loop it hands that work to an Opus subagent, the **reviewer**,
asks whether it passes the quality bar, and acts on one of five verdicts. The
cutoff's report waits for the verdict.

## Who runs it

A session whose serving model is below Opus — Sonnet, Haiku. Opus and anything
above it are exempt and never load this file: each cutoff's pointer carries the
model condition, so reading the pointer is the whole cost to them.

The serving model is not always the configured one, because the runtime falls
back and operators switch mid-session. On the web, `get_session` with no id
gives `external_metadata.last_served_model`, which wins over
`session_context.model`; elsewhere the system prompt names the model. A model
that cannot be determined is exempt, and the cutoff's report says the gate was
skipped for that reason. `MUTHUR_OPUS_GATE=off` skips it silently.

## Where it runs

- **`/plan`** — after the plan is published, before the handoff block. It
  reviews the plan file and what it proposes. A plan this session goes on to
  implement (`/task`'s outcome 3) waits for `/go`'s gate, which reads the plan
  too.
- **`/go`** — the end of Step 3, after `/polish`, before the plan flips to
  `*.completed.md`: a relay has to leave it `*.paused.md`. An elephant's bite
  end is such a Step 3, so each bite is gated.
- **`/finalize`** — straight after its quality passes, before step 1. Anything
  the gate changes after the vet run would make the vet, the base merge, the
  squash body and the attestation's SHA statements about a diff that moved.
- **`/handle`** has no cutoff of its own: its plan and review lanes end in `/go`
  or `/plan`, and `and finalize` ends in `/finalize`.

**The range is what this cutoff produced**: the commits since the last gate that
passed in this conversation, else since `git merge-base origin/<base> HEAD`.
Everything is committed first. The reviewer may read beyond the range for
context.

## The reviewer

`Agent` with `model: "opus"`, in the foreground — the session has nothing else
to do meanwhile — and **without** worktree isolation, since it must be able to
edit this branch. Its brief is all it knows:

- the operator's request verbatim, and the plan path if one exists;
- the range, and the cutoff it ends;
- to read `CLAUDE.md` and judge the work against it and against the plan: the
  ask met in full, nothing silently dropped, no defect a polish pass or a vet
  run would not catch, prose that states the contract rather than narrates the
  change;
- the five verdicts below, and that its reply opens with
  `VERDICT: <pass|revise|fixed|fixed-relay|relay>` on its own line;
- that it commits what it fixes under CLAUDE.md § "Git conventions", never
  pushes, and names no model in a commit or a file.

The brief carries facts and not the session's own opinion of its work: a
reviewer handed a conclusion tends to return it confirmed.

## The verdicts

Best to worst.

1. **`pass`** — the work holds. Continue to the cutoff's report.
2. **`revise`** — the work does not pass and the fix is within the session's
   reach. The reviewer lists the changes by substance, never as code to paste,
   and the session makes them, commits, and **shows the reviewer again**:
   `SendMessage` to the same agent id, or where it cannot be continued, a fresh
   reviewer whose brief adds the earlier verdict and the changes since. Three
   rounds without a `pass` count as `relay`.
3. **`fixed`** — the reviewer fixed it itself and committed. The session reads
   `git log` and `git diff` over what changed, then continues. The reviewer
   prefers `revise` to fixing: Opus tokens spent on work the session can do are
   the cost the gate exists to avoid. It fixes itself where the fix is cheaper
   to do than to describe, or where the session's mistake says it would repeat.
4. **`fixed-relay`** — fixed, but what is left is too hard for this model. Relay
   after the fixes.
5. **`relay`** — the reviewer cannot fix it, for any reason of its own — a limit
   of subagents as such, a flaw that needs the conversation's context. Relay at
   once.

**A relay is `/relay`'s** (`@.claude/skills/relay/SKILL.md`), with the successor
started on Opus, and the reviewer's findings copied into the summary whole — the
successor never sees the subagent's transcript. The Next step is the work the
cutoff would have ended, resumed from those findings.

**A gate that cannot run** — `Agent` refuses `model: "opus"`, say — is reported
at the cutoff with its reason, and the cutoff's report goes on without a
verdict.

## What the reviewer teaches the model notes

The reviewer rewrites the serving model's entry in
`@.claude/skills/go/delegation-model-capabilities.md` in place, under
`delegation.md` § "Keeping `delegation-model-capabilities.md`", and commits it
with its other changes: the kind of work the model passed or failed here, never
the task. A pass with nothing to add leaves the file alone.

## The report

One line at the cutoff's report: that the gate ran, the verdict, and how many
rounds it took. A relay's report is `/relay`'s.
