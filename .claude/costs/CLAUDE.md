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

Nothing in the transcript is the title Claude Code shows. Four fields stand in
for one, and only the last is not read out of the file:

- **`openingPrompt`** — the session's first prompt, unwrapped from the envelope a
  slash command arrives in, so it reads `/handle <branch>`.
- **`prs`** — the numbers off the `pr-link` records, which is what groups the
  several sessions one pull request takes.
- **`url`** — the address a person opens the session at. Its id is a different
  one from the transcript's, and reaches the file only as prose, inside the
  attribution reminder the harness re-sends on a remote session change. That one
  record is what is matched: a commit trailer quoted anywhere in a transcript
  carries a session URL too, usually another session's.
- **`name`** — a few words from the agent whose session it is, which is the only
  thing here that knows what the session turned out to be about.
  `hooks/prompt-session-name.sh` asks for it from the first prompt until it is
  set, and each rewrite carries the existing name forward, since re-reading the
  transcript could never produce one.

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

A couple of percent of slack covers what Claude Code counts and no row can: the
background Haiku calls and each compact's own request, neither of which appears
in the transcript as a response. Together they measured a fraction of a percent;
reading a subagent's file short of its spend was seven, which is the failure
this check exists to catch.

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

**The hook waits the check out.** That check leaves nothing on disk — it reads
the tree and writes to stderr — so its process is the only thing there is to
wait on, and the hook polls for it by name at the last moment before anything it
does can touch the tree. A match that is an **ancestor** of the hook is not the
check: the check is a sibling, and an ancestor carrying the name is a shell that
merely mentions it, so waiting on one would outlast the turn. Whether the look
ever lands while the check is running is unmeasured here.

Every way the wait can fail — no `pgrep`, a renamed check, a look that lands
before the process exists, a check still running after five seconds — falls back
to racing, and so does a failed push, which leaves a commit the check will refuse
on the _next_ turn, attributed to nobody. So the hook re-reads the same two
conditions after its own work and, when they hold, exits 2 with one line naming
the row — the only channel a `Stop` hook has to the agent, spent solely where a
block is already happening. It bails on a re-fired `Stop` (`stop_hook_active`)
exactly as the harness's check does: two hooks that can both block and neither
bail would hold the turn open forever.

**The arrangement is read from the launcher's config, not assumed.** All of the
above holds only while `~/.claude/launcher-settings.json` registers that check;
a harness that renames or drops it leaves this hook waiting on a process that
never runs, and every paragraph here describing a race that is over. So the hook
reads that registration each turn and writes to stderr when the entry is gone:
adjusting quietly is what would leave the rest of this section false.

## The report

`python3 .claude/costs/report.py` sums the rows four ways every run — by month,
week and day, and by the branch that spent it with the pull requests it touched
named beside it; `--json` prints the lot. The spend is the branch's rather than
each PR's, since a session that touched two would otherwise be counted twice.

**Nothing is written to disk.** The totals are wholly derived from the rows, so a
file of them committed beside its own sources would be a merge conflict on every
branch that ran a session — and settling one by summing the two sides
double-counts every session both of them saw. The rows themselves never collide:
one file per session id.

## What the totals do not cover

- **The last turn of a session.** The transcript is written asynchronously and
  lags the live conversation, so each run rewrites the row from the whole file
  and picks up what the previous run was too early to see. The final turn has no
  successor to correct it, and **no turn can close that**: a step in `/finalize`
  runs in the same session and is followed by the turns that invoked it, so it
  moves the blind spot rather than removing it. What closes it is a read that is
  not a turn. A **later session** re-prices the file, which needs the transcript
  to outlive this one — true locally, false in a remote container, discarded
  with `~/.claude/projects/` inside it unless something committed a copy first.
  A **watcher on the transcript** sees the trailing appends, the container
  outliving them by a wide margin, and costs the serialisation § "Running beside
  the harness's Stop check" is built on: it would write and commit with no turn
  in progress.
- **The turn that merges.** `/finalize and merge` merges within its turn and the
  row lands after, on a branch already merged — so that turn's spend reaches
  neither the trunk nor any later merge.
- **Each compact.** The transcript records the compaction call without its
  `usage` — the boundary record carries `preTokens`, the summary arrives as a
  `user` record — so there is nothing to price. Bounded rather than unknown: two
  compacts of one measured session read 526k tokens between them, about $0.30 at
  the cache-read rate a warm prefix gets.
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
