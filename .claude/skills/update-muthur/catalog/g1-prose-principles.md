> ⛔ **Part of [the catalog](../catalog.md), never vendored** — delete `catalog/` wherever `catalog.md` is deleted.

# G1 — Prose & principles

The floor. Nothing here touches GitHub, needs a token, or assumes a stack, so
there is no condition under which it fails to apply.

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `CLAUDE.md` | The always-loaded conventions: the test for what may stay in it, key principles, docstring policy, derive-types-from-source-of-truth, doc-sync rules, commit conventions, the language decision. | — | — | adopt — **merge, don't overwrite** |
| `.claude/rules/` | The path-scoped convention mechanism: a rule file loads only when a session reads a file its `paths:` match. For globs no single directory bounds; one directory's conventions go in that directory's own `CLAUDE.md`. Ships with a README and the loop's own two rules: `stack.md` (what `vet.sh` exits, what a stack landing wires) and `staging.md` (editing a file that loads on every turn through a staged copy). | — | `scripts/staged.sh`, `/finalize` (G2), for `staging.md` — without them, drop it and the line in `.claude/skills/CLAUDE.md` that points at it | adopt |
| `.claude/skills/CLAUDE.md` | The conventions for adding, renaming or cross-referencing a skill: the checks that cover it, names to avoid, naming one bare inside another's argument. Loads on a read of any file under `.claude/skills/`. | — | — | adopt |
| `/dry` | Review the session's diff for DRY opportunities; apply the obvious wins, surface the ambiguous ones. | — | — | adopt |
| `/tend-prose` | Cut prose that shouldn't exist, rewrite what narrates a change into present-tense contracts, trim what names and types already say, delete what survives only to deny a thing the change removed. The long version of CLAUDE.md § "Writing things down". | — | — | adopt |
| `/polish` | Run `/dry` then `/tend-prose` over the branch's diff, committing what they change. `/go` runs it after implementing and `/finalize` ahead of its numbered steps; the operator runs it over work that reached neither. | — | `/dry`, `/tend-prose` (this group) | adopt |
| `.claude/voice/` | The house rule for writing to a person, imported by CLAUDE.md § "Explaining things to people" and so resident in every session. `voice.md` is the rule, and the place a team edits if it wants a house manner of its own; `operators/` holds one file per person and ships carrying this repo's operator. | — | `/tend-prose` (this group) | adopt — **rewrite its `operators/` entries** |
| `/plainly` | Explain something to a person cause-first and in their nouns: re-explain an answer that did not land, or answer a question under the rule from the start. Names six defects so a bad report can be called out in one word. | — | `/tend-prose` (this group) | adopt |
| `scripts/check-skill-catalog.sh` | Assert that no skill `@`-reference dangles. Downstream, that first assertion is the whole value: it is how you find out a subset copy was incomplete. | `bash` | — | adopt |
| `.gitignore` | Take the `tmp/` entry and keep the rest of yours. `CLAUDE.md`'s "dev artifacts go under `tmp/`" principle depends on that path being ignored. | — | — | adopt — merge one line |
| `.claude/hooks/file-tools-nudge.py` | Before each `Bash` call, refuse the first command that reads a project file into the agent's view (`cat`, `head`, `sed -n` …), edits one in place (`sed -i`, `perl -pi` …) or writes one (a heredoc or `echo` into it, `tee`), naming the tool `CLAUDE.md` asks for instead — a read piped onward or inside a `$(…)`, or of a file outside the project, passes; the identical command again in the same session goes through, and a `BATCH_EDIT=1` in front of a command exempts everything after it, for a deliberate batch of edits. Records what it refused under `tmp/`, and fails open. | `python3` ≥3.9, `.claude/settings.json` wiring (G4) | — | adopt |

`CLAUDE.md` is a **donor, not a replacement** — overwriting it is the one way to
make adoption a regression. `ADOPTING.md`'s shared tail owns the merge itself,
and the test the whole merged file is held to afterwards.

Its § "Language" is hydrated rather than merged: one line naming the language
your team reads, the rest of the section holding whatever the project.

Its § "Explaining things to people" ends in an **unbackticked** `@` reference,
which is the one line in this file a tidy-up breaks: the import parser skips code
spans, so backticking it for consistency with its neighbours loads nothing and
says nothing.
