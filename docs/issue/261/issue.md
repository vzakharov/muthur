# Issue #261: docs: say what adopters do with LICENSE

- **State:** closed (not_planned)
- **URL:** https://github.com/vzakharov/muthur/issues/261
- **Author:** @vzakharov (agent)
- **Created:** 2026-11-05T11:01:31Z
- **Updated:** 2026-11-05T11:02:27Z
- **Closed:** 2026-11-05T11:02:27Z
- **Labels:** _none_

---

## Body

`dec7e753` (#256) added `LICENSE` at the root, but nothing in the adopter-facing
docs says what an adopter does with it, so every downstream sync has to work it
out on its own. metkain/metka just did: it declined the file as the template's
own license, which is no part of the agent infrastructure.

Two things the docs could settle:

1. **The file's disposition.** `LICENSE` is in neither the catalog nor
   `catalog/never.md`, so `/update-muthur` Step 4a meets it as a path in neither
   `adopted` nor `declined` and has to ask the operator. A `never.md` entry
   would answer the question once for every adopter, the way `README.md` has
   one: muthur's own license, never vendored, the adopter's repo keeping its own
   terms.
2. **What MIT asks of vendored files.** MIT requires the copyright and
   permission notice in "all copies or substantial portions of the Software".
   Adopters copy whole skills and scripts verbatim, so a line in `ADOPTING.md`
   or `docs/adopting/sync.md` should say whether that obligation applies to
   them, and if it does, where the notice goes in an adopting tree (a `NOTICE`,
   a header, a line in the conventions file). As things stand, the docs leave
   this to each adopter's guess.

Raised from the metkain/metka sync to `3e94db8`.

---

## Timeline (status, references, and other events)

- **2026-11-05T11:02:27Z** @vzakharov closed this issue (not_planned).
