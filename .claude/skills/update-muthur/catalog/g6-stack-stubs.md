> ⛔ **Part of [the catalog](../catalog.md), never vendored** — delete `catalog/` wherever `catalog.md` is deleted.

# G6 — Stack stubs

Every line of a working version of these is bound to a particular stack, so they
ship carrying only the durable part: the shape of the job, and the concerns any
implementation has to answer. Each opens with a banner naming what must be
filled in, and its frontmatter announces that it is a stub.

**An unhydrated stub is worse than a missing skill** — half-following one against
a project it was never written for beats not having it only in appearance. So
copy none of these "for later": take an entry only if you will hydrate it now, and
delete the rest. Three of them tell you when to delete the skill outright
instead (no visual surface, no CI-only tests, no numbered migrations).

- `/release` — Cut a release: version bump, notes, release PR, arm or ship the deploy.
  - **Requires:** a deploy path; hydration
  - **Disposition:** adopt only if hydrating now
- `/hotfix` — Ship an urgent fix past the normal promotion path, then reconcile it into the trunk.
  - **Requires:** a deploy path; hydration
  - **Disposition:** adopt only if hydrating now
- `/preview` — Render a visual change and actually look at it, rather than judging appearance from code.
  - **Requires:** a visual surface; hydration
  - **Disposition:** adopt only if hydrating now
- `/log-review` — Read deployed logs since the last review: a usage readout plus health triage.
  - **Requires:** deployed logs; hydration
  - **Disposition:** adopt only if hydrating now
- `/readonly-probe` — Investigate against real deployed data under an enforced read-only connection.
  - **Requires:** a production datastore; hydration
  - **Disposition:** adopt only if hydrating now
- `/renumber-migration` — Resolve a sequential migration-number collision after another branch landed first.
  - **Requires:** sequential numbered migrations; hydration
  - **Disposition:** adopt only if hydrating now
- `/test-on-gh` — Dispatch the test buckets that can't run locally to CI on the branch, and block for the result.
  - **Requires:** G5, CI-only test buckets; hydration
  - **Disposition:** adopt only if hydrating now
