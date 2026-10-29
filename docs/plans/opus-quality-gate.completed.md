# An Opus quality gate for sessions on a weaker model

## Task

Вова's ask, in substance: a session running on a model below Opus asks an Opus
subagent, at each cutoff of the loop (`/plan` where there is one, `/go`, any
later `/go` or `/handle`, `/finalize`), whether what it just did passes quality.
The subagent answers with one of five verdicts, best to worst:

1. yes;
2. no — make these changes (by substance, not verbatim) and show me again;
3. no — I fixed it, carry on;
4. no — I fixed it, but the work is too hard for you: after the fixes, relay to
   a new session on Opus;
5. no — I cannot fix it (a limit of subagents as such, say): relay now.

The subagent may also edit `delegation-model-capabilities.md` from what it saw.
This branch dogfoods it: its own `/go` cutoff runs the gate.

## Approach

One procedure in one new file, four pointers to it.

- **`.claude/skills/go/review-gate.md`** (new) owns everything: who runs it, the
  cutoffs and the range each reviews, the reviewer's brief, the five verdicts
  and what the session does on each, the round cap, the relay.
  - **Who:** a session whose serving model is below Opus. The serving model is
    `get_session`'s `external_metadata.last_served_model` on the web (the
    runtime can fall back from the configured one), the system prompt's model
    line elsewhere. Opus and above are exempt; an undeterminable model is exempt
    and says so. `MUTHUR_OPUS_GATE=off` switches it off, as
    `MUTHUR_DELEGATION=off` does for delegation.
  - **Reviewer:** `Agent`, `model: "opus"`, foreground (the session has nothing
    to do meanwhile), no worktree isolation — it must edit this branch. The
    brief carries facts, not the session's own verdict (a reviewer handed a
    conclusion tends to confirm it): the operator's words verbatim, the plan
    path, the commit range, the pointer to CLAUDE.md. It commits what it fixes,
    never pushes, and replies with
    `VERDICT: <pass|revise|fixed|fixed-relay| relay>` on the first line.
  - **`revise`:** the session makes the changes and re-shows them to the same
    reviewer through `SendMessage` on its agent id, or to a fresh one with the
    earlier verdict in the brief where the first cannot be continued. Three
    `revise` rounds without a `pass` count as `relay`.
  - **`fixed-relay` / `relay`:** the session runs `/relay` with the reviewer's
    findings in the summary, the successor started on Opus.
  - **Capabilities file:** the reviewer rewrites the session model's entry in
    place, under `delegation.md`'s keeping rules, and commits it with its fixes.
- **Cutoffs**, each one pointer line, itself conditional on the model so an Opus
  session never loads the file:
  - `/plan`: after the PR is published, before the handoff block. A plan the
    same session goes on to implement (`/task` outcome 3) is left to `/go`'s
    gate.
  - `/go`: the end of Step 3, after `/polish`, before the plan flips to
    `*.completed.md` — a relay must leave it `*.paused.md`. An elephant's bite
    end is a Step 3 run, so it is gated too. `/handle`'s plan and review lanes
    run `/go`, its plan-review turn ends in `/plan`, so every `/handle` cutoff
    already passes through one of the two and `/handle` itself gets no pointer.
  - `/finalize`: straight after the `/polish` pass, before step 1. A fix after
    the vet run would make the vet, the base merge, the squash body and the
    attestation's SHA statements about a diff that moved; the quality passes are
    where `/finalize` already puts everything that changes the diff.
- **`/relay` Step 3** gains one clause: a relay the gate asked for starts the
  successor on Opus (`create_session`'s `model`; `--model` in the local recipe).
- **`delegation.md` § "Keeping …"** and the capabilities file's intro name the
  gate's reviewer as a second writer of the entries, and what an entry then
  records: how the model fared as the session's own driver, beside how it fared
  as a delegate.
- **Catalog:** `/go`'s entry in `catalog/g2-pr-loop.md` names `review-gate.md`
  and its `MUTHUR_OPUS_GATE` switch.

## Calls made without asking

- **Placement at `/finalize`** is before the vet run rather than after the
  attestation as the ask reads literally; the reason is above.
- **No new skill.** A skill's description loads on every turn of every session,
  and this one runs only on weak ones; a file the pointers load on demand costs
  the strong sessions nothing.
- **Reviewer fixes vs `revise`:** the reviewer fixes itself only what is cheaper
  for it to do than to describe, or where the weak model's mistake says it would
  repeat; otherwise `revise` — spending Opus tokens on work Sonnet can do is the
  cost the gate exists to avoid.

## DRY notes

- The procedure lives once, in `review-gate.md`; `/plan`, `/go` and `/finalize`
  carry a pointer and the model condition only, and `/handle` inherits through
  the skills it runs.
- The capabilities file is reused as the reviewer's output rather than a new
  verdict log, and `delegation.md`'s keeping rules (kind of work not task, the
  100-line cap `scripts/vet.sh` enforces) apply unchanged by citation.
- The relay mechanics are `/relay`'s; the gate adds only the model argument.
  `/polish`'s scoping (since the last `polish:` commit) is not reused for the
  gate's range, since `/plan` has no polish to key on; the gate's range is
  stated once, in its own file.

## Checklist

- [ ] `.claude/skills/go/review-gate.md`
- [ ] pointers in `plan`, `go`, `finalize`; the clause in `relay`
- [ ] `delegation.md` and `delegation-model-capabilities.md` wording
- [ ] catalog entry
- [ ] `./scripts/vet.sh`'s skill-catalog and markdown checks pass
- [ ] dogfood: the gate runs on this branch at `/go`'s Step 3
