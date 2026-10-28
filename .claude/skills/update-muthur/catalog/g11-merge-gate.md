> ⛔ **Part of [the catalog](../catalog.md), never vendored** — delete
> `catalog/` wherever `catalog.md` is deleted.

# G11 — Merge gate

A hook that merges a PR with no model turn acts on the operator's behalf, so
whether a bare `/merge` may land work unseen by the agent is the operator's call
— the entry is `opt-in: ask`.

- `.claude/merge-gate/` — On a prompt that is exactly `/merge`, squash-merge the
  branch's PR when every mechanical condition of `/merge`'s gate holds, read
  from GitHub, and stop the prompt with the merged SHA; anything short of that
  passes the prompt to the agent untouched. **The cost, which is why it is
  asked:** a merge no agent re-read before it landed — the attestation, CI and
  the squash record stand in for that read. Arrives with a
  `.claude/settings.json` entry to merge and a `scripts/vet.sh` loop running its
  tests.
  - **Requires:** `python3` ≥3.9, `gh`
  - **Pulls in:** `scripts/gh_export/` (G3), `scripts/lib/github.py` (G2),
    `.claude/costs/lib/` (G7), and `/finalize`'s attestation and squash proposal
    (G2), which it reads; with G9, the cold-cache guard's deferral of a bare
    `/merge`
  - **Disposition:** adopt — **opt-in: ask**
