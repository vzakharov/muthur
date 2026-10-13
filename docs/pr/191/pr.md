# PR #191: feat: limit the no-tables rule to agent-facing Markdown

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/191
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/markdown-tables-agent-facing
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-13T19:45:30Z
- **Updated:** 2026-10-13T19:45:55Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 1

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `docs/remove-before-merging/squash-message.md`:19 — unresolved — last: @vzakharov (human) 2026-10-13T19:48:49Z — "а где мы обращаемся к адоптерам с этим?" → [↓](#t01)

---

## Body

## Summary

- `.claude/rules/markdown.md` and `scripts/check-markdown-tables.sh` now cover only agent-facing Markdown: every `CLAUDE.md` and the `.md` files under `.claude/`. A README or a doc under `docs/` is read rendered, where a table is the point, so it is left to its author.
- The catalog's `opt-in: ask` for the rule stays the adopter's call, and now carries the rule of thumb to offer with it: Markdown only agents read gets no tables; Markdown a person may read rendered uses them where they help.
- The check's tests follow the new scope: a nested `CLAUDE.md` is checked, a `README.md` and `docs/` are not.

Follow-up to #190.

## QA Checklist

- [ ] `vet` — `./scripts/vet.sh` passes.
- [ ] `agent-table` — a table added to any `.claude/**/*.md` or `CLAUDE.md` fails `scripts/check-markdown-tables.sh`, naming the file and line.
- [ ] `human-table` — a table added to `README.md` or a file under `docs/` passes it.

```
| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `vet` | yes | yes | the vet run itself |
| `agent-table` | yes | yes | test_markdown_tables.py |
| `human-table` | yes | yes | test_markdown_read_rendered_is_skipped |
```

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-13T19:45:40Z — "Proposed squash title/body: ``` feat: limit the no-tables ru…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-13T19:45:40Z

[https://github.com/vzakharov/muthur/pull/191#issuecomment-6153786791](https://github.com/vzakharov/muthur/pull/191#issuecomment-6153786791)

Proposed squash title/body:

```
feat: limit the no-tables rule to agent-facing Markdown (pr #191)
```

```
A table earns its place where a person reads Markdown rendered, and
costs only where it is read raw: by agents, and in diffs, where editing
one cell rewrites the whole row. The rule from #190 covered every .md
alike, which was the wrong split to hand adopters as the house default.

.claude/rules/markdown.md and scripts/check-markdown-tables.sh now cover
agent-facing Markdown only: every CLAUDE.md and the .md files under
.claude/. A README or a doc under docs/ is left to its author.

The catalog's opt-in ask stays the adopter's call and carries that split
as its rule of thumb: Markdown only agents read gets no tables, Markdown
a person may read rendered uses them where they help.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:19 — unresolved — last: @vzakharov (human) 2026-10-13T19:48:49Z — "а где мы обращаемся к адоптерам с этим?" → [↓](#t01)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:19 — unresolved

```diff
@@ -0,0 +1,26 @@
… 13 lines elided …
+agent-facing Markdown only: every CLAUDE.md and the .md files under
+.claude/. A README or a doc under docs/ is left to its author.
+
+The catalog's opt-in ask stays the adopter's call and carries that split
+as its rule of thumb: Markdown only agents read gets no tables, Markdown
+a person may read rendered uses them where they help.
```

**@vzakharov (human)** — 2026-10-13T19:48:49Z

а где мы обращаемся к адоптерам с этим?

---

## Timeline (status, references, and other events)

- **2026-10-13T19:48:56Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/191#pullrequestreview-5509094991.
