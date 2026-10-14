---
description: Markdown is hard-wrapped at 80 by prettier, except text bound for a GitHub body or comment
paths:
  - '**/CLAUDE.md'
  - '.claude/**/*.md'
  - .prettierignore
  - .prettierrc.json
  - scripts/prettier.sh
---

# Markdown wrapping

Tracked Markdown is hard-wrapped at 80 columns by prettier, so an edit to one
clause diffs as one line rather than as its whole paragraph, and a file's line
count reads as its length, as it does for code. `.claude/hooks/format-md.sh`
wraps each `.md` an agent edits, and `scripts/vet.sh` checks every tracked one,
both through `scripts/prettier.sh`.

**Text bound for a GitHub issue or PR body, or a comment, is never wrapped**,
because GitHub renders its newlines as line breaks. `.prettierignore` lists
every home such text has in the tree, `tmp/` among them for a one-off draft, and
a new home goes into it.
