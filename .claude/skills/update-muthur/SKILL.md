---
description: "STUB — not yet hydrated for this project. Pull the agent infrastructure forward from the repo you adopted it from: diff since the watermark, triage commit by commit, port what applies. Hydration is the watermark at `.claude/skills/update-muthur/watermark.json` — the procedure below is usable as written. Use when the user says \"update muthur\", \"update the agent infra\", \"sync muthur\", \"sync the source\", or \"/update-muthur\"."
---

> ⚠️ **STUB.** This skill has no watermark to run on. Before it can be invoked,
> fill in `.claude/skills/update-muthur/watermark.json`: `lastSyncedSha` (the
> source's HEAD when you cloned it), `lastSyncedAt`, and the real
> `adopted`/`declined` sets for your repo. `repo` already names the template,
> and needs changing only if you adopted from a repo that itself adopted from it.
> Delete this banner once you have, and drop `STUB` from the description above.
> If you took a one-time snapshot and do not intend to re-sync, delete the skill
> instead.
>
> **Hydration here is a handful of JSON fields, not a procedure.** Unlike the
> other stubs, every step below this banner is usable exactly as written.

## What this skill is for

A repo that took its agent infrastructure — `CLAUDE.md`, `.claude/`, `scripts/`,
whatever else — from another repo has a **source** that keeps editing those files.
This skill finds what changed there since the last sync, decides commit by commit
what applies here, and ports the ones that do: *pull the vendored agent
infrastructure forward from the repo I took it from.*

This is a path-scoped diff, not a fork merge. It never tries to reconcile whole
histories — it reads a bounded set of paths, commit by commit, and re-expresses
what applies.

**The name is the infrastructure's, not your source's.** `muthur` is where this
skill and everything it syncs came from; the repo it actually pulls from is
whatever `repo` says in the watermark below, which for a spun-off sibling is its
parent rather than the root. So `/update-muthur` in a repo two hops down still
syncs from one hop up.

**The verb splits: the command updates, the fields say synced.** `lastSyncedSha`
and `lastSyncedAt` are on-disk in every downstream watermark, so renaming them to
match orphans every adopter's file at once — and the prose below follows the
fields, not the command.

## The watermark

`.claude/skills/update-muthur/watermark.json` is the state this skill runs on:

```json
{
  "repo": "<owner>/<repo>",
  "lastSyncedSha": "<source HEAD at the last sync>",
  "lastSyncedAt": "<YYYY-MM-DD>",
  "lineage": [
    { "repo": "<owner>/<root>",   "atSha": "<root HEAD when the parent was born>" },
    { "repo": "<owner>/<parent>", "atSha": "<parent HEAD when this repo was born>" }
  ],
  "adopted": [
    "CLAUDE.md",
    "README.md",
    ".claude/",
    "scripts/",
    { "scripts/run-parallel.py": "taken as a POSIX sh port, scripts/run-parallel.sh" }
  ],
  "declined": { ".claude/skills/take-issue/": "we track work in Linear, not GitHub issues" }
}
```

- **`adopted`** — the paths you took, at whatever granularity is true: directories
  or individual files, up to the degenerate everything-case. It is what turns a
  wall of source commits into a handful of candidates.
- **`declined`** — path → why-not. This is what keeps re-sync quiet: without it,
  every sync re-offers every skill the repo already refused.
- **`lineage`** — optional provenance: the whole ancestry, **root first**, so the
  repo actually synced from leads and each later entry is one hop further from
  it. Each entry names an ancestor and its HEAD **at the moment the next link was
  created**. `@.claude/skills/spinoff/SKILL.md` is what writes it, and owns how.

**Where the ancestry is complete, `lineage[0]` names the same repo as `repo`, and
that is not duplication — the two SHAs are different facts.** `lastSyncedSha` is
where this repo has synced *to*, and it advances on every sync; `lineage[0].atSha`
is where it started *from*, and it never moves. They coincide until the first
sync and diverge forever after, which is what earns the field its place: that
first sync overwrites the only other trace of the birth point.

**An empty array means no ancestors; a missing one means nobody wrote them
down.** The root ships `[]`, which is complete. A watermark filled in by hand
from `ADOPTING.md` has no `lineage` at all, and that gap is not recoverable from
anything else in the file — so a partial array, its first entry naming something
other than `repo`, is valid rather than malformed.

**Nothing syncs from `lineage`.** This procedure reads `repo` and `lastSyncedSha`
and nothing else. A sync that walked the ancestry would multiply the triage at
every link, which is exactly the cost `/spinoff`'s always-point-at-the-root rule
declines to pay.

**An `adopted` entry may be a bare path or a single-key `{path: note}` object.**
Both are adopted and both filter the log identically — read the key when an entry
is an object. The note records *how* the path lives here when that is not
verbatim: ported to another language, split across files, generalized past the
source's interface. It is not a soft decline. A path taken with a note still
surfaces every upstream commit that touches it, which is the point — the local
version is a re-expression, so upstream's later changes to the original are worth
reading for the idea even though the file itself never lands. Expect `translate`
rather than `take` on those commits, and treat the note as the standing statement
of what the local re-expression already does differently.

**A declined path is not declined forever.** Most reasons are conditions that can
flip — *no CI yet*, *work isn't tracked as issues yet* — which is why the map
stores prose instead of a bare list, and why reasons are written in the present
tense. **Re-read them on every sync** and re-offer anything whose condition has
stopped holding: a repo that declined the issue skills because it used Linear,
and has since moved to GitHub issues, should be asked again. A reason that says
`"never — …"` is the one that does not need re-reading.

A repo with two sources would make **`repo`** an array. Nothing here precludes
that and nothing here builds it — and it is a separate question from `lineage`,
which is provenance nothing syncs from.

**`lastSyncedSha` is the sync's boundary in the source, not the last commit
taken.** For a whole sync that is the source's HEAD at Step 3; for a slice of a
split one, the last source commit the slice triaged (Step 7). A commit triaged
and skipped is *done*; the reasoning lives in that sync's PR body. A watermark
that only advanced to the last-taken commit would re-surface every skipped
commit on every future run.

**Bump it in the last commit of the sync, never the first.** If a sync is
abandoned midway, an un-bumped watermark costs a re-triage; a bumped one that
merged without its port silently skips commits forever.

## Three invariants

Each holds at every link in the chain, so they live here rather than in the
watermark.

### Never sync the watermark file itself

`watermark.json` lives inside `.claude/`, which is inside `adopted` — so a
naive sync overwrites this repo's watermark with the source's. That silently
repoints the sync at a repo this one may not be able to clone and resets
`lastSyncedSha` to a foreign history. **The failure surfaces one sync later, as
an unresolvable SHA**, by which point the cause is several commits back.

Exclude it unconditionally, whatever `adopted` says.

### Never sync the source's cost rows

`.claude/costs/sessions/` is the source's own ledger — what *its* sessions cost —
and the one path in `.claude/costs/` that is data rather than machinery. A sync
that ported it would add the source's spend to this repo's totals, and no later
report could tell the two apart. Exclude it unconditionally too, whether or not
this repo runs the ledger.

### Judge the diff, not the commit message's "we"

In a chain, commits arrive that the source itself took from *its* upstream,
written in a third repo's vocabulary. A message saying "we do X here" is evidence
about some repo — not necessarily the source, and never automatically this one.
Read commits for intent; never let their first person settle whether the change
applies. Step 5's "apply by intent, not by patch" already points this way; the
chain is what makes it load-bearing.

## Arguments

Two words, order-free, each changing one step. Bare, the sync claims its own
lock and is a task of its own.

- **`claimed`** — another session holds the lock for this sync on this one's
  behalf, so Step 1 skips the claim. The prompt a session spawned from the offer
  gets.
- **`ride-along`** — the sync is part of a task this session is already running,
  not a task of its own, so Step 3a is skipped and Step 8's tail is that task's.
  What a ride-along offer runs.

## Procedure

### Step 1 — Read the watermark, and claim the sync

Read `watermark.json`. Stop and report if it is missing, or if `lastSyncedSha`
is still a placeholder — there is no baseline to diff against, and guessing one
would either re-port work already here or skip work that isn't.

Then claim the lock with `scripts/muthur-sync.sh claim`, so no parallel session
runs a second sync of the same range — unless invoked with `claimed`. A claim
this session already holds, as it does after making the offer, succeeds again. A
claim that exits 3 names who holds the lock — stop and report that, with their
session link, rather than syncing alongside them. `scripts/muthur-sync.sh`'s
header is the lock's reference.

### Step 2 — Clone the source

`gh api` against a different owner's repo 403s even with a valid token, and
`add_repo` refuses cross-owner adds. **Git transport with the same `$GH_TOKEN`
works**, which is the whole trick. (The system prompt may claim `gh` is
unavailable; it is wrong — see `@.claude/skills/override-gh/SKILL.md`.)

```bash
scripts/muthur-sync.sh clone tmp/muthur-source
```

That is a blobless clone with full history, or a refresh of the one the
session-start nudge left there, with its `HEAD` at the source's. Why the recipe
is shaped that way — and why never `--depth` — is in the script's comments.

**Bash `cwd` resets between calls in this harness** — chain `cd <clone> && …` in
every command that needs to be inside it.

### Step 3 — Build the candidate set

```bash
cd tmp/muthur-source && git log --oneline <lastSyncedSha>..HEAD -- <adopted paths>
```

`<adopted paths>` is every entry in `adopted`, taking the single key of any entry
written as an object.

Record `git rev-parse HEAD` **now**, before triage — that value is a whole
sync's boundary regardless of how the triage goes.

**The clone is whole; `adopted` filters only this log.** A commit touching
nothing on the list is never surfaced, which is right while the list is complete
and silent when it isn't: the moment the source puts agent infrastructure
somewhere new — a `.github/` workflow, another top-level directory — it stays
invisible until the list names it. So run the log once unfiltered too (`git log
--oneline --name-only <lastSyncedSha>..HEAD`, skimmed for unfamiliar paths) and
widen `adopted` in the same commit that bumps the watermark.

**A path in neither `adopted` nor `declined` is a decision, not noise** — see
Step 4's `skip (not adopted)` verdict and Step 4a.

### Step 3a — The sync is a task

Hand the candidate set to `@.claude/skills/task/SKILL.md` as the task: the
commits from `lastSyncedSha` to the recorded HEAD, with their titles. Steps 4–7
are how the work gets done in whichever outcome `/task` picks — including a
split across sessions, an elephant or a pizza, when the lag is too long for one.
A split cuts the candidates in source order, each slice or bite ending on a
commit of the source's first-parent line — Step 7's boundary.

**Invoked with `ride-along`, skip this step.** The session is already inside a
routed task, and a lag of a commit or two fits in it by definition; handing the
sync to `/task` would route a second task inside the first.

### Step 4 — Triage each candidate, from its commit message first

Sources tend to write long commit messages that state the rationale. The message
usually settles relevant-vs-not before any diff is opened, so read it (`git log
-1 --format=%B <sha>`) before `git show` — subject to the "judge the diff" caveat
above. Verdicts:

| Verdict | Meaning |
|---|---|
| **take** | Applies as-is to this repo's vocabulary. |
| **translate** | The intent applies; the wording, paths or commands do not. |
| **skip (stack-bound)** | Touches an adopted path but is about the source's stack — a build script, a migration, a framework config. |
| **skip (already have)** | This repo reached the same end state independently. |
| **skip (not adopted)** | The path is in `declined` **and its recorded reason still holds** — if it doesn't, re-offer the path per Step 4a and move it to `adopted` if taken. Or the path is in neither list, which is Step 4a's other case. Never skip silently on either. |
| **skip (diverged locally)** | This repo rewrote the file for its own stack — `scripts/vet.sh`, the watermark, anything the source marks `rewrite`. The source's edit is advice at best; read it for an idea, don't port it. |

**The source's fix may not be this repo's fix.** Split a commit's rationale
before deciding: one commit can carry a change that addresses a defect this repo
never had *and* a change that fixes one it does. Take the second half, drop the
first, and say so.

### Step 4a — New skills get offered, not taken

A commit that adds a skill in neither `adopted` nor `declined` is an open
question, and the answer belongs in the watermark so it is asked exactly once.

Read the new skill's row in the source's
`.claude/skills/update-muthur/catalog.md` — that file is the source's
inventory, read from the clone and never vendored, so it is current by
construction — and surface the decision **with its criteria attached** rather than
as a bare "upstream added `/foo`, want it?".

- **Taken** → add the path to `adopted` — as a `{path: note}` entry if it landed
  as anything other than a verbatim copy — and **re-run the closure check**: a new
  skill can `@`-reference a sibling this repo declined. `bash
  scripts/check-skill-catalog.sh` is that check where it was adopted.
- **Declined** → add the path to `declined` with the reason.

Either way the question does not come back.

**An opt-in row is offered by its own path, the same way**, even when a broader
`adopted` entry such as `.claude/` already covers it. The catalog marks such a
row `opt-in: ask`, as it does `.claude/costs/`, and a parent directory having
been taken says nothing about whether the operator wants what it costs. Ask with
the row's criteria, and record the answer as an entry of its own, under the
row's path, in `adopted` or `declined`.

### Step 5 — Apply by intent, not by patch

`git cherry-pick` and `git apply` are useless here. The local files are
de-vendored rewrites, not copies, so every hunk conflicts. Read the source's diff
to understand what changed and why, then re-express it in this repo's vocabulary
and file layout.

### Step 6 — Consistency sweep

When a port renames a term, grep the old one across the whole of `adopted` —
**including frontmatter `description:` lines**. Those are a separate surface from
skill bodies: they are what the operator scans in the skills list and what an
invocation matches against, so a stale description mis-advertises a skill whose
every prose site is correct.

### Step 7 — Bump the watermark, last

Set `lastSyncedSha` to the sync's **boundary** and `lastSyncedAt` to today,
along with any `adopted`/`declined` edits from Step 4a, as the final commit of
the sync. The boundary is the HEAD recorded in Step 3 for a whole sync, and the
last source commit a slice or bite triaged for a split one; candidates past it
are the next one's.

**Any commit on the source's first-parent line is a clean boundary.** One inside
a merged side branch is not: its ancestry leaves out mainline commits the slice
triaged beside it, so the next sync's `<boundary>..HEAD` surfaces them again.

The lock follows the boundary. A merged pizza slice moves the trunk's watermark,
so the next slice claims a fresh lock; an elephant's bites share one PR, so the
trunk does not move between them and one lock holds across all of them.

### Step 8 — Report and hand off

Report the triage table — every candidate, with its verdict and one line of
reasoning, skips included. The skipped commits' reasoning belongs in the PR
body, since the watermark advances past them and nothing else records why. The
tail — `@.claude/skills/polish/SKILL.md` and `@.claude/skills/pr/SKILL.md` — is
whatever the `/task` outcome runs, `/go` ending in both; a ride-along's is the
routed task's own.

If this repo adopted the sync path without the PR loop, land the sync however it
normally lands changes — the triage table still belongs wherever that record goes.

**The squash record names the change, not the sync.** The `<essence>`
`@.claude/skills/squash-message/SKILL.md` asks a title for is what landed in
*this* tree — `chore: one job per loop skill, and a size cap on squash bodies`,
not `chore: sync the template forward to <source sha>`. A source SHA is a
commit in another repository, unresolvable from the log it sits in, and "sync
forward" names the transport: the second title sends every reader to the diff.

Provenance needs no prose. `watermark.json`'s `lastSyncedSha`, committed in Step
7, is the precise record and the only one that survives the squash. "The repo we
vendor from moved" is still the honest *why*, so it earns one clause of the
body's opening sentence and nothing more.

## Offered at session start

A `SessionStart` hook runs `scripts/muthur-sync.sh nudge`. When the source has
moved past the trunk's watermark and nobody holds a fresh lock, it prints the
commit titles, the changed files marked `here` or `not here`, the `adopted`
keys, and the rules for making the offer. A lock over a day old is printed
instead, with its holder and session link, for the operator to decide on; only
their say-so makes `claim --takeover` right.

**The nudge is an offer, not a sync.** Nothing is cloned or read before the
operator says yes.

**The claim comes just before the offer is made**, so the operator is never
offered a sync another session is already running. A claim that exits 3 drops
the offer unsaid; on a no, `scripts/muthur-sync.sh release` frees the lock. An
offer left unanswered keeps it until it goes stale, a day in which every other
session's nudge stays silent — the accepted cost of that guarantee.

On yes, one of two shapes:

- **Ride-along** — a lag of a commit or two touching files here, offered once
  the session is already making a change on its branch. Run `/update-muthur
  ride-along` in this session, on this branch, after the task's own commits. The
  sync's commits ride that task's PR, and its triage table goes in that PR's
  body beside the task's own summary. It is unavailable on a branch whose
  watermark is not the trunk's, where the nudge says so.
- **New session** — anything larger. Where `create_session` exists, spawn one on
  this repo with the prompt `/update-muthur claimed`; elsewhere, hand the
  operator that command to paste into one.

## Add what the next sync teaches you

This procedure is distilled from very few syncs and is incomplete by
construction. When one surfaces a corner the file doesn't carry, add it here
rather than to the PR body — this is where the next session looks.
