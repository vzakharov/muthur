# PR #117: feat: split ADOPTING.md along the decisions that make it optional

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/117
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/split-adopting-x3mio3
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-26T01:20:53Z
- **Updated:** 2026-09-26T01:35:29Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- `ADOPTING.md` was 576 lines and every adopter read all of it. It now keeps only what every adoption goes through (310 lines), and each chapter moved out opens at the point where the answer that needs it is given — a "no" means that chapter is never read, and nobody opens more files than before.
- **Web/remote** — the G4 shim, what declining it costs, the setup script with its worked example and screenshot, Known gaps — moves to `docs/adopting/web-remote.md`. `ADOPTING.md` Step 3 sends a web/remote adopter there before Step 4 copies anything.
- **Watermark hydration** moves to `docs/adopting/sync.md`, read only when taking `/update-muthur`; a snapshot adopter deletes the skill instead. The fork-watermark recipe is dropped, since `/detemplate` Step 3 already carries it. Step 4 keeps the one paragraph every adopter needs on declines: record each with its reason, as a present-tense condition.
- Verify stays whole in the core, its conditional items linking to their chapters. The catalog's `never` row, `/detemplate`'s sweep and citations, `/update-muthur`, the README, and the `check-skill-catalog.sh` / `check-repo-identity.sh` scans all cover `docs/adopting/`.

Both plan questions took the recommendation: the chapters live under `docs/adopting/`, and sync gets its own file.

## QA Checklist

- [ ] `core-only` — read `ADOPTING.md` as a laptop adopter taking a one-time snapshot: the procedure completes without opening either chapter.
- [ ] `web-remote` — read it as a web/remote adopter: Step 3 sends you to `web-remote.md` before any copying, and nothing G4- or setup-script-related is left in the core beyond Verify's pointers.
- [ ] `direct-link` — open `docs/adopting/web-remote.md` and `sync.md` cold, as if from a link: each opens with its injection banner and says why you are there.
- [ ] `links` — every relative link and anchor in the three files and in the repointed citations resolves, and the screenshot renders in `web-remote.md`; no `docs/img` reference survives.
- [ ] `vet` — `./scripts/vet.sh` passes, including `check-skill-catalog.sh` and `check-repo-identity.sh` over the new files.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `core-only` | manual-only | — | a reading test of the routing |
| `web-remote` | manual-only | — | a reading test of the routing |
| `direct-link` | manual-only | — | a reading test |
| `links` | unit | partly | `@`-refs are checked by `check-skill-catalog.sh`; Markdown links and anchors were checked by a one-off script, not a vet step |
| `vet` | unit | ✅ | `./scripts/vet.sh` |

https://claude.ai/code/session_01YW6jT2D2yELyMJmVke53MB
https://claude.ai/code/session_015JJmjixnN4guR5J9ghFz6e

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-26T01:21:10Z — "Proposed squash title/body: ``` feat: split ADOPTING.md alon…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-26T01:21:10Z

[https://github.com/vzakharov/muthur/pull/117#issuecomment-5841897786](https://github.com/vzakharov/muthur/pull/117#issuecomment-5841897786)

Proposed squash title/body:

```
feat: split ADOPTING.md along the decisions that make it optional (pr #117)
```

```
Every adopter read all 576 lines of ADOPTING.md, including chapters
that one answer given along the way makes irrelevant. The file now
keeps only what every adoption goes through, and each conditional
chapter opens at the point where the decision that needs it is made,
so a "no" means the chapter is never read and nobody reads more files
than before.

The web/remote chapter (the gh shim and what declining it costs, the
environment setup script with its worked example, and the known gaps)
moves to docs/adopting/web-remote.md, together with its screenshot.
Watermark hydration moves to docs/adopting/sync.md and is read only by
adopters taking /update-muthur; a one-time snapshot deletes the skill
instead. The fork-watermark recipe is dropped, since /detemplate
already carries it. Verify stays whole in the core, its conditional
items pointing to their chapters.

The catalog's never rows, /detemplate's sweep and citations, the
README and the check-skill-catalog and check-repo-identity scans all
cover docs/adopting/.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:4 — unresolved — last: @vzakharov (human) 2026-09-26T01:34:34Z — "скорее refactor" → [↓](#t01)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:4 — unresolved

```diff
@@ -0,0 +1,33 @@
+Proposed squash title/body:
+
+```
+feat: split ADOPTING.md along the decisions that make it optional (pr #117)
```

**@vzakharov (human)** — 2026-09-26T01:34:34Z

скорее refactor

---

## Timeline (status, references, and other events)

- **2026-09-26T01:35:29Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/117#pullrequestreview-5324029489.
