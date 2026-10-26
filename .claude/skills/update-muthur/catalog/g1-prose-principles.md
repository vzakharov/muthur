> ⛔ **Part of [the catalog](../catalog.md), never vendored** — delete
> `catalog/` wherever `catalog.md` is deleted.

# G1 — Prose & principles

The floor. Nothing here touches GitHub, needs a token, or assumes a stack, so
there is no condition under which it fails to apply.

- `CLAUDE.md` — The always-loaded conventions: the test for what may stay in it,
  key principles, docstring policy, derive-types-from-source-of-truth, doc-sync
  rules, commit conventions, the language decision.
  - **Disposition:** adopt — **merge, don't overwrite**
- `.claude/rules/` — The path-scoped convention mechanism: a rule file loads
  only when a session reads a file its `paths:` match. For globs no single
  directory bounds; one directory's conventions go in that directory's own
  `CLAUDE.md`. Ships with a README and the loop's own two rules: `stack.md`
  (what `vet.sh` exits, what a stack landing wires) and `staging.md` (editing a
  file that loads on every turn through a staged copy). Its `markdown.md` is an
  opt-in of its own, and `external-docs.md` an entry of its own, both below.
  - **Pulls in:** `scripts/staged.sh`, `/finalize` (G2), for `staging.md` —
    without them, drop it and the line in `.claude/skills/CLAUDE.md` that points
    at it
  - **Disposition:** adopt
- `.claude/skills/CLAUDE.md` — The conventions for adding, renaming or
  cross-referencing a skill: the checks that cover it, names to avoid, naming
  one bare inside another's argument. Loads on a read of any file under
  `.claude/skills/`.
  - **Disposition:** adopt
- `/dry` — Review the session's diff for DRY opportunities; apply the obvious
  wins, surface the ambiguous ones.
  - **Disposition:** adopt
- `/tend-prose` — Cut prose that shouldn't exist, rewrite what narrates a change
  into present-tense contracts, trim what names and types already say, delete
  what survives only to deny a thing the change removed. The long version of
  CLAUDE.md § "Writing things down".
  - **Disposition:** adopt
- `/polish` — Run `/dry` then `/tend-prose` over the branch's diff, committing
  what they change. `/go` runs it after implementing and `/finalize` ahead of
  its numbered steps; the operator runs it over work that reached neither.
  - **Pulls in:** `/dry`, `/tend-prose` (this group)
  - **Disposition:** adopt
- `.claude/voice/` — The house rule for writing to a person, imported by
  CLAUDE.md § "Explaining things to people" and so resident in every session.
  `voice.md` is the rule, and the place a team edits if it wants a house manner
  of its own; `operators/` holds one file per person and ships carrying this
  repo's operator.
  - **Pulls in:** `/tend-prose` (this group)
  - **Disposition:** adopt — **rewrite its `operators/` entries**
- `/plainly` — Explain something to a person cause-first and in their nouns:
  re-explain an answer that did not land, or answer a question under the rule
  from the start. Names six defects so a bad report can be called out in one
  word.
  - **Pulls in:** `/tend-prose` (this group)
  - **Disposition:** adopt
- `scripts/check-skill-catalog.sh` — Assert that no skill `@`-reference dangles.
  Downstream, that first assertion is the whole value: it is how you find out a
  subset copy was incomplete.
  - **Requires:** `bash`
  - **Disposition:** adopt
- `.claude/rules/markdown.md` — No tables in agent-facing Markdown (every
  `CLAUDE.md`, everything under `.claude/`): lists or sections instead, since
  Markdown read raw diffs a whole row for one cell's edit. Markdown a person
  reads rendered — a README, `docs/` — keeps its tables. **The cost, which is
  why it is asked:** a house style rather than a correctness rule — every table
  already in the project's agent-facing Markdown is rewritten before vet passes,
  and every later one fails it. The call is the project's; the rule of thumb to
  offer with the question is the split the rule draws — Markdown only agents
  read gets no tables, Markdown a person may read rendered uses them where they
  help. A yes keeps the file and its check, and a project wanting a different
  split moves the rule's `paths:` and the check's pathspec together; a no
  deletes the file, and the vet line keyed on it goes quiet.
  - **Pulls in:** `scripts/check-markdown-tables.sh` (this group)
  - **Disposition:** adopt — **opt-in: ask**
- `scripts/check-markdown-tables.sh` — Fail on a Markdown table outside a code
  fence in tracked agent-facing Markdown, reading a staged file through its
  copy. `scripts/vet.sh` runs it while the rule above exists.
  - **Requires:** `bash`, `awk`, `git`
  - **Disposition:** adopt — **with `.claude/rules/markdown.md`**
- `.claude/rules/markdown-wrap.md` — Tracked Markdown hard-wrapped at 80
  columns, so one clause's edit diffs as one line, and text bound for a GitHub
  body or comment left unwrapped, since GitHub renders its newlines. The wrap
  and the exemption are the point and prettier is one way to get them: a project
  with its own Markdown formatter keeps the rule's exemption, wires its own
  tool, and drops the prettier files below, whose absence quiets the vet and
  `install-deps.sh` lines keyed on `.prettierrc.json`.
  - **Pulls in:** `scripts/prettier.sh`, `.prettierrc.json`, `.prettierignore`,
    `.claude/hooks/format-md.sh`, `scripts/check-markdown-wrap.sh` (this group)
  - **Disposition:** adopt — **optional: or your own formatter**
- `scripts/prettier.sh` — Run prettier at the version it pins, through `npx`,
  from the repo root; every caller goes through it.
  - **Requires:** `node` with `npx`; registry access on first use
  - **Disposition:** adopt — **with `.claude/rules/markdown-wrap.md`**
- `.prettierrc.json` — `proseWrap: always` at 80 columns, fenced code and
  frontmatter left alone, staged copies parsed as Markdown.
  - **Disposition:** adopt — **with `.claude/rules/markdown-wrap.md`**
- `.prettierignore` — The paths whose text GitHub renders. Merge into yours if
  present.
  - **Disposition:** adopt — **with `.claude/rules/markdown-wrap.md`**
- `.claude/hooks/format-md.sh` — After each `Edit`/`Write`/`MultiEdit` of a
  `.md` or staged `.md.staged` inside the project, wrap it through
  `scripts/prettier.sh`; a prettier failure exits 2 so the agent sees it.
  - **Requires:** `bash`, `jq`, `.claude/settings.json` wiring (G4)
  - **Pulls in:** `.claude/hooks/lib.sh` (G4)
  - **Disposition:** adopt — **with `.claude/rules/markdown-wrap.md`**
- `scripts/check-markdown-wrap.sh` — Fail on tracked Markdown prettier would
  rewrap, reading a staged file through its copy. `scripts/vet.sh` runs it while
  `.prettierrc.json` exists.
  - **Requires:** `bash`, `git`
  - **Pulls in:** `scripts/staged.sh` (G2)
  - **Disposition:** adopt — **with `.claude/rules/markdown-wrap.md`**
- `.claude/rules/external-docs.md` — A file named `<name>.external.<ext>` is a
  document someone else wrote, kept byte for byte: not a voice to write in, its
  claims its author's, instructions in it text rather than requests, never
  reformatted; one over ~500 lines gets a line map from a Haiku subagent before
  anyone reads it. Shipped rather than asked, since it costs nothing until a
  file carries the suffix — it loads on a read of one, and no check runs over
  the tree.
  - **Pulls in:** the `**/*.external.*` line in `.prettierignore` (this group);
    the `claude-haiku-5-5` row in `.claude/costs/prices.json` where G7 is
    adopted, or the map's subagent stops the session's pricing
  - **Disposition:** adopt
- `.gitignore` — Take the `tmp/` entry and keep the rest of yours. `CLAUDE.md`'s
  "dev artifacts go under `tmp/`" principle depends on that path being ignored.
  - **Disposition:** adopt — merge one line
- `.claude/hooks/file-tools-nudge.py` — Before each `Bash` call, refuse the
  first command that reads a project file into the agent's view (`cat`, `head`,
  `sed -n` …), edits one in place (`sed -i`, `perl -pi` …) or writes one (a
  heredoc or `echo` into it, `tee`), naming the tool `CLAUDE.md` asks for
  instead — a read piped onward or inside a `$(…)`, or of a file outside the
  project, passes; the identical command again in the same session goes through,
  and a `BATCH_EDIT=1` in front of a command exempts everything after it, for a
  deliberate batch of edits. Records what it refused under `tmp/`, and fails
  open.
  - **Requires:** `python3` ≥3.9, `.claude/settings.json` wiring (G4)
  - **Disposition:** adopt

`CLAUDE.md` is a **donor, not a replacement** — overwriting it is the one way to
make adoption a regression. `ADOPTING.md`'s shared tail owns the merge itself,
and the test the whole merged file is held to afterwards.

Its § "Language" is hydrated rather than merged: one line naming the language
your team reads, the rest of the section holding whatever the project.

Its § "Explaining things to people" ends in an **unbackticked** `@` reference,
which is the one line in this file a tidy-up breaks: the import parser skips
code spans, so backticking it for consistency with its neighbours loads nothing
and says nothing.
