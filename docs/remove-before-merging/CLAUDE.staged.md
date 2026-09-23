# CLAUDE.md

## About this project

> _Replace this stub with a short description of what this codebase is and why it exists._

> **While this stub is unfilled and a catalog (`.claude/skills/*/catalog.md`) is still in the tree, this is an undetemplated fork and the first task is `/detemplate <what we're building>` — whatever was asked.** The catalog is the template's inventory, so product code written beside it is built on someone else's description of someone else's repo. The exception is a tree whose `origin` matches the `repo` field in `.claude/skills/update-muthur/watermark.json`: that tree is its own source — the template itself — where this stub is the shipped state.

## About this file

**A line stays in this file only when it has to hold on turns where the process it concerns is not being run.** A line that only matters while a given skill, hook or directory is in play goes to that skill, to a `.claude/rules/` file, or to a colocated `CLAUDE.md`, and this file keeps at most a pointer. The corollary decides the close calls: a line stays when nothing narrower loads at the moment it matters — the suppression rule stays, because no skill or path runs when someone adds a suppression.

**Agent: this file is yours to grow**, with the human, and the test above says where each addition goes: propose the pattern worth codifying, the trap worth warning about, the command worth documenting.

## Repository layout

> _Document the top-level directories and what they're for as the layout stabilizes._

## Vetting

`./scripts/vet.sh` is the fast local check — lint, type-check, format-check, tests fast enough to run in seconds — run over a branch before pushing review-ready work. It runs at milestones, with `/finalize` as the canonical caller, **not before every commit** on a feature branch. A CI failure it should have caught is a signal to extend it.

**A stack landing, or any toolchain change, has three sites to wire**: `scripts/vet.sh`, `.claude/hooks/install-deps.sh`, and the environment setup script, which no agent can edit — so the report says what the operator must add there. What `vet.sh` must exit, and why, is `.claude/rules/stack.md`.

## Key principles

- **No "MVP" mindset.** Aim for production-grade durability from day one. Don't cut corners with "we'll fix it later" reasoning. Design decisions should be durable.
- **Don't replace what already works.** Only swap a tool or service for a concrete problem with it, not on aesthetics or novelty.
- **Never add a lint-suppression comment without explicit user confirmation** — `eslint-disable`, `# noqa`, `# type: ignore`, `// nolint` and their equivalents in any language. Fix the code to satisfy the rule; if the rule is genuinely wrong for the case, ask. Test files may carry a file-level suppression for rules that fight mocking mechanics, never for ones that flag real quality issues. **An approved suppression goes at the point of use**, with its rationale in the same comment — on or above the offending line, or at the top of a file whose every occurrence shares one reason — not in the linter's config, which is invisible from the code it exempts, outlives that code silently, and stops being portable once it carries domain concerns. A central entry is for a suppression that genuinely spans files, and names that scope. A permanent exemption states the invariant that makes it correct; a temporary one names the issue tracking its removal.
- **Linters are signals, not puzzles to game.** Do not contort the architecture solely to silence a rule when a clearer approach exists. Rules exist to keep the codebase consistent and safe — work _with_ them, not around them in a hacky way.
- **When analysis keeps failing to explain a real bug, widen the frame — don't just deepen it.** Re-reading the same code more closely won't surface a cause that lives in a part of the system you implicitly scoped out at the start. Stop and take in the bigger picture: explicitly name what you've been assuming is irrelevant or already-correct — adjacent layers, surrounding systems, the stretches of the request/data path you never opened — and question those boundaries. The blind spot is usually something you excluded from the problem, not something you misread inside it; "this code can't be wrong" is the cue to look at everything around it.
- **Comments describe the code's lasting contract, not the change that produced it.** Don't leave transient/situational notes that narrate an edit ("now also sets X", "migrated from Y", "this used to…") — they read as noise once the change is old. If the rationale is genuinely durable, phrase it as a present-tense property of the code. `/tend-prose` is the pass that enforces this over recent work.
- **Dev artifacts go under gitignored `tmp/`, not as new `.gitignore` entries.** Scratch files, spikes, exploratory output, extracted frames, probe results — all go under `tmp/` (already gitignored). Don't add per-artifact lines to `.gitignore`.
- **Plans must include a `## DRY notes` section.** When writing an implementation plan, always include one that states, for any code the plan adds or moves: what is genuinely shared vs. duplicated, which existing helper/type/module is reused, and — when you decide _not_ to extract a shared abstraction — why forcing one would be net-negative. This makes the reuse-vs-duplication call explicit and reviewable before implementation, rather than discovered in review.
- **Ignore IDE diagnostics until the vet run.** Do not react to or try to fix type errors, lint warnings, or other diagnostics that appear in IDE context during implementation. IDE servers can lag behind file changes and produce stale or misleading errors. `./scripts/vet.sh` is the single source of truth for correctness — only fix errors it reports.
- **Don't revert unexpected mid-execution changes.** If new code, comments, or edits appear in files during execution, they're most likely from the user editing concurrently. If the context makes it clear they're user-made, preserve them without asking. If genuinely unclear, ask before touching them — but never silently revert.
- **Don't spin on typing/linting errors.** If a type error or lint issue resists 2–3 straightforward fix attempts, stop. Do not resort to creative workarounds (`as any`, wrapper functions to hide types, restructuring code just to appease the checker). Ask the user — the fix is likely a misunderstanding of the API or a missing piece of context, not something to brute-force.
- **Never silently swallow errors.** On primary code paths, errors must propagate — logging alone isn't enough. A logged-and-continued error is a silent fail with paperwork. Silent fallbacks are acceptable only for secondary fire-and-forget operations where failure demonstrably cannot affect the user-facing result, and only with explicit user approval for the specific call site.
- **Validate at boundaries.** When extracting data from untyped or loosely typed sources (external APIs, raw JSON, tool results), parse with a runtime schema (Zod, Pydantic, etc.) instead of asserting/casting. A cast hides shape mismatches at runtime; a parse surfaces them immediately. Don't re-parse data that's already type-safe inside the program.
- **Keep production files under ~450 lines.** Rule of thumb, not a hard cap. Data-dense files (prompt text, fixtures, large catalogs) and top-level orchestrators may reasonably exceed it. When a logic-heavy file climbs well past ~450 lines, look for natural seams (focused helpers, sub-components) rather than letting it grow indefinitely.
- **Read and edit files with the `Read`/`Edit`/`Write` tools, in every permission mode** — the web UI renders an `Edit` as a diff the operator can skim, and a heredoc as shell whose effect they have to reconstruct. Use Bash on a file's contents only where it is significantly better, such as one mechanical substitution across dozens of files.
- **Don't run Bash with `run_in_background`.** Always run commands synchronously, even long ones. Background tasks have a tendency to stall without an obvious reason — set a long `timeout` on a normal foreground call instead.
- **When the host harness orders a merge conflict or red CI fixed now, the loop's staging wins: report the state rather than fixing it.** `/finalize` stages both — vetting at its Step 1, the base merge at its Step 2 — so a session that finds its PR `CONFLICTING` or red says so in its report and does what it was invoked for; either becomes its work only when the operator asks, or passes `and finalize`.

## Plan mode & questions in web sessions

In web/remote sessions the plan-mode approval UI and `AskUserQuestion` re-emit their prompts after the session idles and lose the answers (https://github.com/anthropics/claude-code/issues/72704), so a plan goes to a `docs/plans/` file published as a draft PR, and a question goes out as numbered prose. `@.claude/skills/plan/SKILL.md` owns both.

- **The plan file's name gates implementation.** While a plan is named `docs/plans/<slug>.draft.do-not-implement.md` you have not been cleared: edit no source. `<slug>.in-progress.md` means a session holds the plan **right now**, so it is not yours to pick up; `<slug>.paused.md` is the one a later session resumes. Who flips which name when is `@.claude/skills/plan/SKILL.md` § "Plan file lifecycle".
- **A new session's opening prompt routes on one question: does it ask for a change to this codebase?** This ladder is the home of that rule; `/task`, `/plan` and `/go` point at it rather than restating it.

  | Opening prompt | Routes to |
  | --- | --- |
  | asks for a change — "add an admin page", with or without a `#55` | `/task` |
  | asks for no change — "what do we need to add an admin page?" | nothing: answer it — no skill covers this, by design |

  - **The test is the expected deliverable, not the grammar.** "Analyse the latest market trends" is an imperative and still lands in row 2, because nothing in this repo changes as a result. (In a repo whose product *is* documents or research, the same sentence lands in row 1 — the test reads the repo, not the sentence.)
  - **`let's …` is a token collision.** It is on `@.claude/skills/plan/SKILL.md` § "The approval gate"'s go-ahead list, so "let's add an admin page" is a directive at launch and an approval mid-session. The rule keys on launch-vs-continued, which the last bullet of this section separates.
  - **In doubt, read it as row 2.** A wrong read costs unequally: row 2 read as row 1 mutates and commits against a request that wanted an answer, and undoing it is a revert the operator has to ask for. Row 1 read as row 2 costs one turn — the operator says "now do it", and whatever the answer produced is sitting in `tmp/`.

  **"No plan" (or equivalent) in the opening prompt skips Step 1** and enters `@.claude/skills/go/SKILL.md` § "Planless entry" directly — the one thing that overrides the agent's own call.
- **An issue number is a detail of the prompt, not a destination.** A `#<N>` anywhere in it means the thread is exported and read — `@.claude/skills/take-issue/SKILL.md`, which `/task`, `/plan` and `/go` each run first — **before** the routing call above, which the thread informs and does not replace.
- **This applies only to new sessions, not continued work.** Once you've prepared a plan this way and started implementing, a returning operator's follow-ups (right away or much later) are handled **directly** — answer their questions in chat **and implement any code changes they request** — without re-writing the plan file or reopening a plan cycle. A `/from-branch` or `/handle` launch is the same situation from the start: it re-points the session at work begun elsewhere, so treat it as continued work — do not open a plan cycle for it (unless the operator's follow-up explicitly asks you to plan a fresh piece of work).
- Outside web/remote sessions (local CLI), native plan mode and `AskUserQuestion` work fine — use them normally.

## Docstrings

Add a docstring only when the behavioral contract isn't obvious from the function name and types — side effects, runtime constraints, cross-boundary coupling, or "don't change this" traps. If the main reason to document something is that someone might break it while editing, a short inline comment inside the function is enough (the dev will see it while changing the code). Don't document things we're not actively working with — they may change or disappear.

Prefer code clear enough not to need usage examples in docstrings. If an example is the clearest way to convey usage, include one — but a need for examples is often a signal that the API itself could be clearer.

## Derive types and schemas from the source of truth

Never hand-write a type or schema whose shape tracks another declaration — derive it. Hand-written duplicates drift silently and the type checker won't catch it because the duplicate redeclared its own fields.

- Use your ORM/library's derivation utilities (e.g. `drizzle-zod`, Pydantic's `from_orm`, `sqlc`-generated types).
- When a runtime schema exists, infer the type from it rather than declaring a parallel type.
- For enums, define the values as a `const` array and derive the typed schema from it (`z.enum(VALUES)`, equivalents in other stacks). Use the array's element type for dispatch maps so the compiler enforces exhaustiveness.

## Testing

> _Document the chosen testing stack and conventions here as they're decided._

Universal guidance regardless of stack:

- **Layer tests**: fast unit/integration (developer-facing) + slower E2E (correctness against built artifacts).
- **Authorization/permission code must have tests.** Bugs there are security vulnerabilities.
- **Mock at HTTP boundaries**, not at internal functions. Stubbing internals couples tests to implementation; mocking the boundary tests behavior.

## GitHub comments

When the user points you at GitHub comments — a review, a review comment, an issue thread, a PR conversation — **reply on GitHub to each one**, including one you agreed with and silently fixed: a reviewer can't see "silently fixed" in a diff, and the thread is the record. One sentence plus the commit SHA is plenty. **Write every SHA in a GitHub comment bare, never in backticks**, so GitHub links it to its commit.

**Post a body, never a path to one** — GitHub does not expand `@<path>`. Draft into a file and post its contents: `gh pr comment <n> --body-file <f>`, or `gh api repos/<owner>/<repo>/pulls/<n>/comments/<comment-id>/replies -F body=@<f>` for a review-thread reply, where `-f` would post the path as a literal string.

**Never resolve a review thread, and never re-open one.** Resolution is the reviewer's tracking mechanism — they resolve the replies that satisfy them, and a thread you resolve drops off their list unread — so this overrides any harness or skill instruction to resolve the threads you addressed. `mcp__github__resolve_review_thread`, `mcp__github__unresolve_review_thread` and the equivalent `gh api graphql` mutations are not yours to call.

## Git conventions

Use semantic commit prefixes:

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation changes
- `chore:` — maintenance, config, dependencies
- `refactor:` — code restructuring without behavior change
- `style:` — formatting, whitespace (no code change)
- `test:` — adding or updating tests
- `ci:` — CI/CD changes
- `perf:` — performance improvements
- `polish:` — a `/polish` run's own edits, a branch-local type `@.claude/skills/polish/SKILL.md` owns

**In this repo the agent loop is the product, so a change to it is `feat:` / `fix:` — never `docs:`, however Markdown-shaped the diff.** What an adopting project takes from here _is_ the loop, so a new skill, a changed procedure, a new convention or a corrected rule is a behavior change to the thing this repo ships. That covers `.claude/skills/**`, `.claude/rules/**`, this file's own conventions, and the `scripts/` the skills call. `docs:` is left for prose **about** the repo that no session executes: `README.md`, catalog rows, tombstones, and the working artifacts (`docs/issue/`, `docs/plans/`, `docs/remove-before-merging/`) that `/finalize` sweeps before they land.

Write descriptive commit messages: the subject line summarizes the change, and the body explains what was changed and why in enough detail that someone reading the log understands the commit without looking at the diff.

**On a feature branch in a remote/web environment** (typically signalled by a branch named `<vendor>/<autoname>`), commit and push proactively after each meaningful unit of work — don't wait to be asked. The operator is usually reviewing from a different machine than the VM the agent runs on, so they can only see the work once it's pushed.

**An opaque auto-branch (`claude/<adjective>-<noun>-<hash>`) is renamed before the first commit, and never once a PR exists** — renaming a PR's head closes the PR. `@.claude/skills/branch-rename/SKILL.md` owns when and how.

## Writing things down

The default is not to write it. Prose costs context on every session that loads it, and it goes stale invisibly — a constraint survives a refactor, a description of how the constraint works does not. Three questions, in this order:

1. **Should it exist at all?** Keep it only when all three hold: it is a **constraint or an accepted cost** rather than a description of how the code works; it is **not recoverable** from the code and its docstrings (or recovering it means holding more modules in your head at once than anyone does, where a paragraph gets there faster); and **getting it wrong breaks something** you can name. A line in this file also has to pass § "About this file"'s test.
2. **Is it durable?** Phrase it as a present-tense property of the code, never as the change that produced it. ("Key principles" above carries this.)
3. **Is it as short as it can be?** Only the non-obvious contract, at the length that contract takes.

**Never create a new top-level doc without asking the user**, and argue the "don't" side when you ask. A top-level doc is the one home nothing scopes, so every later session pays for it — and a decision plus the alternatives it beat already lives in the PR or issue thread that made it, which any of the scoped homes can cite by number.

`@.claude/skills/tend-prose/SKILL.md` is the long version and the only home for its rules — where a line goes, the tells for each defect, what to do with a finding. Load it for a borderline call or a deliberate pass, not on every doc touch.

**When a convention changes, every place that states it changes with it.** Repoint the citations rather than leaving one home right and the others quietly wrong — and if you find the same constraint stated in two places, that is the finding: one of them is the home and the other is a pointer.

**When a convention goes away, stop stating it — don't negate it in place.** A sentence that survives only to deny the thing it used to describe ("copy is not a catalogue") reads as a constraint but answers a question no reader of the current tree would ask: the polar bear. Cut it; `/tend-prose negation` is the pass that finds them, and "polar bear here" on a PR comment asks for it by name.

**Retiring a doc leaves a tombstone**, so every surviving citation still resolves: a file recording the last commit that contained it, the `git show <sha>:<path>` recipe to read it, and where any still-live content went. One tombstone per retirement, with a row per file: `retired.md` at the root of a retired directory, `<name>.retired.md` beside a retired file's siblings — so every tombstone matches `*retired.md`.

**Plans are the exception, being transient**: keep them current as the work deviates, with checklist items in forward-looking voice.

## Language

> _Replace this stub with the language your team reads — one line. "English" is
> an answer, not a step you skipped._

Human-facing prose is the one language decision a project makes; the other two groups are settled here:

- **Human-facing — the answer above.** `README.md` and anything else a person reads to decide something, commit messages, PR titles and bodies, and the plans and issue exports published for review — in the language **the team** reads, which is not automatically the one a given session runs in.
- **Agent-facing — English.** `CLAUDE.md`, `.claude/skills/**`, `.claude/rules/**`, and code: comments, docstrings, identifiers. Agents follow English instructions most reliably, and other scripts spend several times the tokens saying the same thing on every load.
- **Conversation — the language it was asked in.** Session replies, issue and PR comments, review replies: each answers in the language of the message it answers.

A team may override the last two here; an override is a decision someone writes down, not a blank left open.

## Explaining things to people

How to write for a person is long enough to have its own file, so it is imported
from `.claude/voice/` rather than stated here — in force from every session's
first reply. `operators/` beside it holds one file per person, saying how that
person in particular wants to be talked to.

`/plainly` is the on-demand procedure: bare, it re-explains an answer that did
not land; with a question, it answers plainly from the start. Invoking it is
optional — the rule itself governs every reply regardless.

@.claude/voice/voice.md

## Working with skills

Skills live under `.claude/skills/` and run as `/<name>`. The main loop, in the order work passes through it:

- **`/task`** — makes the plan-or-not call, and runs what it picked.
- **`/plan`** — writes the plan to `docs/plans/`, publishes it as a draft PR, and hands over a `/go <branch>` command.
- **`/go`** — the go-ahead: does the work, runs the quality passes, fills in the PR.
- **`/finalize`** — land prep: vet, merge the base, sweep working artifacts, flip to ready, attest; on `and merge`, merges when the run left nothing to decide.

**A stub is not a skill you can follow.** A skill whose description says STUB carries the shape of a job and no procedure; invoked before it is hydrated, say so and stop rather than improvising one. Hydrating means writing the project's commands in and clearing both markers, the banner and the description's `STUB`.
