> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# The watermark sheds `adopted`/`declined`; what differs goes to `divergence.md`

## Why

Adopter watermarks grow without bound. metkain/metka's, at `76371ef`, is 48 KB:
484 physical lines, 924 once its strings are wrapped at 80 columns, against the
~450-line rule of thumb. `adopted` is 36 KB of it. 67 of its 80 entries carry
notes, and 57 of their 162 paragraphs are sync history ("From `70cbc4b`
(2026-10-15 sync) …", "gone again at …"), because nothing tells a sync to
rewrite a note rather than append to it.

The JSON shape makes it worse: a string is one physical line, so the prose
cannot be wrapped, measured by lines, or diffed by clause, and the
array-of-paragraphs rule in `update-muthur/SKILL.md` exists only to patch that.
And no script needs the lists: `scripts/muthur-sync.sh` reads `adopted` only to
print its keys under the nudge, and nothing reads `declined` but the agent.

## The shape

- **`watermark.json` is the sync's position and nothing else**: `repo`,
  `lastSyncedSha`, `lastSyncedAt`, `lineage`.
- **What is taken verbatim needs no record.** A source path present in this tree
  and mentioned nowhere in the record is taken as is — the nudge already reads
  `here` off the working tree rather than off `adopted`.
- **`.claude/skills/update-muthur/divergence.md` records everything else**:
  paths re-expressed here, paths and ideas declined, and cross-cutting
  differences ("this repo's `AGENTS.md` is upstream's `CLAUDE.md`") stated once
  rather than per path. Free-form: the adopter's agent picks the order, headings
  and grouping. The template ships none — it diverges from nothing.
- **Three hard rules**, stated in `update-muthur/SKILL.md`:
  1. Every path the record discusses is named literally, in backticks, from the
     repo root — Step 4 answers "is there anything about `P`?" with `grep -F`.
  2. A decline reads as a decline, its reason a present-tense condition, and a
     permanent one says "never".
  3. It states the current difference, never the sync that produced it: a sync
     rewrites the passages it touches, and history lives in the sync PR.
- **One file, read whole on every sync, capped at 450 lines** measured as Σ
  ceil(width / 80) over its lines — equal to `wc -l` on a prettier-wrapped file,
  and honest on an adopter that wraps differently or not at all. The cap is on
  the whole record because the whole record enters every sync's context; the
  pressure that keeps it under is rule 3, not splitting.

## Steps

1. **`scripts/check-divergence.sh`** (new), wired into `scripts/vet.sh` keyed on
   the watermark's presence, with a header paragraph beside the others: fails
   when `watermark.json` carries `adopted` or `declined` (an unconverted
   watermark), and when `divergence.md` is over the cap. POSIX `sh` + `awk`, no
   `jq` (the floor `check-squash-message.sh` states). Tests in
   `scripts/test_check_divergence.py`, which `check-muthur.sh` already runs.
2. **`scripts/muthur-sync.sh`**: drop `ADOPTED` and the "You adopted the
   following" block from the nudge; `mark_files` also skips the record
   (`divergence.md`), which is never synced, like the watermark. Update
   `scripts/test_muthur_sync.py`'s fixture and assertions.
3. **The template's `watermark.json`**: drop `adopted` and `declined`.
4. **`.claude/skills/update-muthur/SKILL.md`** (body only — the description
   stays, so no staging):
   - the STUB banner: hydration is the watermark plus the record;
   - § "The watermark": the four fields, and the `adopted`/`declined`/array
     paragraphs replaced by a § "The divergence record" carrying the shape, the
     three rules and the cap;
   - § "Never sync the watermark file itself" covers the record too;
   - Step 1 reads the record whole;
   - Step 3: the candidate set is the unfiltered log, each changed file sorted
     as present-and-unrecorded (a port candidate), recorded (read what the
     record says), or absent-and-unrecorded (Step 4a's question) — the
     filter-then-skim-unfiltered pair collapses into this;
   - Step 4's verdicts and Step 4a's outcomes write to the record; a verbatim
     take writes nothing;
   - Step 7: the record's touched passages are rewritten to current state in the
     same commit as the bump.
5. **Callers and docs**: `docs/adopting/sync.md` (the example and the field
   bullets; declines go to the record), `ADOPTING.md` (declines "land in its
   watermark"), `README.md` (what the watermark records), `catalog.md` and
   `catalog/g0-sync-path.md` (what `/update-muthur` carries, plus the new
   script), `catalog/g3-issue-backlog.md`, the `/implement` and `/issue`
   entries' "put … in `declined`", `/detemplate` Step 5.6 (the pruned groups go
   into the record with the criterion that dropped them, or the first sync
   re-offers every one), `/spinoff` Step 3 (the target's record is the caller's,
   restricted to what travelled, plus a decline for what did not).
6. **Commit as `feat: [attn adopters] …`**, its `Adopters:` paragraph telling
   the next sync to convert by hand while it ports: verbatim entries dropped,
   notes and reasons rewritten into the record under rules 1–3, `notes`-style
   free fields moved to their homes or into the record, the check green before
   the bump. No converter script: rewriting is judgment, which is rule 3's
   point.

No transition period: the new readers need only the four fields an old watermark
already has, and an adopter switches script and file in the one sync PR that
ports this.

## Open question

1. Split the record into parts (`divergence/*.md`) once it nears the cap?
   - **a (recommended, in force above)** — no: one file, total cap. The whole
     record enters every sync, so parts would spread the cost without cutting
     it, and the cap is what forces rule 3.
   - b — allow parts, the cap per file. Easy to add later if (a) pinches.

## DRY notes

- **The size check is new code, not a reuse of `check-claude-md-size.sh`**: that
  one counts characters across an import closure with hysteresis; this counts
  wrapped lines in one file under a flat cap. Sharing either would cost more
  glue than the ten lines of `awk` it saves.
- **"Never synced" stays one list**: `mark_files`'s `case` gains the record
  beside the watermark and the cost rows, and SKILL.md's invariant names all
  three in one place.
- **The three rules have one home**, `update-muthur/SKILL.md`;
  `docs/adopting/sync.md`, `/detemplate` and `/spinoff` point at it rather than
  restating them, replacing the declined-reason paragraphs `sync.md` carries
  now.
