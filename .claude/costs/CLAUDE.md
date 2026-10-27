# The API-rate cost ledger

`sessions/<YYYY-MM>/<session-id>.json` records what a session would have cost at
Claude API rates. The subscription price hides that number, and the point of
having it is to know the size of the bill before subscription pricing stops
being a bargain.

## Where rows live

**`cost-ledger` is the source of truth**: an orphan branch on `origin` holding
every row at its usual path, named once in `lib/ledger_branch.py`. The default
branch carries none. The `Stop` hook writes the row there every turn, on every
branch and the trunk alike, so a session counts whether or not its work merges.

**A branch also carries a display copy until it is finalized**, so its PR's diff
shows what the work cost. It rides the agent's own commits:
`hooks/stage-cost-row.sh`, a `PreToolUse` hook on `Bash`, prices the session and
stages its row before a `git commit` runs, and nothing commits it otherwise. So
the copy is as of the session's last commit, and a session that never commits
leaves none — the ledger counts it all the same. The hook stages nothing where
the row would be wrong in the commit:

- **on the trunk or a finalized branch**, which carry no copy;
- **for a commit in another work tree**, a delegate's worktree, unless the
  command names this root by path as a multi-repo session's `cd <repo> &&` does;
- **while a merge, cherry-pick, revert or rebase is in progress**, whose
  concluding commit takes exactly what git left — `/sync-branch` relies on it;
- **for a command naming `.claude/costs/sessions`**, which manages the rows
  itself: a staged row would make `/finalize`'s `git rm` refuse, or come back in
  the commit that sweeps it;
- **for a commit with nothing else to take** — a clean index, and no
  `git add|rm|mv`, `-a`, `--all` or `--amend` in the command — which would
  otherwise succeed as a row-only commit where git said "nothing to commit".

Finalized means the PR's last `<!-- finalize-attestation <sha> -->` names a SHA
that `HEAD` still contains, and nothing after it touches more than rows. GitHub
is asked until the answer is yes, and the yes is cached in
`tmp/costs/finalized/<branch>`; a work commit after the SHA sends the question
back. `/finalize` carries the copies into the ledger and deletes them before the
branch lands, and `/finalize revoke` withdraws the attestation.

**Readers union the ledger with the default branch's tree**, one row per session
id, the later by `lib/ledger_branch.py`'s `recency` winning. The tree side is
how a repository that has not migrated still counts, and how a copy that reached
the trunk without `/finalize` is counted once.

What each failure costs:

- **A push that loses the ledger's tip** to another session re-reads it and
  rebuilds, up to three tries; rows never collide, so a rebuild loses none.
  After the third, or on a failed fetch, the hook blocks the stop once with
  git's message. The next turn's row covers the missed one, so only a session's
  last turn can be lost, and only when nobody acts on the block.
- **A GitHub query that fails** counts as not finalized: the commit carries its
  display copy and the next asks again. It is the ledger's one silent fallback,
  approved for that call site alone, and its worst case is a copy on a branch
  that merges after it, which the union counts once.

## Reading a transcript

Properties of `~/.claude/projects/<cwd-slug>/<session-id>.jsonl` that decide how
`lib/transcript.py` and `lib/pricing.py` read it. Each is load-bearing: get one
wrong and the totals are confidently incorrect rather than absent.

- **A subagent's spend is in a different file.**
  `<session-id>/subagents/*.jsonl` beside the transcript, one per agent — and it
  is the session's spend, billed to whoever spawned it. A reading that opens the
  main file alone therefore prices every delegating session short, and short in
  the one way nothing shows: the result looks exactly like a session that
  delegated nothing.
- **One API response is written as several records** — one per content block, so
  a turn that thought and called two tools writes three — and each carries that
  response's _whole_ `usage`. Records are deduplicated by `message.id`; summing
  them triples the bill.
- **A subagent's records carry the usage the stream started with.** Their
  `stop_reason` is null and their `output_tokens` a partial count — 16 of a
  response's final 112, 24 of 1,289 — while input and cache counts are already
  final. A matched event supplies the output; without one, the row warns that
  those responses' output is a floor.
- **A response is billed at the rates for its `(model, speed)` pair.** Fast mode
  doubles the rates, so `usage.speed` is read rather than assumed. A row's
  `above` is a second rate card for a model that bills a long prompt higher: a
  response whose prompt — input plus cache reads and writes — runs past its
  `prompt_tokens` is billed whole at it, output included.
- **Cache writes are billed by TTL.** `usage.cache_creation` splits into
  `ephemeral_5m_input_tokens` and `ephemeral_1h_input_tokens` — ×1.25 and ×2 of
  the input rate, against ×0.1 for reads.
- **Thinking tokens are already inside `output_tokens`.** They are reported for
  interest and billed once.
- **An absent field may arrive as an explicit `null`.** `lib/shape.py` reads the
  two alike, and a `<synthetic>` model — the placeholder Claude Code writes for
  a turn no model served — is skipped rather than offered to the price table.

An unpriced `(model, speed)` **raises**. A response silently counted as free
makes every total downstream a lie, and the failure is loud precisely because
`prices.json` is hand-maintained: no machine-readable source of Anthropic's
prices exists, so the table goes stale by sitting still. A new model is a new
row there before its first session can be priced.

## What names a session

Nothing in the transcript is the title Claude Code shows. Three fields stand in
for one, all read out of the file:

- **`openingPrompt`** — the session's first prompt, unwrapped from the envelope
  a slash command arrives in, so it reads `/handle <branch>`.
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

A row's `orientation` is what the session spent finding its bearings — until it
**marks** them found or first **acts**, whichever comes first — and each of its
`compactions` carries the same measure from that boundary on, plus the re-reads
the summary forced. They feed the call on whether a fresh session or a compact
is the cheaper way to shed context. `lib/orientation.py` holds the definitions.

- **Marking is a Bash call running `python3 .claude/costs/oriented.py` bare**,
  which `hooks/estimate-notice.sh` asks for until the stretch has one. Knowing
  what is what comes before the first edit or answer — a session tracing callers
  before it changes anything is already working — and only the agent can tell
  when. A subagent's mark is its own bearings, not the session's.
- **Acting is a write into the repository or a handover to the operator**: an
  `Edit`, `Write` or `NotebookEdit` under the directory the session started in
  and outside its `tmp/`, an `AskUserQuestion` or `ExitPlanMode`, or the
  session's own `end_turn`. A scratch write is how an agent finds its bearings,
  not what it does with them. A subagent's `end_turn` only hands its result back
  to whoever spawned it, but a subagent's edit counts: delegated work is still
  the session starting work. `endedBy` says which ended it, `oriented` for the
  mark, so the report shows how often agents mark.
- **The ending response is left out of the spend**, since its output is the
  mark, the edit or the answer itself.
- **Timestamps order the responses, not file position**, because a subagent's
  spend sits in another file and its clock is what places it against the main
  file's.
- **Each phase stops at the next boundary**, so no response is counted in two.
- **A re-read is an exact repeat of a call made before the latest boundary** — a
  `Read` of the same path and range with no write to it since, or a `Grep`,
  `Glob` or `Bash` with the same input bar its `description` — counted once per
  boundary. Only the session's own calls count: a subagent starts with no
  context the summary could have dropped. The estimate is an estimate because a
  tool result has no `usage`: its tokens are its share, by characters, of the
  cache write of the response it arrived in, and its dollars that write plus a
  cache read on every later response before the next boundary.

**What it misses.** The mark is the agent's word: one made early or late moves
the phase with it, and a forgotten one leaves the phase to end at acting, later
than it did. An edit made through `Bash` is not seen as acting, so such a
session's orientation runs long unless it marks. Re-reads are a floor: a hole
read around — a `cat` after a `Read`, a narrower grep — or one that shows as a
wrong turn goes uncounted, while a repeat that was simply due, a `git status`
before each commit, counts; `byTool` is what lets `Bash` be read apart. The
compaction call itself has no `usage` to price. A resume in a fresh container
reloads the transcript with no boundary to restart at, so what it spends getting
its bearings lands in the work.

## Telemetry

`hooks/start-telemetry-receiver.sh` starts a receiver on `127.0.0.1:4318` at
`SessionStart`, and each `api_request` event Claude Code exports to it lands in
`tmp/telemetry/<session-id>.jsonl`, stripped to its numbers and a few named
fields. `lib/billed.py` joins them to the priced responses by request id.

**The events' worth is the calls the transcript never records.** Where a
response and its event are both there, the table and the event price it alike
once the event's output count stands in for the record's, so the response keeps
the table's price and the event checks it; the row warns when the two drift
apart. An event no response matches is such a call — a prompt suggestion, a
compaction — and goes into `total` and `byRate` at the event's price, and into
`telemetry.unseen` by its `query_source`, which takes values the documentation
does not list (`sdk` for a web session's main thread, `prompt_suggestion`,
`compact`). A compaction's `billedUsd` is the `compact`-tagged call nearest its
boundary. An event does not split its cache write by TTL, so an unseen call's
write is filed under the 5-minute tokens. Events are only as complete as the
receiver's uptime: what Claude Code sent before it started, or after the row was
written, is in no row. The hook also runs after every tool call and starts a
receiver that is missing. That covers a session that checked out a branch
carrying the hook, which registers it with `SessionStart` already past, and a
receiver that died.

**The export is the environment's to switch on, never the repository's.** Claude
Code ignores its OpenTelemetry exporter variables in a project's
`.claude/settings.json` (code.claude.com/docs/en/env-vars), reading them only
from the process environment, user settings and managed settings — so, in a web
session, the cloud environment's own variables. Where they do not point at the
receiver, the hook starts nothing and prints a notice naming them; its list is
the one home of what to set. Claude Code strips `OTEL_*` from every process it
spawns, so the hook reads them from the `claude` process's own environment.
`NO_PROXY` stays off it: the environment's own list already exempts `127.0.0.1`,
and a value set beside the others replaces it.

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

Without events, a row misses what Claude Code counts and the transcript does not
record as a response: prompt suggestions, which are full-context calls on the
session's own model, and each compact's own request. They measured a few percent
of a session's spend; reading a subagent's file short of its spend was seven,
which is the failure this check exists to catch. A row with events has them in
its total.

**The usage panel is not a third opinion, and what breaks it is compaction.**
Against a session that has never compacted it agrees to within 1%, and each
compaction after that puts it out by tens of dollars across a window in which
the transcript gains no responses at all. Its "Cost" also disagrees with its own
Breakdown's cost row, by different factors on different cards — so the gap is
not a unit or a stale rate, which would miss by one factor in both.
anthropics/claude-code#95837 carries the measurements and asks which figure is
authoritative.

## Running beside the harness's Stop check

The harness registers its own `Stop` hook in `~/.claude/launcher-settings.json`
— `stop-hook-git-check.sh`, which ends a turn with exit 2 on a tree that is
unclean, holds untracked files, or is ahead of its remote. **Hooks for one event
run in parallel**, so whatever this hook does to the tree is done while that
check may be reading it.

**The hook leaves the branch alone and the tree clean.** It prices the row into
`tmp/` and writes it to the ledger only. A row it finds differing from `HEAD` is
one no commit took — staged by `hooks/stage-cost-row.sh` for a commit that left
it out (`git commit -- <path>`, a failed commit, a command that only mentioned
one), or written by a hand run of `session_cost.py` — and it goes back to
`HEAD`'s copy, or out of the index and tree where `HEAD` has none. Nothing is
lost: the ledger holds the turn's row, and the next commit stages a fresh one.

**It waits the check out before that put-back.** That check leaves nothing on
disk — it reads the tree and writes to stderr — so its process is the only thing
there is to wait on, and the hook polls for it by name at the last moment before
anything it does can touch the tree, which is after the ledger write: that
touches no file in it. A match that is an **ancestor** of the hook is not the
check: the check is a sibling, and an ancestor carrying the name is a shell that
merely mentions it, so waiting on one would outlast the turn.

**A row the check read before the put-back is named to the agent**: where it was
all that kept the tree unclean, the hook exits 2 with one line saying so — the
only channel a `Stop` hook has to the agent, spent solely where the check's own
exit 2 is already continuing the turn. A put-back that fails exits 2 too, with
the commands that do it by hand. It bails on a re-fired `Stop`
(`stop_hook_active`) exactly as the harness's check does: two hooks that can
both block and neither bail would hold the turn open forever.

**A turn that cannot be priced blocks the stop once**, with the pricing error's
last line — the missing `(model, speed)` pair, as a row to add to `prices.json`.
Anything quieter loses the session from the ledger without anyone knowing. The
same `stop_hook_active` bail applies, and the next turn's row prices the whole
transcript, so nothing is lost by stopping.

**The arrangement is read from the launcher's config, not assumed.** All of the
above holds only while `~/.claude/launcher-settings.json` registers that check;
a harness that renames or drops it leaves this hook waiting on a process that
never runs, and every paragraph here describing a race that is over. So the hook
reads that registration each turn and writes to stderr when the entry is gone:
adjusting quietly is what would leave the rest of this section false.

## Human-hour estimates

A row's `estimate` says how much work the session's spend bought, so the ledger
can price a unit of human work done by an agent and watch that price move —
including whether the same work started costing more. It is the task split into
parts, each the hours one role at one grade would spend on it and the reason for
them. A revision replaces it, so its history is git's.
`hooks/estimate-notice.sh` is the agent-facing home of when and how to set one.

- **The unit is a senior-hour**: an hour of a senior developer, the role and
  grade `rates.json` rates at 1. The table holds a multiplier per role and per
  grade, a part being worth hours × both, and is applied when the report reads a
  row, so retuning one re-rates the whole history alike and the trend stays
  comparable with itself.
- **A repository adds roles of its own in `rates.repo.json` on `cost-ledger`**,
  beside the rows they rate, so a sync of the shared table never collides with
  them. Each is `{"multiplier", "grade", "work"}`, booked at that one grade, so
  its hours land in that grade's column of the report and no estimate, command
  or table has an ungraded path.
  - **The ledger is its only home**, because the rows are written there from
    every branch: a table per branch would leave rows that only an unmerged
    branch could rate. `estimate.py role set` and `role drop` write it through
    the same append the `Stop` hook uses, so `git log cost-ledger` is its
    history; `check_estimates.py` fails a tree copy, and `ledger.py backfill`
    carries one over.
  - **It only adds.** `role set` refuses a role `rates.json` rates, and
    `role drop` refuses a role ledger rows book that the shared table does not
    rate, so every role a row names stays rateable.
  - **A role the shared table takes up later keeps the repository's multiplier
    for that repository's rows**, since they were booked against it, and the
    report, `check_estimates.py` and the notice each name both rates;
    `role drop` adopts the shared one.
- **Of the row's copy and a running session's pending one, the later wins.**
  That is how a `--session` edit to a running session's row survives its next
  `Stop`, and how the session's own later `set` overrides that edit.
- **A branch lands with an estimate on every session it carries.**
  `check_estimates.py`, in the vet run, fails one without: the notice sets no
  deadline, and a `Stop` hook would ask before the size of the work is known.
- **It sizes the task, never the session's pace.** It moves when the task does —
  scope added, a difficulty no estimator would have foreseen, a relay handing
  the rest on. A model that booked its own detours as extra hours would hide
  exactly the regression the figure exists to show.
- **A part's reason is the case for the team, not a summary of the work.** What
  was done is already in the row and the commits; what nothing else carries is
  why that part is that role, at that grade, for those hours — and only that
  lets a reader check the figure rather than take it. It sits on the part it
  justifies, so the one is never read without the other. An older row carries
  one comment for the whole; where it names each part as
  `<grade> <role>: <reason>`, the report moves it onto the parts, and where it
  does not, it stays as written, since placing it would be a guess.

**What the figure cannot tell apart:** the estimator is the model under
measurement, so a changed model may estimate differently too — a person's
`--session` revision is the check, and the row's history in git shows which
figures one touched; and a heavier `CLAUDE.md` or a new mandatory pass raises
the dollars per senior-hour with no change to the model at all.

## The report

`python3 .claude/costs/report.py` sums the rows five ways every run — by month,
week and day, by the branch that spent it with the pull requests it touched
named beside it, and by operator — then orientation's averages, the calls only
the events saw, by `query_source`, as a share of the spend of the rows priced
with events, the dollars per senior-hour over the estimated rows, by month,
week, day and model, and a period's estimated hours by role and grade, in plain
hours; `--json` prints the lot. `--month`, `--week` or `--day`, each named or
`cur` / `prev`, narrows the whole report to the sessions that started in it;
without one, the hours cover the current UTC month. The spend is the branch's
rather than each PR's, since a session that touched two would otherwise be
counted twice.

**The totals are never written to disk.** They are wholly derived from the rows,
so a file of them committed beside its own sources would be a merge conflict on
every branch that ran a session — and settling one by summing the two sides
double-counts every session both of them saw. The rows themselves never collide:
one file per session id.

**The rows can be.** A row in a shape the ledger no longer writes — a key it
dropped, an estimate comment its parts now carry — is read in the current one. A
tree row is rewritten on disk, named on stderr, an ordinary change to commit; a
ledger row is reshaped in memory only, since writing it back would be a commit
on another branch. So the reader keeps every shape the ledger still holds a row
in.

**Across repositories, the rows are read off GitHub.** `--all-my-repos` reads
`cost-ledger` and the default branch's tree of every repository the `gh` user
can reach, unioned per repository as above, and `--repo` just the ones named, so
nothing needs cloning. A `report.py` older than the ledger branch reads the tree
alone and undercounts a migrated repository. A repository counts by its ledger,
not muthur's watermark: the ledger is opt-in, so a watermark alone has nothing
to count. A row GitHub truncates stops the run, since a missing one understates
every total it belongs to, and these rows are never written back: they are
another branch's to change. Each row is rated by this checkout's `rates.json`
plus the `rates.repo.json` on its own repository's `cost-ledger`, since it may
name a role only that repository rates.

## What the totals do not cover

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
- **Repositories the token cannot reach.** `--all-my-repos` sees what the `gh`
  user sees, so an organization that enforces SAML SSO is out of reach until the
  token is authorized for it.
