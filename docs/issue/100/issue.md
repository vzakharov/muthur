# Issue #100: Stage edits to always-loaded files and swap them in at /finalize

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/100
- **Author:** @vzakharov (agent)
- **Created:** 2026-09-23T13:26:44Z
- **Updated:** 2026-09-23T13:26:44Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Problem

Editing an always-loaded file on a branch breaks the prompt cache for every session running on that branch. The file sits at the top of the context, so any change to it forces the whole prefix to be read again, on every turn after the edit. Always-loaded files include `CLAUDE.md`, whatever it imports (`@.claude/voice/voice.md`), and any `.claude/rules/*.md` that has no `paths:`.

#98 got around this by hand. It edited staged copies under `docs/remove-before-merging/` (`CLAUDE.staged.md`, `rules-README.staged.md`) and left the real files alone until `/finalize`, where each copy is `git mv`'d over its original before the quality passes run. The procedure lives only in that PR's plan (§ "Staging") and in a warning at the top of the PR body. Nothing in the loop knows about it, so:

- the next session that edits `CLAUDE.md` loses its cache again, because no rule tells it to stage;
- a `/finalize` that doesn't read the PR body would let the `docs/remove-before-merging/` sweep delete the staged copies, and the change they carry would be lost without anyone noticing.

## What needs to happen

1. **The convention goes in `CLAUDE.md`.** On a branch, edit an always-loaded file only through a staged copy, and swap it in at `/finalize`. Spell out the naming rule: a staged name never ends in `CLAUDE.md`, because a nested `CLAUDE.md` loads on the first read of its directory. Also say that the first commit copies the file unchanged, so every later commit shows up as a diff against the original.
2. **`/finalize` does the swap as a defined step.** Before the quality passes and the vet run, `git mv` each `docs/remove-before-merging/*.staged.*` over the real file it stands for, then commit. The sweep must never delete a staged copy that hasn't been swapped. The mapping from staged name to real path has to be something the step can read, for example a front-matter line or a small manifest, rather than something it guesses from the file name.
3. **Define the set of always-loaded files.** Settle whether it includes skill frontmatter `description:`s, which sit in the system prompt's skill list, and nested `CLAUDE.md` files that a session has already loaded.
4. **Decide whether the vet run should check this.** For example, fail when a staged copy is still present on a branch whose PR is ready for review, or when the swap target doesn't exist.

## Acceptance

- A session asked to edit `CLAUDE.md` stages the edit without being told to.
- `/finalize` on a branch that carries staged copies swaps them in, and the vet run then passes against the real files.
- #98's hand-written warning in the PR body would have been unnecessary.

Raised in review of #98.

---

## Timeline (status, references, and other events)

- **2026-09-23T13:28:41Z** @vzakharov cross-referenced this issue from [#98 feat: #97 trim CLAUDE.md to what every turn needs](https://github.com/vzakharov/muthur/pull/98).
