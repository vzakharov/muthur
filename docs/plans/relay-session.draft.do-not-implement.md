> ⛔ **DRAFT — do not implement.** This plan has not been approved. A session that finds it under this name edits no source; `@.claude/skills/plan/SKILL.md` § "Plan file lifecycle" says who flips it and when.

# `/relay` — hand the session to a fresh one, with a summary we can read

## Why

`/compact` is a black box: it replaces the context with a summary nobody sees being written, at a cost the transcript does not itemize (`.claude/costs/CLAUDE.md` § "Each compact" — the call is recorded without its usage). The alternative is the same move done in the open: the agent writes the summary as an ordinary turn — its tokens priced like any other, its text readable — and starts a **new session** whose opening prompt is that summary.

A new session also beats an in-place compact on what the summary has to carry. The branch already holds the plan, the commits and the PR, and the successor re-reads them from disk, so the summary carries only what the tree does not: what the operator said, what was decided and rejected and why, the dead ends, and the next step.

## What `/relay` does

`.claude/skills/relay/SKILL.md`, invoked bare or as `/relay [what the successor should do next]`:

1. **Leave the branch resumable.** Commit and push everything. If a plan is `*.in-progress.md`, release it per `@.claude/skills/go/SKILL.md` § "Stopping partway releases the plan" — the successor cannot pick up a plan this session still claims. No uncommitted state survives the relay, because the successor's container is not this one.
2. **Write the summary** to `tmp/relay/<timestamp>.md`, in English (it is agent-facing), with these sections — the ones `/compact` asks for, minus what the branch already carries:
   - **The operator's messages**, every one, verbatim and in their language — the one thing no file on the branch recovers, and the one a paraphrase loses.
   - **Intent**: what the operator is after, including what they ruled out.
   - **Decisions**: each with the alternative it beat and why — what a successor would otherwise re-litigate.
   - **Dead ends and fixes**: what was tried and failed, and the errors hit.
   - **State**: branch, PR, last pushed commit, plan file and its name, anything running or waiting (CI, a subscribed PR, a scheduled check-in).
   - **Pointers**: the files that matter, by path — never their contents, which the successor reads fresh.
   - **Next step**: the argument if one was given, else the one the conversation left open, quoting the operator's words it rests on; or "wait for the operator" when nothing is pending.
3. **Build the successor's prompt**: `/from-branch <branch>` plus a follow-up, then the summary under a `## Relayed context` heading:
   - a plan was released in step 1, or a draft plan carries the operator's go-ahead in this session → follow-up `go`;
   - otherwise → the next step as a free-form follow-up, or none.
4. **Start the successor.**
   - **Web/remote**: `create_session` with `source_url` from `origin`, `source_revision` the branch, model and permission mode inherited; confirm with `get_session` that it did not fail at start.
   - **Local CLI**, where no such tool exists: the prompt stays in the file, and the report gives the two ways on — `/clear` and paste it, or `claude "$(cat tmp/relay/<file>)"` in a new terminal.
5. **Report and stop**: the successor's link (or the local recipe), the summary's size (characters and a rough token count at 4 characters a token) as the answer to "what did this cost the new session", and a pointer to the file. This session is left open, not archived — archiving is the operator's call, and they can say so.

## Edits beside the skill

- **`/from-branch` Step 6** learns the shape: a follow-up keyword (`go`) followed by a `## Relayed context` block is still that keyword, the block being context for the dispatched skill rather than a richer instruction. Body edit only, so no staging.
- **The context budget hook's warning** (`.claude/context-budget/hooks/post-tool-context-budget.sh`) offers `/relay` as the new-session route beside `/compact`, since "a new session resumes only from a paused plan" stops being true. Its test gets the assertion if it checks that text.
- **Catalog row** in `.claude/skills/update-muthur/catalog.md`, under **G2 — The PR loop**: Requires `create_session` for the spawn, a paste otherwise; Pulls in `/from-branch`, `/go`. `scripts/check-skill-catalog.sh` fails without it.

## Out of scope

- Automatic relay from the budget hook at its pause line. The hook offers it; firing a new session unasked is outward-facing and stays the operator's word.
- Replacing `/compact` anywhere it is merely mentioned as the in-session option — both remain.

## Decisions (recommendations in force)

1. **Name: `/relay`** — the baton goes to the next runner. Alternatives: `/respawn`, `/handover` (the last collides with the plan's "Handing off" block).
2. **The summary rides in the prompt, not in a committed file.** A committed `docs/relay/` file would need `/finalize` sweeping and adds a commit per relay; the prompt is already visible as the successor's first message. The `tmp/` copy is for this session's operator to read.
3. **No summary length cap**, only guidance: pointers over contents, which keeps it to a few thousand words. A hard cap would drop the operator's messages first, which is backwards.

## Dogfooding

This plan's own implementation is the first relay. On the operator's go-ahead in this session, follow § "What `/relay` does" by hand — the skill file does not exist yet — with follow-up `go`, and the successor implements the plan it was handed.

## DRY notes

- **Reused, not restated**: releasing a plan is `/go` § "Stopping partway"; attaching to the branch is `/from-branch`; plan execution is `/go`. `/relay` cites each by path.
- **Genuinely new**: the summary's section list and the spawn step. `/plan` § "Handing off" also produces a next-session prompt, but a bare `/go <branch>` for the operator to paste — no context, no spawn — so there is nothing to share beyond `/from-branch`, which both already end in.
- **Not extracted**: a shared "session handoff" helper across `/plan`, `/go` § "Stopping partway" and `/relay`. The three produce different things (a command, a renamed plan, a summary plus a spawned session), and a common helper would be a list of branches on who is calling.

## Checklist

- [ ] Write `.claude/skills/relay/SKILL.md`.
- [ ] Teach `/from-branch` Step 6 the `## Relayed context` shape.
- [ ] Offer `/relay` in the context budget hook's warning; update its test if it pins the text.
- [ ] Add the catalog row; `./scripts/vet.sh` passes.
