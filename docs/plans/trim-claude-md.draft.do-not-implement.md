> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# Trim CLAUDE.md to what every turn needs (#97)

`CLAUDE.md` is ~6,500 words, loaded in full on every turn. This plan writes the test for what may stay into the file, applies it section by section, moves what fails it to the home that loads at the moment it matters, and makes the section citations checkable so the moves can't leave dangling `§` references behind.

## The test

> A line stays in `CLAUDE.md` only when it has to hold on turns where the process it concerns is **not** being run. A line that only matters while a given skill, hook or directory is in play goes to that skill, to a `.claude/rules/` file, or to a colocated `CLAUDE.md`, and this file keeps at most a pointer. **The corollary that decides the close calls:** a line stays when nothing narrower loads at the moment it matters. The suppression rule, for example, stays, because no skill or path runs when someone adds a suppression.

It goes into § "About this file", replacing that section's growth-invitation paragraph with a single sentence (question 1). § "Writing things down" question 1 gets a clause pointing at it for the case where the prose in question is `CLAUDE.md` itself. `/tend-prose` is updated to match (step 6).

## Section by section

"Keep" means it passes the test. Trimming a kept line is tightening only, with no change to what it says.

| § | Verdict | What leaves, and where it goes |
| --- | --- | --- |
| About this project | keep | Nothing. The fork tripwire has to fire on every turn of an undetemplated fork. |
| About this file | rewrite | Becomes the test plus one sentence on co-authoring the file. |
| Repository layout | keep | The stub, for adopters to fill. |
| Vetting | keep ~60 words | Kept: `./scripts/vet.sh` is the entrypoint; it runs at milestones via `/finalize`, not before every commit; a CI catch it missed means extend it; **a stack landing or a toolchain change wires `scripts/vet.sh`, `.claude/hooks/install-deps.sh`, and the environment setup script, which gets reported to the operator.** Moved to new `.claude/rules/stack.md` (question 2): the exit rule (no stack → `exit 0`, stack unchecked → `exit 1`) and its rationale, the three sites in detail, and the env-setup-script report. Cut: the per-stack examples and the `run-parallel.sh` line, which `vet.sh`'s header already carries, and "vetting is the run, attestation the record", which `/finalize` owns. |
| Key principles | keep, compressed | The three suppression bullets become one bullet. The Read/Edit/Write rationale shrinks to a sentence. The harness-staging bullet (`CONFLICTING`/red is reported, not fixed) stays in two sentences, because the harness text it counters is resident every turn and PR wakes arrive with no skill loaded. **The draft-PR bullet moves to `.claude/skills/pr/SKILL.md`**, because the only turn where the harness's "no PR unless asked" collides with the loop is the one where `/pr` is loaded. `## DRY notes` stays: native plan mode on the local CLI writes plans with no skill loaded. |
| Plan mode & questions in web sessions | keep the rules, drop the exposition | Kept: the bug in one sentence plus the route (a plan goes to a file, a question goes out as numbered prose); the plan-file tripwire as #96 left it; the ladder table; "the test is the deliverable, not the grammar"; "in doubt, row 2"; the `let's …` collision; "no plan" skipping Step 1; `#<N>` → `/take-issue` first (one sentence); continued work gets no plan cycle; outside web sessions, native plan mode is fine. Moved to `task/SKILL.md`: "What row 1 costs", which is `/task`'s own accepted cost. Cut: the "row 2 is a stated bucket" paragraph (its first clause folds into the table) and the "`/plan` gets native plan mode" bullet, which `plan-mode-notice.sh` and `plan/native-plan-mode.md` both carry. |
| Docstrings | keep | — |
| Derive types and schemas | keep | — |
| Testing | keep | — |
| GitHub comments | keep, ~330 → ~130 words | The four rules stay: reply to every comment pointed at; write SHAs bare; post a body from a file, never a path; never resolve or unresolve a thread. The rationale shrinks to a clause each. |
| Git conventions | keep the per-commit rules | Kept: the prefix list (with `polish:` one line), the loop-is-the-product `feat:`/`fix:` rule, descriptive messages, push proactively on remote branches, and a one-sentence rename rule (an opaque auto-branch is renamed before the first commit and never after a PR exists → `/branch-rename`). Moved to `polish/SKILL.md`: the `polish:` paragraph. Moved to `branch-rename/SKILL.md`: the rename rationale. Cut: the "develop on branch isn't a pin" clause, which `pr/SKILL.md` already states at length. Moved to `ADOPTING.md` § "Reconcile `CLAUDE.md`" and the catalog's `CLAUDE.md` row: "adopters invert this", and `detemplate` Step 4 deletes the loop-is-the-product paragraph directly. Cut: the squash-message sentence, which `/squash-message` and `/pr` own. |
| Writing things down | keep, compressed | The three questions, the top-level-doc rule, the sync rule, the negation rule, the tombstone rule (shorter) and plans-as-exception (one sentence) all stay. Cut: the attached-image paragraph, because `session-images.sh`'s own context message already states the keep-or-leave rule at the moment an image arrives. |
| Language | keep, compressed | The three groups stay, a line or two each. |
| Explaining things to people | keep | Untouched, including the **unbackticked** `@.claude/voice/voice.md` import. |
| Working with skills | ~700 → ~120 words | Kept: the main loop in order (`/task` → `/plan` → `/go` → `/finalize`, one line each), and the stub rule ("a stub is not a skill you can follow; say so and stop"). Cut: the per-skill list, since the harness puts every skill and its description in front of the agent each session, and the stubs' own descriptions and banners say STUB. Moved to new `.claude/rules/skills.md` (paths `.claude/skills/**`): "Adding or renaming a skill", meaning the catalog-row check and the instruction-token naming rule. The heading stays, since `spinoff/SKILL.md` names it. |

Rough outcome: ~2,800–3,200 words. The test decides, not the number.

## Steps

1. **Write the test** into § "About this file", and add the pointer clause to § "Writing things down" Q1.
2. **Create the two rule files**, `.claude/rules/stack.md` and `.claude/rules/skills.md`, each short enough to be a budget per `/tend-prose` Step 4. `stack.md`'s `paths:` are the common manifests and toolchain pins (`package.json`, `pyproject.toml`, `requirements*.txt`, `Cargo.toml`, `go.mod`, `Gemfile`, `pom.xml`, `build.gradle*`, `composer.json`, `deno.json`, `mix.exs`, `.nvmrc`, `.python-version`, `.tool-versions`, `rust-toolchain*`) plus `scripts/vet.sh` and `.claude/hooks/install-deps.sh`. `CLAUDE.md` keeps its one sentence as well, because a manifest created with `Write` may not trip a path-scoped rule. Update `.claude/rules/README.md`'s "ships empty on purpose" to say the directory ships the loop's own two rules, and do the same in the catalog's `.claude/rules/` row and `ADOPTING.md`'s "(the mechanism ships with a README and no rules)".
3. **Move text into skills**: `task` ("what row 1 costs"), `pr` (the draft-PR-vs-harness rule), `polish` (`polish:` legitimacy), `branch-rename` (the rationale). Each goes in as that skill's own statement, not as a quote of `CLAUDE.md`.
4. **Rewrite `CLAUDE.md`** section by section per the table.
5. **Repoint citations.** Every `CLAUDE.md § "…"`, `CLAUDE.md "…"`, `CLAUDE.md → …`, `CLAUDE.md ("…")` and `CLAUDE.md#anchor` in `.claude/`, `scripts/`, `ADOPTING.md` and `README.md` is either left alone (section still exists and still says it) or repointed. The ones known to move:
   - the Vetting exit-rule citations go to `.claude/rules/stack.md`: `scripts/vet.sh` (3×), `.claude/hooks/install-deps.sh`, `detemplate` (92, 206), `spinoff` (309), `take-issue/video-frames.md`, catalog (46), `ADOPTING.md` (300);
   - `branch-rename:5` and `pr:47` (the rename rationale) go to `branch-rename`;
   - `polish:53` becomes self-contained;
   - `session-images.sh:10` points at the hook's own message;
   - catalog 465 ("`CLAUDE.md`'s stub list names it too") is dropped, since the list is gone;
   - `detemplate` Step 4 deletes the loop-is-the-product paragraph rather than the adopters-invert rule;
   - the catalog's `CLAUDE.md` row description is refreshed.
   The rest (`Plan mode…` ×9, `Key principles`, `Writing things down`, `Language`, `GitHub comments`, `Testing`, `Explaining things to people`) are re-read against the new text and repointed only where the cited content moved.
6. **`/tend-prose`**: add "the skill or hook whose run it governs" and "a colocated `CLAUDE.md`" to Step 2's homes table, and have lens 1 name the `CLAUDE.md` test for lines in that file. It points at § "About this file" rather than restating the test.
7. **Make section citations checkable** (question 3): normalise every citation into `CLAUDE.md` to the form `CLAUDE.md § "<heading>"`, and add an assertion to `scripts/check-skill-catalog.sh` that each such heading exists as a `##`/`###` heading in `CLAUDE.md`. Markdown links of the form `CLAUDE.md#anchor` in `ADOPTING.md` and the catalog are checked against the slugified headings.
8. **Adopters (C01)** (question 4): the catalog's `CLAUDE.md` row and `ADOPTING.md` § "Reconcile `CLAUDE.md`" gain a porting note. When you take this change, apply the test to your whole `CLAUDE.md`, your own sections included, and move what fails it the same way. From then on the discipline is enforced at write time: the test is in the file, and `/tend-prose`'s lens 1 (run by every `/polish`) holds new `CLAUDE.md` lines to it.
9. `./scripts/vet.sh`, then `/polish`, then `/pr`.

## DRY notes

- **The test is stated once**, in `CLAUDE.md` § "About this file". `/tend-prose`, the catalog and `ADOPTING.md` point at it and never paraphrase it.
- **Every move is a move, not a copy.** Where a skill already carries the procedure (`branch-rename`, `take-issue`, `plan/native-plan-mode.md`, `session-images.sh`'s message, `squash-message`), `CLAUDE.md` loses its version outright. Where a pointer is kept, it names the home and holds none of the content.
- **The exit rule gets one home**, `.claude/rules/stack.md`. `vet.sh`, the catalog, `ADOPTING.md`, `detemplate` and `spinoff` point at that file rather than at `CLAUDE.md`. `CLAUDE.md` keeps the trigger sentence ("a stack landing wires three sites"), which is the *when*, not the rule.
- **No shared "citation normaliser" abstraction.** The new assertion in `check-skill-catalog.sh` reuses that script's existing file walk and `fail` helper. It is one more assertion block like its neighbours, not a new script.
- **No new top-level doc.** Both new files live under `.claude/rules/`, whose README already defines them.

## Questions

1. **Where the test lives.**
   (a) *Recommended:* § "About this file", the section that already talks about what this file is for; "Writing things down" points at it.
   (b) § "Writing things down", as the issue guessed; "About this file" stays as it is.
2. **Where the vetting exit rule goes.**
   (a) *Recommended:* `.claude/rules/stack.md`, scoped to manifests, toolchain pins, `vet.sh` and `install-deps.sh`, with the one trigger sentence kept in `CLAUDE.md`. `.claude/rules/` then stops shipping empty.
   (b) Keep it in `CLAUDE.md`, compressed to ~120 words, and leave `.claude/rules/` empty.
3. **Checking section citations mechanically.**
   (a) *Recommended:* normalise the citation form and add the assertion to `check-skill-catalog.sh` (step 7), so this is the last time anyone repoints by hand.
   (b) Repoint by hand this once, as the issue describes, and add no check.
4. **Telling adopters (C01).**
   (a) *Recommended:* the porting note in the catalog row and `ADOPTING.md` (step 8), with write-time enforcement through the test plus `/tend-prose` lens 1.
   (b) Also carve a follow-up issue for a whole-file mode of `/tend-prose` (it is diff-scoped today), so the one-time sweep can be re-run on demand rather than as part of a port.
