> ⛔ **Part of [the catalog](../catalog.md), never vendored** — delete `catalog/` wherever `catalog.md` is deleted.

# G5 — CI & landing

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `/bootstrap-workflow-dispatch` | Register a `workflow_dispatch` workflow in Actions metadata with a one-shot branch-scoped push trigger, so `gh workflow run` stops 404ing on a branch whose workflow has not reached the default branch yet. | GitHub Actions, `gh`, push access to the branch | `/test-on-gh` (G6), `/watch-ci` | adopt |
| `/watch-ci` | Watch an in-flight GitHub Actions run incrementally, surfacing failures as they happen so fixes can go out mid-run. | GitHub Actions, `gh`, `scripts/ci-watch-tick.sh`; **G4 on the web** | — | adopt |
| `scripts/ci-watch-tick.sh` | One polling tick of a CI run: what changed since the last tick. | `gh`, `jq`, `scripts/lib/watch-tick-common.sh`, `scripts/lib/gh-repo.sh` (G2) | — | adopt |
| `scripts/lib/watch-tick-common.sh` | The watch loop's tick helpers: the elapsed-aware sleep between ticks, and the `--reset` state-file removal. | `bash` | — | adopt |

The group's three CI-facing skills partition one timeline.
`/bootstrap-workflow-dispatch` ends the moment `gh workflow run` stops 404ing,
`/test-on-gh` is the dispatch that hits that 404 first, and `/watch-ci` watches
the run a successful dispatch produces. `/test-on-gh` ships as a stub, so it is
listed under [G6](g6-stack-stubs.md) with the other stubs — one row, one group.

**G4 is a `/watch-ci` requirement, not a group-wide one** — it is `gh run
watch`'s long-polling that the proxy blocks, counted among the costs of
declining G4 in [that group](g4-remote-plumbing.md).
`/bootstrap-workflow-dispatch` dispatches over REST
(`POST /repos/{owner}/{repo}/actions/workflows/{id}/dispatches`) and works
unshimmed.

**Taking this group without G6 means editing one reference.**
`/bootstrap-workflow-dispatch` `@`-references `/test-on-gh`, and G6's rule is to
copy a stub only if you hydrate it now — so an adopter who skips `/test-on-gh`
strips that clause from the `## Related` section, or
`scripts/check-skill-catalog.sh` reports the dangling pointer.
