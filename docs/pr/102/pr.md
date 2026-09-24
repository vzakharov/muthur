# PR #102: feat: #100 stage edits to always-loaded files, swap them in at /finalize

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/102
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/stage-always-loaded-b0surt
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-23T13:41:00Z
- **Updated:** 2026-09-23T14:02:38Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- Editing `CLAUDE.md` (or anything else rendered into every request's prefix) on a branch invalidates the prompt cache of every session on it. #98 worked around that by hand; this makes it part of the loop.
- New `scripts/staged.sh` stages a byte-identical copy under `docs/remove-before-merging/` through a manifest (staged name → real path → blob at staging time), and swaps it back with a three-way merge when the real file moved meanwhile, so a base merge's edit is never dropped.
- `CLAUDE.md` states the rule; new path-scoped `.claude/rules/staging.md` defines the always-loaded set (root `CLAUDE.md` and its imports, unpathed rules, skill `description:`s) and the conventions. `/finalize` swaps before the quality passes and refuses to sweep an unswapped copy; `/polish` reads a copy by its diff against the real file; the vet run checks the manifest, and cites into a staged `CLAUDE.md` through its copy.
- The branch dogfoods it: its own `CLAUDE.md` edit rides a staged copy that its `/finalize` swaps in.

## QA Checklist

- [ ] `stage` — `scripts/staged.sh stage CLAUDE.md` creates `docs/remove-before-merging/CLAUDE.staged.md` identical to `CLAUDE.md` plus a manifest row; staging it twice, or an untracked path, is refused.
- [ ] `swap-clean` — edit the staged copy, run `swap`: the edit lands in `CLAUDE.md`, the staged file and manifest are gone.
- [ ] `swap-drift` — stage, then change the real file separately (as a base merge would), edit the staged copy elsewhere, run `swap`: both edits survive; overlapping edits stop with conflict markers.
- [ ] `check` — a stray `*.staged.*` with no manifest row, or a row whose target is missing, fails `./scripts/vet.sh`.
- [ ] `sweep-guard` — `/finalize` on a branch with a staged copy swaps it in before `/polish`, and `check --empty` blocks the sweep if anything is still staged.
- [ ] `rule-fires` — a fresh session asked to edit `CLAUDE.md` stages it without being told to.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `stage` | unit | ✅ | `scripts/test_staged.py` in a throwaway repo |
| `swap-clean` | unit | ✅ | same |
| `swap-drift` | unit | ✅ | same, clean and conflicting merges |
| `check` | unit | ✅ | same, each failure mode |
| `sweep-guard` | manual-only | — | Procedure in a skill; observed on this PR's own `/finalize` |
| `rule-fires` | manual-only | — | Agent behavior against a prompt |

Closes #100

https://claude.ai/code/session_012CNM7NfUyxaw7a7w9F5uZV

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-23T13:41:13Z — "Proposed squash title/body: ``` feat: #100 stage edits to al…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-23T13:41:13Z

[https://github.com/vzakharov/muthur/pull/102#issuecomment-5795920225](https://github.com/vzakharov/muthur/pull/102#issuecomment-5795920225)

Proposed squash title/body:

```
feat: #100 stage edits to always-loaded files, swap at /finalize (pr #102)
```

```
Editing CLAUDE.md, or anything else rendered into the prefix of every
request, invalidates the prompt cache of every session on the branch.
#98 avoided that by editing staged copies by hand, a procedure only its
own plan knew about, which left the next edit uncached and the copies
one careless sweep away from being deleted with their change.

scripts/staged.sh now owns the mechanics. `stage` copies a file
byte-identical under docs/remove-before-merging/ and records the
staged name, the real path and the file's blob in a manifest, so
nothing is guessed from a file name. `swap` puts each copy back, with a
three-way merge when the real file moved since staging, so a base
merge's edit is never overwritten. `check` holds the manifest and the
directory to each other, and runs in the vet run.

CLAUDE.md states the rule. A path-scoped .claude/rules/staging.md
defines the always-loaded set (the root CLAUDE.md and its imports,
rules with no paths:, skill description:s) and arrives whenever one of
those files is opened. /finalize swaps before its quality passes, and
refuses to sweep docs/remove-before-merging/ while anything is staged.

Closes #100

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:12 — unresolved — last: @vzakharov (human) 2026-09-23T13:59:37Z — "археология" → [↓](#t01)
- **T02** `.claude/rules/staging.md`:1 — unresolved — last: @vzakharov (human) 2026-09-23T14:00:33Z — "давай добавим ещё какую-то формулировку, которую агент будет…" → [↓](#t02)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:12 — unresolved

```diff
@@ -0,0 +1,35 @@
… 6 lines elided …
+```
+Editing CLAUDE.md, or anything else rendered into the prefix of every
+request, invalidates the prompt cache of every session on the branch.
+#98 avoided that by editing staged copies by hand, a procedure only its
+own plan knew about, which left the next edit uncached and the copies
+one careless sweep away from being deleted with their change.
```

**@vzakharov (human)** — 2026-09-23T13:59:37Z

археология

---

<a id="t02"></a>

### `.claude/rules/staging.md`:1 — unresolved

**@vzakharov (human)** — 2026-09-23T14:00:33Z

давай добавим ещё какую-то формулировку, которую агент будет понимать как "давай за swap-им обратно". Иногда, ценой кэша, это помогает продогфудить какие-то вещи в пиаре.

---

## Timeline (status, references, and other events)

- **2026-09-23T14:02:38Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/102#pullrequestreview-5291984851.
