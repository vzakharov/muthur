---
description: How the path-scoped rule files in this directory work, and what belongs in one
paths:
  - .claude/rules/**
---

# `.claude/rules/`

Path-scoped convention files. Claude Code loads a rule file automatically when a
session touches a file matching its `paths:` globs — so conventions reach the
agent at the moment they're relevant, without being permanently resident in
context the way `CLAUDE.md` is. **A file with no `paths:` loads on every turn**,
exactly as `CLAUDE.md` does, which is why this README carries one — and why
editing such a file goes through a staged copy (`staging.md`).

The directory ships the loop's own three rules — `stack.md` (what
`scripts/vet.sh` exits, and what a stack landing wires), `skills.md` (adding or
renaming a skill) and `staging.md` (editing a file that loads on every turn). Everything else here is yours: rules are mostly project-specific, and the
reusable part is the mechanism. Add rule files as your conventions emerge.

## Format

Each rule is a Markdown file with YAML frontmatter:

```markdown
---
description: One line — what this rule governs, specific enough to be skimmable in a list
paths:
  - src/db/**
  - migrations/**
---

# Database migrations

- Migrations are append-only; never edit one that has run anywhere.
- …
```

- **`description`** — one line, written to be recognizable out of context.
- **`paths`** — globs, relative to the repo root. Quote patterns that start with
  `*` (`'**/*.test.ts'`) so the YAML parses. A single literal path is fine
  (`package.json`).

## What belongs here vs. in `CLAUDE.md`

| | Goes in |
|---|---|
| Holds everywhere in the repo (commit style, error handling, general principles) | `CLAUDE.md` |
| Holds only when touching a particular area (schema rules, styling, test layout, a directory with a trap in it) | a rule file |

The test is scope, not importance. A load-bearing rule that only applies to one
directory still belongs here — that's the point of the mechanism. Moving
area-specific guidance out of `CLAUDE.md` keeps the always-loaded file short
enough to actually be followed; `CLAUDE.md` § "About this file" states the test
for what may stay there.

## Good candidates

- A directory with a non-obvious contract (generated code, a public API barrel,
  a scratch route that must stay auth-free).
- Anything externally owned — schemas provisioned outside the repo, config that
  must be mirrored in a Dockerfile or deploy manifest.
- Traps that have already bitten someone once. If a code review comment would
  apply again to the next person editing that path, it's a rule.
