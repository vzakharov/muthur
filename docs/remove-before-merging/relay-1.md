# Relay 1 — cost ledger beyond main (parked)

## Standing constraints

None stated.

## The conversation

The operator (Vova, `@vzakharov`) wrote in Russian; the session answered in
Russian. The session routed the opening prompt as rung 2 (a question, no change)
and changed no code.

1. **Operator:** «интересно, может наш pnpm costs ловить ветки, которые никогда
   не были смерджены? по сути, если косты были, то они были, вне зависимости от
   того дошло ли это до мейн-а»

   **Agent:** Yes. `report.py` reads only main, but the Stop hook pushes each
   row to its own branch, so origin already holds the rest. Measured: 136 unique
   session ids across 174 remote branches, 113 on main (~$391); 23 ids only on
   branches (~$43). Of those, the PR-less ones are abandoned work
   (`bold-feynman` $6.05, `zen-babbage` $3.32, …), the ones with merged PRs
   (#166, #132, #151, #144) are the "turn that merges" gap, and the ones with
   open PRs are just in flight. Fix: union all refs by session id, the later
   `lastResponseAt` winning. Proposed an orphan ledger branch as the more
   durable option.

2. **Operator (mid-turn):** «и попутный вопрос, если мы будем делать remove
   branch после мерджа пиара, они будут пропадать (в гипотетической ситуации
   когда мы решим вообще их не доводить до мейна, а зачищать при финализации)»

   **Agent:** GitHub keeps `refs/pull/N/head` forever, so a PR's rows survive up
   to its last head. Two things are lost: commits pushed after merge or close
   (the PR head freezes; e.g. #166's head is 1c35b44, while the branch moved on
   to b23950e, a lone `chore: session cost` commit), and branches with no PR.

3. **Operator:** «то есть если делать по принципу "смотри все ветки", а не
   "смотри мейн", то это будет длительная процедура каждый раз?»

   **Agent:** No. My ad-hoc loop was slow, not the approach. One `git ls-tree`
   per ref plus one `git cat-file --batch` over the unique blobs (221) takes
   0.46 s, plus a `git fetch`. `--all-my-repos` via the API costs more: batched
   GraphQL, seconds per repository.

4. **Operator:** «надёжнее отдельная ветка-леджер, скажем сиротская costs. —
   только muthur-cost-tracking. думал об этом, но тогда в ходе работы над пиаром
   мы не будем видеть как продвигаются косты по диффам. хотя можно конечно
   хранить их там а потом переносить при финализации в costs»

   **Agent:** Moving rows at finalize keeps both gaps, because an abandoned
   branch never finalizes and the merge turn comes after finalize. Proposed
   **dual write**: the Stop hook writes the row to the feature branch (a display
   copy, visible in the diff) and to `muthur-cost-tracking` (the source of
   truth, which the report reads). Finalize sweeps the display copy.

5. **Operator:** «гипотетически включа удалённые после закрытия пиара (не уверен
   что сейчас такие есть вообще)»

   **Agent:** Already exists: PRs #1, #10 and #74 are closed with their branches
   deleted. `git fetch origin '+refs/pull/*/head:refs/pr/*'` brings them in; the
   scan over 174 branches plus 148 PR heads gave 222 unique rows in 0.73 s. The
   deferred tail also finished: rows on main are older than their branch copy by
   $29.1 in total. So the report undercounts by about $72 on top of $391 (~18%).

6. **Operator:** «звучит интересно. а как решить проблему, когда она
   автоматически пишется уже _после_ финализации?»

   **Agent:** Proposed that the hook skips the feature-branch copy once the
   branch has been swept, detected by a `Costs-Swept:` trailer on the sweep
   commit via a local `git log`. Noted that finalize already treats a head moved
   only by `.claude/costs/sessions/` as the verified head
   (`.claude/skills/finalize/SKILL.md:339`).

7. **Operator:** «ты тут не смешиваешь понятья мерджа и финализации?»

   **Agent:** Partly. Merge always follows finalize, so the merge turn is
   covered. But claiming that resumed work always re-runs `/finalize` was
   wishful: with the trailer kept for good, rows would never return to the
   branch. Proposed fix: count the branch as swept only while no work commit
   follows the trailer.

8. **Operator:** «так, но на самом деле-то ничего страшного, если хук продолжит
   писать косты на ветку даже после мёрджа, нет -- репорт все равно будет
   смотреть на специальную ветку?»

   **Agent:** Right, after the merge it is harmless. The trailer only guards the
   gap between finalize and merge, where a turn's row would land in main. That
   costs main's tidiness, not the accounting. Suggested starting without the
   trailer.

9. **Operator:** «не то чтобы критичен, но это будет неприятно, тем более что
   ситуации когда "финализировал, а потом ещё пару вопросов туда-сюда" у нас
   вполне стандартная. а что если так: папка, где лежат косты, у нас gitignored
   на мейне, но не в пиарах -- первый вызов costs автоматом убирает гитигнор.
   при финализации, соответственно, принимается версия мейна, и дальше они уже
   не трекаются.»

   **Agent:** Workable, with three traps. The hook commits through plumbing
   (`update-index --cacheinfo`, `commit-tree`;
   `.claude/costs/hooks/stop-session-cost.sh:142`), which ignores `.gitignore`,
   so it must call `git check-ignore` itself. Finalize must restore that one
   line rather than main's whole file, plus `git rm --cached`. Resumed work
   after finalize loses diff visibility. It only makes sense together with the
   ledger branch.

10. **Operator:** «не, чё-то не нравится. ещё вариант: состояние финализации
    читается скриптом ровно один раз. елси оно включено, создаётся файл-маркер в
    сессии (не на ветке), и следующие разы уже можно без network round trip. но
    нужно оставить какую-то лазейку для "unfinalize", который будет либо менять
    текущий аттестационный коммент, либо добавлять новый»

    **Agent:** Misread it as "once at session start" and proposed that
    `/finalize` write the marker itself. Suggested an implicit unfinalize: a
    work commit after the attested SHA, checked locally. Key property: every
    failure costs only diff visibility or a stray file in main, never
    accounting.

11. **Operator:** «я имел в виду при запуске скрипта который пишет косты»

    **Agent:** The final shape (see Decisions). Left one question to the
    operator: if the GitHub query fails, treat the branch as not finalized? That
    is a silent fallback, which CLAUDE.md requires the operator to approve per
    call site. **Unanswered.**

12. **Operator:** «ага. ну вроде решили. ещё одно: как будет работать pnpm costs
    --all-my-repos с учётом того что не все репы сразу перейдут на новый
    процесс. backward comp какой-то нужен?»

    **Agent:** The new reader adds a second object to the same discovery query
    (`refs/heads/muthur-cost-tracking:.claude/costs/sessions` beside the `HEAD:`
    one at `.claude/costs/lib/github.py:121`). It unions both by session id, the
    later `lastResponseAt` winning, so no migration copy is needed. Discovery
    must also accept a repo whose ledger lives only on the ledger branch. The
    reverse direction can't be fixed: an un-updated `report.py` running
    `--all-my-repos` sees only a migrated repo's frozen main and silently
    undercounts. So run the cross-repo report from an updated repo, and say so
    in the `/update-muthur` port.

13. **Operator:** «кажется, нас раздуло. давай запаркуем, я подумаю ещё и потом
    продолжим с новой сессии»

    **Agent:** `/relay park` — this file.

## Intent

Make the cost ledger count every session that spent money, whether or not its
branch reached main: abandoned branches, the turn that merges, and turns after
finalize. Keep the costs visible in the PR diff while the work is in progress,
and keep main free of stray rows. The operator is still thinking it over;
nothing is approved for implementation.

Ruled out by the operator: moving rows to the ledger branch only at finalize,
and the gitignore-toggle scheme («не, чё-то не нравится»).

## Decisions

- **Ledger branch name:** `muthur-cost-tracking`, an orphan branch, not `costs`.
- **Dual write:** the Stop hook always writes the row to `muthur-cost-tracking`.
  It also writes a display copy to the feature branch until the branch is
  finalized. The report reads only the ledger branch, plus main for history (see
  backward compatibility). This beat moving rows at finalize, which loses
  abandoned branches and the merge turn.
- **Finalized detection:** on each run of the Stop hook, while the branch is not
  known to be finalized, one GraphQL query for the PR and its attestation
  comment. On "yes", write a marker `tmp/costs/finalized/<branch>` holding the
  attested SHA (container-local, keyed by branch because `/from-branch` switches
  a session's branch); later runs need no network. This beat a commit trailer
  and the gitignore toggle.
- **Implicit unfinalize:** on each run the hook checks locally whether a commit
  after the attested SHA touches anything outside `.claude/costs/sessions/`. If
  so, the marker is stale: the hook writes to the branch again and re-queries
  GitHub. A re-finalize then yields a new attestation SHA. The marker is a cache
  of the latest attestation.
- **Explicit unfinalize:** a skill marks the attestation comment as revoked
  (edit in place, one source) and deletes the marker in its own session. Stale
  markers in other sessions are harmless.
- **Failure property:** every failure costs only diff visibility or a stray row
  in main, never accounting, because the ledger branch is always written.
- **Reading all refs is cheap:** batch with `git cat-file --batch` over unique
  blobs. Not needed if the ledger branch exists, but it is the recipe for any
  one-off reconciliation of old branches.
- **Backward compatibility:** the reader unions `HEAD:` and the ledger branch
  per repo; no seeding; discovery accepts either. Old readers can't be fixed.
- **Open:** the network-failure fallback (treat as not finalized?) needs the
  operator's explicit approval per CLAUDE.md § "Never silently swallow errors".
- **Not discussed yet:** how concurrent pushes to `muthur-cost-tracking` race
  (the agent's view: rebase-and-retry on non-fast-forward, safe because files
  never collide); whether old branch rows get backfilled into the ledger branch
  once.

## Errors and dead ends

- An ad-hoc per-(session × branch) loop spawning `git ls-tree`/`git show`/Python
  ran over two minutes. The batched recipe above replaced it.
- The `Costs-Swept:` trailer (kept forever, it suppressed rows after resumed
  work) and the gitignore toggle (plumbing ignores `.gitignore`, whole-file
  restore clobbers branch edits). Both were superseded.
- The agent conflated "finalize re-runs after resumed work" with a guarantee;
  the operator caught it (message 7).

## State

- **Branch:** `claude/cost-ledger-branch-pz4s1a`, renamed from
  `claude/gallant-lovelace-pz4s1a`. Deleting the old remote ref got a 403 from
  the git proxy, so the old ref lingers; it carries no PR.
- **PR:** none. No plan file. The branch carries only `chore: session cost`
  commits and this summary.
- **Running:** nothing after this park (keepalive stopped).
- **Estimate (this session):** 1.5 h senior analyst ("measuring what the remote
  refs hold beyond main takes git plumbing across ~300 refs and judging which
  gaps are abandoned work vs in flight") + 2 h senior architect ("the
  ledger-branch design trades accounting completeness, diff visibility, network
  cost and cross-repo compatibility; each option needed its failure modes
  weighed"). No remainder handed on: implementation is not yet scoped, and the
  successor sizes it when it is.

## Pointers

- `.claude/costs/CLAUDE.md` § "What the totals do not cover" names the two gaps
  (abandoned branches, the turn that merges) that this design closes. It will
  need rewriting with the change.
- `.claude/costs/hooks/stop-session-cost.sh`: the Stop hook, plumbing commit at
  ~142–158. The dual write goes here.
- `.claude/costs/report.py` (`rows_in`, local read) and
  `.claude/costs/lib/github.py` (`REPO_FIELDS` at 119, `discover`,
  `ledger_texts`) are the readers to change.
- `.claude/skills/finalize/SKILL.md:339`: the existing tolerance for cost-only
  commits after attestation. Finalize also gains the display-copy sweep.
- Re-measure the gap: `git fetch origin '+refs/pull/*/head:refs/pr/*'`, then
  `git ls-tree -r <ref> -- .claude/costs/sessions` over `refs/remotes/origin/*`
  and `refs/pr/*`, and compare session ids with `origin/main`.
- Predecessor transcript:
  https://claude.ai/code/session_01NgUZSXMZuxiwQHduuBy6yC

## Next step

Wait for the operator. They parked to think («я подумаю ещё и потом продолжим с
новой сессии»). When they return, the one open question is message 11's
network-failure fallback. Implementation, once asked for, goes through `/task`.
