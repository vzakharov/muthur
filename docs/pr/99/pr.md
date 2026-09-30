# PR #99: feat: one directory's conventions go in its own CLAUDE.md

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/99
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← claude/nested-claudemd-over-rules-4tdcis
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-23T13:10:28Z
- **Updated:** 2026-09-30T17:24:45Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- One directory's conventions now go in that directory's own `CLAUDE.md`. `.claude/rules/` is kept for globs no single directory bounds (`'**/*.test.ts'`, several scattered paths). Measured on Claude Code 2.1.280: both load at the same moment, on a `Read` of a file they cover, and the nested file sits where the directory's next editor looks and travels with the directory.
- Neither loads on the `Write` that creates a new file, nor through Bash. That is now the second reason in the CLAUDE.md principle to use `Read`/`Edit`/`Write`, with the working rule "read something in a directory before creating a file in it".
- `.claude/rules/README.md` gets `paths: ['.claude/rules/**']`. Every `.md` in that directory is a rule, so the unscoped README was loading into every session.
- The other places that stated the old convention now match: tend-prose's homes table, ADOPTING, the catalog row, squash-message, qa-checklist and spinoff.

## QA Checklist

- [ ] `readme-scoped` — in a fresh session from the repo root, `.claude/rules/README.md` is not in the startup context, and it appears after a `Read` of any file in `.claude/rules/`.
- [ ] `nested-loads` — a `Read` of `.claude/costs/report.py` brings `.claude/costs/CLAUDE.md` into context.
- [ ] `one-home` — `grep -rn "rules/" CLAUDE.md ADOPTING.md .claude/skills` shows no place still saying a single directory's conventions go in `.claude/rules/`.
- [ ] `catalog` — `./scripts/check-skill-catalog.sh` passes.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `readme-scoped` | manual-only | no | Needs a fresh Claude Code session; checked on 2.1.280 in a scratch repo with a marker string |
| `nested-loads` | manual-only | no | Checked live in the authoring session |
| `one-home` | unit | no | A grep, but no check asserts it |
| `catalog` | unit | yes | Runs in `scripts/vet.sh` |

https://claude.ai/code/session_017QoXj56LQkFUHtBSYfTkBK

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-23T13:10:42Z — "Proposed squash title/body: ``` feat: one directory's conven…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-23T13:10:42Z

[https://github.com/vzakharov/muthur/pull/99#issuecomment-5795448880](https://github.com/vzakharov/muthur/pull/99#issuecomment-5795448880)

Proposed squash title/body:

```
feat: one directory's conventions go in its own CLAUDE.md (pr #99)
```

```
A nested CLAUDE.md and a .claude/rules/ file scoped to one directory
load at the same moment: on a Read of a file they cover, and again on
the next such read after compaction. Measured on Claude Code 2.1.280,
neither loads on the Write that creates a new file, nor through Bash.
The nested file sits beside the code its next editor opens and travels
with its directory, so it is now the home for one directory's
conventions, and .claude/rules/ is kept for globs no directory bounds.

The Read/Edit/Write principle gains a second reason: those tools are
what load a directory's conventions, so an agent reads something in a
directory before creating a file there, until
anthropics/claude-code#96361 makes Write load them too. The rules
README scopes itself to its own directory with paths:, since every .md
under .claude/rules/ is a rule and an unscoped one loads into every
session. tend-prose's homes table and the other places stating the old
convention follow.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/rules/README.md`:5 — unresolved — last: @vzakharov (human) 2026-09-30T17:22:23Z — "не нарушаем ли мы этим самым правилом требования этого прави…" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:4 — unresolved — last: @vzakharov (human) 2026-09-30T17:23:55Z — "давай добавим `ADOPTERS, read body` где-то в начале. А в бод…" → [↓](#t02)

<a id="t01"></a>

### `.claude/rules/README.md`:5 — unresolved

```diff
@@ -1,12 +1,22 @@
+---
+paths:
+  - '.claude/rules/**'
+---
+
```

**@vzakharov (human)** — 2026-09-30T17:22:23Z

не нарушаем ли мы этим самым правилом требования этого правила, где говорим, что если правило относится к одной папке, оно лежит в виде CLAUDE.md в этой папке?

---

<a id="t02"></a>

### `docs/remove-before-merging/squash-message.md`:4 — unresolved

```diff
@@ -0,0 +1,30 @@
+Proposed squash title/body:
+
+```
+feat: one directory's conventions go in its own CLAUDE.md (pr #99)
```

**@vzakharov (human)** — 2026-09-30T17:23:55Z

давай добавим `ADOPTERS, read body` где-то в начале. А в боди соответственно добавим что адоптерам предлагается сделать свип по своим правилам и посмотреть, какие из них стоит переделать в папочные клод.мд

---

## Timeline (status, references, and other events)

- **2026-09-30T17:24:45Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/99#pullrequestreview-5369651527.
