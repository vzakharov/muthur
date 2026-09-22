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

The **group** is the section heading rather than a column: groups partition the
inventory, so every item appears under exactly one, and
`scripts/check-skill-catalog.sh` fails if a skill picks up a second row.

### Three dispositions, not two

- **adopt** — copy as-is.
- **rewrite** — copy the shape, replace the contents for your repo. One row
  carries it: `scripts/vet.sh`, whose exit turns on whether your repo has a stack
  yet, with [`CLAUDE.md` § "Vetting"](../CLAUDE.md#vetting) the contract's home.
  Elsewhere the word qualifies an **adopt** — `/update-muthur`'s watermark,
  `.claude/voice/`'s `operators/` entries — where the item travels whole and one
  file inside it is yours to write.
- **never** — describes or maintains *this* repo, so it is meaningless in yours.

## Groups

Group membership is the coarse decision; **Requires** carries the orthogonal
conditions, and any row can be escaped individually.

| Group | Adopt when |
| --- | --- |
| [G0 — The sync path](#g0--the-sync-path) | Always, unless you want a one-time snapshot and no future updates. The sync half ships unhydrated: filling in the watermark is what makes it runnable. |
| [G1 — Prose & principles](#g1--prose--principles) | Always. Zero external dependencies, no stack assumptions, no GitHub. |
| [G2 — The PR loop](#g2--the-pr-loop) | A change is a branch → PR → squash-merge, on GitHub, with `gh` and `$GH_TOKEN` reachable. **In a web/remote session, needs G4.** |
| [G3 — Issue & backlog](#g3--issue--backlog) | G2 **and** work is actually tracked as GitHub issues. Same web-session dependency on G4. |
| [G4 — Remote-session plumbing](#g4--remote-session-plumbing) | Sessions run on Claude Code web/remote. Inert locally — but a **prerequisite** of G2/G3/G5 on the web, not a nicety. Declinable at a stated cost. |
| [G5 — CI & landing](#g5--ci--landing) | CI runs on GitHub Actions, reachable via `gh`. `/watch-ci` additionally needs **G4** in a web session, not merely recommends it; the rest of the group works through the proxy unshimmed. |
| [G6 — Stack stubs](#g6--stack-stubs) | Per row, and only if you will hydrate it now. |
| [Never](#never) | — |

### G0 — The sync path

The group owns the whole source-and-target relationship, in both directions:
`/update-muthur` pulls later changes at your source forward into your repo,
and `/spinoff` pushes a new sibling repo out of it. Adopting the first is what
makes every later change at the source reachable; skipping it leaves you with a
snapshot.

**`/update-muthur` ships unhydrated**, this repo having no source of its own
to sync from. Hydrating it is filling in the watermark, not writing a procedure:
every step of the skill is usable as written. The [G6 hydrate-now-or-delete
rule](#g6--stack-stubs) applies here too, and `scripts/check-skill-catalog.sh`
enforces it the same way.

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `/update-muthur` | Pull the agent infrastructure forward from the repo you adopted it from: diff since the watermark, triage commit by commit, port what applies. Carries `watermark.json` — which repo you sync from, the SHA you last synced to, what you adopted or declined, and the ancestry that led here — shipped pointed at this repo with the rest as placeholders, this tree being the root. | `gh`, `$GH_TOKEN`, git transport to the source repo; hydration (the watermark) | `/polish` (G1); `/pr`, `/squash-message` (G2); `/override-gh` (G4) | adopt — **rewrite the watermark** |
| `/spinoff` | Seed a new sibling repo out of the adopter you are standing in: triage what travels, write the target's watermark, seed its `main` and a session branch, and hand over a session in it. Ships hydrated. | `gh`, `$GH_TOKEN`, repo-creation rights on the target's owner; a caller that adopted this infrastructure rather than being it | `/update-muthur` (this group); `/pr` (G2) | adopt |

**Both skills are inert in this repo, for one structural reason: this tree is the
root.** There is no source above it to sync from, and it is not an adopter, so
there is nothing to spin off out of either — `/spinoff` refuses the moment it
finds this catalog. Downstream both work.

`/update-muthur`'s Step 8 hands off to `/polish` and `/pr`, and
cites `/squash-message` for how the sync's own squash record is titled; `/polish`
comes with G1, which you are adopting anyway. `/spinoff` reaches `/pr` as
well, at its Step 4, to open the seed PR in the new repo. **G2 is the escape**:
if you decline it, strip those citations from both skills and land the sync PR —
and the seed PR — however your repo normally does. `scripts/check-skill-catalog.sh`
will otherwise report the dangling references, which is the intended behavior
rather than a nuisance.

### G1 — Prose & principles

The floor. Nothing here touches GitHub, needs a token, or assumes a stack, so
there is no condition under which it fails to apply.

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `CLAUDE.md` | The always-loaded conventions: key principles, docstring policy, derive-types-from-source-of-truth, doc-sync rules, commit conventions, the language decision. | — | — | adopt — **merge, don't overwrite** |
| `.claude/rules/` | The path-scoped convention mechanism: a rule file loads only when a session touches the paths it declares. Ships with a README and no rules. | — | — | adopt |
| `/dry` | Review the session's diff for DRY opportunities; apply the obvious wins, surface the ambiguous ones. | — | — | adopt |
| `/tend-prose` | Cut prose that shouldn't exist, rewrite what narrates a change into present-tense contracts, trim what names and types already say, delete what survives only to deny a thing the change removed. The long version of CLAUDE.md § "Writing things down". | — | — | adopt |
| `/polish` | Run `/dry` then `/tend-prose` over the branch's diff, committing what they change. `/go` runs it after implementing and `/finalize` before anything else it does; the operator runs it over work that reached neither. | — | `/dry`, `/tend-prose` (this group) | adopt |
| `.claude/voice/` | The house rule for writing to a person, imported by CLAUDE.md § "Explaining things to people" and so resident in every session. `voice.md` is the rule, and the place a team edits if it wants a house manner of its own; `operators/` holds one file per person and ships carrying this repo's operator. | — | `/tend-prose` (this group) | adopt — **rewrite its `operators/` entries** |
| `/plainly` | Explain something to a person cause-first and in their nouns: re-explain an answer that did not land, or answer a question under the rule from the start. Names six defects so a bad report can be called out in one word. | — | `/tend-prose` (this group) | adopt |
| `scripts/check-skill-catalog.sh` | Assert that no skill `@`-reference dangles. Downstream, that first assertion is the whole value: it is how you find out a subset copy was incomplete. | `bash` | — | adopt |
| `.gitignore` | Take the `tmp/` entry and keep the rest of yours. `CLAUDE.md`'s "dev artifacts go under `tmp/`" principle depends on that path being ignored. | — | — | adopt — merge one line |

`CLAUDE.md` is a **donor, not a replacement** — overwriting it is the one way to
make adoption a regression. `ADOPTING.md`'s shared tail owns the merge itself.

Its § "Language" is hydrated rather than merged: one line naming the language
your team reads, the rest of the section holding whatever the project.

Its § "Explaining things to people" ends in an **unbackticked** `@` reference,
which is the one line in this file a tidy-up breaks: the import parser skips code
spans, so backticking it for consistency with its neighbours loads nothing and
says nothing.

### G2 — The PR loop

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `/task` | Judge for itself whether a task needs a plan, write the draft, then judge whether the operator has to look — a question, a draft, and a question, running whichever of the three outcomes they pick. `/task <what to do>` is a conditional go-ahead scoped to that task, and CLAUDE.md's entry ladder routes every change-asking prompt here. | — | `/go`, `/plan`, `/pr`; **conditionally** `/take-issue` (G3) | adopt |
| `.claude/hooks/prompt-route-notice.sh` | Point the session's first prompt at that ladder, at the moment the routing call is made — a pointer, not a copy, the rows being in context already. Skips a prompt the operator routed themselves with a leading `/`, and every prompt after the first. | `bash`, `jq`, `.claude/settings.json` wiring (G4) | `.claude/hooks/lib.sh` (G4), `/task` | adopt |
| `/plan` | Write the plan to a `docs/plans/` file whose name is the approval gate, publish it as a draft PR so it is reviewed as a diff, and ask questions as numbered prose. Also owns the call on whether work is beyond one PR, and the bar that keeps the answer usually "no". Carries `carving.md`, the procedure for the work that is: how coarse the parked slices may be, and what the plan names as its proposed parent and children; and `native-plan-mode.md`, the recovery for a session that reached native plan mode anyway, which is plan mode's own exit rather than an override of it. | `gh` | `/finalize`, `/go`, `/pr`; **conditionally** `/take-issue`, `/propose-issue` (G3) | adopt |
| `/go` | The go-ahead: flip the plan file, file the issues the plan proposed, do the work, run the quality passes, hand the PR back to `/pr`. Also takes a branch to attach to, or a task with no plan behind it. | — | `/polish` (G1); `/from-branch`, `/plan`, `/pr`, `/task`; **conditionally** `/take-issue`, `/propose-issue` (G3) | adopt |
| `/implement` | Redirect to `/go`, for handoff blocks written before the rename. | — | `/go` | conditional — see below |
| `/pr` | Own the PR object: rename the auto-branch, push, then open the draft PR or refresh the one that exists. | `gh` | `/branch-rename`, `/qa-checklist`, `/squash-message` | adopt |
| `/finalize` | Land prep: the quality passes, vet, merge the base, sweep working artifacts, flip to ready, reconcile the squash message, attest — and, on `and merge`, merge the PR when the run turned up nothing to decide. | `gh`, `scripts/vet.sh` | `/polish` (G1); `/check-merge`, `/from-branch`, `/plan`, `/squash-message`; **conditionally** `/take-issue` (G3), `/watch-ci` (G5) | adopt |
| `/from-branch` | Attach the session to an existing branch or PR, abandoning the auto-created session branch. | `gh` | `/finalize`, `/go` | adopt |
| `/handle` | Pick up a branch and do what it needs: attach, read off whether it carries an approved plan, a plan still under review, or feedback on shipped code, run that lane, land-prep only if asked. The target defaults to the branch you are on. | `gh`; `scripts/export-github-item.py` (G3) for the review lane's thread export | `/from-branch`, `/go`, `/plan`, `/finalize` | adopt |
| `.claude/hooks/prompt-handle-pr-export.sh` | Re-export the PR of the branch a `/handle` prompt names, on **every** such prompt rather than a session's first, and report as a `git diff` what arrived since the export `/handle` committed last turn. A PR moves while the branch works, so unlike the issue hook it never skips what has landed. Commits nothing itself, and reports a failure rather than raising one. | `bash`, `jq`, `gh`, `python3` ≥3.9, `scripts/export-github-item.py` (G3), `.claude/settings.json` wiring (G4) | `.claude/hooks/lib.sh` (G4), `/handle` | adopt — **with `/handle`** |
| `/branch-rename` | Rename a harness auto-branch (`claude/<adjective>-<noun>-<hash>`) to a semantic name, keeping the random suffix. | `gh` | `/pr` | adopt |
| `/squash-message` | Produce and post the copy-ready squash title/body for a PR; owns the format and the draft-then-tighten discipline. Carries `working-file.md`, which picks the working file in the one case the tracked draft is not on the branch — a first run, or a run after `/finalize` already swept it. | `gh`, `jq`, `scripts/check-squash-message.sh` | `/tend-prose` (G1) | adopt |
| `/qa-checklist` | Generate a QA checklist from the branch's change and write it into the PR body, with each step classified for automatability. | `gh`, `python3` ≥3.9, `scripts/pr-body.py` | — | adopt |
| `/check-merge` | Check once whether the PR's base advanced or the PR landed since the branch was last attested, and reconcile the squash proposal. | `gh`, `scripts/check-merge.sh` | `/finalize`, `/from-branch`, `/squash-message` | adopt |
| `/sync-branch` | Bring a branch up to date with its merge target, resolving mechanically and logically in one merge commit. | `gh`, `scripts/vet.sh` | `/check-merge` | adopt |
| `scripts/check-merge.sh` | The git/GitHub polling behind `/check-merge`. | `gh`, `jq`, `git`, `scripts/lib/gh-repo.sh` | — | adopt |
| `scripts/lib/gh-repo.sh` | Resolve `owner/repo` for `gh`, falling back to parsing the `origin` remote when a sandboxed proxy defeats `gh`'s own detection. | `bash` | — | adopt |
| `scripts/pr-body.py` | Pull a PR body to `docs/pr/<n>/body.md` for local editing and PATCH it back. Stdlib-only. | `python3` ≥3.9, `$GH_TOKEN` or `gh auth token`, `scripts/lib/github.py` | — | adopt |
| `scripts/lib/github.py` | Shared GitHub plumbing for the stdlib-only Python scripts: the proxy-then-direct `fetch` ladder every request goes through, token resolution, `origin` repo detection, and the `die` they report through. | `python3` ≥3.9 | — | adopt |
| `scripts/lib/media.py` | Map a content type — or, when it is missing or generic, the leading magic bytes — to a file extension. Shared by the attachment download in G3 and the session-image extraction in G4, which is why it sits here rather than inside either. | `python3` ≥3.9 | — | adopt |
| `scripts/check-squash-message.sh` | Measure the squash proposal against the size caps `/squash-message` states, locating it in the worktree or in history once `/finalize` has swept it. POSIX `sh`. | `sh`; `git` for the history rungs | — | adopt |
| `scripts/vet.sh` | The vet run: the fast lint/type-check/test pass before pushing review-ready work. | your stack's own commands | `scripts/check-skill-catalog.sh` (G1), `scripts/check-squash-message.sh`, `scripts/check-muthur.sh` (never) | **rewrite** |
| `scripts/run-parallel.sh` | Optional helper for `scripts/vet.sh`: run the checks concurrently, print output only for the ones that failed, and name files an autofix step rewrote. POSIX `sh`. | `sh`; `git` for the autofix check only | — | adopt |

Two things in this group are less optional than they look — see
[Closure](#closure-is-not-optional).

### G3 — Issue & backlog

Adopt on top of G2, and only if work is genuinely tracked as GitHub issues. If
you plan in Linear, Jira or a doc, decline the group and record why in
`watermark.json`'s `declined` map so re-sync stops offering it.

**A fork reverses the default.** The rule above weighs the group against a
process the repo already has; a whole-tree fork has none and inherits this
one's, so `/detemplate` keeps G3 unless the operator says otherwise — and files
the project's first issue on the way through.

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `/take-issue` | Pull a GitHub issue onto the branch: export the thread and its attachments, commit them, hand the number back. Decides nothing — its callers are `/task`, `/plan` and `/go`, each running it first when the prompt carries a `#<N>`. Carries `video-frames.md`, which installs `ffmpeg` and extracts readable frames when an attachment turns out to be a video. | G2, `gh`, `scripts/export-github-item.py` | `/finalize`, `/plan` (G2) | adopt |
| `.claude/hooks/prompt-issue-export.sh` | Export the `#<N>` a session's first prompt *ends* in — skipping what is already on disk — so `/take-issue` Step 1 is done before the agent reads that prompt. A later `#<N>` is left to the agent, and any other prompt costs one `jq`. Commits nothing, and reports a failure rather than raising one. | `bash`, `jq`, `python3` ≥3.9, `scripts/export-github-item.py`, `.claude/settings.json` wiring (G4) | `.claude/hooks/lib.sh` (G4), `/take-issue` | adopt |
| `/issue` | Redirect for the name `/take-issue` was split out of: with a `#<N>` it runs `/plan` on the argument and names `/task` and `/go` as the same-shape alternatives; with none it names `/propose-issue` and stops. | G2 | `/plan` (G2), `/propose-issue` | conditional — see below |
| `/propose-issue` | File a unit of work as an issue, deduping against what's already open. Steps 1–2 are read-only and may run a turn earlier than Step 3, which is also where a `#<tbd>` on the branch gets its number. | G2, `gh`, `jq` | `/pr`, `/plan` (G2) | adopt |
| `/audit-github-backlog` | Sweep every open issue and PR against today's code and leave a reviewable close/refile/keep plan, prioritising `P0`–`P3` everything it keeps. Mutates nothing on GitHub. | G2, `gh` | `/go`, `/plan` (G2); `/propose-issue`; `/override-gh` (G4) | adopt |
| `scripts/export-github-item.py` | Download an issue — body, comments, timeline, attachments — into `docs/issue/<n>/`, or a PR (plus review threads, each one's resolved/unresolved state, and the lines its comment hangs off) into `docs/pr/<n>/`. Threads and comments are always indexed above their bodies. Stdlib-only. | `python3` ≥3.9, `$GH_TOKEN` or `gh auth token`, `scripts/lib/github.py` (G2), `scripts/gh_export/` | — | adopt |
| `scripts/gh_export/` | The exporter's pieces, one module per concern: argument parsing, the REST/GraphQL client, attachment download, the index-plus-bodies layout, and a renderer each for the header and comments, the review threads, and the timeline. | `python3` ≥3.9, `scripts/lib/github.py` (G2) | — | adopt |

### G4 — Remote-session plumbing

Inert on a laptop, load-bearing on the web. The agent proxy in Claude Code
web/remote sessions blocks long-polling calls and most of `gh`'s GraphQL
surface; `gh-shim.sh` installs a shim that routes the real binary around the
proxy so the rest of the infrastructure works at all.
`plan-mode-notice.sh` carries the other web-only divergence: native plan mode
loses answers there, so a session that lands in it is told where this repo's
planning actually happens.

`session-images.sh` is the one member that earns its keep on a laptop too: an
attached image exists only inside the transcript wherever the session runs. It
writes into gitignored `tmp/` and commits nothing, so it needs no `git`, leaves
the working tree clean, and behaves the same everywhere.

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `.claude/hooks/gh-shim.sh` | On session start, install a `gh` shim at `$HOME/.local/bin/gh` that runs the real binary unproxied. Finding no `gh` to wrap, it reports that into the session context and continues. Web/remote only. | `bash`; **`gh` already on `PATH`**; web/remote sessions | — | adopt |
| `.claude/hooks/install-deps.sh` | On session start, re-sync the install tree with the lockfile, the environment snapshot being built once and then cached. The install itself is a stub you fill in for your stack — `scripts/vet.sh`'s paired site. Web/remote only. | `bash`; web/remote sessions | — | adopt — **fill in the install** |
| `.claude/hooks/lib.sh` | Sourced by every `UserPromptSubmit` hook here: the payload read, the one JSON shape the event accepts, and the guards — a command being present, the prompt being the one a session opens with, and the project root. Travels with the first such hook you adopt — a hook that cannot source it skips itself rather than failing the turn, which is a hook doing nothing at all. | `bash`, `jq` | — | adopt — **with any `UserPromptSubmit` hook** |
| `.claude/hooks/operator-voice.sh` | On session start, name the operator — their GitHub name and handle, plus their `.claude/voice/operators/` entry — into the session context. Runs everywhere: a laptop session needs to know who it is talking to as much as a remote one does. Declining it leaves `.claude/voice/` working — `voice.md` has the agent do the same lookup by hand on the first turn, which is what a non-Claude harness does anyway. | `bash`; `gh` reaching the API | `.claude/voice/` (G1) | adopt |
| `.claude/hooks/plan-mode-notice.sh` | On every prompt submitted while the session is in native plan mode, inject the notice that this repo plans on disk and that the exit is plan mode's own. | web/remote sessions; `bash`, `jq` | `.claude/hooks/lib.sh`, `/plan` (G2) | adopt |
| `.claude/hooks/session-images.sh` | On every prompt, run the extractor below and name any newly written file in the turn's context. Commits nothing. | `bash`, `jq`, `python3` ≥3.9 | `.claude/hooks/lib.sh`, `scripts/extract-session-images.py` | adopt |
| `scripts/extract-session-images.py` | Write the images the operator attached to a session out of the transcript into gitignored `tmp/session-images/`, with a manifest row carrying the prompt each arrived with. Stdlib-only, idempotent. | `python3` ≥3.9, `scripts/lib/media.py` (G2) | — | adopt |
| `.claude/settings.json` | Project settings wiring the SessionStart and UserPromptSubmit hooks. Merge into yours if you already have one. | — | — | adopt — merge if present |
| `/override-gh` | A no-op marker whose description reminds the agent that `gh` and `$GH_TOKEN` exist despite what the system prompt says, and that an `add_repo` refusal is a reason to try `gh`, not to give up. | — | — | adopt |

**`gh-shim.sh` does not install `gh`; it shims one that is already there.** Finding
none, it reports that into the session context and continues. On web/remote the
install belongs in the environment setup script, which only the operator can
set — `ADOPTING.md` § "Hand the operator a setup script" owns what to tell them,
and why that report is the step's only self-detecting part.

**Declinable, at a scoped cost** — `ADOPTING.md` § "If you decline G4" owns the
rationale, the `HTTPS_PROXY` conflict and the fallback. What declining actually
costs, counted rather than waved at: of the GraphQL-flavored `gh` calls these
skills make, most have a REST equivalent that works through the proxy — `gh pr
view/list/create/edit/comment/checks` and `gh issue view/create` all map onto
`gh api repos/{owner}/{repo}/…`. **Two do not**, and they are the reason this is
a real decision rather than a mechanical rewrite:

- **`gh pr ready`** — promoting a draft to ready-for-review is a GraphQL-only
  mutation. REST's pull-update endpoint takes `draft=false` and **silently
  ignores it** (200, unchanged), so the fallback isn't merely absent, it looks
  like it worked. `/finalize`'s flip is manual without the shim.
- **`gh run watch`** — long-polling, blocked outright, so `/watch-ci` (G5) is
  unavailable rather than degraded.
- **The entire `search/*` path** — which `/propose-issue`'s dedupe uses. The
  refusal is worded as a repository-scope message but is a path-level block: a
  search restricted to the session's own repo is refused too. Substitute
  `repos/{owner}/{repo}/issues` and filter locally.

All three come back with the shim installed; they are the price of declining G4,
not standing defects.

**`/override-gh` travels beyond G4.** `/update-muthur` (G0) and
`/audit-github-backlog` (G3) `@`-reference it, so **a repo that declines G4
entirely still needs this one file** if it takes either of those — otherwise the
reference dangles. Concretely: copy `.claude/skills/override-gh/` even when you
skip the hook and `settings.json`. It is a no-op marker, so copying it is cheaper
than editing two skills to remove the citation.

### G5 — CI & landing

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `/bootstrap-workflow-dispatch` | Register a `workflow_dispatch` workflow in Actions metadata with a one-shot branch-scoped push trigger, so `gh workflow run` stops 404ing on a branch whose workflow has not reached the default branch yet. | GitHub Actions, `gh`, push access to the branch | `/test-on-gh` (G6), `/watch-ci` | adopt |
| `/watch-ci` | Watch an in-flight GitHub Actions run incrementally, surfacing failures as they happen so fixes can go out mid-run. | GitHub Actions, `gh`, `scripts/ci-watch-tick.sh`; **G4 on the web** | — | adopt |
| `scripts/ci-watch-tick.sh` | One polling tick of a CI run: what changed since the last tick. | `gh`, `jq`, `scripts/lib/watch-tick-common.sh`, `scripts/lib/gh-repo.sh` (G2) | — | adopt |
| `scripts/lib/watch-tick-common.sh` | The watch loop's tick helpers: the elapsed-aware sleep between ticks, and the `--reset` state-file removal. | `bash` | — | adopt |

The group's three CI-facing skills partition one timeline.
`/bootstrap-workflow-dispatch` ends the moment `gh workflow run` stops 404ing,
`/test-on-gh` is the dispatch that hits that 404 first, and `/watch-ci` watches
the run a successful dispatch produces. `/test-on-gh` ships as a stub, so it is
listed under [G6](#g6--stack-stubs) with the other stubs — one row, one group.

**G4 is a `/watch-ci` requirement, not a group-wide one** — it is `gh run
watch`'s long-polling that the proxy blocks, counted among the costs of
declining G4 in [that group](#g4--remote-session-plumbing).
`/bootstrap-workflow-dispatch` dispatches over REST
(`POST /repos/{owner}/{repo}/actions/workflows/{id}/dispatches`) and works
unshimmed.

**Taking this group without G6 means editing one reference.**
`/bootstrap-workflow-dispatch` `@`-references `/test-on-gh`, and G6's rule is to
copy a stub only if you hydrate it now — so an adopter who skips `/test-on-gh`
strips that clause from the `## Related` section, or
`scripts/check-skill-catalog.sh` reports the dangling pointer.

### G6 — Stack stubs

Every line of a working version of these is bound to a particular stack, so they
ship carrying only the durable part: the shape of the job, and the concerns any
implementation has to answer. Each opens with a banner naming what must be
filled in, and its frontmatter announces that it is a stub.

**An unhydrated stub is worse than a missing skill** — half-following one against
a project it was never written for beats not having it only in appearance. So
copy none of these "for later": take a row only if you will hydrate it now, and
delete the rest. Three of them tell you when to delete the skill outright
instead (no visual surface, no CI-only tests, no numbered migrations).

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `/release` | Cut a release: version bump, notes, release PR, arm or ship the deploy. | a deploy path; hydration | — | adopt only if hydrating now |
| `/hotfix` | Ship an urgent fix past the normal promotion path, then reconcile it into the trunk. | a deploy path; hydration | — | adopt only if hydrating now |
| `/preview` | Render a visual change and actually look at it, rather than judging appearance from code. | a visual surface; hydration | — | adopt only if hydrating now |
| `/log-review` | Read deployed logs since the last review: a usage readout plus health triage. | deployed logs; hydration | — | adopt only if hydrating now |
| `/readonly-probe` | Investigate against real deployed data under an enforced read-only connection. | a production datastore; hydration | — | adopt only if hydrating now |
| `/renumber-migration` | Resolve a sequential migration-number collision after another branch landed first. | sequential numbered migrations; hydration | — | adopt only if hydrating now |
| `/test-on-gh` | Dispatch the test buckets that can't run locally to CI on the branch, and block for the result. | G5, CI-only test buckets; hydration | — | adopt only if hydrating now |

### Never

These are meaningless in a repo that selects a subset. Most of them describe or
maintain *this* repo, so copying one means shipping a document about someone
else's template. `/detemplate` is the row that is `never` for the other reason:
it describes no repo at all, it *converts* a whole-tree fork — an operation a
subset adopter is not performing and a fork performs exactly once, deleting the
skill as it finishes.

**A clone can also hold working state.** `/finalize` deletes `docs/plans/`,
`docs/issue/` and `docs/remove-before-merging/` before a branch goes green, but
the sweep is a discipline rather than a guarantee: a merge that bypassed it
leaves them behind, and a clone taken mid-flight from a feature branch has them
by construction. Seeing any of those directories means you are looking at
someone else's work in progress, not the product.

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `README.md` | What this repo is, and the two ways to acquire it. Yours already exists. | — | — | never |
| `ADOPTING.md` | The acquisition procedure. Read once, over the network, from the clone. | — | — | never |
| `docs/img/` | `ADOPTING.md`'s only asset — the screenshot locating the environment setup script. Goes when that file does, or it is left an orphan. | — | — | never |
| `.claude/skills/update-muthur/catalog.md` | This file, and the only row naming something a skill directory would otherwise carry in: taking `/update-muthur` brings it along, which must not happen. Read it from a fresh clone on every sync instead, so it cannot go stale downstream — both copy steps name it as a carve-out. | — | — | never |
| `/detemplate` | Turn a fresh template fork into a project: prune the `never` rows and unused groups, hydrate what stays, hand back the setup script. Routes through `/plan` and deletes itself last. | `gh`, `$GH_TOKEN`; a whole-tree fork, not a subset copy | `/plan` (G2); `/spinoff`, `/update-muthur` (G0) | never |
| `scripts/check-muthur.sh` | The one vet line behind which everything that tests only this repo's own machinery sits, so a sync offers it as a single decision. Keyed on this catalog's presence, so it exits 0 the moment it is downstream. | `bash` | `scripts/check-repo-identity.sh`, `scripts/test_*.py` (both never) | never |
| `scripts/check-repo-identity.sh` | Assert that this repo's own `owner/repo` appears only where a human copies it by hand, and nowhere under a stale name — everything else compares `origin` against the watermark's `repo` field instead. Keyed on this catalog's presence, so it exits 0 the moment it is downstream. | `bash`, `jq`, `git` | — | never |
| `scripts/test_*.py` | The unit tests over the loop's own scripts — today the export's agent/human labelling, its hunk trimming and its layout. They join the line above by matching the pattern, which is why adding one never edits `scripts/vet.sh`. | `python3` ≥3.9 | — | never |

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
  noisier for no behavioral gain. `CLAUDE.md`'s stub list names it too, and that
  one *is* rewritten — not for closure, but because the list stops being true
  when the stubs go.
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
