# Delegation lessons travel to adopters

## The task, as asked

Operator, after the go-delegation work (see `go-delegation.completed.md`):

> «Причина в том, что чтение кэша у Sonnet стоит столько же, сколько у Opus
> ($0.2 за миллион токенов).» — это достойно запоминания. и навеяло на важное:
> адоптеры должны не просто игнорировать твой файл "уроков", а изначально
> принимать его (в обезличенном от конкретных задач виде), и при последующих
> синках смотреть, есть ли в нём что полезное что они ещё не узнали и что к ним
> тоже применимо.

## Done

Nothing yet beyond the go-delegation commits already on the branch.

## Left

1. **Remember the cache-read lesson as a general one.** In
   `.claude/skills/go/delegation-model-capabilities.md`, add a short cross-model
   section (before the per-model entries) holding lessons about delegation
   economics that are not one model's: cache reads cost the same on Sonnet 5.5
   and Opus 5.5 at `.claude/costs/prices.json` rates, so the saving comes from
   output tokens and from the delegator's context staying small — a sub-task of
   a few hundred lines saves nothing. Phrase it against `prices.json` so it is
   rechecked when rates change. Trim the sonnet entry's cost line to the
   model-specific part.
2. **Lessons are written impersonally.** In `.claude/skills/go/delegation.md` §
   "Keeping `delegation-model-capabilities.md`": an entry states what kind of
   work and what happened, never the task, branch, file or PR it came from, so
   it holds in any repo. Rewrite the existing sonnet entry to that standard ("a
   unittest suite against a hook" is fine; drop counts tied to this branch where
   they don't change the pick).
3. **Adopters take the file at adoption and merge it on every sync.**
   - Catalog: `.claude/skills/update-muthur/catalog/g2-pr-loop.md` `/go` entry —
     the notes file's disposition is adopt at first adoption, then **merge on
     each sync** rather than port-or-skip.
   - `.claude/skills/update-muthur/SKILL.md` — in the triage/apply steps (Step 4
     / Step 5; read them first), a change to the source's
     `delegation-model-capabilities.md` is never applied as a patch: read the
     source's file whole, fold in each lesson the adopter's own file does not
     already hold and that applies to their models and setup, keep their own
     lessons, stay under 100 lines. Check § "The divergence record" / the three
     invariants so this does not contradict "never sync" rules.
   - Check `docs/adopting/` (and `/detemplate`'s keep-or-prune for G2) so a
     fresh adopter keeps the file rather than pruning it as template state.
4. Then `/polish`, refresh the PR body and the squash proposal
   (`docs/remove-before-merging/squash-message.md`) to mention that the notes
   travel to adopters, and flip this file to `*.completed.md`.

## Decisions already made

- The notes file name is `delegation-model-capabilities.md` (operator asked for
  a more telling name than `models.md`).
- The hooks' shared session-state code lives in `.claude/hooks/session_state.py`
  (operator: «выноси-выноси»).
