# The API-rate cost ledger

`sessions/<YYYY-MM>/<session-id>.json` records what a session would have cost at
Claude API rates. The subscription price hides that number, and the point of
having it is to know the size of the bill before subscription pricing stops
being a bargain.

## Reading a transcript

Properties of `~/.claude/projects/<cwd-slug>/<session-id>.jsonl` that decide how
`lib/pricing.py` reads it. Each is load-bearing: get one wrong and the totals are
confidently incorrect rather than absent.

- **A subagent's spend is in a different file.** `<session-id>/subagents/*.jsonl`
  beside the transcript, one per agent — and it is the session's spend, billed to
  whoever spawned it. A reading that opens the main file alone therefore prices
  every delegating session short, and short in the one way nothing shows: the
  result looks exactly like a session that delegated nothing.
- **One API response is written as several records** — one per content block, so
  a turn that thought and called two tools writes three — and each carries that
  response's _whole_ `usage`. Records are deduplicated by `message.id`; summing
  them triples the bill.
- **A response is billed at the rates for its `(model, speed)` pair.** Fast mode
  doubles the rates, so `usage.speed` is read rather than assumed.
- **Cache writes are billed by TTL.** `usage.cache_creation` splits into
  `ephemeral_5m_input_tokens` and `ephemeral_1h_input_tokens` — ×1.25 and ×2 of
  the input rate, against ×0.1 for reads.
- **Thinking tokens are already inside `output_tokens`.** They are reported for
  interest and billed once.
- **An absent field may arrive as an explicit `null`.** `lib/shape.py` reads the
  two alike, and a `<synthetic>` model — the placeholder Claude Code writes for a
  turn no model served — is skipped rather than offered to the price table.

An unpriced `(model, speed)` **raises**. A response silently counted as free
makes every total downstream a lie, and the failure is loud precisely because
`prices.json` is hand-maintained: no machine-readable source of Anthropic's
prices exists, so the table goes stale by sitting still. A new model is a new
row there before its first session can be priced.

## What names a session

Nothing in the transcript is the title Claude Code shows. Three fields stand in
for one, all read out of the file:

- **`openingPrompt`** — the session's first prompt, unwrapped from the envelope a
  slash command arrives in, so it reads `/handle <branch>`.
- **`prs`** — the numbers off the `pr-link` records, which is what groups the
  several sessions one pull request takes.
- **`url`** — the address a person opens the session at. Its id is a different
  one from the transcript's, and reaches the file only as prose, inside the
  attribution reminder the harness re-sends on a remote session change. That one
  record is what is matched: a commit trailer quoted anywhere in a transcript
  carries a session URL too, usually another session's.

**`operator`** is whose session it was: the GitHub handle
`.claude/hooks/operator-voice.sh` resolved at startup, read off the record that
hook leaves in the transcript. It is null wherever the hook named nobody — no
`gh`, or a token that is a bot's — rather than guessed from the pusher, who is
the token and so may be the agent's own account.

## Orientation

A row's `orientation` is what the session spent before it first **acted**, and
each of its `compactions` carries the same measure from that boundary on, plus
the re-reads the summary forced. They feed the call on whether a fresh session
or a compact is the cheaper way to shed context. `lib/orientation.py` holds
the definitions.

- **Acting is a write into the repository or a handover to the operator** — an
  `Edit`, `Write` or `NotebookEdit` under the directory the session started in
  and outside its `tmp/`, an `AskUserQuestion` or `ExitPlanMode`, or the
  session's own `end_turn`. A scratch write is how an agent finds its bearings,
  not what it does with them. A subagent's `end_turn` only hands its result
  back to whoever spawned it, but a subagent's edit counts: delegated work is
  still the session starting work.
- **The acting response is left out of the spend**, since its output is the
  edit or the answer itself.
- **Timestamps order the responses, not file position**, because a subagent's
  spend sits in another file and its clock is what places it against the main
  file's.
- **Each phase stops at the next boundary**, so no response is counted in two.
- **A re-read is an exact repeat of a call made before the latest boundary** —
  a `Read` of the same path and range with no write to it since, or a `Grep`,
  `Glob` or `Bash` with the same input bar its `description` — counted once per
  boundary. Only the session's own calls count: a subagent starts with no
  context the summary could have dropped. The estimate is an estimate because a
  tool result has no `usage`: its tokens are its share, by characters, of the
  cache write of the response it arrived in, and its dollars that write plus a
  cache read on every later response before the next boundary.

**What it misses.** An edit made through `Bash` is not seen as acting, so such a
session's orientation runs long. Re-reads are a floor: a hole read around — a
`cat` after a `Read`, a narrower grep — or one that shows as a wrong turn goes
uncounted, while a repeat that was simply due, a `git status` before each
commit, counts; `byTool` is what lets `Bash` be read apart. The compaction call
itself has no `usage` to price. A resume in a fresh container reloads the
transcript with no boundary to restart at, so what it spends getting its
bearings lands in the work.

## Telemetry

`hooks/start-telemetry-receiver.sh` starts a receiver on `127.0.0.1:4318` at
`SessionStart`, and each `api_request` event Claude Code exports to it lands in
`tmp/telemetry/<session-id>.jsonl`, stripped to its numbers and a few named
fields. `lib/billed.py` joins them to the priced responses by request id.

**The events' worth is the calls the transcript never records.** Where a
response and its event are both there, the table and the event price it alike,
so the response keeps the table's price and the event checks it; the row warns
when the two drift apart. An event no response matches is such a call — a
prompt suggestion, a compaction — and goes into `total` and `byRate` at the
event's price, and into `telemetry.unseen` by its `query_source`, which takes
values the documentation does not list (`sdk` for a web session's main thread,
`prompt_suggestion`, `compact`). A compaction's `billedUsd` is the
`compact`-tagged call nearest its boundary. An event does not split its cache
write by TTL, so an unseen call's write is filed under the 5-minute tokens.
Events are only as complete as the receiver's uptime: what Claude Code sent
before it started, or after the row was written, is in no row.

**The export is the environment's to switch on, never the repository's.**
Claude Code ignores its OpenTelemetry exporter variables in a project's
`.claude/settings.json` (code.claude.com/docs/en/env-vars), reading them only
from the process environment, user settings and managed settings — so, in a
web session, the cloud environment's own variables. Where they do not point at
the receiver, the hook starts nothing and prints a notice naming them; its list
is the one home of what to set. Claude Code strips `OTEL_*` from every process
it spawns, so the hook reads them from the `claude` process's own environment. `NO_PROXY` stays off it: the environment's own
list already exempts `127.0.0.1`, and a value set beside the others replaces it.

## Checking the arithmetic

The table has no published source to check itself against, but the transcript
can carry a second opinion: `cost-state` records, where Claude Code writes its
own running total for the session. The last one lands in the row as
`claudeCodeTotalUsd`, and `report.py` compares. Not every Claude Code build
writes them, so a row without one is reported as unchecked rather than passed.

**The comparison runs one way only, and that is what makes it sound.** Both
figures count the same session upward, and Claude Code's is read out of the very
file the row was priced from — so it was written at or before the moment the row
was. A row coming out **under** it has missed a source. A row coming out over it
means only that the session kept going, which every row's last turn does.

Without events, a row misses what Claude Code counts and the transcript does
not record as a response: prompt suggestions, which are full-context calls on
the session's own model, and each compact's own request. They measured a few
percent of a session's spend; reading a subagent's file short of its spend was
seven, which is the failure this check exists to catch. A row with events has
them in its total.

**The usage panel is not a third opinion, and what breaks it is compaction.**
Against a session that has never compacted it agrees to within 1%, and each
compaction after that puts it out by tens of dollars across a window in which the
transcript gains no responses at all. Its "Cost" also disagrees with its own
Breakdown's cost row, by different factors on different cards — so the gap is not
a unit or a stale rate, which would miss by one factor in both.
anthropics/claude-code#95837 carries the measurements and asks which figure is
authoritative.

## Running beside the harness's Stop check

The harness registers its own `Stop` hook in `~/.claude/launcher-settings.json` —
`stop-hook-git-check.sh`, which ends a turn with exit 2 on a tree that is
unclean, holds untracked files, or is ahead of its remote. **Hooks for one event
run in parallel**, so writing and committing the row is work done while that
check may be reading the tree.

**The row never makes the tree look unfinished.** It is priced into `tmp/`,
committed in a throwaway index, and pushed before the branch moves; only then do
the branch, the index entry and the file follow. So the tree differs from `HEAD`
only between the ref move and the rename, and is never ahead of `origin` while a
push is in flight. `commit-tree` runs no commit hooks, which suits a file no
formatter should rewrite, and signs only when asked, so the hook passes `-S`
where `commit.gpgsign` is on.

**The hook also waits the check out**, which leaves it only those two steps to guard.
That check leaves nothing on disk — it reads the tree and writes to stderr — so
its process is the only thing there is to wait on, and the hook polls for it by
name at the last moment before anything it does can touch the tree. A match that
is an **ancestor** of the hook is not the check: the check is a sibling, and an
ancestor carrying the name is a shell that merely mentions it, so waiting on one
would outlast the turn.

**What neither covers is a tree that was unclean before the hook started.** A
hand run of `session_cost.py` rewrites the row in place, and a failed push
leaves a commit the check will refuse on the _next_ turn, attributed to nobody.
So the hook reads the tree after its own work and, where the row was part of what
the check saw, exits 2 with one line naming it — the only channel a `Stop` hook
has to the agent, spent solely where the check's own exit 2 is already
continuing the turn. It bails on a re-fired `Stop` (`stop_hook_active`) exactly
as the harness's check does: two hooks that can both block and neither bail
would hold the turn open forever.

**The arrangement is read from the launcher's config, not assumed.** All of the
above holds only while `~/.claude/launcher-settings.json` registers that check;
a harness that renames or drops it leaves this hook waiting on a process that
never runs, and every paragraph here describing a race that is over. So the hook
reads that registration each turn and writes to stderr when the entry is gone:
adjusting quietly is what would leave the rest of this section false.

## The report

`python3 .claude/costs/report.py` sums the rows five ways every run — by month,
week and day, by the branch that spent it with the pull requests it touched
named beside it, and by operator — then orientation's averages, and the calls
only the events saw, by `query_source`, as a share of the spend of the rows
priced with events; `--json` prints the lot. The spend is the
branch's rather than each PR's, since a session that touched two would otherwise
be counted twice.

**The totals are never written to disk.** They are wholly derived from the rows,
so a file of them committed beside its own sources would be a merge conflict on
every branch that ran a session — and settling one by summing the two sides
double-counts every session both of them saw. The rows themselves never collide:
one file per session id.

**The rows can be.** A row carrying a key the current shape no longer writes is
rewritten without it as the report reads it, and the report names each one on
stderr. Retiring a field is therefore a change to the shape alone: the first
report in each repository clears it, and those rewrites are ordinary changes to
commit.

## What the totals do not cover

- **The turn that merges.** `/finalize and merge` merges within its turn and the
  row lands after, on a branch already merged — so that turn's spend reaches
  neither the trunk nor any later merge.
- **Each compact, without events.** The transcript records the compaction call
  without its `usage` — the boundary record carries `preTokens`, the summary
  arrives as a `user` record — so only the events price it. One compaction of a
  230k-token context with a warm cache measured about $0.22, most of it output.
- **A rate that changed after a row was written.** Each row records the
  `pricesAsOf` it was priced under and is never re-priced — its transcript is
  usually gone by then — so a table update applies forward only, and `report.py`
  prints the table's age and how many rows were priced under an older one. The
  unpriced-pair error catches a **new** `(model, speed)` pair and is blind to a
  number that changed; the `cost-state` comparison above is what covers that.
- **Abandoned branches.** Rows reach the trunk by merge, so work that is thrown
  away is thrown out of the ledger too — an undercount biased toward exactly the
  sessions that spent without delivering.
- **Other repositories.** The transcript directory is keyed by working
  directory, so these totals are this repo's. A cross-repo month needs a home
  outside any one repository.
- **The trunk itself.** The hook declines to commit a row on `main` or
  `master`, where there is no branch to carry it.
