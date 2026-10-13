> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# Markdown: no tables, hard-wrapped at 80 by prettier

## Goal

Every tracked `.md` file diffs line by line:

- **No tables.** A table row is one physical line however much prose it holds,
  so any edit to a cell rewrites the whole row in the diff, and prettier's
  column alignment rewrites every row when one cell widens. Tables earn their
  keep only rendered, and these files are read raw — by agents and in diffs.
- **Prose hard-wrapped at 80 columns**, by prettier (`proseWrap: always`), run
  automatically after every agent edit and checked by `scripts/vet.sh`.

## What the dry run on a copy showed

- prettier 3.8.1 is on `PATH` from the environment (`/opt/node22/bin`); the repo
  has no `package.json` and no prettier config.
- Wrapping all 74 tracked `.md` files changes 72 of them (+5084/−2576). Beyond
  wrapping it only normalizes `*em*` to `_em_` and pads table cells.
- **prettier does not wrap tables** — it can't, a GFM row has to be one line. It
  pads every cell to its column's widest, so a table with one paragraph-sized
  cell grows delimiter rows hundreds of dashes long. This is why the tables go
  before the reformat, not after.
- Under an indented table inside a list (CLAUDE.md's routing ladder) it dropped
  the blank line before the nested list that follows. Moot once that table is a
  list.
- **Skill frontmatter is reflowed but parses to the same value** (checked with a
  YAML load), so the skill listing's text — and the prompt cache — is unchanged,
  and no `SKILL.md` needs staging for it.
- **CLAUDE.md grows ~620 characters** (continuation lines of list items get a
  two-space indent). The size check reads 29061/30000 today, so it lands near
  29700 before the table conversion's own delta. Tight but under; step 4
  re-measures.
- 30 tables live outside code fences across 29 files; 2 more sit inside fences.
- **One script parses tables**: `scripts/check-skill-catalog.sh` reads catalog
  rows as `^\| *\`path\` *\|`. Converting the catalog means changing that parser
  in the same commit.

## Approach

Each step is its own commit, in this order, so the table conversion is reviewed
unwrapped and the reformat is a pure whitespace-and-emphasis commit.

1. **Pin prettier in one place.** Add `scripts/prettier.sh`, a wrapper that runs
   `npx --yes prettier@3.8.1 "$@"` — the version lives only there. Add
   `.prettierrc.json` (`proseWrap: always`, `printWidth: 80`) and
   `.prettierignore` (`tmp/`, `docs/issue/` — exported GitHub threads are quoted
   verbatim and swept at `/finalize`). Nothing is reformatted yet.

2. **Convert every unfenced table** to a list, or to sections where a row is
   long enough to be a subsection of its own:
   - a two-column key/value table becomes `- **Key** — value`;
   - a wider table becomes one list item per row, the first cell leading in bold
     and the other cells as the item's sentences, or as nested items when they
     are separate facts;
   - a row whose cells run to paragraphs (`/hotfix`'s concerns, `/pr`'s
     invocation modes) becomes a `###` section;
   - the meaning each table carries stays exactly as is — this is a change of
     shape, and every converted table is re-read against its original before
     the commit.

   **Exception: a table that is a template for GitHub-rendered output** — today
   only `/qa-checklist`'s, which `/pr` writes into the PR body, where people do
   read it rendered. It moves inside a fenced block so it reads as an output
   template and prettier leaves it alone. The two tables already fenced stay.

   **The catalog** (`.claude/skills/update-muthur/catalog.md` and `catalog/*.md`)
   becomes one list item per entry, `` - `path` — … ``, and
   `scripts/check-skill-catalog.sh` reads the first backticked token of a
   top-level list item instead of a table row's first cell. Prose that
   describes the catalog's shape — "row", "first column" in `/update-muthur`,
   `/detemplate`, `.claude/skills/CLAUDE.md`, CLAUDE.md — says "entry" instead.

   CLAUDE.md's routing ladder goes through a staged copy
   (`scripts/staged.sh stage CLAUDE.md`), per `.claude/rules/staging.md`.

3. **Stage the rest of the always-loaded set** that the reformat will touch:
   `.claude/voice/voice.md` and every `.claude/rules/*.md` with no `paths:`.
   Their staged copies are what step 4 formats (with `--parser markdown`, since
   the `.staged` suffix hides the extension); the real files change once, at
   `/finalize`'s swap.

4. **Reformat:** `scripts/prettier.sh --write` over every tracked `.md` and
   every staged copy, as a single `style:` commit. Re-run
   `scripts/check-claude-md-size.sh` against the staged CLAUDE.md.

5. **Format automatically and check it.**
   - `.claude/hooks/format-md.sh`, a `PostToolUse` hook on `Edit|Write|MultiEdit`
     registered in `.claude/settings.json`: when the touched path is a `.md` or
     a `.md.staged` copy, it runs `scripts/prettier.sh --write` on that one
     file. Claude Code tells the agent a file changed under a formatter, so the
     next edit works from the wrapped text. On failure — say `npx` cannot reach
     the registry — it exits 2 with prettier's message, so the agent sees it
     rather than the edit passing unformatted in silence.
   - `scripts/vet.sh` runs `scripts/prettier.sh --check` over the tracked `.md`
     and the staged copies, beside its other repo-wide checks.
   - `.claude/hooks/install-deps.sh` runs `scripts/prettier.sh --version` once,
     so the first edit of a session does not pay for the download.

6. **Write the convention down where it loads.** A path-scoped
   `.claude/rules/markdown.md` (`paths: ["**/*.md"]`), so it arrives on the read
   of any Markdown file: no tables, lists or sections instead, the
   GitHub-output exception, and that wrapping is prettier's job — never wrap or
   unwrap by hand. And a guard in `scripts/vet.sh`: a small check that fails on
   a table delimiter row outside a code fence in any tracked `.md`.

7. **Catalog the new files** — `.prettierrc.json`, `.prettierignore`,
   `scripts/prettier.sh`, `.claude/hooks/format-md.sh`,
   `.claude/rules/markdown.md`, the table check — in the catalog group that
   carries the prose principles, so `/update-muthur` and `/detemplate` know
   they exist.

## For the operator

- **Every adopter's next `/update-muthur` sees all of this at once**: nearly
  every Markdown file reflowed, plus a hook that reflows their own. Their local
  edits to the same files will conflict on sync. That is the price of the
  change, paid once.
- **The environment setup script needs nothing** — `node`/`npx` are already
  there. `npx` fetches `prettier@3.8.1` through the proxy on first use and
  caches it.

## DRY notes

- **One pin site.** `scripts/prettier.sh` is the only place that names the
  prettier version; the hook, `vet.sh` and `install-deps.sh` all call it.
- **One table parser.** `scripts/check-skill-catalog.sh` stays the only code that
  reads catalog entries; the list form changes its one regex, nothing else.
- **No table-to-list converter script.** The 30 tables differ in shape and in
  what their cells say, and a generic converter produces mechanical prose that
  then needs rewriting by hand anyway. Converting by hand is the cheaper path
  for a one-time change; the vet guard keeps the result from regressing.
- **The table guard is new code, not a prettier option** — prettier has no
  setting to forbid tables, and markdownlint (which does) would add a second
  Markdown toolchain for one rule.

## Open questions

Each has a recommendation, and the plan above is written with it in force.

1. **Where prettier comes from.**
   - a) _(recommended)_ `scripts/prettier.sh` running `npx --yes prettier@3.8.1`
     — pinned, no `package.json`, which in a template would tell adopters this
     is a JS project and collide with their own.
   - b) a root `package.json` with prettier as a devDependency and a lockfile,
     installed by `install-deps.sh` — offline-proof, but see a).
   - c) whatever prettier the environment has — unpinned; the formatting drifts
     when the environment updates.
2. **What "automatically" means.**
   - a) _(recommended)_ the `PostToolUse` hook plus the vet check.
   - b) the vet check only, with `/finalize` running `--write` before it — no
     reflow mid-session, but the branch carries unwrapped text until landing.
   - c) a git pre-commit hook — not tracked by git, so every clone has to
     install it by hand.
3. **The catalog.**
   - a) _(recommended)_ convert it like the rest and change the parser — it is
     the biggest table set and the one that diffs worst.
   - b) keep it as the one exception.
4. **Guarding against new tables.**
   - a) _(recommended)_ the path-scoped rule plus the vet check.
   - b) the rule only.
