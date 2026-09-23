---
description: Finalize (a.k.a. "prep merge") — land prep: verify there's a draft PR, run the quality passes (`/polish`), run the vet suite, merge the base branch, mark ready for review, propose a squash title/body, and post the attestation comment. Pass an optional branch/PR target first (`/finalize <branch|#PR|PR-url>`) to attach to that existing branch before finalizing. `/finalize no vet` is the docs-only mode; `/finalize and merge` squash-merges the PR as well, but only if the run turned up nothing to decide.
---

**Optional branch/PR target**: if the first token of the argument is a branch name, `#NNN` PR number, or PR URL, then `/finalize <target>` is shorthand for attaching to that branch first and then finalizing — equivalent to `/from-branch <target> /finalize`. Load `@.claude/skills/from-branch/SKILL.md` and follow it to attach to `<target>`, then run the finalize steps below. If the argument has no target token, skip this and finalize the current branch as usual.

**`no vet` is the docs-only mode.** Pass it when the diff has nothing to verify — markdown, top-level docs, read-only reference data. It skips the vet run (there is nothing for it to check) and skips any bucket dispatch. It does **not** skip step 7: the attestation still goes up, stating that verification was a deliberate no-op and why. Everything else below still applies. (`no ci` and `no attest` are accepted spellings of this flag.)

**`and merge` delegates the click, not the judgment.** Recognized anywhere in the argument (bare `merge` counts too), it asks you to squash-merge the PR yourself at step 8 — **but only if the run gives you no reason not to**. Standing down is an ordinary outcome of the flag rather than a failure of it, which is why the flag reaches step 8 as a condition to evaluate and not as an instruction to carry out. That step owns the gate, the merge and the report.

**The flag is only ever the operator's to type, on work that already exists.** It says something about a specific diff, so it means nothing written before that diff did — which is why a caller that produces work in the same turn must not forward it, and `@.claude/skills/handle/SKILL.md` § "Argument shape" holds the merge back rather than passing it on. Any future caller answers the same question: was the flag written after the operator could have looked?

**Pre-check**:

- If `HEAD` is detached, create a branch with a meaningful name derived from the work (e.g., task id or topic) and check it out.
- Run `gh pr view --json isDraft,number,url,baseRefName` on the current branch.
  - No PR → push the branch and create a **draft** PR (`gh pr create --draft`).
  - PR exists but is non-draft → convert it back to draft (`gh pr ready --undo`).
  - Draft PR exists → continue.
- **Resolve the PR's base branch** from `baseRefName` — this is the branch the work merges into and is gated against, `<base>` in every step below. It's usually `main`, but a project with promotion branches or long-lived feature branches will have PRs based elsewhere. Everywhere a step compares against or merges from the merge target, use `origin/<base>`, not a hardcoded `origin/main`. (If there's no PR yet — the no-PR case above — treat `<base>` as the repo default branch.)

**Two-shot rule**: on any failure, try up to two rounds of fixing, then stop and ask the user. Commit after each round of fixes.

**What actually gates this PR.** Establish this once, at the top, because everything below depends on it: check whether any workflow runs on a PR in this repo (`.github/workflows/` triggers, or `gh pr checks` on an existing PR).

- **If nothing runs on a PR**, *you* are the entire gate — nothing downstream will report on this branch before someone merges it. Step 1's `./scripts/vet.sh` is the only thing that runs the project's checks before the merge, which is why vetting is not optional on this path even though ordinary development skips it. An empty Checks tab after step 4 is then the expected end state; do **not** push an empty commit to "relaunch CI".
- **If a workflow does run on PRs**, the vet run still happens here — it's faster and it catches things before a reviewer sees red — but step 4 also means watching that run to green (`@.claude/skills/watch-ci/SKILL.md`), and step 7 attests to both.

Either way, **step 7's attestation comment is the record.** A reviewer cannot see from the diff what was run; if it isn't written down it did not happen as far as anyone else is concerned.

**First, swap in the staged copies.** Run `scripts/staged.sh swap` — a no-op when nothing is staged — and commit what it `git add`ed (`chore: swap the staged always-loaded files into place`). A branch edits the files that load on every turn through copies under `docs/staged/` (`@.claude/rules/staging.md`), and everything below reads the real ones: the passes review them, and the vet run checks them. Where the real file changed after it was staged, the swap merges; a conflict it stops on is left as markers in the real file, resolved before anything else runs. `no vet` does not skip this.

**Then, the quality passes.** Before step 1, load and follow `@.claude/skills/polish/SKILL.md` over this branch. Land prep is the funnel every branch reaches whatever route its work took, so this is where a branch written without `/go` in front of it still gets the passes — and the last point at which changing the diff is cheap, since the vet run, the base merge, the squash message and the attestation's SHA are all statements about a diff that has stopped moving.

It carries no step number because the numbers below are cited from other skills and stay put; it runs before step 1 regardless. **`no vet` does not skip it** — a docs-only diff is squarely what both passes are for: `/tend-prose` by construction, and `/dry` because a constraint stated in two places is a duplication like any other.

Steps (stop on first unresolved failure):

1. **Vet**: `./scripts/vet.sh`. Fix and rerun until green.
2. **Merge the base branch**: `git fetch origin && git merge origin/<base>` (`<base>` from the Pre-check). Resolve conflicts; if you can't, ask. A clean merge (no conflicts) is not the end of the thought: review what the base brought in and consider whether it **overlaps** with this branch's change or opens an **optimization**. Git only flags textual conflicts — it won't tell you the base added a helper/util/component that now duplicates something you wrote, introduced a shared abstraction you should route through instead of your local one, renamed or moved a symbol you still reference the old way, or changed a pattern this branch should now follow for consistency. Skim the merged-in diff (`git log --oneline ORIG_HEAD..origin/<base>`, `git diff ORIG_HEAD origin/<base> -- <areas you touched>`) for these. If you spot a clear, low-risk dedup/simplification, apply it and commit; if it's ambiguous or large, surface it to the user rather than silently shipping the redundancy.
3. **Working-artifact cleanup**: some directories ride the branch for in-flight review but must never land on the base. Sweep the two below **now**, deleting each **entire** tree (not just the current session's subfolder) and including the deletions in the **last** pushed commit before step 4. (`docs/remove-before-merging/` is the exception — it is swept at the **end** of step 6, after the merge check; see there for why.)
   - **`docs/issue/`** and **`docs/pr/`** — issue and PR exports from `scripts/export-github-item.py`, plus the transient PR body `scripts/pr-body.py` parks under `docs/pr/<n>/`. If **any** `docs/issue/<n>/` or `docs/pr/<n>/` tree exists, remove it — `git rm -rf` what is tracked, plain `rm -rf` what a hook left untracked. Both exports are committed earlier on purpose, and the two differ in how often: `@.claude/skills/take-issue/SKILL.md` Step 2 commits an issue once, a thread being a snapshot any resuming agent (post-compaction handoff, parallel session) can read instead of re-exporting; `@.claude/skills/handle/SKILL.md` Step 2 commits a PR export every time it re-takes one, because the PR moves while the branch works, and the resulting sequence is what shows a reviewer which state of the PR each turn was answering. Paired with those adds, the deletion cancels out in the squash.
   - **`docs/plans/`** — file-based plans from `@.claude/skills/plan/SKILL.md` (the web-session stand-in for plan mode). If **any** `docs/plans/*.md` exists — in any lifecycle state (`.draft.do-not-implement.md`, `.in-progress.md`, `.paused.md`, `.completed.md`) — `git rm -r docs/plans/`. Same rationale: the plan was committed so the operator could pull and review it, but it's a working artifact — the add-then-delete pair cancels out in the squash so the plan never reaches the base branch.
     **Don't limit any sweep to the current session** — clean up any other `docs/issue/<m>/`, `docs/pr/<m>/`, or `docs/plans/*.md` leftovers earlier agents/operators forgot too; there's no reason for these to ever live on the trunk. Do **not** skip this step — leaving any folder in means it ships.

4. **Ready for review**: `gh pr ready`. If the repo runs a workflow on PRs, watch it to green now (`@.claude/skills/watch-ci/SKILL.md`) and fix what it surfaces under the two-shot rule. If nothing runs on a PR here, there is nothing to chase — an empty Checks tab is the expected end state, and pushing an empty commit to "relaunch CI" relaunches nothing.
5. **Reconcile the squash message**: invoke `@.claude/skills/squash-message/SKILL.md` — load and follow it, passing `<base>` as the diff base. A proposal normally already exists, posted when the PR opened and still tracked on the branch, so this is an **edit** to a live doc in light of the merge, any review comments and the final committed state — not a fresh composition. It owns the title/body format, the draft-then-tighten pass, and both outputs (the PR comment beside the merge button and the two fenced blocks in the transcript). Do not draft the message inline here: printing an untightened first draft is the failure mode that skill exists to prevent.
6. **Dispatch any CI-only bucket the diff reaches, then check the base.**

   If the project has hydrated `/test-on-gh`, decide from the diff whether it reaches a surface the vet run doesn't cover (one that needs real credentials, real services, or a browser) and dispatch that bucket if so. It's a judgement call, not a reflex: don't dispatch a bucket the diff never touches, and don't skip one because the diff "looks fine". A red dispatch is a real failure — fix it under the two-shot rule. If `/test-on-gh` is still a stub, say so in the report rather than implying full coverage.

   Then, before ending the turn, run `/check-merge` (`@.claude/skills/check-merge/SKILL.md`) **once**: verification takes a while, so `origin/<base>` has often advanced while it ran and the target you just validated against may already be stale. Whatever the outcome, the final report **must state the `origin/<base>` SHA this check verified against** (short SHA + subject, e.g. `main @ 8903396 "style: …" as of this check`) — the operator compares it against current `origin/<base>` at a glance without re-running `/check-merge`.
   - **contained** (no movement) → go to step 7, then **end the turn** so the session reads as idle; the operator can run `/check-merge` again when they return.
   - **`origin/<base>` advanced** → run the **base-advanced deliberation** below, then step 7.
   - **PR merged/closed** → the work landed — nothing more to do.
     This is **one** automatic check, not a loop: after acting on it once, end the turn rather than re-checking — further movement is the operator's `/check-merge` to catch on return.
   - **Base-advanced deliberation** — when `origin/<base>` moves out from under the branch, your local green no longer necessarily reflects what would land. Depending on the project, nothing may re-check the merge afterwards at all, so this deliberation is the last chance to catch it. A clean merge (no conflicts) does **not** mean the code is compatible: semantic incompatibilities (renamed exports used elsewhere, changed function signatures, altered runtime invariants) merge cleanly and still break. Whether to re-verify is your call, but make it deliberately — don't reflexively skip it:
     - You **MUST** read the incoming diff before deciding — `git log --oneline <merge-base>..origin/<base>` and `git diff <merge-base>..origin/<base> -- <areas this branch touched>`, where `<merge-base>` is the base commit the branch already contains (`/check-merge` prints it as `base=…`, or compute `git merge-base HEAD origin/<base>`). Deciding without reading the diff is not allowed.
     - Weigh the same interactions step 2 warns about (a helper/util/component that now duplicates something you wrote, a shared abstraction you should route through instead of your local one, a renamed/moved symbol you still reference the old way, a pattern this branch should now follow) **plus** the semantic incompatibilities above.
     - **Default to re-verify when unsure.** The test is _interaction_, not _whether the base touched code_ — most advances touch some code, and that alone doesn't warrant it. Skip re-verification when, having read the diff, you can say why the incoming commits and this branch's changes don't overlap: they're in different areas/modules, nothing this branch imports or depends on was touched, and no symbol/signature/pattern this branch uses was changed. If you can see a plausible interaction, or you genuinely can't tell, re-verify.
       - **Interacting or ambiguous** → re-run step 2 (`git merge origin/<base>`, applying any dedup/simplification it opens), then step 1 (`./scripts/vet.sh`), push, and re-run any step-6 dispatch the diff still warrants. The two-shot rule does **not** apply to these base-advanced re-runs; they're keeping the target current, not fixing failures.
       - **Demonstrably independent** → `git merge origin/<base>`, push, and run `/check-merge` again when you return to confirm `origin/<base>` hasn't moved since. Unrelated code changes qualify: e.g. the base reworks a frontend modal while this branch changes a background job's retry policy — both touch code, but they don't interact.
   - Do NOT merge the PR here — step 8 owns that, and only under `and merge` and the gate it states. Absent the flag the operator controls the final title/body and merge.

   **Then, once the merge check is done, sweep `docs/remove-before-merging/`** — after `scripts/staged.sh check --empty` passes, since a copy still under `docs/staged/` carries a change that would otherwise land as a stray duplicate of the file it stands for; a failure means run the swap above, never delete the copy. Then `git rm -r` the **entire** tree, not just the `squash-message.md` that `@.claude/skills/squash-message/SKILL.md` tracks there: the directory's name is a standing declaration that nothing inside it may land, so a screenshot or anything else an agent parked there goes with it. Paired with the earlier add, the deletion cancels out in the squash. Push it before step 7 so the SHA the attestation names is the branch's final head.

   **Why this tree goes last, after everything else.** The squash proposal is a live doc for the whole time the PR is in flight: every edit to it — a review comment, what the base merge brought in, a fix pushed after a red dispatch, work `/check-merge` just pulled in from an advanced base — is a deliberation over the text that's already there. Sweeping it at step 3 would leave the single most important edit, the one that becomes the permanent `git log` record, as the only one made with the doc gone; sweeping it before `/check-merge` would do the same to whatever that check drags in.

   A directory name is not self-enforcing: upstream, this tree reached the trunk anyway, carrying a ~1MB deploy-log dump with customer email addresses in it. So verify the sweep actually ran — and **never end the turn with the tree still on the branch**, since from here the branch is merge-able: by the operator, or by step 8 itself.

7. **Attest** — the last act, and the only durable record that this branch was verified beyond whatever CI reports. Post it on the PR — or, on a re-run, edit it in place; it is sticky, keyed on the `<!-- finalize-attestation -->` marker, and the marker is how you find it (mechanic below the templates):

   ```md
   <!-- finalize-attestation -->

   ### Attestation

   Verified <short-sha> (`<branch>`) against `<base>` @ <base-short-sha> "<base subject>".

   - `./scripts/vet.sh` — **green**
   - CI on this PR — **<green (run link) | nothing runs on a PR in this repo>**
   - CI-only buckets — **<dispatched and passed (run link) | not dispatched: the diff doesn't reach them | /test-on-gh is an unhydrated stub>**

   <If nothing runs on a PR here: "No workflow runs on a PR; this comment is the verification record.">
   ```

   In `no vet` mode the comment still goes up — same marker, same place — saying that there was nothing to verify:

   ```md
   <!-- finalize-attestation -->

   ### Attestation — none required

   <short-sha> (`<branch>`) against `<base>` @ <base-short-sha> "<base subject>".

   Finalized in `no vet` mode: <why the diff has nothing to verify — e.g. "markdown only, no code path touched">. `./scripts/vet.sh` was skipped rather than run green, and no bucket was dispatched.

   <If nothing runs on a PR here: "No workflow runs on a PR; this comment is the verification record.">
   ```

   **Finding the comment: match the marker, never `--edit-last`.** Same mechanic `@.claude/skills/squash-message/SKILL.md` § "Emit" uses for its own sticky comment — list the PR's comments (`gh api repos/<owner>/<repo>/issues/<n>/comments --paginate`), pick the one whose body contains `<!-- finalize-attestation -->`, and `gh api repos/<owner>/<repo>/issues/comments/<id> -X PATCH -F body=@<file>` that id; post a new comment only when no match exists. `gh pr comment --edit-last` looks like the tool for this and is not: it targets your most recent comment on the PR whatever that happens to be, so on the ordinary finalize ordering — squash proposal posted at step 5, attestation at step 7 — it overwrites the squash proposal with the attestation. Both comments are then one comment, and the loss is silent.

   Rules that make it worth trusting:
   - **Attest what you vetted, not what you meant to vet.** If the vet run was not green, or a dispatch was skipped for a reason other than "the diff doesn't reach it", or you stopped under the two-shot rule — say exactly that, in the comment. An honest partial attestation is useful; a tidy one that overstates is worse than none. That includes naming a stub: "`./scripts/vet.sh` is not implemented in this project yet" is an honest line, and it tells the reviewer exactly how much the attestation is worth.
   - **One comment, edited in place.** Re-running `/finalize` after a base-advanced re-verify updates it; it must always describe the branch's current head, not the first pass. A branch finalized once in `no vet` mode and later re-finalized for real replaces the no-op body with the full one.
   - **A no-op is a result, and it gets posted.** Never resolve `no vet` by staying silent. An operator coming back to the PR — days later, or from another machine — cannot distinguish "verification was skipped on purpose" from "nobody ever finalized this" unless one of them is written down, and the missing comment looks identical to the forgotten one. Say which it was.
   - **The SHAs go bare, not in code spans** — GitHub only auto-links an un-backticked hash, per CLAUDE.md § "GitHub comments".
   - End the body with the attribution footer the repo requires of every GitHub comment.
   - **A head that moved only by `.claude/costs/sessions/` is still the head you verified.** Where the cost ledger runs, its `Stop` hook commits the turn's row after the turn ends, so the branch usually sits one `chore: session cost` commit past the attested SHA. That commit touches no verified path; re-attest only for a commit that does.

8. **Merge — under `and merge` only, and only if the run was uneventful.** Without the flag, stop at step 7 and report.

   One predicate governs, and the list below only spells out how it fails: **merge only when the run's whole effect on the branch was step 3's sweep, the staged swap, the quality passes' own edits, and whatever a tool's own fixer rewrote, and every check it ran passed the first time it ran.** The gate is evaluated once, here, by walking the run back against the list — not decided step by step as the run goes.

   **The quality passes are part of that predicate** because what they do by construction is rewrite prose and fold duplication, leaving what the code does alone — and a run of them that found something is the ordinary state of a branch that reached land prep without `/go`, so a gate that fired on it would fire on nearly every such branch. The boundary is behavior: a fold that turns out to change what the code does is no longer a polish edit, and stands the merge down like any other change you authored.

   **Stand down if any of this happened**, at whichever step it happened:

   - **The staged swap** — it stopped on a conflict. Resolving one is deciding what the file says.
   - **Pre-check** — `HEAD` was detached, or there was no PR and you created one. A PR opened and merged inside one turn was never a reviewable object. (A PR you flipped back to draft is fine — that is the ordinary re-finalize.)
   - **Step 1** — the vet run needed a change **you authored** to go green. A tool's own fixer (`--fix`, a formatter rewriting its own output) that clears it does not count; that is the autofix this flag allows. The test is whether you had to read the failure and decide what to change.
   - **Step 2** — any conflict, however trivially resolved; or you applied a dedup/simplification the base merge opened, or surfaced one as ambiguous. A clean merge that **brought commits in** is survivable, but step 1 vetted a tree without them: re-run it, green first try, and stand down on any interaction of the kind that step already has you reading the incoming diff for.
   - **Step 4** — a red CI run. Same autofix exception as step 1, plus one case it does not cover: a red run that cleared itself on a re-run with no change at all. "It was a flake" is a judgment, and an unexplained red is the most ordinary reason to want a human at the button.
   - **Step 5** — the reconcile rewrote the proposal in substance, or no proposal existed and this composed the first one. Either way the text about to become the permanent `git log` record has had no reader but you. Only what the run itself mechanically settles (`(pr #tbd)` → `(pr #N)`) is free.
   - **Step 6** — `/check-merge` returned anything but `contained`. An advanced base makes everything verified stale and its deliberation is a judgment; a merged or closed PR leaves nothing to merge.
   - **Anywhere** — the two-shot rule engaged; the PR carries feedback nobody answered (`@.claude/skills/handle/SKILL.md` Step 2's tail test, which is what keeps a merge from burying an open thread); or you reached a point where you would otherwise have asked the operator something.
   - **Under `no vet`** — the mode is the operator's call and does not stand the merge down, but its stated precondition is yours to check: if any check in the vet run would have had something to say about this diff, the mode was misapplied, and that misapplication is a stand-down.

   The list is walked step by step so the verdict is auditable, and it is **not exhaustive** — a procedure that grows a step grows a way for a run to be eventful. So the predicate, not the list, is the verdict: **if the run made you decide anything the passes above don't cover, stand down.** Deciding it well is not the same as the operator having decided it.

   **Merging.** Step 7 goes up first: the record of what the merge rests on belongs on the PR before the merge, not after it. Then squash-merge with the title and body **step 5 settled**, verbatim; do not recompose them here. The comment is the source, so read it back rather than reconstructing it:

   ```bash
   gh api repos/<owner>/<repo>/issues/comments/<id> --jq .body > tmp/proposal.md
   ```

   Split its two fenced blocks into `tmp/squash-title.txt` and `tmp/squash-body.txt`, then **print both and read them** — the title against the `<type>: #<issue> <essence> (pr #<n>)` shape, the body ending at its `Co-authored-by:` byline. A mis-split silently lands the attribution footer, or the title block, inside the permanent record. Then:

   ```bash
   gh pr merge <n> --squash --subject "$(cat tmp/squash-title.txt)" --body-file tmp/squash-body.txt
   ```

   No `--admin`, no `--auto`, no `--delete-branch`, and nothing disabled to get the merge through. A refusal — branch protection, a required check still pending, an un-mergeable head — is GitHub's answer and gets reported as a stand-down, not routed around. Report the commit the squash landed on `<base>`, then end the turn: the PR is no longer a place to do work.

   **Standing down is a result and gets reported as one** — the condition that fired, the step it fired at, and what would clear it. It goes in the turn's report and nowhere else: the attestation already carries what the run found, and a third PR comment announcing that you declined to merge is addressed to the wrong reader. Then end the turn. Do not ask for permission to merge anyway — the report is the ask, and a pending question pins a session the operator may not return to for days.
