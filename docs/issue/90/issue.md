# Issue #90: tend-prose negation: grep the final text for negators, after the other lenses have rewritten it

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/90
- **Author:** @vzakharov (agent)
- **Created:** 2026-09-22T17:25:11Z
- **Updated:** 2026-09-22T17:25:11Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

`/tend-prose`'s negation lens can miss a polar bear in two ways. First, only one of its two tells has a search behind it. Second, it runs before the lens that manufactures bears, and nothing checks the rewritten prose afterwards.

## 1. The second tell has no search

The lens has two tells. The first, "a subject from Step 1's removed-noun list", is a grep over names the diff deleted. The second, "a negated predicate in clean present tense", has no search at all, so it depends on reading attention.

That leaves a change that removes a **property** rather than a noun with no mechanical coverage. vzakharov/vovazakharov.com#78 is the case in point. It made page PDFs build artifacts instead of committed files. The PDFs, their manifests and the render script all still exist, so the removed-noun list came back empty. The lens then missed three bears, which the operator caught in review:

- "The PDFs are build artifacts, **not** committed files."
- "**Nothing** is committed and **nothing** is vetted:"
- "**nothing** that is **not** stored can go stale" (stated twice, in two files)

Every one carries a negator.

## 2. The durability lens makes bears, and runs after the negation check

Step 3's resolve order is existence, negation, durability, tightness. The durability fix for narration is to "rephrase to a present-tense property", and its own worked example does exactly this: "The emoji is no longer parsed" → "Nothing parses the emoji." A narrating sentence about a removal ("X used to happen, now it doesn't") becomes a clean present-tense denial ("X doesn't happen"). That is the negation lens's second tell, and it appears after the negation lens has already run. Tightness can do the same when it trims the positive half off a sentence that had both.

## Proposal

One mechanism covers both. After all four lenses have applied their fixes, grep the **resulting** text of every prose line the pass touched or scoped in. Look for a closed list of negators: `not`, `no`, `nothing`, `none`, `neither`, `nor`, `never`, `nobody`, `without`, `cannot`, `n't`. Put each hit through the constraint-vs-residue discriminator, the same as a removed-noun hit. The grep only proposes. Most negative sentences in a codebase are constraints, and the discriminator is what stops the lens from over-deleting.

Two things follow:

- **It is a closing pass, not a fifth lens.** It runs over the text as it stands after the rewrites, so a bear durability wrote is in scope.
- **It greps comments and Markdown only.** On the #78 diff (486 added lines across scripts, rules, workflow and docs) a bare grep matched 52 lines. Most of the noise was code — `--no-sandbox`, `--no-pdf-header-footer`, error strings like "wrote no file at" — and a string literal is never a bear.

## Open

- Whether `no longer` belongs in the list, or stays durability's tell alone. After durability has run it should have no survivors, so a hit there means durability missed one.

Carried over from vzakharov/vovazakharov.com#80, closed in favour of this issue.

---

## Timeline (status, references, and other events)

- **2026-09-22T17:25:17Z** @vzakharov cross-referenced this issue from [#80 tend-prose negation: grep the added lines for negators, not only for removed nouns](https://github.com/vzakharov/vovazakharov.com/issues/80).
