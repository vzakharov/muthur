# PR #79: feat: extract /go's quality passes into /polish

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/79
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← claude/polish-skill-jzaozq
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-15T10:45:15Z
- **Updated:** 2026-09-15T11:22:01Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **`/polish` is the new home of the two mandatory passes** — `/dry` then `/tend-prose`. They lived only inside `/go` Step 3, so work that reached a PR by any other route (a task asked for and done directly, a branch another session wrote) got them only when the operator named both by hand.
- **It owns the scope, which neither pass could resolve on its own.** Both bottom out at unpushed work, which falls through to "nothing to review" on an already-pushed branch; the composite fetches the base and hands `git diff origin/<base>...HEAD` to both. Running it on its own diff caught the stale-ref case: against an unfetched `origin/main` the range covered 19 files where the branch had touched 8.
- **Three call sites**: `/go` Step 3 (unchanged in effect, now by reference), `/finalize` ahead of its numbered steps — land prep being the funnel every branch reaches — and the operator directly, which is the entry the other two exist to make unnecessary and routinely don't.
- **`/finalize`'s `and merge` gate gains a clause**: a `/polish` run that changed anything stands the merge down, the edit being a judgment about the diff made after the operator last looked at it. Finding nothing clears it, which is the ordinary outcome on a branch `/go` already polished.

The `/finalize` call is unnumbered on purpose — its step numbers are cited from five other skills, so inserting a Step 1 would have been a wide mechanical renumber with a stale citation as its likeliest outcome.

## QA Checklist

- [ ] `polish-standalone` — in a session that made a change without `/go`, say "polish this" and confirm `/polish` runs both passes over the branch diff rather than reporting nothing to review.
- [ ] `polish-scope-stale` — on a branch whose `origin/<base>` is behind, confirm the run fetches first and scopes to the branch's own files.
- [ ] `go-step-3` — run `/go` on a task and confirm Step 3 loads `/polish` rather than the two passes inline, and that the plan file still flips to `*.completed.md` afterwards.
- [ ] `finalize-first` — run `/finalize` on a branch that never saw `/go` and confirm the passes run before the vet suite.
- [ ] `finalize-merge-gate` — run `/finalize and merge` on a branch where `/polish` changes something and confirm it stands down.
- [ ] `catalog` — `./scripts/vet.sh` is green, i.e. `/polish` has exactly one catalog row and no `@`-reference dangles.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `polish-standalone` | no | no | Agent-behavior check; only a live session exercises it. |
| `polish-scope-stale` | partially | no | The `git fetch` + `git diff origin/<base>...HEAD` pair is scriptable; whether the agent runs it is not. |
| `go-step-3` | no | no | Same. |
| `finalize-first` | no | no | Same. |
| `finalize-merge-gate` | no | no | Judgment clause in a stand-down list — prose, not code. |
| `catalog` | yes | yes | `scripts/check-skill-catalog.sh`, inside `scripts/vet.sh`. |

https://claude.ai/code/session_01MF7oPiszoCcz2W9GP3fPyx

---

## Comments

### Comment by @vzakharov (agent) on 2026-09-15T10:45:39Z

[https://github.com/vzakharov/muthur/pull/79#issuecomment-5678908530](https://github.com/vzakharov/muthur/pull/79#issuecomment-5678908530)

Proposed squash title/body:

```
feat: extract /go's quality passes into /polish (pr #79)
```

```
The two mandatory quality passes, /dry then /tend-prose, lived only
inside /go Step 3. Work that reached a PR by any other route — a task
asked for and done directly, a branch another session wrote — got them
only when the operator named both by hand.

/polish is their home: the pair, the order, and the scope. Scope is the
part neither pass could resolve alone, since both bottom out at unpushed
work and so fall through to "nothing to review" on a branch already
pushed. The composite fetches the base and hands the branch's net diff
against it to both.

Three call sites reach it. /go Step 3 loads it in place of the two
passes it used to name; /finalize runs it ahead of its numbered steps,
land prep being the funnel every branch reaches whatever route its work
took; and the operator invokes it over work that took neither. That last
entry is the one the other two exist to make unnecessary and routinely
don't. /finalize's `and merge` gate gains a clause to match: a run that
changed anything stands the merge down, the edit being a judgment about
the diff made after the operator last looked at it.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

### `.claude/skills/polish/SKILL.md`:1 — unresolved

**@vzakharov (human)** — 2026-09-15T11:17:24Z

давай добавим ещё watermark (возможно в remove-before-merging), чтобы скилл не проверял то, что уже проверялось (т.е. смотрел именно на дифф)

---

### `.claude/skills/finalize/SKILL.md`:33 — unresolved

```diff
@@ -28,6 +28,10 @@ description: Finalize (a.k.a. "prep merge") — land prep: verify there's a draf
 
 Either way, **step 7's attestation comment is the record.** A reviewer cannot see from the diff what was run; if it isn't written down it did not happen as far as anyone else is concerned.
 
+**First, the quality passes.** Before step 1, load and follow `@.claude/skills/polish/SKILL.md` over this branch. Land prep is the funnel every branch reaches whatever route its work took, so this is where a branch written without `/go` in front of it still gets the passes — and the last point at which changing the diff is cheap, since the vet run, the base merge, the squash message and the attestation's SHA are all statements about a diff that has stopped moving.
+
+It carries no step number because the numbers below are cited from other skills and stay put; it runs first regardless. **`no vet` does not skip it** — a docs-only diff is the case `/tend-prose` exists for.
```

**@vzakharov (human)** — 2026-09-15T11:18:24Z

and `/dry` too has at least a certain relation to prose

---

### `.claude/skills/finalize/SKILL.md`:115 — unresolved

```diff
@@ -108,6 +112,7 @@ Steps (stop on first unresolved failure):
    **Stand down if any of this happened**, at whichever step it happened:
 
    - **Pre-check** — `HEAD` was detached, or there was no PR and you created one. A PR opened and merged inside one turn was never a reviewable object. (A PR you flipped back to draft is fine — that is the ordinary re-finalize.)
+   - **The quality passes** — `/polish` changed anything. An edit there is a judgment about the diff, made after the operator last looked at it, and it is the ordinary outcome on a branch that never went through `/go`. Finding nothing is what clears this.
```

**@vzakharov (human)** — 2026-09-15T11:19:33Z

нет, давай это не будем включать. "полировочные" изменения по определению не меняют работу кода.

---

## Timeline (status, references, and other events)

- **2026-09-15T11:22:01Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/79#pullrequestreview-5209251676.
