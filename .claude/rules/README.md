---
paths:
  - '.claude/rules/**'
---

# `.claude/rules/`

Path-scoped convention files. Claude Code loads a rule file when a session reads
a file matching its `paths:` globs — so conventions reach the agent at the moment
they're relevant, without being permanently resident in context the way the root
`CLAUDE.md` is.

**Every `.md` under this directory is a rule, this README included.** One with no
`paths:` loads into every session at launch, which is why this file scopes itself
to the directory it describes.

**This directory ships with no rules on purpose.** Rules are inherently
project-specific; the reusable part is the mechanism. Add rule files as your
conventions emerge.

## Format

Each rule is a Markdown file with YAML frontmatter:

```markdown
---
description: One line — what this rule governs, specific enough to be skimmable in a list
paths:
  - '**/*.test.ts'
  - '**/*.test.tsx'
---

# Unit tests

- Mock at the HTTP boundary, never an internal module.
- …
```

- **`description`** — one line, written to be recognizable out of context.
- **`paths`** — globs, relative to the repo root. Quote patterns that start with
  `*` (`'**/*.test.ts'`) so the YAML parses. A single literal path is fine
  (`package.json`).

## What belongs here vs. in a `CLAUDE.md`

| | Goes in |
|---|---|
| Holds everywhere in the repo (commit style, error handling, general principles) | the root `CLAUDE.md` |
| Holds in one directory's files (schema rules under `src/db/`, a directory with a trap in it) | that directory's own `CLAUDE.md` |
| Holds in files no single directory bounds (`'**/*.test.ts'`, several scattered paths) | a rule file here |

The test is scope, not importance. A directory's `CLAUDE.md` loads exactly as a
rule scoped to that directory would — on a read of a file beneath it — and it
sits where the next person editing that directory will see it, so a rule file
earns its place only when its globs could not be a directory. Both load on a
`Read` only; CLAUDE.md § "Key principles" on the `Read`/`Edit`/`Write` tools says
what that costs.

## Good candidates

- A kind of file rather than a place — tests, stories, generated code —
  wherever it sits.
- One contract spread over paths that share no parent short of the root: a schema
  provisioned outside the repo and the Dockerfile or deploy manifest that must
  mirror it.
- Traps that have already bitten someone once, when the files they live in share
  a pattern rather than a directory. If a code review comment would apply again
  to the next person editing those files, it's a rule.
