# Adopters say hello

## Why

The repo has its first handful of stars and no way to know who took it, or for
what. The ask: an open, public record of adopters, written by their agents with
their operators' consent — at adoption for new adopters, and after the fact for
existing ones, via the sync they already run. The after-the-fact channel becomes
a named convention, since it will not be the last action an adopter is offered
retroactively.

## What lands

### 1. The welcome thread — an issue in `vzakharov/muthur`

Created by this session before any file cites it, so every citation carries a
real number (`#<N>` below).

- **Title:** `👋 Adopters: say hello`
- **Body (English):** what the thread is for — knowing who uses muthur and for
  what, in the open; what to post — a sentence or two: what you build with it,
  or just that you took it; that a private repo needn't be named; that the post
  is usually written by an adopter's agent on the operator's say-so, and a
  human's own hello is just as welcome.
- Pinning has no REST endpoint, so the report asks the operator to pin it by hand.

### 2. `docs/adopting/hello.md` — the one home of the procedure

A chapter beside `sync.md`/`costs.md`/`web-remote.md`, so it is fetched from the
source, never copied (the `docs/adopting/` `never` row already covers it). Its
URL on `main` is what every other site cites, including commit bodies read in
trees that have never seen it. It says:

- **Consent is the gate.** Ask the operator once, showing the exact text; post
  only on a yes. A no — or no answer — is final: never re-asked, reminded of, or
  called still open.
- **What to write.** One or two sentences in the operator's voice: what the
  project is and what muthur does for it. Probe `gh api repos/<R> --jq
  .visibility`; for a private repo, name neither repo nor product unless the
  operator says to — "took it, hi" is a complete hello. A public repo may link
  itself.
- **How to post.** `gh api repos/vzakharov/muthur/issues/<N>/comments -F
  body=@<file>`. A cross-owner write may 403 through a web session's proxy; then
  hand the operator the text and the thread's URL to paste. Either way the
  report says which happened.

### 3. The adoption paths offer it

- **`ADOPTING.md`** — a shared-tail section, `### Say hello, if your operator
  agrees`, pointing at the chapter; and the intro's "its two chapters" becomes a
  count-free phrasing (there are three, about to be four).
- **`/detemplate`** — the chapter is deleted with `docs/adopting/` at Step 5.2,
  so the plan carries what the `/go` session needs (Step 2's read-into-plan
  principle):
  - Step 1's numbered questions gain the hello, asked with its draft text and
    the visibility the probe found;
  - Step 4's list gains the hello draft, the answer, and the post/fallback
    recipe;
  - Step 5 gains a final item after the vet run: post it on a yes, or put the
    text and link in the report on a 403. Appended rather than inserted, so the
    `Step 5.N` citations elsewhere in the skill keep pointing at the same items.
- **`README.md`** — one line under § "Getting it": using it? say hello in
  `#<N>`, or let your agent offer to.

### 4. The convention: `[attn adopters]`

**Writing side — `/squash-message` § format rules, title bullet.** A change that
offers adopters an action their sync's port doesn't perform by itself — a hello,
a setting only the operator can flip, a one-off migration of adopter-side state —
carries `[attn adopters]` right after the type's colon:
`feat: [attn adopters] #<issue> <essence> (pr #<n>)`. The body gives the
offer its own paragraph, addressed to the adopter's agent: what to offer, that
it waits on the operator's yes, and a URL into the source for anything the
adopter's tree may not have yet. Not for a change that is merely worth porting —
the sync's triage already reads every commit. The 16 characters come out of the
80-char title cap; `scripts/check-squash-message.sh` needs no change.

**Reading side — `/update-muthur` Step 4.** A subject carrying the marker
addresses this repo whatever verdict the commit gets: the sync's report puts the
body's offer to the operator once, in its own words, under the same never-chase
rule as the sync offer. A skipped marked commit still delivers its offer.

The nudge prints commit titles unfiltered (`scripts/muthur-sync.sh nudge`), so an
adopter sees the marker at session start without any change there.

### 5. This PR's own squash record is the first use

Its title carries the marker, and its body's adopter paragraph asks an existing
adopter's agent to offer the hello per the chapter's URL. That is the whole
after-the-fact path for adopters who already took muthur — including ones whose
`/update-muthur` predates the marker, since `[attn adopters]` reads plainly to
any agent triaging from commit messages first.

## Out of scope

`/spinoff`: the sibling is born from a repo whose operator already got the offer
at their own adoption. See the open question.

The marker was first `[ADOPTERS, read body]`; the operator shortened it to
`[attn adopters]`, the convention itself telling agents what it means.

## Open questions

1. **Spinoff.** (a, recommended) no hello at spinoff — same operator, already
   asked; (b) offer it too, a spinoff being a new "what for".

## DRY notes

- **One home for the procedure**: `docs/adopting/hello.md`. `ADOPTING.md`,
  `README.md` and the squash body cite it; `/detemplate` copies its essentials
  into the plan it writes, because the chapter is deleted before that plan
  executes — the same read-then-delete pattern the skill already applies to the
  catalog, not a second home.
- **The marker** is defined once in `/squash-message` (writing) and consumed once
  in `/update-muthur` (reading); each cites the other rather than restating it.
- **The never-chase rule** is `/update-muthur` § "Offered at session start"'s;
  the reading side points at it rather than restating it. The chapter states its
  own version for adoption time, where that section is not loaded.
- Nothing shared in code: no script changes.
