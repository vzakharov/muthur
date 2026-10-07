# Relay 1 — keeping an idle session's prompt cache warm

## 1. Standing constraints

None stated by the operator. One granted for this conversation's experiments only: the operator asked for live tests with background alarms, which CLAUDE.md § "Key principles" otherwise forbids (`Don't run Bash with run_in_background`). That grant covered the experiments; making it a convention needs the operator's sign-off in a plan.

## 2. The conversation

All operator messages are in Russian; the operator is Vova (@vzakharov), addressed as «ты».

1. **Operator:** «а можно ли сделать как-то, чтобы ты за несколько минут до истечения кеша делал "релей без релея"? То есть готовил сообщение и давал оператору строку, с которой начать новую сессию?»
   **Agent:** Routed as row 2 (a question). Yes in principle: the summary is cheap while the cache is warm (a cache read ≈ 0.1× vs a 1h re-cache at 2× input), unlike `/relay` on a cold cache, which `.claude/cold-cache/CLAUDE.md` already notes pays the full re-cache. Proposed `send_later` (Claude Code Remote MCP) armed at last response + TTL − 5 min, re-armed per turn via `update_trigger`; on fire, run `/relay` Steps 1–2, skip Step 3, print the `/relay take` line. Noted it would let the cold-cache guard offer a fresh session even when decisions live only in chat.
2. **Operator:** «так, тогда, получается, просто можно каждые 55 минут выдавать сообщение "я всё ещё тут"? что меня смущает -- это что, получается, это (выставлять send_later) нужно будет делать при каждом ответе пользователю -- как-то не айс»
   **Agent:** Yes, a keepalive ping beats a pre-written summary: for Opus 5.5 (`.claude/costs/prices.json`) cache read $0.20/M vs 1h write $8.00/M, 40×; on 300k context ≈ $0.06/ping vs ≈ $2.40 re-cache, break-even ≈ 40 idle hours, so cap it (e.g. a day) and write the relay summary on the last ping. Proposed one recurring cron trigger instead of per-turn arming, with a `UserPromptSubmit` hook blocking pings while the cache is warm. Unknowns: cron minimum interval (hourly = TTL, a race), how a blocked ping looks, whether a trigger message passes through `UserPromptSubmit`.
3. **Operator:** «а может агент вызвать тулу и *не* ответить? тогда обновлять кеш можно было бы без user-facing сообщений»
   **Agent:** A turn can end without text, but the waking message is what's visible, and any request refreshes the cache — no tool needed. Proposed two ways to wake without a user message: (1) a background Bash alarm (`run_in_background`), which re-invokes the agent on exit, needing an exception to the CLAUDE.md ban and surviving container reclaim; (2) a Stop hook holding the turn. Favoured (1).
4. **Operator:** «давай попробуем. давай начнём с 5 минут, чтобы раньше увидеть "как выглядит"»
   **Agent:** Ran a 5-minute background `sleep 300`, planning to end the wake turn silently.
5. *(Alarm fired 17:03:07Z.)* The silent turn was rejected by the harness: «[Your previous response had no visible output. Please continue and produce a user-visible response.]» **Agent:** reported the wake works but a fully silent turn is impossible, and a silent attempt costs two requests instead of one.
6. **Operator:** «на какой телефон? выглядело это вот так.» + screenshot (`tmp/session-images/` in the old container): the task notification itself is not shown in the feed; only the agent's forced reply is.
   **Agent:** Clarified "phone" meant the Claude app's push; launched a 50-minute alarm recording boot ids.
7. *(Alarm fired 17:55:23Z, same boot id.)* **Agent:** reported the container survived 50 min idle.
8. **Operator:** «а ты убедился что кеш не протух?»
   **Agent:** Checked transcript usage: the wake request read 118 600 from cache, wrote 707 — warm. Contrast: a real cold gap earlier (14:07→16:50) read only 44 449 (the environment-shared prefix) and wrote 60 796.
9. **Operator:** «так.. хорошо.. что-то нарисовывается, что-то нет. а что если будет например подагент который пингует каждые 55 минут? когда пингует подагент, это (а) работает для обновления кеша и (б) может проходить без выдачи сообщения пользователю?»
   **Agent:** Tested: `fork` agent type does not exist here; a `general-purpose` subagent's request read 38 186 (shared prefix only) and wrote 22 516 of its own — it cannot touch the main conversation's cache.
10. **Operator:** «ну что он начинает с нуля это понятно, просто идея такая: 1- ты запускаешь подагента-хранителя кеша 2- каждые 55 минут подагент тебе пишет "ку-ку" 3- ты, получив это сообщение, получаешь его в *свой* контекст, соответственно, по логике, это обновляет кеш»
    **Agent:** Agreed point 3 refreshes the cache, but it is the background alarm with an extra model in the middle; the open question is (б). Launched a background subagent that waits 2 min and returns «ку-ку».
11. **Operator:** «да но будильник тебя будит и требует что-то мне ответить, а подагент, возможно, не будет. давай подождём 1.40 и посмотрим сможешь ли ты ничего не ответить *мне* в ленту»
    *(Subagent returned.)* The silent turn was again rejected with the same harness line. **Agent:** the visible-reply rule does not depend on who woke the session; the subagent is costlier and (per the next screenshot) noisier.
12. **Operator:** «да, но это получается прямо при каждом ответе нужно запускать "будильник"?»
    **Agent:** No: a watcher script can poll the transcript's last-response time and fire only after 55 idle minutes, so it is re-armed once per idle hour, not per reply. Noted the container had restarted (boot id changed) — processes die, files persist — so a resume needs re-arming, e.g. a `SessionStart:resume` hook reminder.
13. **Operator:** «хм, то есть контейнер умер, но кеш нет?»
    **Agent:** Yes: the cache lives server-side, keyed by prompt prefix. The first request after the resume read 131 033, wrote 10 589 (the re-injected skills listing plus the message).
14. **Operator:** «но тем не менее будильник переживает смерть контейнера -- сейчас же он тебя разбудил?»
    **Agent:** No — the operator's message woke it; no alarm was pending when the container died (the 50-min one had fired at 17:55).
15. **Operator:** «вот это сообщение? т.е. отправил "Вова, не вышло" ты до того как контейнер умер?» + screenshot showing a «Message from subagent ›» label in the feed.
    **Agent:** Yes, sent 18:01:14 in the old VM; the new VM booted 18:19:27, 27 s before the operator's next message. The subagent wake is visibly labelled in the feed, unlike the Bash alarm's. Hypothesised a running background task keeps the VM alive.
16. **Operator:** «а почему ты уверен, что будильник не переживёт? может его отдельное что-то держит, а не процесс контейнера?»
    **Agent:** Conceded it was inferred. Showed the container is a Firecracker microVM cold-booted at 18:19:27 (PID 1 `/process_api --firecracker-init`), disk kept, all processes new. Started a 40-min alarm to test.
17. **Operator (mid-turn):** «но если грубо говоря твой sleep будет ознаать, что всё это время контейнер не умрёт, то и ок»
18. **Operator:** «поставь на пару часов -- 50 минут мы проверили, имеет смысл проверить дольше. а я пока не буду соваться в эту сессию чтобы не разбудить»
    **Agent:** Replaced the 40-min alarm with a cycle: 55-min alarm, one line per wake, re-arm, for ~2 h; log in `tmp/keepalive/cycle.log`.
19. *(18:45:53Z.)* Harness: «The container was restarted. The following background tasks were running and are now stopped: … Re-create them if still needed.» **Agent:** the VM died between 18:29:41 (last write by the old VM, `/root/.claude/.last-cleanup`) and 18:45:46 despite the running `sleep`; the CLI itself woke the agent to report the lost task; cache warm (163 908 read). Re-armed. Asked whether the operator had opened the session at 18:45.
20. **Operator:** «хм, интересно, а такое тебе выдаётся только если есть бэкграунд-таски? что интересно, я не открывал сессию в 18-45, значит она перезагрузилась как-то сама?»
    **Agent:** Likely only with lost background tasks (the 18:19 restart, with none running, produced no notice and no wake) — one case each. Two hypotheses for the self-restart: the platform raises a session with pending background tasks to report their loss, or coincidental host maintenance.
21. **Operator:** «зачем интересно она сама будила контейнер, который никто не звал. ладно, ждём»
    **Agent:** Guess: the platform keeps the "you'll be notified" promise of a background task even when the VM dies.
22. *(Wakes at 19:41:10Z and 20:36:21Z, same VM boot 18:45:46, cache reads 180 220 and 182 367, writes ~600.)* **Agent:** two consecutive successful ~55-min cycles; ≈ $0.04 per wake vs ≈ $1.46 re-cache on this context; stopped re-arming after ~2 h; offered «делай» → `/task`.
23. *(Overnight the cache expired; the cold-cache guard stopped the operator's morning prompt; they resent it with `!`.)* **Operator:** «пришёл с утра, иронично что он таки протух (что логично). давай релейнем в новую сессию, здесь ещё есть о чём поговорить; только переименуй ветку уже сейчас, до первой правки (релейного файла)»
    **Agent:** Renamed the branch to `claude/cache-keepalive-he98hv` and ran this relay.

## 3. Intent

The operator wants an idle web session to stop losing its prompt cache, or at least to hand off cheaply before it does, with as little feed noise and per-turn ritual as possible. Ruled out or disliked: re-arming something on every reply («как-то не айс»); visible messages per ping where avoidable. The conversation is still exploratory — no «делай» has been given; nothing is approved for implementation.

## 4. Decisions and findings

- **Keepalive beats a pre-expiry summary** on cost: a ping is a cache read (40× cheaper than a 1h write on Opus 5.5). A relay summary is still the right last step once a cap on idle pinging is reached.
- **Background Bash alarm (`run_in_background`) is the cheapest wake found.** Its task notification is invisible in the feed; the agent's reply is what shows.
- **A fully silent turn is impossible**: the harness injects «Your previous response had no visible output…» and forces a second request, whatever woke the session (alarm or subagent). So the minimum footprint is one short line per wake (the agent used «🕯 кеш продлён»).
- **Subagents cannot keep the main cache warm** (own prefix); a `fork` type that would inherit context does not exist here. A subagent's hand-back shows as «Message from subagent ›» in the feed.
- **Cron triggers / `send_later`** (alternative wake) post a user-turn message — visible — and hourly cron races a 60-min TTL. Not tested.
- **The cache survives container restarts** (server-side, prefix-keyed). A resume adds ~10k tokens (re-injected skills listing).
- **Container (Firecracker microVM) restarts kill background processes; the disk persists.** A running `sleep` did not prevent the 18:29–18:45 death; the same alarm setup then survived two ~55-min idle spells. The cause of that one death is unknown.
- **After a restart that kills a background task, the CLI wakes the agent unprompted** with a lost-task notice — observed once, at 18:45, with no operator action. A restart with no background tasks (18:19) produced no notice and no wake. This may make a separate "re-arm after resume" hook unnecessary.
- **Re-arming per reply is avoidable**: a watcher polling the transcript's last main-chain response time fires only after TTL − 5 min of silence, so it is re-armed once per idle wake.
- Terms: **«релей без релея»** — write the relay summary and print the `/relay take` line without spawning the successor. **будильник** — the background alarm. **хранитель (кеша)** — the subagent keeper idea (rejected).

## 5. Errors and dead ends

- Silent wake turns (tried twice) — rejected by the harness each time.
- Subagent keeper — cannot refresh the main cache; `fork` not available.
- Hypothesis "a running background task keeps the VM alive" — refuted by the 18:29–18:45 death.
- Agent overclaimed twice and was corrected: "the alarm won't survive" (was inference, operator challenged it — «а почему ты уверен…»), and "the 18:20 wake was the alarm" (it was the operator's message).
- `pkill -f "sleep 2400"` killed its own shell (exit 144) since its command line matched; it still stopped the alarm.
- The repo's `file-tools-nudge.py` PreToolUse hook blocks `echo >>` logging; `BATCH_EDIT=1` prefix passes it.

## 6. State

- Branch `claude/cache-keepalive-he98hv`, renamed from `claude/lucid-ramanujan-he98hv`; no code changes, no PR, no plan file. The old remote ref `claude/lucid-ramanujan-he98hv` could not be deleted (git proxy 403) and lingers, empty.
- Nothing running: no alarm armed, no trigger, no PR subscription.
- Experiment logs (`tmp/keepalive/`: `armed*`, `fired*`, `cycle.log`) are in the old container's gitignored `tmp/` and not on the branch; the figures that matter are quoted above.
- Estimate: this session 2 h senior architect — "settling whether an idle session can keep its prompt cache warm took live experiments across the harness's wake paths, VM lifecycle and cache accounting, each needing a design reading to be conclusive". The remainder (the design discussion and any implementation) is the successor's to size.

## 7. Pointers

- `.claude/skills/relay/SKILL.md` — the relay this would extend («релей без релея»: Steps 1–2 without Step 3).
- `.claude/cold-cache/CLAUDE.md`, `.claude/cold-cache/hooks/cold_cache.py` — the guard that stopped the morning prompt; its "way on" pricing and once-per-cold-spell logic.
- `.claude/context-budget/CLAUDE.md` — the per-operator `auto-relay/<handle>` opt-in pattern a keepalive opt-in would mirror.
- `.claude/costs/prices.json`, `.claude/costs/lib/restart.py` — cache rates and TTL detection.
- CLAUDE.md § "Key principles" — the `run_in_background` ban a keepalive needs an exception to.
- Predecessor transcript: https://claude.ai/code/session_01DwfPjCkcuxrKzaestJzFQU

## 8. Next step

No to-be first message was given. The operator's latest words: «здесь ещё есть о чём поговорить» — continue the discussion. Wait for the operator; do not start implementing (no «делай» given).
