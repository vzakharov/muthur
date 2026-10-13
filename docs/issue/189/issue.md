# Issue #189: Replace Markdown tables with lists or sections

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/189
- **Author:** @vzakharov (human)
- **Created:** 2026-10-13T18:02:46Z
- **Updated:** 2026-10-13T18:02:46Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

Markdown in this repo is read raw — by agents and in diffs — and a table row is one physical line, so editing any cell rewrites the whole row in the diff. The rendered table is the only thing a table buys, and almost nobody reads these files rendered.

Split out of https://github.com/vzakharov/muthur/pull/187 (prettier hard-wrapping all `.md` at 80 columns), which should land **after** this: prettier cannot wrap a table, it pads every cell to its column's widest, so reflowing with tables still present grows delimiter rows hundreds of dashes long. With the tables gone first, #187's reflow commit touches nothing but line breaks.

## What to do

- Convert every table outside a code fence to a list, or to sections where a row is long enough to be a subsection of its own — 30 tables across 29 files today, including CLAUDE.md's routing ladder (through a staged copy, per `.claude/rules/staging.md`). A two-column key/value table becomes `- **Key** — value`; a wider one becomes one item per row with the first cell leading in bold; rows whose cells run to paragraphs (`/hotfix`'s concerns, `/pr`'s modes) become `###` sections. The meaning each table carries stays exactly as is.
- Convert the update-muthur catalog (`catalog.md` and `catalog/*.md`) to one list item per entry, `` - `path` — … ``, and change `scripts/check-skill-catalog.sh` — the only code that parses a table — to read the first backticked token of a top-level list item. Prose describing the catalog's shape ("row", "first column") says "entry".
- Keep `/qa-checklist`'s table: it is a template for the PR body, which people do read rendered on GitHub. Move it inside a fenced block so it reads as an output template.
- Guard against new tables: a path-scoped `.claude/rules/markdown.md` (`paths: ["**/*.md"]`) stating the convention and the GitHub-output exception, and a `scripts/vet.sh` check that fails on a table delimiter row outside a code fence. Catalog both.

## Done when

- No tracked `.md` has a table outside a code fence, and vet fails if one is added.
- `scripts/check-skill-catalog.sh` passes on the list-form catalog and fails when a skill's entry is removed.
- `scripts/check-claude-md-size.sh` passes on the staged CLAUDE.md.

---

## Timeline (status, references, and other events)

- **2026-10-13T18:03:40Z** @vzakharov cross-referenced this issue from [#187 feat: hard-wrap Markdown at 80 columns with prettier](https://github.com/vzakharov/muthur/pull/187).
- **2026-10-13T18:03:44Z** @vzakharov referenced this issue in a commit: https://api.github.com/repos/vzakharov/muthur/commits/add303539b12272a4e158713be445dca476ac276.
