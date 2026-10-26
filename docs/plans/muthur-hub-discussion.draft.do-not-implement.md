> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# Muthur hub: one private repo listing an operator's live work

## Goal

An operator who opts in gets a private `<handle>/muthur-hub` repository whose
issues are their **matters** — one per piece of live work, a discussion or a
task, across every muthur adopter they work in. The loop keeps each issue
current (sessions, PR, status) without the agent having to remember to; the
operator works the list in GitHub's own UI: close an issue to drop a matter,
label it, comment on it, bookmark the filtered list.

Settled in the discussion (`docs/remove-before-merging/relay-1.md` and this
session):

- **Individual, never a team hub** — for now. A shared hub is a later idea.
- **Push, not pull.** A session writes to the hub itself, with the operator's
  own `gh` token, which reaches their private repos outside the session's
  attached scope (checked: `ADMIN` on `vzakharov/life` from a session attached
  to `vzakharov/muthur`). No GitHub Action: a private repo's minutes are not
  free.
- **Storage is issues**, so two sessions never race on one file, and labels give
  priority and the rest room to grow. The one file the operator reads, the hub's
  `README.md`, is rendered from them by code (§ "The overview"). A GitHub
  Project board over them is the follow-up issue filed with this plan, not this
  PR.
- **The code name is `matter`**; people see an issue.
- **A cross-repo matter** is not modelled — later.

## Operator settings

One JSON object per operator holds every per-operator muthur flag — `hub` and
`manualRelay` now — read by one helper, so a new flag is a key, not a new file
layout.

- **Global by default: a secret gist** in the operator's account holding
  `muthur-settings.json`, found by filename through `gh api gists`. One answer
  covers every adopter.
- **The operator is told before the gist is created, and may refuse.** The first
  write of any setting with no store yet puts it to them: a secret gist is
  unlisted, not private — anyone holding its URL reads it — and the alternative
  is a file in this repository, at the price of being asked again in every
  adopter. A refusal writes `.claude/operator-settings/<handle>.json` with
  `"store": "repo"`, committed with their words quoted.
- **Precedence**: the repository file when it exists, else the gist, else unset.
  So a refusal holds in the repository that heard it, and a new adopter asks
  both questions afresh, as the operator accepted.
- **Read once per session, then locally.** A `SessionStart` hook resolves the
  store and caches the object in `tmp/operator-settings/<handle>.json`; the
  `PostToolUse` context-budget hook reads that cache, never the network.
  `settings.py set` writes the store and the cache together.
- **`manual-relay/<handle>` becomes `manualRelay`.**
  `.claude/context-budget/hooks/post-tool-context-budget.sh` reads it from the
  cache (the `MUTHUR_MANUAL_CONTEXT_BUDGET_RELAY` environment switch is
  unchanged), and `.claude/context-budget/CLAUDE.md` § "Manual relay" is
  rewritten to point at the settings store. The tree holds no `manual-relay/`
  files today; an adopter's existing ones are carried into the store by the
  catalog entry's port note.
- **A failure to reach the gist is said, never read as unset**: the hook prints
  one line naming it and the session proceeds as though nothing were stored,
  without offering any question that would overwrite a store it could not read.

Home: `.claude/operator-settings/` — `settings.py` (`get <key>`,
`set <key> <value>`, `where`), a `CLAUDE.md` holding the contract above, the
hook, tests. `settings.py` goes into `.claude/settings.json`
`permissions.allow`.

## Opting in

- **`hub` unset → asked once.** The settings hook prints, while `hub` is unset
  and the operator is resolved, that the agent should ask in its first reply —
  plainly, what the hub is and that it creates a private repo. An existing
  `<handle>/muthur-hub` with `hub` unset is a yes already: the hook sets `true`
  and asks nothing.
- **`/update-muthur` asks too** when it ports the hub group, since the session
  running it started before the hook existed in its tree — under the same rule:
  only while `hub` is unset and no `<handle>/muthur-hub` exists; an existing hub
  sets `true` silently.
- **Yes** → `settings.py set hub true`, then `.claude/hub/create.sh`
  (allowlisted in `permissions.allow`, so the auto-mode classifier lets it
  through): `gh repo create <handle>/muthur-hub --private`, the first render of
  `README.md`, the hub session's files (§ "The hub session"), and the `status:*`
  labels. The creating session's claude.ai account goes into the `accounts`
  setting with an empty label, as the default (§ "A matter"). Then `/hub` runs
  its tour and offers seeding.
- **No** → `settings.py set hub false`, never asked again where the store
  reaches.

## A matter

- **Keyed by repository and branch**: the issue body carries
  `<!-- muthur-matter <owner>/<repo>@<branch> -->`. A relay successor, a
  `/from-branch` and a `/handle` land on the same branch and so in the same
  matter with no guessing; a "start a new session to fix this" gets its own
  branch and so its own matter, whatever `parent_session_id` says.
- **Found by listing, not searching**: issues labelled `repo:<repo>`, the marker
  matched client-side. The search index lags, and a lag here is a duplicate.
- **The body's managed block** — repository, branch, PR, and one line per
  session (link, claude.ai account, opening prompt, date) — is rewritten by the
  sync; anything outside it is the operator's. **The title** is the opening
  prompt at creation and never touched again, so the operator renames freely.
- **Labels**: `repo:<repo>` and one `status:*`, the only labels the sync writes;
  every other label is the operator's.
- **Status, derived from the tree and the PR, never set by hand from the loop**:
  `status:planning` (a draft plan), `status:in-progress` (an in-progress or
  completed plan, or commits with no plan), `status:paused` (a paused plan),
  `status:review` (a PR out of draft), `status:discussion` otherwise. A merged
  PR closes the issue with a comment; a closed-unmerged one leaves it to the
  operator.
- **A closed matter stays closed.** The sync never reopens one — closing is the
  operator's "no longer live". The `Stop` hook tells the operator so itself,
  once per session, as a `systemMessage` — shown to them, not to the agent, so
  no turn is spent relaying it: "this branch's matter is closed in the hub".
- **One GitHub account, several claude.ai accounts, one hub.** The hub follows
  the `gh` token, so an operator working one repository from a personal and a
  corporate claude.ai account has one hub, and both accounts' sessions on a
  branch share its matter. A session link opens only in the account that owns
  it, so a session line names its account by the label the `accounts` setting
  (`{"<email>": "<label>"}`) gives it, else by the email's domain. An empty
  label names nothing: the default account, the one that created the hub, is
  written with one, so an operator on a single account never sees a label. The
  email is the `userEmail` of the transcript's `session_context` record, read
  beside `.claude/costs/lib/identity.py`'s other readers. Several GitHub
  accounts are out of scope.
- **The default branch has no matter**: work there is nobody's matter.
- **A branch rename moves the marker**: `/branch-rename` calls
  `hub.py rename <old> <new>`, since a turn may already have created the matter
  under the old name.

## The sync

A `Stop` hook, `.claude/hub/hooks/stop-hub-sync.sh` → `hub.py sync`, every turn
where `hub` is `true`:

1. Compute the matter's state locally — branch, plan file state, session URL and
   opening prompt via `.claude/costs/lib/identity.py`.
2. One `gh pr list --head` for the PR's number and state.
3. Compare with the last state written, cached in `tmp/hub/<session>.json` with
   the issue number; write to GitHub only on a difference.
4. After a turn that wrote an issue, re-render the overview (below).

**A failed write blocks the stop once**, with `gh`'s message, bailing on
`stop_hook_active` — the ledger hook's rule, for the same reason: quieter loses
the matter's update without anyone knowing, and the next turn retries.

## The overview

The hub's `README.md` is the one page the operator reads, so a pin to it
replaces the dozens of session pins: open matters grouped by repository, ordered
within a repository by a `P0`–`P3` label where the operator set one, then by
status; each line the issue title linked, its status, its PR, and its latest
session with that session's account.

- **Rendered by code, never by an agent.** The page is a pure function of the
  open issues, so `hub.py render` produces it with no judgement to spend tokens
  on, and the same listing always renders the same bytes.
- **Many writers, no race.** Every adopter's sync renders it, so there is no
  single owner to keep alive. The write goes through the contents API with the
  file's current blob `sha`; a concurrent write makes it fail with a conflict,
  and the loser re-lists the issues and renders again, up to three tries. Every
  version of the page is therefore a render of a real listing — a stale
  overwrite cannot land. A render equal to the current page is not written, so
  the hub's history is the overview's history.
- **The operator's own edits** in GitHub's UI — a close, a label — show on the
  page at the next sync from any adopter, or when the hub session renders it.
- Below the list, a fixed section says what the hub is and how to work it, so
  the page is also the hub's introduction.

## The hub session

A claude.ai session in the hub repository is the place to talk about the matters
— "what's on today?", "close the German one" — and the one session pin the
operator keeps. The hub has none of muthur's tooling, so `create.sh` seeds it
with what that session needs, from `.claude/hub/hub-repo/`:

- `CLAUDE.md` — what the hub is; that the agent reads the page and the issues
  with `gh`, acts on issues, and changes the page only by rendering it — the
  same `sha`-conditioned write as the sync; and that a session past about 250k
  tokens of context hands over through `create_session` with a short summary of
  what is live, telling the operator to re-pin — there is no relay here.
- `.claude/skills/brief/SKILL.md` — the morning brief: render the page from the
  issues (the seeded copy of `render.py`), then summarise what moved since the
  last brief.
- `render.py` — the renderer, the one file `hub.py` imports, so both render the
  same bytes. Until `/hub refresh` re-seeds a hub whose copy is older, the brief
  and the sync can render the page differently, and whichever wrote last shows —
  a cosmetic flip, never lost data, since both render the same issues.

## Seeding and the tour — the `/hub` skill

- **`/hub`** — the tour: where the hub is, what a matter is, what the loop
  updates and what is the operator's (close, labels, comments, plain chat —
  "закрой дело про немецкий" is a `gh issue close` any session can run).
- **`/hub seed`** — web only (`list_sessions` is a Claude Code Remote tool): the
  operator's sessions updated in the last 14 days, grouped by repository and
  branch (which folds relay chains for free), dropping a branch whose PR merged
  or which no longer exists; plus any session the operator names or shows in a
  screenshot. The list goes to the operator in chat; only what they keep is
  created. `list_sessions` sees only its own claude.ai account, so the tour says
  to run it once from each account the operator works in; a second run merges
  into existing matters rather than duplicating them.
- **`/hub refresh`** — re-seeds the hub session's files from this adopter's
  `.claude/hub/hub-repo/` when they differ, after saying which.

The `SKILL.md` is new and its description is always loaded, so it is written
through a staged copy per `.claude/rules/staging.md`.

## Shipping it

- **Catalog**: a new group, `g11-hub.md`, **opt-in: ask**, requiring `gh` (with
  the `gist` scope for the global store) and `python3`; the operator settings
  ride with it, and G8's entry names its new dependency on them.
- **Three wiring sites** (CLAUDE.md § "Vetting"): `scripts/vet.sh` runs the new
  tests; `.claude/hooks/install-deps.sh` needs nothing new; the environment
  setup script needs nothing new.
- **Tests** at the `gh` boundary — a stub `gh` on `PATH` answering canned JSON:
  settings precedence and the refusal path, the cache, status derivation for
  each plan state and PR state, the marker round trip, rename, the closed-matter
  rule, the write-only-on-change cache, two accounts' sessions in one matter
  with their labels and the default account's none, the render's grouping and
  order, and the conflict retry on a stale `sha`.

## Not in this PR

- The Project board — vzakharov/muthur#225.
- **The operator's voice entry in the settings store** — a follow-up issue,
  filed when this plan is approved: `voice.md` beside `muthur-settings.json` in
  the same gist, read when the repository has no
  `.claude/voice/operators/<handle>.md`, so the entry follows the operator into
  every adopter. It changes `operator-voice.sh`, the voice rule's "written down
  in the entry" and what `/detemplate` and `/spinoff` carry, and whether an
  entry stays visible to the team is a call of its own — review enough for its
  own PR. The store needs nothing from this PR for it: a gist holds several
  files.
- A team hub; cross-repo matters; one operator on several GitHub accounts.

## DRY notes

- **Operator resolution** — `.claude/hooks/operator-voice.sh` and the
  context-budget hook each call `gh api user` and lowercase the login. The
  settings hook makes a third caller; it reuses the same expression rather than
  a shared library, since the two existing ones are shell one-liners and a
  library for one `jq` filter would cost more than it saves.
- **Session identity** — the sync reuses `.claude/costs/lib/identity.py`
  (`session_url_in`, `prompt_text_of`) rather than re-reading the transcript its
  own way. That couples G11 to G7's lib, named in the catalog entry's **Pulls
  in**.
- **The yes/no reading** — `switch()` in the context-budget hook goes away with
  the file it read; `settings.py` owns parsing a flag.
- **The block-once `Stop` rule** — shared in spirit with
  `.claude/costs/hooks/stop-session-cost.sh`, but the two hooks fail on
  different things and the rule is two lines; no shared helper.
- **The renderer** — one `render.py`, imported by `hub.py` and seeded into the
  hub as a copy. The copy is a duplicate by necessity, since the hub carries no
  muthur tree to import from; `/hub refresh` is what keeps it from drifting.
- **Plan state** — `docs/plans/` suffixes are read by several skills in prose;
  the sync is the first code to read them, so it owns a small mapping rather
  than inventing a shared one.
