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
   `.prettierignore`. Nothing is reformatted yet.

   **The ignore list is every file whose text becomes a GitHub issue or PR
   body or a comment**, because GitHub renders a newline in those as a line
   break, so hard-wrapped prose posts as ragged 80-column lines:
   - `docs/pr/` — `scripts/pr-body.py`'s `body.md`, PATCHed back as the PR
     body, and the exported PR threads beside it;
   - `docs/issue/` — exported issue threads, quoted verbatim;
   - `docs/remove-before-merging/squash-message.md` — posted as the squash
     proposal comment;
   - `tmp/` — where comment and review-reply drafts are written before
     posting.

   Text in a code fence inside a skill — a PR-body or comment template — is
   already outside prettier's reach.

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
   GitHub-output exception, that wrapping is prettier's job — never wrap or
   unwrap by hand — and that text bound for an issue, a PR body or a comment is
   never hard-wrapped, so a new home for such drafts goes into
   `.prettierignore`. And a guard in `scripts/vet.sh`: a small check that fails on
   a table delimiter row outside a code fence in any tracked `.md`.

7. **Catalog the new files** — `.prettierrc.json`, `.prettierignore`,
   `scripts/prettier.sh`, `.claude/hooks/format-md.sh`,
   `.claude/rules/markdown.md`, the table check — in the catalog group that
   carries the prose principles, so `/update-muthur` and `/detemplate` know
   they exist. The prettier wrapper, config and hook are marked optional for an
   adopter that wraps with its own tooling; the rule and the table check are
   not.

## Adopters

A sync that diffs across the reflow sees nearly every Markdown file rewritten
line by line, and the changes that matter drown in "one line became four". So
the squash is titled `[attn adopters]` and its body carries an `Adopters:`
paragraph (`/squash-message` § "Format rules") that tells their agent to split
the sync at this commit, `C`:

1. **Port `<watermark>..C^` as usual** — every change up to the reflow,
   readable line by line.
2. **Read `C` itself with the reflow hidden** —
   `git show -w --word-diff=plain --word-diff-regex='[^[:space:]]+' C` shows
   only what changed in words: the tables become lists, the catalog's new
   shape and its parser, the new rule and tooling. The only noise left is the
   reflow's own marks — a `>` on each new continuation line of a blockquote and
   `*em*` turned `_em_` — which their formatter produces or not on its own
   terms. Port the rest; never port the reflow as a diff.
3. **Wrap their own Markdown with their own tooling.** Each adopter likely
   has a formatter already; the prettier wrapper and hook here are on offer,
   not imposed — the catalog lists them as optional. Whatever wraps, the
   GitHub-bound exceptions above hold for them too.
4. **Port `C..<latest>` as usual** — both sides are wrapped by then, so the
   diffs read line by line again.

None of this needs their operator's yes beyond what a sync already asks.

## For the operator

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

## Decisions

- **prettier comes through `npx`, pinned in `scripts/prettier.sh`.** A root
  `package.json` was ruled out because in a template it tells adopters this is
  a JS project and collides with their own; the environment's unpinned
  prettier, because the formatting would drift when the environment updates.
- **"Automatic" is the `PostToolUse` hook plus the vet check.** Formatting only
  at `/finalize` leaves the branch unwrapped until landing; a git pre-commit
  hook is untracked, so every clone would install it by hand.
- **The catalog converts like everything else**, with its parser — it is the
  biggest table set and the one that diffs worst.
- **New tables are guarded twice**: the path-scoped rule and the vet check.
