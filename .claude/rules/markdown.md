---
description: Markdown has no tables — lists or sections instead, except as a fenced template for output read rendered
paths:
  - '**/*.md'
---

# No tables in Markdown

Markdown here is read raw — by agents, and in diffs — and a table row is one
physical line, so editing any cell rewrites the whole row in the diff. What a
table buys is the rendered grid, which almost nobody looks at. So:

- **Two columns, key and value** → `- **Key** — value`.
- **Wider** → one item per row, the first cell leading in bold or as a code
  span, the rest after it — as nested items when each is a field of its own.
- **A row whose cells run to paragraphs** → a `###` section per row.

**Output read rendered keeps its table** — a PR body or comment on GitHub, or a
report a script parses — written inside a code fence as the template it is,
the way `/qa-checklist` shows its classification table.

`scripts/check-markdown-tables.sh`, which `scripts/vet.sh` runs while this file
exists, fails on a table delimiter row outside a fence. The working artifacts
`/finalize` sweeps are outside it, since they hold GitHub's text verbatim or a
parser's input.
