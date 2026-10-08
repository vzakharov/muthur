# Issue #170: PR export: warn on a large review up front and route it through subagents

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/170
- **Author:** @vzakharov (agent)
- **Created:** 2026-10-08T19:24:07Z
- **Updated:** 2026-10-08T19:24:07Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Problem

`/handle` on a PR with a large review spends the whole session reading the export before doing anything. It happened on vzakharov/vovazakharov.com#115: the export `docs/pr/115/pr.md` was 3,164 lines (~150 KB, ~37k tokens of file, far more once it is read in pages), with 104 posts awaiting an answer. The agent read it whole, as `/handle` Step 2 currently implies ("follow the verdict's links… open the posts it lists"), and crossed the context budget's 200k warning before editing a single file. The session ended with a triage plan and a relay, and the successor has to open the same export again.

Nothing warned the agent beforehand. The export already knows how big it is and how many rows the verdict has, before anyone reads a line.

## Proposal

When the export crosses a size threshold, say so **at the top of the verdict**, where the hook (`prompt-handle-pr-export.sh`) already prints it before the turn, and say what to do instead:

- **Criteria** (any one fires it): awaiting rows above ~20; the export file above ~40k tokens (chars / 4); or the export alone above some fraction of the context budget's warning line (`.claude/context-budget/`), so the threshold follows the budget rather than a constant.
- **The warning**: the size (lines, ~tokens, awaiting count), and the instruction: do not read the file whole; batch the awaiting rows (by file, or by kind: code / content / questions) and hand each batch to a subagent with its anchors and the export path, keeping the main session for code, commits and replies.
- **Optionally**, make the batching cheap: the exporter can write the awaiting threads as one file per thread (or per batch) beside `pr.md`, so a subagent opens only its slice and the main session never pages the whole document.

Homes: `scripts/gh_export/awaiting.py` / `scripts/export-github-item.py` for the measurement and the banner, `.claude/skills/handle/SKILL.md` Steps 2–3 for the rule that a flagged export is worked through subagents.

---

