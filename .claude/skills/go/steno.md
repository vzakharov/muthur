# Steno: you dictate the edits, Haiku takes them down

An experimental mode of `/go`'s Step 2, on only under `MUTHUR_STENO=on`. You
decide every edit a stretch of work needs and dictate them as one list; a Haiku
subagent applies the list in your own tree and reports item by item; you review
the diff and commit. Haiku applies a named change exactly and only as named, and
misreads anything it has to restate — so the list leaves it nothing to restate.

## Where it pays

Count waves, not edits. A **wave** is one dictation: you write the list, Haiku
applies it, you review the diff and the tests. Whatever the review turns up — a
missed item, a test the edit broke, a stale line next to an edit — is the next
wave's list, and every wave pays a near-fixed fee: Haiku starting up with this
repository's `CLAUDE.md` and skill listing, plus your dictating and reviewing
turns, each a re-read of your whole context. Editing directly pays that re-read
once per turn instead, and absorbs what it finds on the spot: you write the next
edit looking at the last one's result.

So the mode pays when the work is settled and mechanical — a design already
decided, edits you could name without seeing each other's results, landing in
files you have not read or read long ago — and costs when each step teaches the
next. An edit's size barely matters: its text is output you pay for once either
way.

**Forecast before dictating.**
`python3 .claude/costs/delegation.py --forecast --turns <n> --waves <w>` prices
both from your current context: `<n>` the turns the work would take you —
sequential `Edit`s, test runs and fixes, not the one-turn ideal of parallel
calls — and `<w>` the waves you expect, counting one for what the review usually
turns up. Dictate only where steno comes out cheaper.

What `delegation.md` § "What qualifies" keeps with you stays yours to decide:
steno moves your hands, never your judgement, so prose the loop executes may go
through it once you have written every word of it into the list.

## The list

One numbered item per edit, each standing alone:

- **file** — the path from the repository root;
- **where** — text to find, quoted exactly and unique in the file, or a
  structural anchor that names one place only ("after the line `## Launching`",
  "the end of the file", "the `def main` function's first line");
- **what** — the exact text to put there, fenced, whole: never "reword this",
  "add a test for X" or "update the docs to match". A new file's item is its
  whole content.

A change the same in many places is still one item per place: Haiku does not
look for the same defect elsewhere, so "and everywhere else it appears" is an
instruction it will half-follow.

A formatter re-wraps a Markdown paragraph after every edit to it, so a second
item in the same paragraph anchors on a short phrase within one line, never on a
line break: the break it quoted may have moved.

## Launching

`Agent` with `model: "haiku"`, in the foreground, **without** a worktree: it
edits your tree while you wait, so there is nothing to merge. The brief is the
list plus:

- apply each item exactly as written with `Read` then `Edit` or `Write`;
- change nothing the list does not name, and list in the final message anything
  near an edit that looks wrong or stale, with its file and line;
- an item whose anchor is missing or matches more than one place is skipped and
  reported, never guessed at;
- no commits, no pushes, no other tools' side effects;
- the final message is one line per item, applied or skipped and why, then what
  it noticed.

## Review and commit

`git diff` whole against the list: every applied item where it belongs, nothing
outside the list, skipped items applied yourself or sent back with a sharper
anchor. What Haiku noticed is checked, not trusted, and what holds goes into the
next wave or your own edit. Commit under your own name, and say in the body that
steno applied it and what the review changed.

Then weigh it per `delegation.md` § "Weighing the cost", adding the forecast's
inputs: `delegation.py <agent-id> --turns <n> --waves <w>`, with the `<n>` and
`<w>` you forecast with. That files the wave's forecast beside its measured cost
on the ledger branch, which is what later forecasts calibrate from. Fold the
verdict into the `haiku` entry of `delegation-model-capabilities.md`.
