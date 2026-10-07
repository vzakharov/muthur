> ⛔ **This file describes the source repo, and is never vendored.** Its presence
> is what marks a tree as the template rather than a repo that adopted it —
> `scripts/check-skill-catalog.sh` and `/spinoff` both key on that. If you are
> reading this in a repo that *adopted* this infrastructure, it rode along with
> `.claude/skills/**` by mistake: **delete the file.** Do not prune its rows to
> match your tree — that repairs the symptom (assertion 3 failing on rows you
> can never satisfy) and leaves the sentinel permanently wrong.

# Catalog: what's here, and how much of it you need

The per-item inventory of this repo's agent infrastructure. One row per skill,
script and file, carrying the criteria for deciding whether it belongs in your
repo.

Two audiences:

- **Adopting a subset into an existing repo** — read this alongside
  [`ADOPTING.md`](../../../ADOPTING.md), which owns the procedure. This file owns
  the inventory; it does not restate the steps.
- **`/update-muthur`, on every run** — when a commit at the source adds a skill
  that is in neither your `adopted` nor your `declined` list, the sync reads that
  skill's row here to surface the decision with its criteria attached.

Both audiences read it from a fresh clone of the source repo, which is what lets
the banner's rule hold: no adopter needs a copy, so no copy can go stale.

## How to read a row

| Column | Meaning |
| --- | --- |
| **Item** | `/name` is a skill (`.claude/skills/name/`); anything else is a repo-relative path. |
| **What it does** | The one-liner. Descriptions live here and nowhere else. |
| **Requires** | External conditions and tools that must hold for the item to work at all. |
| **Pulls in** | Siblings it cannot work without. Copy these too; only `@`-references are machine-checked, so see [Closure](#closure-is-not-optional). |
| **Disposition** | `adopt`, `rewrite`, or `never` — see below. |

The **group** is the part a row lives in (`catalog/`) rather than a column: groups partition the
inventory, so every item appears under exactly one, and
`scripts/check-skill-catalog.sh` fails if a skill picks up a second row.

### Three dispositions, not two

- **adopt** — copy as-is.
- **rewrite** — copy the shape, replace the contents for your repo. One row
  carries it: `scripts/vet.sh`, whose exit turns on whether your repo has a stack
  yet, with [`.claude/rules/stack.md`](../../rules/stack.md) the contract's home.
  Elsewhere the word qualifies an **adopt** — `/update-muthur`'s watermark,
  `.claude/voice/`'s `operators/` entries — where the item travels whole and one
  file inside it is yours to write.
- **never** — describes or maintains *this* repo, so it is meaningless in yours.

**`opt-in: ask` qualifies an adopt** whose cost lands on every session and whose
worth turns on what the operator wants rather than on anything in the tree. Such
a row is asked, never inferred from the profile: `ADOPTING.md` Step 2,
`/detemplate` Step 1 and `/update-muthur` Step 4a each put the question with the
row attached, and record the answer so it is asked once. The row itself states
the cost and what a yes and a no each change in the tree.

## Groups

Group membership is the coarse decision; **Requires** carries the orthogonal
conditions, and any row can be escaped individually.

| Group | Adopt when |
| --- | --- |
| [G0 — The sync path](catalog/g0-sync-path.md) | Always, unless you want a one-time snapshot and no future updates. The sync half ships unhydrated: filling in the watermark is what makes it runnable. |
| [G1 — Prose & principles](catalog/g1-prose-principles.md) | Always. Zero external dependencies, no stack assumptions, no GitHub. |
| [G2 — The PR loop](catalog/g2-pr-loop.md) | A change is a branch → PR → squash-merge, on GitHub, with `gh` and `$GH_TOKEN` reachable. **In a web/remote session, needs G4.** |
| [G3 — Issue & backlog](catalog/g3-issue-backlog.md) | G2 **and** work is actually tracked as GitHub issues. Same web-session dependency on G4. |
| [G4 — Remote-session plumbing](catalog/g4-remote-plumbing.md) | Sessions run on Claude Code web/remote. Inert locally — but a **prerequisite** of G2/G3/G5 on the web, not a nicety. Declinable at a stated cost. |
| [G5 — CI & landing](catalog/g5-ci-landing.md) | CI runs on GitHub Actions, reachable via `gh`. `/watch-ci` additionally needs **G4** in a web session, not merely recommends it; the rest of the group works through the proxy unshimmed. |
| [G6 — Stack stubs](catalog/g6-stack-stubs.md) | Per row, and only if you will hydrate it now. |
| [G7 — Session cost ledger](catalog/g7-cost-ledger.md) | **The operator says yes when asked** — never by inference from the profile. |
| [G8 — Context budget](catalog/g8-context-budget.md) | **The operator says yes when asked**, as G7. |
| [G9 — Cold-cache guard](catalog/g9-cold-cache.md) | **The operator says yes when asked**, as G7. |
| [G10 — Cache keepalive](catalog/g10-cache-keepalive.md) | **The operator says yes when asked**, as G7 — and **G7 is a prerequisite**, not a recommendation. |
| [Never](catalog/never.md) | — |

## Closure is not optional

A skill copied without the siblings it `@`-references leaves a pointer to a file
that isn't there, and **that failure is silent**: the agent reads the surviving
prose and skips the step they could not load. Resolve each group's **Pulls in**
column before copying, then run `bash scripts/check-skill-catalog.sh` in your
repo to prove nothing dangles.

**The script proves `@`-references and nothing else.** A sibling read at a fixed
path when the item runs — `operator-voice.sh` `cat`s an entry out of
`.claude/voice/operators/` — breaks as silently as a dangling `@`-pointer, and
the column is the only place that says so.

Four closure facts are counter-intuitive enough to state outright:

- **`/plan` travels with G2 even for a local-only adopter.** A web-session bug is
  what prompted it, so a local repo reasonably assumes it can skip it. Two
  reasons not to. The references: `/go`, `/finalize`, `/propose-issue` and
  `/audit-github-backlog` all cite it, so dropping it means stripping those too.
  And the bug is no longer the point — a plan on disk is reviewable from another
  machine, holds a **DRY notes** section the operator can argue with before any
  code exists, and ends by handing over a copy-pasteable `/go <branch>`
  line that starts the next session with the approval already recorded. Native
  plan mode gives none of that even where it works correctly.
- **`scripts/vet.sh` is not optional within G2.** `/finalize`, `/sync-branch` and
  `/watch-ci` run it, and `/finalize` attests to whatever it reports — so a stub
  exiting 0 over an unchecked stack certifies a run that verified nothing. Hence
  its
  **rewrite** disposition rather than a choice: there is no version of G2 that
  does not run your checks. (Three more skills *name* it — `/go` to say vetting is
  not its job, `/update-muthur` and `/test-on-gh` as an example — so a grep
  overcounts the dependency.) Its three lines calling
  `scripts/check-skill-catalog.sh`, `scripts/check-squash-message.sh` and
  `scripts/check-muthur.sh` are the part a rewrite decides separately;
  the comment above them says what dropping each costs.
- **`/finalize` and `/plan` reach into G3 conditionally, and `/finalize` into G5
  as well.** `/finalize`'s working-artifact sweep cites `/take-issue` and its CI
  steps cite `/watch-ci`; `/plan` cites `/take-issue` for the `#<N>` export and
  its `carving.md` cites `/propose-issue` for the filing, and `/go` and `/task`
  carry the same `#<N>` pointer. Every citation is guarded by a prose condition ("if a
  workflow runs on PRs", "a `#<N>` in the argument"), so the behavior degrades
  gracefully — but the `@`-references still dangle if you decline those groups.
  Strip the citations, or adopt the groups.

  **`carving.md` is the one worth reading before you strip it.** It states the
  filing in full because the carve is one procedure, and cutting it at the group
  line would leave the half you keep stopping exactly where its reader needs the
  next sentence. Declining G3 means stripping the filing half — the
  `/propose-issue` calls, the `sub_issues` link, the `#<tbd>` marker — and
  keeping the judgment: the bar, the seams, the first slice specced in full and
  the rest coarse. Where the remaining slices then live is **yours to decide**:
  in the plan file, in a backlog doc, in whatever tracker you do use. This repo
  writes no degradation path for it, and that is a choice rather than an
  omission — a path written here would be a guess about your tracker.
- **`/override-gh` is pulled in by G0 and G3**, not just G4. See G4 above.

Two G2 rows are adopter choices rather than defaults:

- **`/go` is a local name, not a contract.** It reads ambiguously in a Go
  project, and this is a stack-agnostic template. Rename it to whatever your
  language or framework leaves unambiguous; `scripts/check-skill-catalog.sh`
  verifies the pointers once you have.
- **The `/implement` redirect is worth taking only where `/implement` was already
  the shipped name** — that is where a handoff block in a live plan file or PR
  comment might still say it. Never adopted `/implement` → take `/go` alone and
  put `.claude/skills/implement/` in `declined`: there is no downstream caller to
  redirect, and the stub would be a permanent extra row standing in for a name
  the repo never had. Already adopted it → ask the operator whether the backwards
  compatibility is worth that extra row, and record either answer in
  `watermark.json` so the question does not come back. A **fork** is neither
  case and asks nothing: it carries `/implement` because it carries everything,
  and a tree one commit old has no plan file or PR comment old enough to say it,
  so `/detemplate` deletes it outright.

**The `/issue` redirect is the same choice one group over.** It is worth taking
only where `/issue` was already the shipped name — that is where a handoff block,
a PR comment, or an operator's own muscle memory might still say it. Never
adopted `/issue` → decline the row and put `.claude/skills/issue/` in `declined`:
there is nothing to redirect, and the stub would be a permanent extra row
standing in for a name the repo never had. **A first adoption is that case** —
take `/take-issue` alone, and leave the redirect for a later sync to offer if the
name ever does ship. Already adopted it → take the redirect, since the name
covers two operations with different destinations, and record the answer in
`watermark.json` so the question does not come back. A **fork** is neither case
and asks nothing: it carries `/issue` because it carries everything, and a tree
one commit old has no handoff block or muscle memory old enough to say it, so
`/detemplate` deletes it outright.
Declining
G3 outright takes the redirect with it: its no-number branch names
`/propose-issue`, which you do not have.

## Reverse closure

The same fact read backwards, for the fork that **deletes** a group instead of
declining to copy it: every `@`-reference *into* the dropped group has to be
stripped, or `scripts/check-skill-catalog.sh` reports the dangle. It is worth
counting rather than deriving, because the cost is unevenly distributed and the
expensive half is knowing which mentions to **leave alone**.

The distinction that does the work: a mention is either **guarded** — prose that
reads correctly when the target is absent ("`/test-on-gh`, if the project has
hydrated it") — or an **assertion** that the file exists. Only assertions break.
And a bare `/name` is invisible to the checker either way, so a broken one fails
silently, in prose, forever.

- **Dropping G6** costs exactly **one** `@`-reference edit:
  `.claude/skills/bootstrap-workflow-dispatch/SKILL.md` cites
  `@.claude/skills/test-on-gh/SKILL.md`. Six further files carry **guarded**
  bare-name prose about it that must be left alone — `/sync-branch`,
  `/watch-ci`, `/qa-checklist`, `/pr`, `/finalize` (twice) and `/from-branch`.
  "`/test-on-gh`, if the project has hydrated it" reads correctly when the answer
  is "it hasn't", and editing it makes every future `/update-muthur` diff
  noisier for no behavioral gain.
- **Dropping G5** costs **two** `@`-references, both in `/finalize` and both to
  `@.claude/skills/watch-ci/SKILL.md`, plus **two dead bare names** in
  `/override-gh` — `/watch-ci` and `scripts/ci-watch-tick.sh` — which unlike the
  G6 mentions *assert* that those files exist rather than guarding on it.
  `/bootstrap-workflow-dispatch` references `/watch-ci` as well and needs no
  edit: it is inside G5, so it goes with the group.

## Keeping this file honest

The one-row-per-skill invariant is machine-checked by
`scripts/check-skill-catalog.sh`, so a skill added without a row here fails the
check rather than going unnoticed.
