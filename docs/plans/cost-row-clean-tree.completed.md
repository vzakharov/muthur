# Keep the tree clean while the cost row is written (#105)

## What actually leaves the tree dirty

The issue blames the pricing run, but that stretch is already clean:
`session_cost.py`'s `write_atomic` prices into `tmp/` (gitignored) and renames the
row into place only once it is done. The harness check starts beside the hook and
reads the tree in well under the time pricing takes, so it normally reads a clean
tree. The tree looks unclean to it in three places instead:

1. **Before the hook starts, on every turn that names the session.**
   `prompt-session-name.sh` tells the agent to run `session_cost.py --name` and
   leave the file for the `Stop` hook to commit. That run rewrites the tracked row
   in place, so the tree is dirty for the whole turn end and the check exits 2
   every time — no race involved. This fits the issue's report best: its message
   is "uncommitted changes", which is a tracked row named on a later turn (a
   first-turn name would be an untracked file, and a different message).
2. **Between `git add` and the end of `git commit`**, signing included (~100 ms
   here): the index differs from `HEAD`.
3. **Between the commit and the end of the push**, a network round trip: the
   branch is ahead of `origin`, which the check refuses as well.

2 and 3 only matter when the one look for the check's process misses it — how
often that happens is not measured anywhere.

## Changes

1. **`--name` stops touching the tracked tree.** It writes the name to
   `tmp/costs/names/<session-id>` and nothing else. The row's name comes from
   `--name`, then that file, then the previous row. `prompt-session-name.sh` goes
   quiet once either the row or that file holds a name, and its prompt says the
   `Stop` hook folds the name into this turn's row.
2. **The `Stop` hook commits the row without dirtying the tree.**
   `session_cost.py` gains `--out <path>`, writing the row there instead of into
   place. The hook then:
   - prices into a `mktemp` file under `tmp/`;
   - compares its blob to `HEAD:<row>` and stops if they are the same (this
     replaces the `dirty "$row"` test);
   - builds the commit in a throwaway index (`read-tree HEAD`,
     `update-index --cacheinfo`, `write-tree`, `commit-tree`, with `-S` when
     `commit.gpgsign` is on), so work the agent has staged stays out of it;
   - **pushes that commit before moving the branch** (`push origin <sha>:refs/heads/<branch>`),
     so the branch is never ahead of `origin` while the push is in flight;
   - then moves the branch (`update-ref` with the old value as a guard), sets the
     row's index entry, and renames the file into place.

   The tree now differs from `HEAD` for two sub-millisecond steps rather than for
   the commit and the push. When the commit cannot be made, the row still goes
   into place, uncommitted, as it does today. A failed push still leaves the
   branch committed and ahead, which the closing verdict already reports.
   `commit-tree` runs no commit hooks — accepted: the row is machine output, and a
   formatter hook rewriting it would be the bug.
3. **The verdict also speaks when the check was counting the row.** If the row
   differed from `HEAD` before the hook wrote anything — a hand run left it — the
   check saw that too. So when the harness check is registered and
   `stop_hook_active` is false, the hook exits 2 with one line: the row was left
   uncommitted at turn end, it is now committed and pushed, and there is nothing
   to do. The check's own exit 2 is already continuing the turn, so this adds no
   turn; it only makes that one short. It stays silent outside the harness,
   where no check ran.
4. **The wait stays.** It now guards two sub-millisecond steps rather than a
   commit and a push, which is cheap to keep and does no harm.
   `.claude/costs/CLAUDE.md` § "Running beside the harness's Stop check" is
   rewritten to match: the clean-tree write is how the race is avoided, the wait
   is a backstop, and the verdict names the one case — a row left behind by a
   hand run — in which the check sees the row.
5. **Tests: `.claude/costs/test_stop_hook.py`**, which runs the hook the way the
   harness does. Each case gets a scratch repo with a bare `origin`, a copy of
   `.claude/costs/` and `lib.sh`, a small transcript, and its own `HOME`. The
   cases:
   - a first row is committed and pushed, leaving the tree clean and level with
     `origin`;
   - a re-run with no change makes no commit;
   - work the agent has staged stays staged and stays out of the commit;
   - a row left dirty with the check registered exits 2 with the new line, and
     stays silent with the check unregistered or under `stop_hook_active`;
   - an unreachable `origin` reports "committed but not pushed";
   - `--name` leaves the tree clean, and the next `Stop` puts the name in the row.

   `scripts/vet.sh`'s loop already runs every `.claude/costs/test_*.py`.

## DRY notes

- **The commit sequence has one home, the `Stop` hook.** Only the hook commits
  rows; a hand run (without `--out`) keeps `write_atomic` and leaves committing to
  the person.
- **The name file's path appears twice**, in `session_cost.py` and in
  `prompt-session-name.sh`, one in Python and one in shell. Having the shell hook
  call Python just to learn a path would cost a Python start on every prompt, so
  each copy carries a comment naming the other.
- **The test reuses `test_pricing.py`'s record builders** where they fit rather
  than writing new ones. Where importing them would drag in that module's
  fixtures, it writes the two records it needs.
- **`dirty()` and `outstanding()` in the hook are reused as they are**, for the
  new "was the row already dirty" test and for the verdict.
