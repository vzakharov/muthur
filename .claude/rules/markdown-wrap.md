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
clause diffs as one line rather than as its whole paragraph.
`.claude/hooks/format-md.sh` wraps each `.md` an agent edits, and
`scripts/vet.sh` checks every tracked one, both through `scripts/prettier.sh`.

**Text bound for a GitHub issue or PR body, or a comment, is never wrapped**,
because GitHub renders its newlines as line breaks. Such a draft goes under
`tmp/` or outside the tree, which nothing wraps; a new home for such drafts
inside the tree goes into `.prettierignore`.
