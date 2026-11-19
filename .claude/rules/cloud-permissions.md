---
description: A permission added to the project's settings files does not reliably reach a cloud session; the environment setup script is the route there
paths:
  - .claude/settings.json
  - .claude/settings.local.json
---

# Approving an action for cloud sessions

**A rule in this file is not how a cloud session gets an approval.** Both files
are project settings, part of the clone, and what reaches a cloud session from
them is narrow:

- **`autoMode` is never read from them**, on any surface — the classifier reads
  it from user and managed settings only, so a checked-in repo cannot approve
  its own actions ([docs](https://code.claude.com/docs/en/auto-mode-config)). An
  `autoMode` entry here is dead text.
- **`permissions.allow` applies only in a single-repository session outside a
  project**; a multi-repository session or a project thread reads none of the
  file's permission rules, hooks or `env`
  ([docs](https://code.claude.com/docs/en/settings)). Even where it applies,
  auto mode keeps only narrow rules, dropping broad ones such as `Bash(*)`.
- **Observed beyond the docs:** in a cloud auto-mode session, a run spelled
  exactly as a narrow project `allow` rule was still denied by the classifier
  ([muthur#239](https://github.com/vzakharov/muthur/pull/239)). The docs say
  that rule should hold; which case that session was in is not on record, so the
  gap is unexplained rather than ruled out.

So a project `allow` rule is worth keeping for local sessions, and is never the
whole answer for cloud ones.

**The route that does reach a cloud session is an `autoMode.allow` entry in the
container's `~/.claude/settings.json`, written by the environment setup
script.** Only the operator can change that script — it lives in the
environment's settings, with no API or file behind it — so the agent's part is:

1. **Narrow what is approved to a fixed command**, usually a script under
   `scripts/` that refuses any other use, since the entry is prose the
   classifier weighs against the command's text. `scripts/pr-comment.sh`'s
   header is the pattern: both approvals, which sessions each reaches, what a
   denial on the web means.
2. **Add the entry to the worked example** in `docs/adopting/web-remote.md` § "A
   worked example", beside the ones it carries, so the text the operator pastes
   lives in the repo and is reviewed with the change that needs it.
3. **Hand the operator the entry in the report**: the exact text, fenced, and
   that it goes into the setup script's `autoMode.allow` list. Where it goes in
   the UI, and how to check it landed (`claude auto-mode config`), are that
   doc's § "Hand the operator a setup script" — point at it rather than
   restating it. It reaches only sessions whose container is built after the
   edit.
