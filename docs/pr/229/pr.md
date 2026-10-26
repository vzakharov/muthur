# PR #229: feat: [attn adopters] a capped divergence.md replaces adopted/declined

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/229
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/watermark-divergence-1dwzoj
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-26T14:49:56Z
- **Updated:** 2026-10-26T18:56:45Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 2

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `docs/remove-before-merging/squash-message.md`:4 — unresolved — last: @vzakharov (human) 2026-10-26T18:51:28Z — "это приватная репа, её нельзя упоминать -- да и вообще, кажд…" → [↓](#t01)
- **T02** `scripts/check-divergence.sh`:1 — unresolved — last: @vzakharov (human) 2026-10-26T18:55:23Z — "давай-ка уберём всё это; при апдейте адоптер сам и посчитает…" → [↓](#t02)

---

## Body

## Summary

- Adopter watermarks grow without bound — metkain/metka's is 48 KB, 924 lines once its JSON strings are wrapped at 80 columns — because per-path notes accumulate sync history and JSON prose can't be wrapped, measured by lines, or diffed by clause.
- `watermark.json` keeps only the sync's position (`repo`, `lastSyncedSha`, `lastSyncedAt`, `lineage`); `adopted`/`declined` leave it, since no script needs them and a verbatim take is already visible on disk. The nudge drops its "You adopted" block.
- What differs from the source goes to a free-form `.claude/skills/update-muthur/divergence.md` under three rules (paths named literally, declines read as declines, current state not history), read whole on every sync and capped at 450 lines at 80 columns. `/update-muthur` Step 3 sorts the unfiltered log against tree and record instead of filtering by `adopted`; Step 7 rewrites the passages a sync touched.
- `scripts/check-divergence.sh`, run by `vet.sh`, fails an unconverted watermark and an oversized record. `/detemplate` and `/spinoff` write the record with a decline for everything they leave out. The squash is `[attn adopters]`: each adopter converts by hand in the sync that ports it.

## QA Checklist

- [ ] `nudge` — in an adopter fixture lagging its source, `scripts/muthur-sync.sh nudge` prints commits and `here`/`not here` files, no "You adopted" block, and never lists `divergence.md` or `watermark.json`.
- [ ] `old-watermark` — a `watermark.json` still carrying `adopted` or `declined` makes `scripts/check-divergence.sh` fail with a message naming the record to convert into.
- [ ] `cap` — a `divergence.md` of 451 lines, or 151 lines of 161 characters, fails the check; 450 passes, Cyrillic lines of 80 characters count as one each; no record at all passes.
- [ ] `template` — on this repo, `scripts/vet.sh` passes with the trimmed shipped watermark and no record.
- [ ] `prose` — `update-muthur/SKILL.md`, `docs/adopting/sync.md`, `/detemplate`, `/spinoff`, README and the catalog no longer tell anyone to write `adopted`/`declined`.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `nudge` | integration | ✅ | `scripts/test_muthur_sync.py` — `LagTest.test_titles_and_files` |
| `old-watermark` | unit | ✅ | `scripts/test_check_divergence.py` |
| `cap` | unit | ✅ | `scripts/test_check_divergence.py` — boundary, long-line and character-width cases |
| `template` | integration | ❌ | the vet run itself, at `/finalize` |
| `prose` | manual | ❌ | a grep and a read of the touched skills |

https://claude.ai/code/session_01Eeow5zrMDxzvWKcnWiw5GK

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-26T14:50:14Z — "Proposed squash body: ``` Adopter watermarks grew without bo…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-26T14:50:14Z

[https://github.com/vzakharov/muthur/pull/229#issuecomment-6419041875](https://github.com/vzakharov/muthur/pull/229#issuecomment-6419041875)

Proposed squash body:

```
Adopter watermarks grew without bound: metka's reached 48 KB, 924 lines
once its JSON strings are wrapped at 80 columns. Per-path notes gathered
a paragraph per sync, since nothing said to rewrite them, and JSON prose
can be neither wrapped, measured by lines, nor diffed by clause.

watermark.json now holds only the sync's position: repo, lastSyncedSha,
lastSyncedAt, lineage. A path taken verbatim needs no record, its
presence on disk saying so; everything else that differs from the
source - re-expressions, declines, cross-cutting differences stated
once - goes to a free-form update-muthur/divergence.md. Three rules
bind it: every path named literally from the root, a decline reading
as one, and current state rather than sync history. The sync reads it
whole, sorts the unfiltered log against disk and record, and rewrites
the passages it touches.

scripts/check-divergence.sh, run by vet.sh, fails a watermark still
carrying adopted/declined and a record past 450 lines counted at 80
columns, which holds whatever formatter the adopter uses. The nudge no
longer prints adopted; /detemplate and /spinoff write the record with a
decline for everything they leave out, so a first sync re-offers none.

Adopters: in the sync that ports this, convert by hand - drop entries
taken verbatim, rewrite notes and reasons into divergence.md under the
three rules (history out, cross-cutting differences once), move free
fields such as notes to their homes, and get the check green before
the bump. No operator yes is needed.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:4 — unresolved — last: @vzakharov (human) 2026-10-26T18:51:28Z — "это приватная репа, её нельзя упоминать -- да и вообще, кажд…" → [↓](#t01)
- **T02** `scripts/check-divergence.sh`:1 — unresolved — last: @vzakharov (human) 2026-10-26T18:55:23Z — "давай-ка уберём всё это; при апдейте адоптер сам и посчитает…" → [↓](#t02)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:4 — unresolved

```diff
@@ -0,0 +1,36 @@
+Proposed squash body:
+
+```
+Adopter watermarks grew without bound: metka's reached 48 KB, 924 lines
```

**@vzakharov (human)** — 2026-10-26T18:51:28Z

это приватная репа, её нельзя упоминать -- да и вообще, каждый сам для себя посчитает

просвипь, не упоминаем ли ещё где-то (хотя это было бы само по себе нарушением durability)

---

<a id="t02"></a>

### `scripts/check-divergence.sh`:1 — unresolved

**@vzakharov (human)** — 2026-10-26T18:55:23Z

давай-ка уберём всё это; при апдейте адоптер сам и посчитает и, если вылезает, сократит. Rationale: имеет смысл в будущем вообще ввести ограничение для размеров любых md, но это не дело конкретного файла тут. Добавь только в attn adopters чтобы старались держать  в разумных пределах и выделяли в отдельные подфайлы и/или урезали, если не влезает

ну а то чтобы не оставить "случайно" джсона это нужно быть совсем гпт 3.5 чтобы не увидеть запроса

---

## Timeline (status, references, and other events)

- **2026-10-26T14:50:19Z** @vzakharov renamed from «feat: [attn adopters] the watermark sheds adopted/declined; what differs goes to divergence.md» to «feat: [attn adopters] a capped divergence.md replaces adopted/declined».
- **2026-10-26T18:38:40Z** @vzakharov cross-referenced this pull request from [#231 fix: [attn adopters] split watermark explanations by thought, not script](https://github.com/vzakharov/muthur/pull/231).
- **2026-10-26T18:56:45Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/229#pullrequestreview-5657358522.
