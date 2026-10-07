> ⛔ **Part of [the catalog](../catalog.md), never vendored** — delete `catalog/` wherever `catalog.md` is deleted.

# Never

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
| `docs/adopting/` | `ADOPTING.md`'s chapters, each read only by some adopters, and the screenshot locating the environment setup script. Goes when that file does, or it is left an orphan. | — | — | never |
| `.claude/skills/update-muthur/catalog.md` | The catalog's index, and one of two rows naming something a skill directory would otherwise carry in: taking `/update-muthur` brings it along, which must not happen. Read it from a fresh clone on every sync instead, so it cannot go stale downstream — both copy steps name it as a carve-out. | — | — | never |
| `.claude/skills/update-muthur/catalog/` | The catalog's parts, one file per group: the same file as the index, split, and never vendored for the same reason. Wherever the index is deleted or carved out, this goes with it. | — | — | never |
| `/detemplate` | Turn a fresh template fork into a project: prune the `never` rows and unused groups, hydrate what stays, hand back the setup script. Routes through `/plan` and deletes itself last. | `gh`, `$GH_TOKEN`; a whole-tree fork, not a subset copy | `/plan` (G2); `/spinoff`, `/update-muthur` (G0) | never |
| `scripts/check-muthur.sh` | The one vet line behind which everything that tests only this repo's own machinery sits, so a sync offers it as a single decision. Keyed on this catalog's presence, so it exits 0 the moment it is downstream. | `bash` | `scripts/check-repo-identity.sh`, `scripts/test_*.py` (both never) | never |
| `scripts/check-repo-identity.sh` | Assert that this repo's own `owner/repo` appears only where a human copies it by hand, and nowhere under a stale name — everything else compares `origin` against the watermark's `repo` field instead. Keyed on this catalog's presence, so it exits 0 the moment it is downstream. | `bash`, `jq`, `git` | — | never |
| `scripts/test_*.py` | The unit tests over the loop's own scripts — today the export's agent/human labelling, its hunk trimming and its layout. They join the line above by matching the pattern, which is why adding one never edits `scripts/vet.sh`. | `python3` ≥3.9 | — | never |
