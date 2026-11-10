> ⛔ **Part of [the catalog](../catalog.md), never vendored** — delete
> `catalog/` wherever `catalog.md` is deleted.

# G12 — Artifacts

Reusable claude.ai artifacts, built from TypeScript in a tree of their own. The
cost is a Node toolchain and a scoped `node_modules` in a repo that may have
neither, and whether a review surface outside GitHub is worth that is the
operator's call — the entry is `opt-in: ask`. A yes adds the directory and the
skill, and with them a vet step and an install step; a no adds nothing, and the
two lines that key on the directory stay quiet.

- `.claude/artifacts/` — The home of artifact apps: a scoped `package.json`
  (TypeScript run by plain `node`, esbuild, zod, and the MASD checkers —
  ESLint's boundaries, Steiger, `check:masd`, `masd:clusters`, madge), the apps
  under `src/` composed along `src/masd.json`, and its own `vet.sh`.
  `scripts/vet.sh` and `.claude/hooks/install-deps.sh` each carry one line keyed
  on the directory.
  - **Requires:** node ≥22.18, pnpm, in the environment setup script
  - **Pulls in:** `scripts/run-parallel.sh` and `scripts/prettier.sh` (G1)
  - **Disposition:** adopt — **opt-in: ask**
- `/review-board` — Builds a branch's changed files into the review board
  artifact, publishes it with its URL in a sticky PR comment, and handles the
  line comments sent to Claude from it as review feedback: fix, push, republish,
  reply with the commit.
  - **Requires:** `gh`, the `comments`, `db` and `user` artifact capabilities
  - **Pulls in:** `.claude/artifacts/`, `scripts/pr-comment.sh` (G2), `/handle`
    (G2), whose feedback lane it follows; the watch hand-over across a relay is
    `/relay`'s, in G2
  - **Disposition:** adopt — **opt-in: ask**, with the directory
