# The edit relay: you list the edits, Haiku applies them

An experimental mode of `/go`'s Step 2, on only under `MUTHUR_EDIT_RELAY=on`.
You decide every edit a stretch of work needs and write them out as one list; a
Haiku subagent applies the list in your own tree and reports item by item; you
review the diff and commit. Haiku applies a named change exactly and only as
named, and misreads anything it has to restate — so the list leaves it nothing
to restate.

## Where it pays

Each `Edit` you make yourself is a turn re-reading your whole context, and each
file you open to place an edit stays in that context for the rest of the
session. The relay pays when it saves those:

- the edits land in files you have not read, or read long ago — Haiku does the
  reading, at its own rate and in its own context;
- an anchor is easier to name than to quote: a heading, a function, "the bullet
  that opens **X**" — you need not have the exact text in hand;
- there are enough of them that applying, re-reading after a formatter, and
  retrying a stale anchor would cost you several turns.

It does not pay for edits you could send as parallel `Edit` calls in one turn
from text already in your context: that is one turn either way, and the relay
adds Haiku's run and your review. What `delegation.md` § "What qualifies" keeps
with you stays yours to decide: the relay moves your hands, never your
judgement, so prose the loop executes may go through it once you have written
every word of it into the list.

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

## Launching

`Agent` with `model: "haiku"`, in the foreground, **without** a worktree: it
edits your tree while you wait, so there is nothing to merge. The brief is the
list plus:

- apply each item exactly as written with `Read` then `Edit` or `Write`; change
  nothing the list does not name, and fix nothing it notices;
- an item whose anchor is missing or matches more than one place is skipped and
  reported, never guessed at;
- no commits, no pushes, no other tools' side effects;
- the final message is one line per item: applied, or skipped and why.

## Review and commit

`git diff` whole against the list: every applied item where it belongs, nothing
outside the list, skipped items applied yourself or sent back with a sharper
anchor. Commit under your own name, and say in the body that the relay applied
it and what the review changed.

Then weigh it per `delegation.md` § "Weighing the cost", `--turns` being the
turns the same edits would have taken you, and fold the verdict into the `haiku`
entry of `delegation-model-capabilities.md`.
