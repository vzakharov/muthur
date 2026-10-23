---
description: Markdown is hard-wrapped at 80 by prettier, except text bound for a GitHub body or comment
paths:
  - '**/CLAUDE.md'
  - '.claude/**/*.md'
  - .claude/format.json
  - .prettierignore
  - .prettierrc.json
  - scripts/format.py
  - scripts/prettier.sh
---

# Markdown wrapping

Tracked Markdown is hard-wrapped at 80 columns by prettier, so an edit to one
clause diffs as one line rather than as its whole paragraph, and a file's line
count reads as its length, as it does for code. The `markdown wrap` entry in
`.claude/format.json` does both halves through `scripts/prettier.sh`:
`scripts/format.py` wraps each `.md` an agent edits, and checks every tracked
one in the vet run.

**Text bound for a GitHub issue or PR body, or a comment, is never wrapped**,
because GitHub renders its newlines as line breaks. `.prettierignore` lists
every home such text has in the tree, `tmp/` among them for a one-off draft, and
a new home goes into it.
