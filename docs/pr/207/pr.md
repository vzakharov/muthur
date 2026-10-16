# PR #207: fix: attest only a head /finalize's step 1 actually verified

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/207
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← fix/finalize-attest-verified-head
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-16T05:33:03Z
- **Updated:** 2026-10-16T06:05:36Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 2

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `docs/remove-before-merging/squash-message.md`:7 — unresolved — last: @vzakharov (human) 2026-10-16T06:03:26Z — "не понимаю, объясни /plainly: что значит "own vet covered" и…" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:12 — unresolved — last: @vzakharov (human) 2026-10-16T06:04:12Z — "опять же что за "vet part"? и вопрос, если бы был CI, он бы…" → [↓](#t02)

---

## Body

## Summary

- `/finalize` verifies at step 1 and merges the base at step 2. When that merge brought commits in, `/sync-branch`'s vet covered the merged tree, but nothing re-ran anything else a project puts in step 1 (an adopter's release gate, say), so step 7 could attest a head that gate never saw — two branches each green alone, merged into one nobody built.
- Step 1 now states it is the branch's whole local verification and that any merge bringing base commits in re-runs all of it on the merged head, `/sync-branch`'s vet counting as the vet part. Base-advanced's interacting path re-runs it the same way; the `and merge` gate reads that re-run.
- Base-advanced's "demonstrably independent" path keeps its skip, but the attestation now keeps `Verified <sha>` on the head step 1 ran on and adds a line naming the unverified merge on top and why it was judged independent, so anything trusting the attestation can tell the two heads apart.
- Reordering (merge before step 1) was the alternative; it was not taken because step 6's late base advance merges after verification anyway, so the re-run rule is needed either way.

## QA Checklist

- [ ] `rerun-rule` — read `.claude/skills/finalize/SKILL.md` step 1–2: a step-2 merge that brought commits in leads to a full step-1 re-run before step 3.
- [ ] `base-advanced` — read `.claude/skills/finalize/base-advanced.md`: the interacting path re-runs step 1; the independent path leads to the attestation's extra line.
- [ ] `attestation` — the step-7 template's `Verified` names the step-1 head, the marker the final head, and the conditional line appears only when they differ.
- [ ] `gate` — `.claude/skills/finalize/merge.md` step 2 bullet cites step 1's re-run.
- [ ] `vet` — `./scripts/vet.sh` passes (skill cross-references, wrapping).

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `rerun-rule` | no | no | procedure prose, judged by reading |
| `base-advanced` | no | no | procedure prose |
| `attestation` | no | no | template shape |
| `gate` | no | no | procedure prose |
| `vet` | yes | yes | `scripts/vet.sh` |

https://claude.ai/code/session_01N1PwAWABtUMit7j8cPHDTj

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-16T05:33:19Z — "Proposed squash body: ``` /finalize verifies at step 1 and m…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-16T05:33:19Z

[https://github.com/vzakharov/muthur/pull/207#issuecomment-6208837043](https://github.com/vzakharov/muthur/pull/207#issuecomment-6208837043)

Proposed squash body:

```
/finalize verifies at step 1 and merges the base afterwards, so a merge
that brought commits in produced a head nobody had built. /sync-branch's
own vet covered that head, but anything else a project put in step 1 -
an adopter's release gate - never ran on it, and step 7 attested it
anyway: two branches green alone could land as a red trunk.

Step 1 is now the branch's whole local verification, and any merge that
brings base commits in re-runs all of it on the merged head, with
/sync-branch's vet standing in for the vet part. The base-advanced
deliberation's interacting path re-runs it the same way, and the
and-merge gate reads that re-run. Merging before step 1 was not enough
on its own, since a late base advance at step 6 merges after
verification regardless.

A late advance judged independent still skips the re-run, so the
attestation now keeps `Verified <sha>` on the head step 1 ran on, the
marker on the final head, and a line naming the merge on top and why
it was judged independent - anything trusting the attestation can tell
the two apart.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:7 — unresolved — last: @vzakharov (human) 2026-10-16T06:03:26Z — "не понимаю, объясни /plainly: что значит "own vet covered" и…" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:12 — unresolved — last: @vzakharov (human) 2026-10-16T06:04:12Z — "опять же что за "vet part"? и вопрос, если бы был CI, он бы…" → [↓](#t02)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:7 — unresolved

```diff
@@ -0,0 +1,29 @@
… 1 line elided …
+
+```
+/finalize verifies at step 1 and merges the base afterwards, so a merge
+that brought commits in produced a head nobody had built. /sync-branch's
+own vet covered that head, but anything else a project put in step 1 -
+an adopter's release gate - never ran on it, and step 7 attested it
```

**@vzakharov (human)** — 2026-10-16T06:03:26Z

не понимаю, объясни /plainly: что значит "own vet covered" и что за "anything else a project put"?

---

<a id="t02"></a>

### `docs/remove-before-merging/squash-message.md`:12 — unresolved

```diff
@@ -0,0 +1,29 @@
… 7 lines elided …
+anyway: two branches green alone could land as a red trunk.
+
+Step 1 is now the branch's whole local verification, and any merge that
+brings base commits in re-runs all of it on the merged head, with
+/sync-branch's vet standing in for the vet part. The base-advanced
```

**@vzakharov (human)** — 2026-10-16T06:04:12Z

опять же что за "vet part"?

и вопрос, если бы был CI, он бы так же срабатывал в случае мерджа из мейна?

---

## Timeline (status, references, and other events)

- **2026-10-16T06:05:35Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/207#pullrequestreview-5543670230.
