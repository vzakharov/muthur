# `and merge`

Loaded by `@.claude/skills/finalize/SKILL.md` when the run carries `and merge`,
typed or read from an operator's ask to merge. Step numbers below are that
file's.

## The flag

**`and merge` delegates the click, not the judgment.** It asks you to
squash-merge the PR yourself at step 8 — **but only if the run gives you no
reason not to**. Standing down is an ordinary outcome of the flag rather than a
failure of it, which is why the flag reaches step 8 as a condition to evaluate
and not as an instruction to carry out.

**The flag is only ever the operator's to type, on work that already exists.**
It says something about a specific diff, so it means nothing written before that
diff did — which is why a caller that produces work in the same turn must not
forward it, and `@.claude/skills/handle/SKILL.md` § "Argument shape" holds the
merge back rather than passing it on. Any future caller answers the same
question: was the flag written after the operator could have looked?

**An operator's ask to merge a branch not yet finalized is
`/finalize and merge`**, whatever words carry it — "merge", "мерджи", "land it".
Finalized means the PR is ready for review and its
`<!-- finalize-attestation -->` comment names the current head, give or take
what step 7's last rule lets ride past it; anything short of that is a diff no
run has verified, so merging it as asked would skip every gate this skill exists
for. **Open the reply by saying you read the ask that way** — the operator asked
for a click and is getting land prep, which can stand the merge down at step 8 —
then run the skill with the flag. The paragraph above holds here too: an ask
that also requests changes was written before the diff it would merge, so land
prep runs and the merge is held.

## Step 8 — the gate

One predicate governs, and the list below only spells out how it fails: **merge
only when the run's whole effect on the branch was step 3's sweep, the staged
swap, the quality passes' own edits, and whatever a tool's own fixer rewrote,
and every check it ran passed the first time it ran.** The gate is evaluated
once, at step 8, by walking the run back against the list — not decided step by
step as the run goes.

**The quality passes are part of that predicate** because what they do by
construction is rewrite prose and fold duplication, leaving what the code does
alone — and a run of them that found something is the ordinary state of a branch
that reached land prep without `/go`, so a gate that fired on it would fire on
nearly every such branch. The boundary is behavior: a fold that turns out to
change what the code does is no longer a polish edit, and stands the merge down
like any other change you authored.

**Stand down if any of this happened**, at whichever step it happened:

- **The staged swap** — it stopped on a conflict. Resolving one is deciding what
  the file says.
- **Pre-check** — `HEAD` was detached, or there was no PR and you created one. A
  PR opened and merged inside one turn was never a reviewable object. (A PR you
  flipped back to draft is fine — that is the ordinary re-finalize.)
- **Step 1** — the vet run needed a change **you authored** to go green. A
  tool's own fixer (`--fix`, a formatter rewriting its own output) that clears
  it does not count; that is the autofix this flag allows. The test is whether
  you had to read the failure and decide what to change.
- **Step 2** — any conflict, however trivially resolved; or you applied a
  dedup/simplification the base merge opened, or surfaced one as ambiguous. A
  clean merge that **brought commits in** is survivable, but step 1 vetted a
  tree without them: re-run it, green first try, and stand down on any
  interaction of the kind that step already has you reading the incoming diff
  for.
- **Step 4** — a red CI run. Same autofix exception as step 1, plus one case it
  does not cover: a red run that cleared itself on a re-run with no change at
  all. "It was a flake" is a judgment, and an unexplained red is the most
  ordinary reason to want a human at the button.
- **Step 5** — the reconcile rewrote the proposal in substance, or no proposal
  existed and this composed the first one. Either way the text about to become
  the permanent `git log` record has had no reader but you. The title counts the
  same way: a reconcile that rewrote the PR title in substance stands the merge
  down.
- **Step 6** — `/check-merge` returned anything but `contained`. An advanced
  base makes everything verified stale and its deliberation is a judgment; a
  merged or closed PR leaves nothing to merge.
- **Anywhere** — the two-shot rule engaged; the PR carries feedback nobody
  answered — a fresh `python3 scripts/export-github-item.py <n>` whose
  `## Awaiting an answer` count is not `none` (`rm -rf` the `docs/pr/<n>/` it
  writes, the sweep having run), that heading being
  `@.claude/skills/handle/SKILL.md` Step 2's tail test already run, and what
  keeps a merge from burying an open thread; or you reached a point where you
  would otherwise have asked the operator something.
- **Under `no vet`** — the mode is the operator's call and does not stand the
  merge down, but its stated precondition is yours to check: if any check in the
  vet run would have had something to say about this diff, the mode was
  misapplied, and that misapplication is a stand-down.

The list is walked step by step so the verdict is auditable, and it is **not
exhaustive** — a procedure that grows a step grows a way for a run to be
eventful. So the predicate, not the list, is the verdict: **if the run made you
decide anything the passes above don't cover, stand down.** Deciding it well is
not the same as the operator having decided it.

## Merging

Step 7 goes up first: the record of what the merge rests on belongs on the PR
before the merge, not after it. Then squash-merge with the title and body **step
5 settled**, verbatim; do not recompose them here. The PR and its comment are
the source, so read both back rather than reconstructing them:

```bash
gh pr view <n> --json title --jq '.title + " (#<n>)"' > tmp/squash-title.txt
gh api repos/<owner>/<repo>/issues/comments/<id> --jq .body > tmp/proposal.md
```

Extract the comment's last fenced block — the body, after the title block a
one-commit PR carries — into `tmp/squash-body.txt`, then **print both files and
read them** — the title against the `<type>: #<issue> <essence> (#<n>)` shape,
the body ending at its `Co-authored-by:` byline. A mis-split silently lands the
attribution footer inside the permanent record. Then:

```bash
gh pr merge <n> --squash --subject "$(cat tmp/squash-title.txt)" --body-file tmp/squash-body.txt
```

The subject is passed rather than left to GitHub's default, because a repository
whose `squash_merge_commit_title` is `COMMIT_OR_PR_TITLE` titles a one-commit PR
by that commit's subject.

No `--admin`, no `--auto`, no `--delete-branch`, and nothing disabled to get the
merge through. A refusal — branch protection, a required check still pending, an
un-mergeable head — is GitHub's answer and gets reported as a stand-down, not
routed around. Report the commit the squash landed on `<base>`, then end the
turn: the PR is no longer a place to do work.

## Standing down

**Standing down is a result and gets reported as one** — the condition that
fired, the step it fired at, and what would clear it. It goes in the turn's
report and nowhere else: the attestation already carries what the run found, and
a third PR comment announcing that you declined to merge is addressed to the
wrong reader. Then end the turn. Do not ask for permission to merge anyway — the
report is the ask, and a pending question pins a session the operator may not
return to for days.
