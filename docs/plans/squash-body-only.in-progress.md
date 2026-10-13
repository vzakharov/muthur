# Squash proposal: body only, the PR title is the squash title

## Why

Merging means copying two blocks out of the `Proposed squash title/body:`
comment, the title and the body. GitHub's "Squash and merge" already prefills
the title as `<PR title> (#<n>)`, which is the title we want. The only
difference is `(#n)` against our `(pr #n)`, and that difference is cosmetic.
So the title block is busywork. It is also a second copy of the title that can
drift from the PR's own title.

The change: the proposal carries **one** block, the body, and the squash title
**is** the PR title, which every run of `/squash-message` keeps current.

## Changes

1. **`/squash-message` (`SKILL.md`, description staged).**
   - The proposal is one fenced block under the header `Proposed squash body:`.
   - The title format rules (conventional type, `[attn adopters]`, `#<issue>`,
     essence) carry over unchanged, except that they now describe **the PR
     title**. The ` (pr #<n>)` suffix is dropped, because GitHub appends
     ` (#<n>)` itself. The cap becomes **72 chars**: the old 80 minus room for
     the suffix GitHub adds.
   - Every run composes the title along with the body, and Step 4 PATCHes the
     PR title whenever it differs (`gh api repos/<o>/<r>/pulls/<n> -X PATCH -f
     title=…`). This is how the operator's condition holds: the PR title always
     equals the squash title minus `(#n)`. The re-run triggers in § "When to
     (re)run" stay as they are, since a change to the record can change the
     title too.
   - The `(pr #tbd)` placeholder goes away, because the number is no longer
     ours to write.
   - Finding the existing comment matches the prefix `Proposed squash `. That
     catches both the new header and the old `title/body:` one on PRs already
     in flight, so the run edits the old comment into the new format instead
     of stacking a second comment.
2. **`/pr` Step 4.** The title is composed per `/squash-message`'s title rules,
   which stay the only home of the format. Step 6 loses its `(pr #N)` remark.
3. **`scripts/check-squash-message.sh`.** It measures one block, the body. The
   title can't be measured any more: it no longer lives in the file, and the
   script must stay free of `gh`, so the 72-char cap is prose in the skill.
   A file still holding two blocks (the old format, restored from history on a
   branch that was in flight across the change) fails, and the message says to
   re-run `/squash-message`.
4. **`/finalize` (description staged).**
   - Step 8 merges with `--subject "<PR title> (#<n>)"`, the title read from
     `gh pr view --json title`, and `--body-file` set to the single block.
   - The subject is passed explicitly because this repo has
     `squash_merge_commit_title = COMMIT_OR_PR_TITLE`. Under that setting,
     a PR with one commit gets the commit's subject as its default title, not
     the PR title.
   - Step 8's stand-down list drops the `(pr #tbd)` → `(pr #N)` exemption.
5. **`/check-merge` (description staged).** Step 3 and the description describe
   one block plus the PR title it keeps in step.
6. **Catalog and pointers.** Update the `/squash-message` entry in
   `catalog/g2-pr-loop.md`, and update `/update-muthur`'s mention of the
   squash `<essence>`, which now names the PR title.
7. **The squash title of this PR** carries `[attn adopters]`. The `Adopters:`
   paragraph asks their operator to set `squash_merge_commit_title` to
   `PR_TITLE` (see the question below), because that setting lives outside
   their tree.

From this PR on, history titles read `… (#n)`. Nothing in the repo parses
`(pr #n)` out of `git log`: the only hits are prose in the skills listed above.

## DRY notes

- The title format stays in one home, `/squash-message`. `/pr` Step 4 and
  `/finalize` Step 8 point at it instead of restating the shape.
- The one PATCH-the-title call exists twice: in `/pr` refresh mode, which
  already does it, and in `/squash-message` Step 4. They don't merge into one
  because they fire at different moments. `/pr` opens or refreshes the PR
  object. `/squash-message` re-syncs on every push that changes the record,
  and that path is the one guaranteeing the title stays current. `/pr`'s
  call stays because `gh pr create` needs a title before the PR exists.
- The comment lookup in `/squash-message` Step 4 and `/finalize` Step 7 already
  shares one mechanic by reference. Only the marker string changes.

## Question

1. **Should I switch this repo's `squash_merge_commit_title` to `PR_TITLE`?**
   Recommended. Without it, the GitHub merge button prefills the commit
   subject instead of the PR title on any PR with a single commit, and that
   breaks the very thing this change relies on. `/finalize and merge` is
   covered either way by its explicit `--subject`; the button is not. It is a
   repository setting outside the diff, so it waits for your yes:
   `gh api repos/vzakharov/muthur -X PATCH -f squash_merge_commit_title=PR_TITLE
   -f squash_merge_commit_message=COMMIT_MESSAGES`. The second field must
   be passed along and keeps its current value: the API takes the title and
   message as a valid pair.
