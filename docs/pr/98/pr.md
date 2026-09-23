# PR #98: feat: #97 trim CLAUDE.md to what every turn needs

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/98
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/trim-claude-md-w8am6w
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-23T12:18:01Z
- **Updated:** 2026-09-23T13:11:30Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

> ⚠️ **`/finalize` must swap the staged files in first.** Editing an always-loaded file invalidates the prompt cache of the session doing it, so the new `CLAUDE.md` and `.claude/rules/README.md` are on this branch as `docs/remove-before-merging/CLAUDE.staged.md` and `rules-README.staged.md`. Before its quality passes, `git mv` each over its real file and commit — otherwise `docs/remove-before-merging/`'s sweep deletes the trim. The plan's § "Staging" records this.

## Summary

- Writes the test for what may stay in `CLAUDE.md` into § "About this file": a line stays only when it has to hold on turns where the process it concerns is not being run, and when nothing narrower loads at the moment it matters. `/tend-prose`'s lens 1 sends every root-`CLAUDE.md` line through it and gains the skill and colocated-`CLAUDE.md` homes.
- Applies it to every section: ~6,500 words → ~3,550. The vetting exit rule goes to a new `.claude/rules/stack.md` (manifests, toolchain pins, `vet.sh`, `install-deps.sh`), skill authoring to `.claude/rules/skills.md` (`.claude/skills/**`), and four skills take the rest (`/task`, `/pr`, `/polish`, `/branch-rename`). Text a hook or skill already carried is cut. The rules README gets its own `paths:`, since without one it loaded every turn too.
- Repoints the moved citations, normalises every citation into a `CLAUDE.md` to the `§ "…"` form, and adds `check-skill-catalog.sh` assertion 6: a section citation, or a `CLAUDE.md#anchor` link, that names no heading fails the vet run. It follows a nested `CLAUDE.md`'s path, so `.claude/costs/` citations are checked too.
- Tells adopters, in `ADOPTING.md` § "Reconcile `CLAUDE.md`" and the catalog, to hold their whole merged `CLAUDE.md` to the test and to drop the loop-is-the-product commit rule; `/detemplate` Step 4 deletes that rule directly.

## QA Checklist

- [ ] `test-stated-once` — The test appears once, in the staged `CLAUDE.md` § "About this file"; `/tend-prose`, the rules README and `ADOPTING.md` point at it without paraphrase.
- [ ] `sections-checked` — Every section of the staged `CLAUDE.md` reads as something a turn with no skill loaded still needs.
- [ ] `moves-landed` — Each moved paragraph is present in its named home (rule file, skill, hook message), not just deleted.
- [ ] `citations-resolve` — With the staged files swapped in, `./scripts/vet.sh` passes; renaming `## Language` makes assertion 6 fail on `detemplate` and `ADOPTING.md`.
- [ ] `rules-load` — After the merge, reading `package.json` (or `scripts/vet.sh`) surfaces `.claude/rules/stack.md`; reading a `.claude/skills/*/SKILL.md` surfaces `.claude/rules/skills.md`; the rules README no longer loads on turns that touch nothing under `.claude/rules/`.
- [ ] `import-intact` — The unbackticked `@.claude/voice/voice.md` import still loads the voice rule.
- [ ] `swap-done` — After `/finalize`, `docs/remove-before-merging/` is gone and `CLAUDE.md` is the trimmed text.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `test-stated-once` | grep | no | reviewer read |
| `sections-checked` | manual | no | judgment call, per section |
| `moves-landed` | manual | no | diff read |
| `citations-resolve` | vet | yes | assertion 6; the rename was run against a swapped scratch tree |
| `rules-load` | manual | no | live session only |
| `import-intact` | vet | partly | `check-skill-catalog.sh` checks `CLAUDE.md` imports |
| `swap-done` | shell | no | `/finalize`'s own check |

Closes #97

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_015Qc785VvP7pYgXbSZKPFHB

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-23T12:18:11Z — "Proposed squash title/body: ``` feat: #97 trim CLAUDE.md to…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-23T12:18:11Z

[https://github.com/vzakharov/muthur/pull/98#issuecomment-5794661030](https://github.com/vzakharov/muthur/pull/98#issuecomment-5794661030)

Proposed squash title/body:

```
feat: #97 trim CLAUDE.md to what every turn needs (pr #98)
```

```
CLAUDE.md loads in full on every turn and had grown to ~6,500 words,
most of it procedure that only a session running a particular skill
needs. A rule buried in a long always-loaded file is followed less
reliably than one that loads when it applies.

The file now states its own test in § "About this file": a line stays
only when it must hold on turns where the process it concerns is not
running, and when nothing narrower loads at the moment it matters.
Every section was held to it. The vetting exit rule and the
skill-authoring rules moved to path-scoped `.claude/rules/` files,
other procedure moved into the skills that run it, and text a hook or
skill already carried was cut.

Section citations into CLAUDE.md are normalised and checked by
`check-skill-catalog.sh`, so a moved or renamed section fails the vet
run instead of leaving a dangling reference. Adopters are told,
through the catalog and ADOPTING.md, to hold their whole CLAUDE.md to
the same test; /tend-prose's existence lens holds new lines to it.

Closes #97

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Timeline (status, references, and other events)

- **** @vzakharov reviewed (PENDING): https://github.com/vzakharov/muthur/pull/98#pullrequestreview-5291570409.
