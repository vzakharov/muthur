---
description: Agent-facing Markdown has no tables — lists or sections instead, except as a fenced template for output read rendered
paths:
  - '**/CLAUDE.md'
  - '.claude/**/*.md'
---

# No tables in agent-facing Markdown

Agent-facing Markdown, in CLAUDE.md § "Language"'s sense — the `CLAUDE.md` files
and everything under `.claude/` — is read raw, by agents and in diffs, and a
table row is one physical line, so editing any cell rewrites the whole row in
the diff. What a table buys is the rendered grid, which nobody reading it raw
sees. So:

- **Two columns, key and value** → `- **Key** — value`.
- **Wider** → one item per row, the first cell leading in bold or as a code
  span, the rest after it — as nested items when each is a field of its own.
- **A row whose cells run to paragraphs** → a `###` section per row.

**Markdown a person reads rendered may use a table** where it reads best — a
`README.md`, a doc under `docs/`, a PR body or comment on GitHub. Inside an
agent-facing file, such output is written as a template inside a code fence, the
way `/qa-checklist` shows its classification table.

`scripts/check-markdown-tables.sh`, which `scripts/vet.sh` runs while this file
exists, fails on a table delimiter row outside a fence in the files this rule
covers.
