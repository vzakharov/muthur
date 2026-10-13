> ⛔ **Part of [the catalog](../catalog.md), never vendored** — delete
> `catalog/` wherever `catalog.md` is deleted.

# G2 — The PR loop

- `/task` — Judge for itself whether a task needs a plan, write the draft, then
  judge whether the operator has to look — a question, a draft, and a question,
  running whichever of the three outcomes they pick. `/task <what to do>` is a
  conditional go-ahead scoped to that task, and CLAUDE.md's entry ladder routes
  every change-asking prompt here.
  - **Pulls in:** `/go`, `/plan`, `/pr`; **conditionally** `/take-issue` (G3)
  - **Disposition:** adopt
- `.claude/hooks/prompt-route-notice.sh` — Point the session's first prompt at
  that ladder, at the moment the routing call is made — a pointer, not a copy,
  the rungs being in context already. Skips a prompt the operator routed
  themselves with a leading `/`, and every prompt after the first.
  - **Requires:** `bash`, `jq`, `.claude/settings.json` wiring (G4)
  - **Pulls in:** `.claude/hooks/lib.sh` (G4), `/task`
  - **Disposition:** adopt
- `/plan` — Write the plan to a `docs/plans/` file whose name is the approval
  gate, publish it as a draft PR so it is reviewed as a diff, and ask questions
  as numbered prose. Also owns the call on whether work is beyond one session,
  and which shape splits it: an elephant, a bite per session in one PR, or a
  pizza, slices carved into issues. Carries `elephant.md`, the megaplan's shape
  and how a bite is taken; `carving.md`, what a pizza's plan names as its
  proposed parent and children and what `/go` files from it; and
  `native-plan-mode.md`, the recovery for a session that reached native plan
  mode anyway, which is plan mode's own exit rather than an override of it.
  - **Requires:** `gh`
  - **Pulls in:** `/finalize`, `/go`, `/pr`; **conditionally** `/take-issue`,
    `/propose-issue` (G3)
  - **Disposition:** adopt
- `/go` — The go-ahead: flip the plan file, file the issues the plan proposed,
  do the work, run the quality passes, hand the PR back to `/pr`. Also takes a
  branch to attach to, or a task with no plan behind it.
  - **Pulls in:** `/polish` (G1); `/from-branch`, `/plan`, `/pr`, `/task`;
    **conditionally** `/take-issue`, `/propose-issue` (G3)
  - **Disposition:** adopt
- `/implement` — Redirect to `/go`, for handoff blocks written before the
  rename.
  - **Pulls in:** `/go`
  - **Disposition:** conditional — see below
- `/pr` — Own the PR object: rename the auto-branch, push, then open the draft
  PR or refresh the one that exists.
  - **Requires:** `gh`
  - **Pulls in:** `/branch-rename`, `/qa-checklist`, `/squash-message`
  - **Disposition:** adopt
- `/finalize` — Land prep: swap in staged copies, the quality passes, vet, merge
  the base, sweep working artifacts, flip to ready, reconcile the squash
  message, attest — and, on `and merge`, merge the PR when the run turned up
  nothing to decide.
  - **Requires:** `gh`, `scripts/vet.sh`, `scripts/staged.sh`
  - **Pulls in:** `/polish` (G1); `/check-merge`, `/from-branch`, `/plan`,
    `/squash-message`; **conditionally** `/take-issue` (G3), `/watch-ci` (G5)
  - **Disposition:** adopt
- `/from-branch` — Attach the session to an existing branch or PR, abandoning
  the auto-created session branch.
  - **Requires:** `gh`
  - **Pulls in:** `/finalize`, `/go`
  - **Disposition:** adopt
- `/relay` — Hand the session to a fresh one instead of compacting it: write a
  summary to a committed `docs/remove-before-merging/relay-<N>.md`, numbered one
  past the branch's previous relay, start a successor on the branch with
  `/relay take <branch>`, and stop. The successor attaches, reads the
  highest-numbered summary, and dispatches on its Next step.
  - **Requires:** `create_session` for the spawn on the web; a typed line
    locally
  - **Pulls in:** `/from-branch`, `/go`, `/finalize`
  - **Disposition:** adopt
- `/handle` — Pick up a branch and do what it needs: attach, read off whether it
  carries an approved plan, a plan still under review, or feedback on shipped
  code, run that lane, land-prep only if asked. The target defaults to the
  branch you are on.
  - **Requires:** `gh`; `scripts/export-github-item.py` (G3) for the review
    lane's thread export
  - **Pulls in:** `/from-branch`, `/go`, `/plan`, `/finalize`
  - **Disposition:** adopt
- `.claude/hooks/prompt-handle-pr-export.sh` — Re-export the PR of the branch a
  `/handle` prompt names, on **every** such prompt rather than a session's
  first, and report as a `git diff` what arrived since the export `/handle`
  committed last turn. A PR moves while the branch works, so unlike the issue
  hook it never skips what has landed. Commits nothing itself, and reports a
  failure rather than raising one.
  - **Requires:** `bash`, `jq`, `gh`, `python3` ≥3.9,
    `scripts/export-github-item.py` (G3), `.claude/settings.json` wiring (G4)
  - **Pulls in:** `.claude/hooks/lib.sh` (G4), `/handle`
  - **Disposition:** adopt — **with `/handle`**
- `/branch-rename` — Rename a harness auto-branch
  (`claude/<adjective>-<noun>-<hash>`) to a semantic name, keeping the random
  suffix.
  - **Requires:** `gh`
  - **Pulls in:** `/pr`
  - **Disposition:** adopt
- `/squash-message` — Produce and post the copy-ready squash title/body for a
  PR; owns the format and the draft-then-tighten discipline. Carries
  `working-file.md`, which picks the working file in the one case the tracked
  draft is not on the branch — a first run, or a run after `/finalize` already
  swept it.
  - **Requires:** `gh`, `jq`, `scripts/check-squash-message.sh`
  - **Pulls in:** `/tend-prose` (G1)
  - **Disposition:** adopt
- `/qa-checklist` — Generate a QA checklist from the branch's change and write
  it into the PR body, with each step classified for automatability.
  - **Requires:** `gh`, `python3` ≥3.9, `scripts/pr-body.py`
  - **Disposition:** adopt
- `/check-merge` — Check once whether the PR's base advanced or the PR landed
  since the branch was last attested, and reconcile the squash proposal.
  - **Requires:** `gh`, `scripts/check-merge.sh`
  - **Pulls in:** `/finalize`, `/from-branch`, `/squash-message`
  - **Disposition:** adopt
- `/sync-branch` — Bring a branch up to date with its merge target, resolving
  mechanically and logically in one merge commit.
  - **Requires:** `gh`, `scripts/vet.sh`
  - **Pulls in:** `/check-merge`
  - **Disposition:** adopt
- `scripts/check-merge.sh` — The git/GitHub polling behind `/check-merge`.
  - **Requires:** `gh`, `jq`, `git`, `scripts/lib/gh-repo.sh`
  - **Disposition:** adopt
- `scripts/lib/gh-repo.sh` — Resolve `owner/repo` for `gh`, falling back to
  parsing the `origin` remote when a sandboxed proxy defeats `gh`'s own
  detection.
  - **Requires:** `bash`
  - **Disposition:** adopt
- `scripts/pr-body.py` — Pull a PR body to `docs/pr/<n>/body.md` for local
  editing and PATCH it back. Stdlib-only.
  - **Requires:** `python3` ≥3.9, `$GH_TOKEN` or `gh auth token`,
    `scripts/lib/github.py`
  - **Disposition:** adopt
- `scripts/lib/github.py` — Shared GitHub plumbing for the stdlib-only Python
  scripts: the proxy-then-direct `fetch` ladder every request goes through,
  token resolution, `origin` repo detection, and the `die` they report through.
  - **Requires:** `python3` ≥3.9
  - **Disposition:** adopt
- `scripts/lib/media.py` — Map a content type — or, when it is missing or
  generic, the leading magic bytes — to a file extension. Shared by the
  attachment download in G3 and the session-image extraction in G4, which is why
  it sits here rather than inside either.
  - **Requires:** `python3` ≥3.9
  - **Disposition:** adopt
- `scripts/check-squash-message.sh` — Measure the squash proposal against the
  size caps `/squash-message` states, locating it in the worktree or in history
  once `/finalize` has swept it. POSIX `sh`.
  - **Requires:** `sh`; `git` for the history rungs
  - **Disposition:** adopt
- `scripts/staged.sh` — Stage an always-loaded file as a byte-identical copy at
  `.claude/staged/<path>.staged`, and swap it back at `/finalize` — merging in
  whatever the real file gained meanwhile. Also the check the vet run makes, and
  the lookup `check-skill-catalog.sh` cites through.
  - **Requires:** `bash`, `git`
  - **Disposition:** adopt
- `scripts/check-claude-md-size.sh` — Cap the root `CLAUDE.md` the branch will
  land plus everything it `@`-imports — each file's staged copy where there is
  one — with hysteresis: the total may grow to a ceiling, and a branch that
  crosses it lands it at a lower target. The numbers are constants in the
  script, changed in a commit that says why. POSIX `sh`.
  - **Requires:** `sh`, `git`
  - **Disposition:** adopt
- `scripts/vet.sh` — The vet run: the fast lint/type-check/test pass before
  pushing review-ready work.
  - **Requires:** your stack's own commands
  - **Pulls in:** `scripts/check-skill-catalog.sh` (G1),
    `scripts/check-squash-message.sh`, `scripts/staged.sh`,
    `scripts/check-claude-md-size.sh`, `scripts/check-muthur.sh` (never)
  - **Disposition:** **rewrite**
- `scripts/run-parallel.sh` — Optional helper for `scripts/vet.sh`: run the
  checks concurrently, print output only for the ones that failed, and name
  files an autofix step rewrote. POSIX `sh`.
  - **Requires:** `sh`; `git` for the autofix check only
  - **Disposition:** adopt

Two things in this group are less optional than they look — see
[Closure](../catalog.md#closure-is-not-optional).
