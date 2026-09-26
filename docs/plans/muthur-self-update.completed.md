# Adopters update muthur themselves

A sync 20–30 commits behind is miserable to run in one go. So an adopter's
sessions keep the lag small without being asked. At session start they notice the
source has moved and offer the operator an update at a natural moment: carried
along with the task at hand when the lag is a commit or two, or as a new session
when it is more. A lock branch on the adopter's own origin stops parallel sessions
from running two syncs of the same range.

Agreed in the session that wrote this plan. What follows is that design, plus the
mechanics it left open.

## The lock

- **Name:** `muthur-sync-lock-<lastSyncedSha>`. `<lastSyncedSha>` is the first 12
  characters of the watermark **on the trunk**, not in the working tree, because
  a session on an old branch would otherwise check the wrong lock. When a sync
  lands, the trunk's watermark moves, so every session asks about a new name and
  the old lock drops away without anyone deleting it. **Old locks stay** as a
  record of who synced what, and when.
- **Content:** one claim commit, built with `git commit-tree` on the trunk's
  tree, with the trunk as its parent. Its message carries the holder:

  ```
  chore: claim the muthur sync from <lastSyncedSha>

  Claimed-By: @<handle>
  Session: <url | local>
  ```

  `<handle>` comes from `gh api user`. `<url>` is
  `https://claude.ai/code/session_<id>`, where `<id>` is
  `$CLAUDE_CODE_REMOTE_SESSION_ID` with its `cse_` prefix dropped. That mapping
  is observed on a live session, not documented, so it is built in exactly one
  place. Where the variable is absent (local CLI), the line reads `local`.
- **Claim:** `git push origin <commit>:refs/heads/<lock>
  --force-with-lease=refs/heads/<lock>:`, where the empty expected value means
  the ref must not exist yet. The server checks it atomically, so of two
  concurrent claims exactly one wins. This was probed from this session: a
  non-`claude/` ref pushes through the harness proxy, and a second claim is
  rejected with `stale info`. A delete through `git push --delete` hangs up at
  the proxy while `gh api -X DELETE …/git/refs/…` works, and nothing here
  deletes a lock anyway.
- **Takeover** of a lock the operator agreed is dead: the same push, with the
  lease set to the lock's current SHA.
- **Staleness:** the claim commit's committer date. A lock younger than 24h makes
  the nudge silent. An older one is reported to the operator with its
  `Claimed-By` and `Session`, so a stuck session of their own is one click away,
  and someone else's has a URL to send them to. The operator decides whether to
  take it over; no timeout does it on its own.

## `scripts/muthur-sync.sh`

One script, three subcommands. They share the watermark read, the lock name and
the source URL, so none of those exists twice.

- **`nudge`** — what the SessionStart hook prints:
  1. Stay silent when there is nothing to nudge about:
     - no watermark on the trunk (the adopter declined `/update-muthur`);
     - `lastSyncedSha` not 40 hex characters (an unhydrated stub);
     - `origin` naming the watermark's `repo` (this is the template itself; the
       origin is resolved with `gh_resolve_repo` from `scripts/lib/gh-repo.sh`);
     - `git ls-remote` on the source reporting `HEAD == lastSyncedSha`, which is
       the common case, at about 0.4s.
  2. Check the lock (`git ls-remote origin refs/heads/<lock>`). If it exists,
     fetch it into `FETCH_HEAD` (not `--depth`, which would mark the adopter's
     clone shallow) and read its date and trailers. Younger than 24h → silent.
     Older → print the holder block and stop.
  3. Otherwise clone the source blobless into `tmp/muthur-source/`, or fetch into
     it if it is already there (about 1s, measured on muthur). Then print:
     - the one-line commit titles of `lastSyncedSha..HEAD`;
     - the files `git diff --name-only lastSyncedSha HEAD` names, each marked
       `here` or `not here` by whether it exists in this tree, with the two
       invariant exclusions (`watermark.json`, `.claude/costs/sessions/`)
       dropped;
     - the `adopted` keys verbatim, as "you adopted the following…".

     No path filtering: the agent matches the files against `adopted`, and the
     `here` marker catches a file taken without being listed. Output is capped at
     40 lines plus "and N more". Past the cap the lag is large anyway, so the
     offer is a new session and the exact list no longer matters.
  4. Print the offer rules (§ "What the agent is told").
  5. If the working tree's watermark differs from the trunk's, add that
     ride-along is unavailable on this branch, and that a new session is the
     offer.

  Any failure (no `jq`, the network, a clone) prints one line into the context
  saying the check could not run and why, and the hook exits 0. The failure is
  reported, not raised, as `prompt-issue-export.sh` does: a session must not fail
  to start over a nudge.
- **`claim [--takeover]`** — the push above. Exit 0 on a claim. Exit 3 when the
  lock is held, printing the holder.
- **`clone <dir>`** — the credential-helper blobless clone that
  `/update-muthur` Step 2 describes. The skill's Step 2 calls it, and the
  recipe's rationale (`-c` after `clone`, no `--depth`) moves into the script's
  comments, so the recipe has one copy.

Wired in `.claude/settings.json` as a second `SessionStart` entry, matcher
`startup` only (a resume already has the nudge in context), `timeout: 30`.

## What the agent is told

The nudge prints the rules with the data, so the agent has everything the offer
needs, and nothing to go and fetch:

- **Do not investigate before the operator says yes.** No clone, no `git show`,
  no reading of diffs, no claim. The titles and the file list are the whole
  input for the offer.
- **Offer at a natural moment, once.** A ride-along is offered only once the
  session is doing a change on this branch ("by the way, …"), never in answer to
  a question that changes nothing. A new session is offered at the end of a turn
  that delivered something. Declined → not offered again in this session.
- **Which offer:** a ride-along when the listed changes are one or two commits
  touching files here; a new session otherwise.
- **On yes:**
  - *Ride-along* — `scripts/muthur-sync.sh claim`, then run `/update-muthur
    claimed` in this session on this branch, its commits after the task's own.
  - *New session* — `claim` first, so nobody else takes the lock in the gap. Then,
    where `create_session` exists, spawn one on this repo with the prompt
    `/update-muthur claimed`. Elsewhere, hand the operator that command to paste.
  - A claim that exits 3 lost a race. Say who holds the lock and drop the offer.

The fuller procedure (the ride-along's place in the PR, the `claimed` argument)
goes in `/update-muthur` § "Offered at session start". The nudge carries only
what the agent needs before the operator answers.

## `/update-muthur` changes

The body changes; the `description:` does not, so there is nothing to stage.

- **Step 1** reads the watermark, then claims the lock via
  `scripts/muthur-sync.sh claim`, unless the argument says `claimed` (a parent
  session holds it for this one). Held → stop and report the holder.
- **Step 2** calls `scripts/muthur-sync.sh clone`.
- **New Step 3a — the sync is a task.** Once the candidate set exists, hand it to
  `@.claude/skills/task/SKILL.md` as the task. Steps 4–7 are how the work gets
  done in whichever outcome `/task` picks, including a split into an elephant or
  a pizza. A ride-along skips this step: it is already inside a routed task, and
  a lag of a commit or two fits by definition.
- **Step 7** sets `lastSyncedSha` to the sync's **boundary**: the HEAD recorded
  in Step 3 for a whole sync, or the last source commit a slice or bite took.
  Candidates past the boundary are left for the next one. Any commit on the
  source's first-parent line is a clean boundary. For the lock, a merged pizza
  slice moves the trunk's watermark, so the next slice claims a fresh lock; an
  elephant holds one lock across all its bites.
- **Step 8** keeps the triage-table report. The `/polish` + `/pr` handoff becomes
  whatever tail the `/task` outcome runs, since `/go` already ends in both.
- **New § "Offered at session start"** — the ride-along and new-session
  mechanics above, and what `claimed` means.

## Catalog, tests

- `catalog.md` G0: the `/update-muthur` row says it carries `scripts/muthur-sync.sh`
  and a `SessionStart` entry. A new row for `scripts/muthur-sync.sh`
  (`adopt — with /update-muthur`). The `.claude/settings.json` row names the new
  entry.
- `scripts/test_muthur_sync.py`, picked up by `check-muthur.sh` through the
  `scripts/test_*.py` pattern. It runs real git against local bare repos as the
  source and the origin, redirected with
  `GIT_CONFIG_COUNT` / `url.<file>.insteadOf` rather than a test-only knob in
  the script, and a fake `gh` on `PATH` for the handle. Cases:
  - each of the silent exits;
  - the lag output: titles, the `here` / `not here` marks, the exclusions, the
    `adopted` keys, the cap;
  - the working-tree watermark behind the trunk's;
  - a fresh lock (silent) and a stale one (the holder printed), with dates set
    through `GIT_COMMITTER_DATE`;
  - two claims (the second exits 3);
  - a takeover;
  - a failure (an unreachable source) reported as one line with exit 0.
- `./scripts/vet.sh` green.

## DRY notes

- **Shared, one copy each:** the source clone recipe (moves from the skill's
  prose into `muthur-sync.sh clone`, which the skill calls), the lock name, the
  watermark read, and the session-URL derivation. All of them live in the one
  script, with no second consumer outside it.
- **Reused:** `gh_resolve_repo` from `scripts/lib/gh-repo.sh` for the origin's
  `owner/repo`.
- **Duplicated on purpose:**
  - The trunk-ref ladder (`origin/HEAD` → `origin/main` → `origin/master`)
    becomes its third copy, beside `check-squash-message.sh` and
    `prompt-handle-pr-export.sh`. One of those is POSIX `sh` and the other wants
    only the first rung, so a shared helper would have to span two shells to
    save five lines.
  - `gh api user` repeats `operator-voice.sh`'s single call, and a wrapper
    around one `gh` call is not worth a file.
- **Not built:** hook-side filtering by `adopted`. The agent matches instead,
  which removes the machinery rather than sharing it.

## Where the build differs from the text above

- `load_watermark` fetches the trunk before trusting its watermark, so a sync
  that landed since the clone last fetched is not offered again.
- The credential helper stores `$GH_TOKEN` unexpanded, so no token lands in a
  clone's config; `/update-muthur` Step 2 therefore shares the nudge's
  `tmp/muthur-source` rather than cloning into the scratchpad.
- `clone <dir>` on an existing clone fetches and moves its `HEAD` to the
  source's, and refuses a directory cloned from anything else.
- `claimed` and `ride-along` are defined in `/update-muthur` § "Arguments";
  a ride-along runs `/update-muthur ride-along`, which skips Step 3a.
- The claim comes just before the offer rather than after the yes, and a no
  runs `muthur-sync.sh release`. A claim this session already holds succeeds
  again.
- `scripts/muthur-sync.sh` has no catalog row of its own; the `/update-muthur`
  row carries it (#116 applies the same rule catalog-wide).
