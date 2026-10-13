# Markdown hard-wrapped at 80 by prettier

## Goal

Every tracked `.md` file diffs line by line: prose hard-wrapped at 80 columns by
prettier (`proseWrap: always`), run automatically after every agent edit and
checked by `scripts/vet.sh`. An unwrapped paragraph is one physical line, so
editing one clause rewrites the whole paragraph in the diff.

This PR is the reflow and its tooling, nothing else, so that its Markdown diff
is pure line breaks an adopter can skip outright.

## Depends on #189 landing first

https://github.com/vzakharov/muthur/issues/189 replaces every table with lists
or sections. prettier cannot wrap a table — a GFM row has to be one line — so it
pads every cell to its column's widest instead, and a table with one
paragraph-sized cell grows delimiter rows hundreds of dashes long. Reflowing
after #189 means this PR touches no table.

**`/go` starts by merging `main`, then checks that no tracked `.md` has a table
delimiter row outside a code fence.** If one remains, #189 has not landed: stop
and report, rather than reflowing over it.

## What the dry run on a copy showed

- prettier 3.8.1 is on `PATH` from the environment (`/opt/node22/bin`); the repo
  has no `package.json` and no prettier config.
- Wrapping all 74 tracked `.md` files changes 72 of them (+5084/−2576). Beyond
  wrapping it only normalizes `*em*` to `_em_`, and adds a `>` to each new
  continuation line of a blockquote.
- **By default prettier also reformats embedded languages**: the YAML
  frontmatter, and the text inside a ` ```markdown ` fence — the attestation and
  table templates in `/finalize` and `/qa-checklist`.
  `embeddedLanguageFormatting: off` leaves both byte-identical, so no skill
  description and no GitHub-bound template changes.
- **CLAUDE.md grows ~620 characters** (continuation lines of list items get a
  two-space indent). The size check reads 29061/30000 today; step 3 re-measures
  against whatever #189 left.

## Approach

1. **Pin prettier in one place.** Add `scripts/prettier.sh`, a wrapper that runs
   `npx --yes prettier@3.8.1 "$@"` — the version lives only there. Add
   `.prettierrc.json` (`proseWrap: always`, `printWidth: 80`) and
   `.prettierignore`.

   **The ignore list is every file whose text becomes a GitHub issue or PR body
   or a comment**, because GitHub renders a newline in those as a line break, so
   hard-wrapped prose posts as ragged 80-column lines:
   - `docs/pr/` — `scripts/pr-body.py`'s `body.md`, PATCHed back as the PR body,
     and the exported PR threads beside it;
   - `docs/issue/` — exported issue threads, quoted verbatim;
   - `docs/remove-before-merging/squash-message.md` — posted as the squash
     proposal comment;
   - `tmp/` — where comment and review-reply drafts are written before posting.

   Text in a code fence inside a skill — a PR-body or comment template — stays
   out of prettier's reach through `embeddedLanguageFormatting: off`.

2. **Stage the always-loaded set** the reformat touches, per
   `.claude/rules/staging.md`: CLAUDE.md, `.claude/voice/voice.md`, and every
   `.claude/rules/*.md` with no `paths:`. Their staged copies are what step 3
   formats (with `--parser markdown`, since the `.staged` suffix hides the
   extension); the real files change once, at `/finalize`'s swap.

3. **Reformat:** `scripts/prettier.sh --write` over every tracked `.md` and
   every staged copy, as a single `style:` commit containing nothing else.
   Re-run `scripts/check-claude-md-size.sh` against the staged CLAUDE.md.

4. **Format automatically and check it.**
   - `.claude/hooks/format-md.sh`, a `PostToolUse` hook on
     `Edit|Write|MultiEdit` registered in `.claude/settings.json`: when the
     touched path is a `.md` or a `.md.staged` copy, it runs
     `scripts/prettier.sh --write` on that one file, which honours
     `.prettierignore`. Claude Code tells the agent a file changed under a
     formatter, so the next edit works from the wrapped text. On failure — say
     `npx` cannot reach the registry — it exits 2 with prettier's message, so
     the agent sees it rather than the edit passing unformatted in silence.
   - `scripts/vet.sh` runs `scripts/check-markdown-wrap.sh`, a
     `scripts/prettier.sh --check` over the tracked `.md` with each staged file
     read through its copy, covered with the hook by
     `scripts/test_markdown_wrap.py`.
   - `scripts/check-skill-catalog.sh` matches a `CLAUDE.md § "…"` citation
     across a line break, which wrapping makes common.
   - `.claude/hooks/install-deps.sh` runs `scripts/prettier.sh --version` once,
     so the first edit of a session does not pay for the download.

5. **Write the convention down where it loads**, in its own path-scoped
   `.claude/rules/markdown-wrap.md`: prettier wraps, and text bound for an
   issue, a PR body or a comment is never hard-wrapped, so a new home for such
   drafts goes into `.prettierignore`.

6. **Catalog the new files** — `.prettierrc.json`, `.prettierignore`,
   `scripts/prettier.sh`, `.claude/hooks/format-md.sh` — in the group that
   carries the prose principles, marked optional for an adopter that wraps with
   its own tooling.

## Adopters

A sync that diffs across the reflow sees nearly every Markdown file rewritten
line by line. Because this commit carries no other Markdown change, the fix is
to skip that part of it. The squash is titled `[attn adopters]` and its body
carries an `Adopters:` paragraph (`/squash-message` § "Format rules") telling
their agent to split the sync at this commit, `C`:

1. **Port `<watermark>..C^` as usual.**
2. **From `C`, port only the tooling and the rule** — the files step 6 catalogs,
   the `settings.json` hook entry, the `vet.sh` and `install-deps.sh` lines, the
   rule, and the citation fix in `check-skill-catalog.sh`. Never port its reflow
   of existing `.md` files as a diff.
3. **Wrap their own Markdown with their own tooling** — each adopter likely has
   a formatter already; the prettier files here are optional. The GitHub-bound
   exemptions hold whatever wraps.
4. **Port `C..<latest>` as usual** — both sides are wrapped by then, so the
   diffs read line by line again.

None of this needs their operator's yes beyond what a sync already asks.

## For the operator

- **The environment setup script needs nothing** — `node`/`npx` are already
  there. `npx` fetches `prettier@3.8.1` through the proxy on first use and
  caches it.

## Decisions

- **prettier comes through `npx`, pinned in `scripts/prettier.sh`.** A root
  `package.json` was ruled out because in a template it tells adopters this is a
  JS project and collides with their own; the environment's unpinned prettier,
  because the formatting would drift when the environment updates.
- **"Automatic" is the `PostToolUse` hook plus the vet check.** Formatting only
  at `/finalize` leaves the branch unwrapped until landing; a git pre-commit
  hook is untracked, so every clone would install it by hand.
- **Tables are #189's**, landed first, so this commit's Markdown diff is pure
  reflow.

## DRY notes

- **One pin site.** `scripts/prettier.sh` is the only place that names the
  prettier version; the hook, `vet.sh` and `install-deps.sh` all call it.
- **One ignore list.** `.prettierignore` is the only statement of which files
  stay unwrapped; the hook and vet both go through prettier, which reads it, so
  neither repeats the paths.
- **The rule is a file of its own, not a paragraph in #189's `markdown.md`.**
  That file is an opt-in an adopter deletes to keep tables, and `vet.sh` keys
  the table check on it, so sharing it would drop the wrap convention with the
  tables; each now goes with its own tooling.
