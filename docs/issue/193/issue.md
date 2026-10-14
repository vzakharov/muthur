# Issue #193: Keepalive: give the renewal-line example in English

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/193
- **Author:** @vzakharov (agent)
- **Created:** 2026-10-14T07:50:05Z
- **Updated:** 2026-10-14T07:50:05Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

An adopter's agent read the keepalive hook and reported "one of its prompts is in Russian" as a reason the hook carries muthur's own setup. The behavior is language-neutral: the renewal instruction says to reply "in the conversation's language". But the only example it gives of that reply is Russian (`.claude/keepalive/hooks/keepalive.py`, lines 176–177):

```
(e.g. «🕯 кеш продлён {spent}/{renewals} · скажи «запаркуй», чтобы зафиксировать и не продлевать, или «стоп», чтобы просто остановить»)
```

The example should be in English (`🕯 cache extended {spent}/{renewals} · say "park" to record it and stop extending, or "stop" to just stop`), like every other example in a source that ships in English. The Russian trigger words next to English ones (`"стоп", "stop"`, `"запаркуй", "park it"`) are fine as they are: they demonstrate "in any words", the same pattern `/finalize` and `/relay` use.

---

