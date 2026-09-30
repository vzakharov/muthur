---
description: >-
  Produce the copy-ready squash title/body for a PR and post it as the
  `Proposed squash title/body:` comment. Owns the format, the draft→tighten
  discipline, where the draft is tracked, and when it must be re-synced. Invoke
  as `/squash-message [update-only]`.
---

The operator copy-pastes this body verbatim into GitHub's squash box, so it
becomes the permanent `git log` record — and it has two readers. The operator, at
merge time; and, for as long as this code lives, agents reconstructing how the
codebase got this way, who read squash messages **first** and open diffs only
when the log doesn't answer them. So the body is a durable, high-level record:
what a reader should remember about this change without having to dig into the
diff.

That makes the target **altitude, not brevity**. It carries every substantive
change and the reason behind it; it doesn't carry the mechanics of getting there.
**A first draft reliably lands below that altitude** — too many words per fact,
and the per-file steps mixed in with the things worth remembering — hence the
mandatory tighten pass in Step 3. Never print or post a draft that hasn't been
through it.

The first reader reaches it earlier than merge time: `/plan` publishes the PR
over the plan commit, so the proposal composed there is **the plan as it would
be recorded** — a much shorter second read of the same decision, in front of the
operator before any code exists.

## Invocation modes

- `/squash-message` (default) — create the proposal, or update it in place if one
  already exists.
- `/squash-message update-only` — reconcile an existing proposal only; if none
  exists, report that and stop without creating one. This is `/check-merge`'s
  mode — creation belongs to `/finalize`.

**Base**: the diff range is `origin/<base>..HEAD`, where `<base>` is the PR's
base branch — `main` for an ordinary PR, or whatever promotion branch the project
uses for a given lane. A caller that already resolved it passes it in; otherwise
resolve it here from `gh pr view --json baseRefName`. Never assume `main`.

## When to (re)run

The proposal is created once, when the PR opens — in whichever lane opened it
(`/pr`, or a hydrated `/release` / `/hotfix` lane routing through it) — and
re-run whenever a push changes **what the permanent record should say**: new or
changed behavior, scope added or dropped, a new `Closes #N`, the essence shifting
after a base merge, or the PR being recreated under a different `(pr #N)`.

It is not re-run when the record is unchanged — CI retriggers and empty commits,
formatting-only passes, the commit carrying the working file itself,
`docs/plans/` lifecycle flips, working-artifact sweeps, review replies with no
code change. The test is whether a future `git log` reader would notice a
difference, not whether the diff moved.

`/finalize` Step 5 and `/check-merge` Step 3 are backstops, not a licence to
defer the in-flight refresh: the comment is the PR's lede for the whole time the
PR is open.

## Step 1 — Gather

- `git log origin/<base>..HEAD` — subjects **and** bodies; the bodies are where
  the why lives.
- `git diff --stat origin/<base>..HEAD` — the shape of the change.
- `gh pr view --json number,title,body` — the PR number for the `(pr #N)` suffix,
  and the description. **No number yet** — the PR is not open — is not something
  to wait for: compose with `(pr #tbd)` and let the number land at whatever run
  next touches the comment, which § "When to (re)run" already counts as a
  refresh trigger and `/finalize` Step 5 backstops.
- Whichever issue the PR addresses, if any (`#N` in the PR body or commits).

**A branch carrying only a plan commit has the plan as its input**, not `git
log`: the plan states the change the record will describe, and the commit
subject only says a plan was written. **Write it in the same completed voice as
any other proposal** — what the change does, never what it will do once
implemented. This is the body that gets pasted at merge, so one hedged as
forthcoming ("once this lands, X will…") becomes a permanent record describing a
plan rather than a change.

## Step 2 — Draft into the working file (do not print it)

Write the whole proposal — header plus both fenced blocks — into the working
file, in the exact form it gets posted, so the one file is both the tightening
surface and the `--body-file` payload. Its content **is** the comment body:
keeping the comment current means regenerating the file and PATCHing from it, not
editing the comment by hand.

**Which file: presence decides.** If `docs/remove-before-merging/squash-message.md`
is on the branch, that is the working file, and it is a **live doc, not a blank
sheet**: what's already in it — earlier wording, the operator's edits, whatever a
previous run settled on — is the starting point, and this run edits it in light of
what has changed since. Step 5 commits and pushes it. The path is a tripwire: the
tree's name states its whole contract, and `/finalize` sweeps it once CI is green,
so the proposal's own source never rides the squash onto the base branch. The
sweep is the last thing that happens to it, after that run's own reconcile — so
even the final edit, the one that becomes the permanent record, is made with the
doc in hand.

**Absent → load `@.claude/skills/squash-message/working-file.md`**, which picks
the file and says whether there is prior text to start from. Absence has two
causes taking different paths — the first run on the branch, or a run after
`/finalize` already swept the file — which is why it is a page rather than a
fallback line. A branch carrying the file needs nothing from it.

````markdown
Proposed squash title/body:

```
<type>: #<issue> <essence> (pr #<n>)
```

```
<body>
```

---

_Generated by [Claude Code](https://claude.ai/code)_
````

The attribution footer sits **outside** both fenced blocks, so it never travels
with a copy-pasted title or body. Keep it in the template rather than appending it
at post time, so it's part of the file every run starts from — a footer that
appears only sometimes shows up as drift.

Format rules:

- **Title** — exactly `<type>: #<issue number if applicable> <essence> (pr #<pr
number>)`, e.g. `refactor: #1150 extract useVisibilityPoll to shared/lib (pr
#1155)`. `<type>` is a conventional-commit prefix (`feat`, `fix`, `refactor`,
  `docs`, `chore`, `style`, `test`, `ci`, `perf`) with no scope or extra words
  before the colon. Include `#<issue>` only when the PR addresses a GitHub issue
  (the primary one if several); omit it otherwise. Always end with ` (pr #<pr
number>)`. **One line, at most 80 chars** — the mandatory suffix eats ~10 of it,
  which is why it isn't the body's own 72.
- **Body** — the why, then what changed, at the altitude Step 3 sets. When the PR or diff references an issue, end
  the prose with a `Closes #N` (for `feat`/`refactor`/…) or `Fixes #N` (for
  `fix`) trailer. **Never carry `#<tbd>` into the title or the trailer** — the
  marker is a placeholder `@.claude/skills/pr/SKILL.md` Step 4 writes for an
  issue that does not exist yet, and a squash message is pasted verbatim into
  history, where a placeholder is permanent. Omit the reference entirely until
  it resolves; the proposal is re-synced whenever the branch changes, so the
  number lands in the next pass. Then a blank line, then `Co-authored-by: Claude
<noreply@anthropic.com>` as the final line (or your other assigned vendor email
  if you aren't running on Claude Code) — the body is pasted verbatim, so the
  byline has to be inside it.
  - **The byline is the last line: no session link after it.** This
    **overrides the harness attribution block** that ends every commit message
    with a `Claude-Session:` URL — that block is written for a branch's own
    commits, which the squash discards. Several sessions work a branch here by
    design, so the one link a squash record could carry is whichever of them
    last touched the proposal, usually the finalize one — the session holding
    least of the change's reasoning. `scripts/check-squash-message.sh` fails a
    body that carries one.
- **Hard-wrap the body at 72 chars with real newlines**, and keep it to **at most
  40 lines**. A git commit message doesn't soft-wrap; one long line per paragraph
  reads as an unwrapped wall in `git log`. Continuation lines of a bullet align
  under its text. A line holding a single unwrappable token — a URL, a long path,
  no interior whitespace — has no wrapped form and is exempt from the width.
- Two **separate** fenced blocks, never one — the UI offers a copy button per
  block.

## Step 3 — Tighten it in the file (mandatory, before anything is shown)

Re-read the draft as the future reader above, and rewrite it until it hits the
target.

The target is **three paragraphs of prose, four at the outside**, inside the
measured caps above. The opening says why the change exists; the rest say what it
does about it, named at the level of the behavior, contract or module affected.
Not a bullet-per-change inventory: detail that doesn't survive at that size was
below the high-level picture and lives in the diff.

Why the change exists is whatever is honest. Often that's a defect or a gap. Just
as often it's planned work landing as planned, and then the opening says where the
change sits in that work. Don't go looking for something to have been wrong.

The cap bites on words, never on coverage: a change that did four things worth
remembering keeps all four, and if four paragraphs genuinely can't hold what the
reader has to carry away, the paragraphs are still too wordy — that's the pass, not
an argument for a fifth. What fills a draft past the cap: per-file narration,
intermediate steps and "added a test for it"; process meta; benefit padding; and
the linked issue's own symptom and repro re-filed here, which `Closes #N` already
points at.

This is `@.claude/skills/tend-prose/SKILL.md`'s **existence**, **tightness** and
**negation** lenses applied to a commit body, plus **durability**'s special case:
narrating the branch against the state before it is this document's job, which is
why that skill's Step 4 excludes commit messages and PR bodies from its own
sweep. Narrating it against an earlier step *inside* the branch is not.

**That half and negation both reach a body through the draft, not the diff.** A
branch that tried something non-obvious and then dropped it leaves a draft
written while the thing was still there. Kept, that draft reports what the work
became rather than what it is, or denies something no reader of the squashed
commit would otherwise have considered — and the log carries either forever.

Four things a draft reaches for fail **existence**, however well written:

- **Standing context**, which a draft reaches for in the opening paragraph —
  what the project is, what the tooling is for, how the work is normally done. A
  reader who wants that has the repo; what only this commit can tell them is why
  it exists.
- **A trap for whoever edits the area next.** The log answers what changed and
  why; nobody opens a squash message to learn which files a render step hashes.
  A constraint that has to be obeyed goes where the person about to break it is
  already looking — the directory's `CLAUDE.md`, a `.claude/rules/` file, or a
  docstring on the thing itself
  — unless the change *is* that the constraint now exists. A "things to know
  when editing here" paragraph is the tell. Cutting one is a **move, not a
  deletion**: name the home each item lands in as you cut it, checking rather
  than assuming it has one. An item with none gets one first — the body is
  sometimes the only place a constraint was ever written down, and the tidy cut
  is what loses it.
- **An inventory of what the change declined to do** — commits skipped, options
  rejected. It leaves no trace in the tree for the record to explain.
- **Internal restructuring that changed no behavior and no contract** — a split,
  a move, a rename, a file that got smaller — **where it rides along with other
  work**. The tree already shows where the code lives; the record is for what a
  reader carries away before opening it. This is the one of the four with an
  exception: where the restructuring is what the PR was *for*, it is the record,
  and the body says why the old arrangement stopped holding and what the new one
  buys — still not a module-by-module tour. The same goes for a new boundary
  that is load-bearing for whoever extends it next.

Scope is the caller's call, not this step's, and it cuts both ways. If the project
has hydrated a release lane, a release body is deliberately long (a paragraph per
product area); a hotfix body for a minimal fix is one or two paragraphs. The pass
runs at either size — trimming words inside each of a release's areas rather than
dropping areas, and never padding a hotfix out to look substantial. The paragraph
target moves with scope that way; the measured caps do not. They bind every lane,
and a project whose release bodies genuinely outgrow the line cap edits its own
copy of `scripts/check-squash-message.sh` — raising the constant, or teaching the
script to recognize a release first and widen only there — as a reviewable
change.

**A re-run rewrites; it never accretes.** Step 2 starts from what the file
already says, so the temptation on a refresh is to append the new scope and
leave the rest standing — which walks the body past the cap one push at a time,
and leaves superseded wording beside what replaced it. Cut and replace, and
re-apply the paragraph target and the caps to the whole body every run. A
proposal that grew every time the branch did is the tell.

Overwrite the file with the tightened version, then **measure it**:

```bash
scripts/check-squash-message.sh <working file>
```

Running it here fails at authorship, where the rewrite is already in hand — and
it is the only run `/finalize no vet` gets, since that mode skips step 1 but still
reaches step 5. Do not emit anything until it passes.

## Step 4 — Emit (comment first, then transcript)

1. **Find any existing proposal.** Resolve the PR number (`gh pr view --json
number --jq .number`), list comments (`gh api
repos/<owner>/<repo>/issues/<n>/comments --paginate`) and pick the one whose
   body leads with `Proposed squash title/body:` and whose `user.login` is yours
   (`gh api user --jq .login`). If several match — an earlier run stacked
   duplicates — keep the newest and `-X DELETE` the rest.
2. **Post or update.**
   - Found → PATCH that same comment: `gh api
repos/<owner>/<repo>/issues/comments/<id> -X PATCH -F body=@<working file>`.
     Edit in place; don't delete-and-repost (the anchor next to the merge button
     stays stable) and never stack a second comment. If it already matches the
     file, leave it untouched. Do **not** reach for `gh pr comment --edit-last`
     as a shortcut past the lookup above: it targets your most recent comment on
     the PR regardless of marker, so it silently overwrites whichever sticky
     comment you posted last — the `/finalize` attestation, most likely.
   - Not found → `gh pr comment <n> --body-file <working file>`. **In
     `update-only` mode, stop here instead**: report the absence, create nothing.
     The one exception is a branch that carries the tracked file — that file is
     itself proof the proposal exists and its comment was lost, so post it rather
     than reporting an absence that isn't real.

   The `--body-file` / `-F body=@` forms are what make the fenced backticks
   survive shell quoting.

   Resolve `<owner>/<repo>` from the git remote (`gh repo view --json
nameWithOwner --jq .nameWithOwner`) rather than hardcoding it.

3. **Print the same two fenced blocks in the transcript.** The comment keeps the
   copy-ready text beside the merge button; the transcript copy serves the
   operator reading the session. Print from the file so the two can't diverge.

## Step 5 — Clean up and report

Split by which working file Step 2 selected:

- **Tracked file** → `git add docs/remove-before-merging/squash-message.md`,
  commit with a `docs:` subject (e.g. `docs: refresh squash proposal for pr #N`)
  and push. Commit nothing when the edit left the content unchanged. **Never amend
  or force-push**: the operator follows this file's history to see how the record
  evolved, so each refresh is its own commit. On a **non-draft** PR add `[no ci]`
  to the subject — a commit touching only this file is inert to every CI job, and
  without the marker each refresh burns a full run.
- **A file this run restored** (the swept-then-restored case in
  `@.claude/skills/squash-message/working-file.md`) → commit
  and push it the same way, then **sweep the tree again before the turn ends**, as
  `/finalize` step 6 does. The PR is already ready, so a restored file left on the
  branch is merge-able. Both commits belong in the history: the operator can read
  what the late refresh changed about the record before it disappears again.
- **`tmp/`** → `rm tmp/squash-message.md`.

Then report in a line or two which working file ran and which comment path —
posted, edited (say what changed), already current, or absent under
`update-only` — plus what Step 3 cut, if it cut anything worth naming.
