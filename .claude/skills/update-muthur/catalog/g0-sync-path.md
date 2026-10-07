> ⛔ **Part of [the catalog](../catalog.md), never vendored** — delete `catalog/` wherever `catalog.md` is deleted.

# G0 — The sync path

The group owns the whole source-and-target relationship, in both directions:
`/update-muthur` pulls later changes at your source forward into your repo,
and `/spinoff` pushes a new sibling repo out of it. Adopting the first is what
makes every later change at the source reachable; skipping it leaves you with a
snapshot.

**`/update-muthur` ships unhydrated**, this repo having no source of its own
to sync from. Hydrating it is filling in the watermark, not writing a procedure:
every step of the skill is usable as written. The [G6 hydrate-now-or-delete
rule](g6-stack-stubs.md) applies here too, and `scripts/check-skill-catalog.sh`
enforces it the same way.

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `/update-muthur` | Pull the agent infrastructure forward from the repo you adopted it from: diff since the watermark, triage commit by commit, port what applies — claiming a lock first, and handing the candidates to `/task`, which can split a long lag across sessions. Carries `watermark.json` — which repo you sync from, the SHA you last synced to, what you adopted or declined, and the ancestry that led here — shipped pointed at this repo with the rest as placeholders, this tree being the root. Carries `scripts/muthur-sync.sh` too, and the `SessionStart` entry that runs its nudge. | `gh`, `$GH_TOKEN`, `jq`, git transport to the source repo; hydration (the watermark) | `/polish` (G1); `/task`, `/pr`, `/squash-message` (G2); `/override-gh` (G4) | adopt — **rewrite the watermark** |
| `/spinoff` | Seed a new sibling repo out of the adopter you are standing in: triage what travels, write the target's watermark, seed its `main` and a session branch, and hand over a session in it. Ships hydrated. | `gh`, `$GH_TOKEN`, repo-creation rights on the target's owner; a caller that adopted this infrastructure rather than being it | `/update-muthur` (this group); `/pr` (G2) | adopt |

**Both skills are inert in this repo, for one structural reason: this tree is the
root.** There is no source above it to sync from, and it is not an adopter, so
there is nothing to spin off out of either — `/spinoff` refuses the moment it
finds this catalog. Downstream both work.

`/update-muthur`'s Step 8 hands off to `/polish` and `/pr`, and
cites `/squash-message` for how the sync's own squash record is titled; `/polish`
comes with G1, which you are adopting anyway. `/spinoff` reaches `/pr` as
well, at its Step 4, to open the seed PR in the new repo. **G2 is the escape**:
if you decline it, strip those citations from both skills and land the sync PR —
and the seed PR — however your repo normally does. `scripts/check-skill-catalog.sh`
will otherwise report the dangling references, which is the intended behavior
rather than a nuisance.
