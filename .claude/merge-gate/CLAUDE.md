# The merge gate

`hooks/merge_gate.py` takes a prompt that is exactly `/merge` and, when the
branch's PR passes every mechanical condition of `/merge`'s gate, squash-merges
it and blocks the prompt with the merged SHA. A blocked prompt makes no API
request, so landing a finalized PR costs no model turn and re-caches nothing.

- **It mirrors two prose homes, which stay the source.**
  `.claude/skills/finalize/merge.md` § "Step 8 — the gate" and § "Merging" say
  what `/merge` checks and how it reads the squash record back;
  `.claude/skills/finalize/attest.md` says which value each attestation line may
  hold. A change there is a change here, and `test_merge_gate.py` reads
  `attest.md`'s template so the attestation patterns cannot drift from it.
- **Every fact comes from GitHub, never the checkout**: a container that woke
  for this prompt may hold a stale tree.
- **A decline prints nothing**, whether a check failed or the gate raised, so
  the prompt reaches the agent as typed and its `/merge` re-checks everything
  with judgement. That is not a swallowed error: the agent meets the same
  failure and reports it. A traceback goes to stderr.
- **A `no vet` attestation declines**, because whether the skipped vet run had
  anything to check is judgement. The `/test-on-gh is an unhydrated stub` line
  passes only while that skill on the PR head is still a stub.
- **The cold-cache guard defers a bare `/merge` to this hook** while this file
  exists, since hooks of one event run in parallel and a merged prompt must not
  come back with a price stop beside it. On a decline the gate runs the guard
  itself, as a subprocess with the event marked `merge_gate_declined`.
- **A subprocess, not an import, because `scripts/lib/` and `.claude/costs/lib/`
  both carry a `lib.github`.** The gate imports `lib` as one namespace package
  across both, so `lib.github` is the scripts' one, and no ledger module that
  imports its own may be imported here.
- **After a merge, the model is told**: `tmp/merge-gate/<session_id>.json` holds
  the merge, and every prompt that reaches the model carries it as context until
  a response lands after it.

Deleting `.claude/merge-gate/` turns it off, and the cold-cache guard takes
`/merge` back without an edit.
