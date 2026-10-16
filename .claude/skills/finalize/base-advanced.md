# Base-advanced deliberation

Loaded by `@.claude/skills/finalize/SKILL.md` step 6, and by
`@.claude/skills/check-merge/SKILL.md` run standalone, when `origin/<base>`
moved out from under the branch. Step numbers below are `/finalize`'s.

Your local green no longer necessarily reflects what would land. Depending on
the project, nothing may re-check the merge afterwards at all, so this
deliberation is the last chance to catch it. A clean merge (no conflicts) does
**not** mean the code is compatible: semantic incompatibilities (renamed exports
used elsewhere, changed function signatures, altered runtime invariants) merge
cleanly and still break. Whether to re-verify is your call, but make it
deliberately — don't reflexively skip it:

- You **MUST** read the incoming diff before deciding —
  `git log --oneline <merge-base>..origin/<base>` and
  `git diff <merge-base>..origin/<base> -- <areas this branch touched>`, where
  `<merge-base>` is the base commit the branch already contains (`/check-merge`
  prints it as `base=…`, or compute `git merge-base HEAD origin/<base>`).
  Deciding without reading the diff is not allowed.
- Weigh the collisions `@.claude/skills/sync-branch/SKILL.md` Step 4 reads the
  incoming diff for **plus** the semantic incompatibilities above.
- **Default to re-verify when unsure.** The test is _interaction_, not _whether
  the base touched code_ — most advances touch some code, and that alone doesn't
  warrant it. Skip re-verification when, having read the diff, you can say why
  the incoming commits and this branch's changes don't overlap: they're in
  different areas/modules, nothing this branch imports or depends on was
  touched, and no symbol/signature/pattern this branch uses was changed. If you
  can see a plausible interaction, or you genuinely can't tell, re-verify.
  - **Interacting or ambiguous** → re-run step 2 (`/sync-branch`, which vets and
    pushes) and with it the whole of step 1 it re-runs, and re-run any step-6
    dispatch the diff still warrants. The two-shot rule does **not** apply to
    these base-advanced re-runs; they're keeping the target current, not fixing
    failures.
  - **Demonstrably independent** → `/sync-branch no vet`, and run `/check-merge`
    again when you return to confirm `origin/<base>` hasn't moved since. Step 1
    never ran on the merged head, which step 7's attestation states, with this
    judgment as its reason. Unrelated code changes qualify: e.g. the base
    reworks a frontend modal while this branch changes a background job's retry
    policy — both touch code, but they don't interact.
