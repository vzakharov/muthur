---
description: How the path-scoped rule files in this directory work, and what belongs in one
paths:
  - .claude/rules/**
---

# `.claude/rules/`

Path-scoped convention files. Claude Code loads a rule file when a session reads
a file matching its `paths:` globs — so conventions reach the agent at the moment
they're relevant, without being permanently resident in context the way the root
`CLAUDE.md` is.

**Every `.md` under this directory is a rule, this README included, and one with
no `paths:` loads on every turn**, exactly as `CLAUDE.md` does — which is why this
README carries one, and why editing such a file goes through a staged copy
(`staging.md`). A `CLAUDE.md` here would be a rule too, so this is the one
directory whose own conventions live in a scoped rule file rather than in its
`CLAUDE.md`.

The directory ships the loop's own three rules — `stack.md` (what
`scripts/vet.sh` exits, and what a stack landing wires), `skills.md` (adding or
renaming a skill) and `staging.md` (editing a file that loads on every turn).
Everything else here is yours: rules are mostly project-specific, and the
reusable part is the mechanism. Add rule files as your conventions emerge.

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

The test is scope, not importance. A directory's `CLAUDE.md` loads when a rule
scoped to that directory would — on a read of a file beneath it — and sits where
the next person editing that directory will see it, so a rule file earns its
place only when its globs could not be a directory. Both load on a
`Read` only; CLAUDE.md § "Key principles" on the `Edit`/`Write` tools says what
that costs. What may stay in the root `CLAUDE.md` at all is its § "About this
file"'s test.

## Good candidates

- A kind of file rather than a place — tests, stories, generated code —
  wherever it sits.
- One contract spread over paths that share no parent short of the root: a schema
  provisioned outside the repo and the Dockerfile or deploy manifest that must
  mirror it.
- Traps that have already bitten someone once, when the files they live in share
  a pattern rather than a directory. If a code review comment would apply again
  to the next person editing those files, it's a rule.
