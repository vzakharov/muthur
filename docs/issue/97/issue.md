# Issue #97: Trim CLAUDE.md to what every turn needs, and write that test into it

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/97
- **Author:** @vzakharov (agent)
- **Created:** 2026-09-23T12:04:23Z
- **Updated:** 2026-09-23T12:12:26Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Why

`CLAUDE.md` is loaded in full on every turn of every session, and it has grown to ~6,500 words. Much of that is procedure only a session running a particular skill needs, and that skill already carries it. Every other session pays for it anyway, and a rule buried in a long file is followed less reliably than one in a short file.

The plan-file bullet in § "Plan mode & questions in web sessions" was cut this way in #96 (fe2be2e): from ~190 words to ~60. It keeps the three tripwires every session needs (a draft name means no source edits, `in-progress` is another session's, `paused` is where to resume) and points at `/plan` § "Plan file lifecycle" for the rest.

## What to do

1. **Write the test into `CLAUDE.md` itself**, most likely in § "Writing things down": a line stays in `CLAUDE.md` only when it has to hold on turns where the process it concerns is **not** being run. A line that only matters while a given skill, hook or directory is in play goes to that skill, a `.claude/rules/` file or a colocated doc, and `CLAUDE.md` keeps at most a pointer. Say it once, and update `/tend-prose`'s existence lens to match if it needs to.
2. **Apply the test to every section of `CLAUDE.md`**, as #96 did to the plan-file bullet. Where the procedure already has a home, cut the text and leave a pointer. Where it has none, move it first and then cut.
3. **Keep citations resolving.** Skills cite `CLAUDE.md § "<section>"` in many places. `scripts/check-skill-catalog.sh` checks `@` paths, not section anchors, so each section that is renamed or removed needs its citations found and repointed by hand.

## Done when

- The test is in `CLAUDE.md`, stated once.
- Every section has been checked against it, and what stays is only what every turn needs.
- `CLAUDE.md` is substantially shorter. No specific word target; the test decides.
- Every `CLAUDE.md § "…"` citation in `.claude/` and `scripts/` names a section that exists.

Raised in review on #96: https://github.com/vzakharov/muthur/pull/96#discussion_r4082102919

---

## Comments

- **C01** @vzakharov (human) — 2026-09-23T12:12:08Z — "и отдельно нужно подумать о том, как мы сообщим адоптерам сд…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (human) on 2026-09-23T12:12:08Z

[https://github.com/vzakharov/muthur/issues/97#issuecomment-5794567968](https://github.com/vzakharov/muthur/issues/97#issuecomment-5794567968)

и отдельно нужно подумать о том, как мы сообщим адоптерам сделать то же с их CLAUDE.md-ами -- не только в части адопченной отсюда, но и в принципе как дисциплину

---

