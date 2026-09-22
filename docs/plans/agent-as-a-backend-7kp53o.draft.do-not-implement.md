> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# Agent-as-a-backend

Let someone who does not know the word "repository" use their own Claude Code
through a button on a web page — on their subscription, their limits, their
infrastructure, with no agent chat anywhere in sight.

The front end writes a request to a queue. Something starts an isolated Claude
Code run in that person's own estate. The run reads the row, does the work,
writes progress and a result back. The front end polls and renders. Nobody ever
sees the word "branch".

This generalizes a case that already works: `vzakharov/leisan-psy-work`, a
repository whose primary operator does not know it is a repository. There the
intermediary is an agent chat; here a button takes its place.

## What this session established empirically

Recorded so it is not rediscovered.

| Question | Answer | Evidence |
| --- | --- | --- |
| Can a session be started in a user's account from outside | Yes — `POST /v1/claude_code/routines/{trig_id}/fire` with a per-routine token | [API reference](https://platform.claude.com/docs/en/api/claude-code/routines-fire) |
| How many such starts per day | Pro 5, Max 15 — per account, not per routine | Routine daily cap |
| Are account credentials present inside a cloud container | No. `claude auth status` reports `loggedIn`, but the provider is host-managed | `claude -p --cloud <nonexistent id>` → an auth error, not "not found" |
| Does a routine-fired session have `create_session` | No. The `Claude_Code_Remote` server is not mounted there at all | Routine run "create_session check" |
| Does an ordinary cloud session | Yes, and it works — ~7s to spawn | Session "Проверка create_session" |
| Does it recurse | Yes. A grandchild was born, and its `parent_session_id` points at the child, so the hierarchy is real | Session "Recursion test" |
| Is there a depth limit on sessions | None found. The only brake is a manual `interrupt_session` | Same run |
| Does GitHub Actions support subscription auth | Yes — `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token` | [GitHub Actions](https://code.claude.com/docs/en/github-actions) |
| What that token can do | Model requests only; one year; no Remote Control, no connectors | [Authentication](https://code.claude.com/docs/en/authentication) |

That settles the execution lane. The rejected one is kept under "The
researched alternative"; the reason fits in a sentence. Everything load-bearing
in the session lane is undocumented **and already demonstrably varies by
surface**, and its failure mode is unbounded reproduction sharing one account
rate limit, with a manual brake.

## Architecture, v0

```
button on the front end
      │
      ▼
 app backend ──► row in the queue (status queued)
      │
      ▼
 POST /repos/<user>/<repo>/dispatches   (client_payload: {request_id})
      │
      ▼
 GitHub Actions, an ephemeral runner in the user's own estate
      │  checkout → npx claude -p "/handle-request <id>"
      ▼
 the skill reads the row, works, calls ./scripts/answer
      │
      ▼
 queue: progress as it goes, then result ──► the front end polls
```

There is no dispatcher. One `repository_dispatch` is one run is one task,
ephemeral and unaware that any other exists.

**The executor runs the bare CLI, not `claude-code-action`.** The action exists
for GitHub integration — comments, PRs, reacting to `@claude` — none of which
this needs, and it drags in a GitHub App with twelve permissions plus an **actor
check**: any bot initiator is rejected on every event unless listed in
`allowed_bots`, and a dispatch from our backend is exactly that. A bare
`npx @anthropic-ai/claude-code -p` checks nothing, needs no App, and leaves
`CLAUDE_CODE_OAUTH_TOKEN` as the repository's only secret.

The executor's contract is stated once and does not depend on what started it:

- **Only a `request_id` crosses the boundary.** The skill reads the row itself
  and treats its contents as untrusted: never concatenated into a system prompt,
  never followed as instructions.
- **The skill writes through `./scripts/answer`, never raw queries.** One place
  validates the schema, and the agent cannot corrupt another row.
- **Request type maps to skill as configuration, not as a model's judgment.**
- **Progress comes from Claude Code hooks**, not from the model's diligence:
  `PostToolUse` and `Stop` fire whether or not it remembers to report.

## The template knot, untied

There are three artifacts, and the confusion comes from collapsing the second
into the third:

| | What it is | How it comes about |
| --- | --- | --- |
| **A. The engine** | The development repository: dispatch backend, front end, and the source of the thin template. Runs the full muthur loop — `/plan`, `/go`, PRs, squashes | a muthur fork, then `/detemplate` |
| **B. The thin template** | What an app author forks: request-type skills, `scripts/answer`, the workflow, a runbook. No `/plan`, no `/go`, no mention of branches | **a build artifact of A** |
| **C. A front repo** | "Pick clothing" — one author's actual app | "Use this template" on B |

**B is not a repository anyone maintains; it is a `template/` directory inside
A**, which a release workflow publishes to a separate repository carrying
GitHub's template flag. The "Use this template" button needs a repository; the
source of truth does not. That removes the only real difficulty — two trees kept
in step by hand, where B falls behind A silently.

Until someone needs B, it is just a directory. Publishing it is the last step,
not the first.

## Steps

### Step 0 — create A and move in

Runs from muthur, and ends with this session no longer needed.

1. `gh repo create vzakharov/<A-name> --template vzakharov/muthur --private`
2. Carry this plan file into A as its first commit, under the same name.
3. Close the muthur PR **without merging**: the plan describes work in another
   repository and must not reach the template.
4. In A: `/detemplate <what we're building>`, the ordinary way, through `/plan`.

Everything below happens in A.

### Step 1 — the executor contract

Independent of the launch lane, so it comes first: whatever is decided between
Actions and sessions, none of this is rewritten.

- Request-row schema: `id`, `type`, `status` (`queued` / `working` / `done` /
  `failed`), `input`, `progress[]`, `result`, `error`, timestamps. Declared once
  in zod; the type is inferred from it and the table schema derived from it.
- `scripts/answer` as the only write path: `answer <id> --status working --note "…"`,
  `answer <id> --result <file.json>`, `answer <id> --failed "…"`. Validates
  against the type's schema.
- One request-type skill with a hard input/output contract.
- Hooks in `.claude/settings.json` that append to `progress[]` automatically.
- Verification: hand-write a row, run the skill, see the row correctly filled.

### Step 2 — the launch lane

- `.github/workflows/handle-request.yml`, `on: repository_dispatch: types: [request]`.
- Steps: `actions/checkout`, then
  `npx @anthropic-ai/claude-code@latest -p "/handle-request ${{ github.event.client_payload.request_id }}"`
  with `CLAUDE_CODE_OAUTH_TOKEN` from secrets and an `--allowedTools` listing
  exactly what this request type needs.
- `timeout-minutes`, a `concurrency` ceiling, `--max-turns` — so a stuck run
  costs minutes rather than a day.
- Secrets: `CLAUDE_CODE_OAUTH_TOKEN`, plus whatever `scripts/answer` needs to
  reach the queue.
- Verification: `gh api repos/<repo>/dispatches` by hand, and watch a row travel
  to `done`.

### Step 3 — front end and dispatch

- One button. Writes a row, polls it, renders `progress[]` and `result`.
- The app backend holds a GitHub credential scoped to `actions: write` on one
  repository. It **never** holds a Claude credential — that one lives at GitHub.
- "Logging in" is the user naming their repository and granting that narrow
  access. No device-authorization protocol is warranted: this is handing over a
  key, not binding a device.

### Step 4 — the thin template, B

- `template/` in A: `.claude/skills/<types>/`, `scripts/answer`,
  `.github/workflows/handle-request.yml`, `CLAUDE.md` (agent-facing, English,
  contracts only), `README.md` (a setup runbook in human language).
- A release workflow that publishes `template/` to repository B.
- B carries **no** development loop: no `/plan`, no `/go`, no `/finalize`. The
  end user never converses with that repository, so there is nothing there to
  plan.

### Step 5 — runbook and a first live user

An honest list of what a person does by hand, once:

1. "Use this template" on B → their own private repository.
2. Install Claude Code, run `claude setup-token`, and put the result in the
   repository's secrets as `CLAUDE_CODE_OAUTH_TOKEN`. **A terminal is needed
   here and nowhere else** — there is no browser path to minting that token.
3. On the app's site, name the repository and grant access.

Step 2 is the single place the runbook meets a command line. Screenshots and
verbatim commands are mandatory there; everything else is clicks.

## DRY notes

- **`scripts/answer` exists once, in `template/`.** It is part of the product,
  not of A's tooling. A does not use it; A publishes it.
- **The request schema is a single source of truth.** One zod schema per type,
  the TypeScript type inferred from it, the table schema derived from it, nothing
  hand-written twice — a direct application of CLAUDE.md § "Derive types and
  schemas from the source of truth".
- **`template/` is the source and repository B is a copy.** Two trees exist, but
  one is edited and the other is built. Any other arrangement is the classic pair
  that diverges silently.
- **The "launch mechanism" abstraction is one function** in the backend,
  `dispatch(requestId)`. Not an interface, not a factory, not a strategy: with
  one implementation there is nothing to generalize. A second appears if and when
  the session lane works, and then it is an `if`.
- **No shared library between A and B.** The temptation is real — both sides know
  the request schema — but A and B ship at different rates and live with
  different people, so a shared package between them means versioning for the
  sake of two files. The schema lives physically in `template/` and reaches A by
  the build, not by an import.
- **Request-type skills inherit nothing from muthur's skills.** The only thing in
  common is the file format; extracting a "base skill" would abstract over two
  unrelated jobs.

## Risks

| Risk | What we do |
| --- | --- |
| Injection through the request payload | Only an `id` crosses; contents are read by the skill and handled as data. `--allowedTools` per request type, never one blanket list |
| The user's Claude token leaking | It never passes through our backend. It lives in their repository's secrets, can only make model requests, and is revoked by reissuing |
| Our GitHub credential leaking | Scoped to `actions: write` on one repository; worst case is spurious runs burning the owner's limits, which the `concurrency` ceiling also bounds |
| Actions minutes | 2000/month on private repos at ~2 min per request is roughly a thousand requests. Monitor; do not optimize ahead of it |
| A stuck run | `timeout-minutes` plus `--max-turns` plus the concurrency ceiling |
| A retry running the work twice | Idempotency on the queue side: `queued → working` as an atomic update, and a repeat against a claimed row is a no-op |

## The researched alternative: cloud sessions

Kept because it works, not because it is a fallback. If Anthropic documents
`create_session`, it becomes the simpler of the two.

**Shape.** A long-lived dispatcher — an ordinary cloud session in Auto mode —
waits for requests and spawns an executor per request. Which spawning mechanism
is not obvious, and the right answer is hybrid: **sessions for succession,
subagents for work.** Subagents have a real depth limit
(`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` is set in the environment) and sessions
have none, so the path that runs per request must be the mechanically bounded
one.

**Survival** is not achieved by preventing death but by three moves:

- Planned rotation: the dispatcher spawns its successor before its context fills.
  Self-recursion makes that free, and reduces "must live a day" to "must live
  until handover".
- A mutual watchdog: two dispatchers, a heartbeat each, either able to spawn a
  replacement for the other.
- A correlated failure still needs a human in a browser. A routine cannot
  resurrect them: its session cannot spawn sessions.

**What it lacks before it can be chosen:** documentation, a depth limit on
sessions, and a non-browser genesis — Auto mode is set by a person. The first two
are not ours to supply.

**What it shares with the chosen lane:** everything but Step 2. The executor
contract, the schema, `scripts/answer`, the skills and the template all carry
over unchanged. That is why Step 1 precedes Step 2 rather than the other way
round.

## Open questions

Each is written into the plan in its recommended form; an answer that differs is
a plan revision, and silence is a valid resolution.

1. **A's repository name.** In the plan: `agent-as-a-backend`, as a working name
   that can be changed.
2. **v0 scope:** one user (Vova himself, no auth, no pairing) or multi-user from
   the start. In the plan: **one**.
3. **Where the queue lives:** Supabase with RLS / GitHub Issues in the user's
   repository / files in the repository. In the plan: **Supabase**.
4. **The first request type.** In the plan: **`pick-clothing`** — weather plus
   wardrobe, self-contained, and it exercises the whole path.
5. **B as a build artifact of A**, or a separately maintained repository. In the
   plan: **build artifact**.
