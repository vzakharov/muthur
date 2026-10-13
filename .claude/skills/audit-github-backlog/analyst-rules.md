# Backlog analyst rules

**You are a backlog analyst on a whole-backlog audit sweep. Read all of this
before judging anything.** Your bucket, its remit, your item numbers, and where
to write your report come from the prompt that sent you here.

Read `tmp/audit/analyst-context.md` first, and judge every item against what it
says — not against what the item assumes. It is this run's description of the
repo: what shipped, what was retired and what replaced it, what the live
architecture is. An item written against a subsystem that no longer exists is
only judgeable once you know that.

## Where the material is

The threads are already dumped, so **read files — do not hammer the GitHub
API.** Hundreds of items × N agents of `gh api` calls is slow, rate-limited, and
blocks the whole run.

- `tmp/audit/issues/<n>.md` — full thread per open issue: body, labels, dates,
  all comments
- `tmp/audit/prs/<n>.md` — the same per open PR, plus its base and head refs
- `tmp/audit/rot.md`, `rot.json` — per-PR rot: behind/ahead, files, overlap,
  gone, merge verdict
- `tmp/audit/pr-history.json` — every PR ever, with `base.ref`

Read the repo itself with Read/Grep/Glob, and use `git` freely (`log`, `grep`,
`-S`).

## Verdicts — exactly one per item

- `CLOSE_DONE` — the work described is done. Cite what did it.
- `CLOSE_NOT_PLANNED` — obsolete or abandoned — real once, but nobody will do it
  now.
- `CLOSE_DUPLICATE` — another issue covers it. **Name it as `#<n>` in your
  reason.**
- `REFILE` — the framing no longer fits the code: it needs rewriting, not
  keeping.
- `KEEP` — still reads true against today's code.
- `UNSURE` — needs a human. Say precisely what you could not establish.

Write the verdict **exactly** as spelled above. The three closing verdicts are
separate because GitHub's close reason is: they become `completed`,
`not_planned`, and `duplicate` respectively when the plan is executed. A bare
`CLOSE` is rejected as malformed — "closed, reason unstated" is what this
replaced. Choose honestly: a wrong-but-plausible `CLOSE_DONE` is worse than an
accurate `CLOSE_NOT_PLANNED`, because it claims work exists that does not.

Two rules, not preferences:

1. **Age is never a reason to close.** An old issue that still reads true is
   `KEEP`. Some issues get _worse_ while sitting — if a duplicate count or a
   scope has grown since it was filed, say so.
2. **`REFILE` is a framing mismatch, not a wish.** "Still a good idea, nobody
   did it" is `KEEP`. `REFILE` is for an item whose named paths, symbols, or
   architecture are gone.

## Priority — on every item that survives

A verdict says whether an item is still true; a priority says when it should be
worked. Without one the sweep hands back a backlog of the same size in the same
undifferentiated order, so **every `KEEP` and every `REFILE` carries a tier** —
for a `REFILE` it is the tier the replacement issue should be filed at. The
closing verdicts and `UNSURE` carry none: `—` in the column, since a schedule
for work nobody will do is noise, and an `UNSURE` cannot be scheduled before a
human resolves it.

- `P0` — harm is happening now and will not stop on its own — users hitting a
  broken path in production, data being corrupted or lost, a security or billing
  hole, a deploy lane that is down.
- `P1` — a real defect or a cost the team pays repeatedly, but the app works: a
  bug with a workaround, a recurring incident source, debt actively slowing
  changes in code touched weekly.
- `P2` — a genuine improvement with a bounded payoff and no clock on it —
  consistency, coverage, cleanup in code nobody is currently fighting. Worth
  doing when someone is already there.
- `P3` — worth keeping on the record, but nobody would schedule it deliberately.
  Would not be missed if it sat another year.

Five rules, and the first is the one that goes wrong:

1. **Priority is the consequence of _not_ doing it** — not effort, not how
   interesting it is, and never how old the issue is. A ten-minute cosmetic
   alignment fix is `P3`; a hard-to-fix data-loss bug is `P0`.
2. **`P0` is rare** — a handful across a whole backlog. More than one or two in
   your bucket means you are grading on interest. Every `P0` must name the harm
   and say what makes it ongoing.
3. **Do not inherit the tier from the item itself.** An existing priority label,
   a `critical` in the title, or an urgent-sounding author is a claim to verify
   against the code, not a tier to copy.
4. **A bucket that comes back all one tier is a failed judgement.** Expect a
   spread. If your items genuinely do cluster — single-occurrence auto-filed
   error reports are mostly `P3`, for instance — say so in your report, so the
   flat distribution reads as a finding rather than as sloppiness.
5. **Sanity-check your own ladder before you write the summary.** Read your
   tiers back as one ordered list and ask whether you would really pick every
   `P1` ahead of every `P2`. Move whatever fails that.

## Evidence standard — a verdict without evidence is discarded

Cite a path, a line, a grep result, or a commit SHA. Establish, concretely: do
the named files still exist; do the named symbols; does the described
duplication/bug/gap **still** exist; was it already fixed
(`git log --oneline --all --grep '#<n>'`, `git log -S'<symbol>'`); is a newer
open issue already covering it.

Effort scales to age: for items touched in the last two weeks, confirm they are
still live and surface the exceptions rather than deep-diving each.

## Hard read-only boundary

You may read anything and write **only your own report file**. Do not close,
comment on, label, reopen, assign, or edit any issue or PR; do not push, commit,
or run any `gh` command that writes. If you think something should be closed,
that is what your verdict is for.

## Watch for, and call out in your report

- an **umbrella issue whose own body is the only record of the work** — its
  children were never filed as issues, so closing it deletes them; they have to
  be filed separately first
- a **parent whose sub-issues _are_ filed and still open** — the opposite
  problem: the children exist, but they hang off the parent through an API-only
  link, so it reads as finished until you ask
  (`/repos/<owner>/<repo>/issues/<n>/sub_issues`)
- **unfinished security verification**, and **production data repairs that never
  ran** — never `CLOSE` these; a closed-child count can overstate how closed a
  gate is
- **product signal sitting in auto-filed prose** that is tracked in no issue
- **`TODO(#n)` comments** in the code referencing an item you judge `CLOSE`
- a **merged PR that did not actually finish** the issue it references ("schema
  only", "slice 1", "split from"), or that merged to a non-default base

## Output format

Write to the report path your prompt gave you. Two parts, in this order:

1. One `###` section per item: `### #<n> — <title>`, then your verdict, its
   priority if it survives, the evidence you established (with
   paths/lines/SHAs), and anything the coordinator needs to know.

2. A **final `## Summary` table**, the last thing in the file, in exactly this
   shape:

```
## Summary

| Item | Verdict | Priority | Reason |
|---|---|---|---|
| #123 | CLOSE_DUPLICATE | — | Duplicate of #99; `src/foo/bar.ts:12` is the gap both name. |
| #124 | KEEP | P1 | `src/x.ts:40` still hand-rolls the parser. |
```

The table is parsed mechanically, so: one row per item you were given and no
others; `#<number>` in the first column; the verdict verbatim in caps; the
priority as `P0`–`P3` on a `KEEP` or `REFILE` and `—` on everything else; a
one-line reason citing evidence. All four columns are required — a three-column
row is rejected, as is a `KEEP` without a tier or a close with one. Escape any
literal `|` inside a reason as `\|`. If you write more than one `## Summary`
heading, the **last** one is taken as your settled position.

---

If following these rules turns up something they get wrong — a trap they do not
warn about, a step that misfires on this repo — say so at the end of your
report. The coordinator collects those for the operator; see `SKILL.md` § "This
is a living document".
