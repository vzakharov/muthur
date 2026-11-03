#!/usr/bin/env python3
"""Refuse `/finalize` in a session whose bash is older than 4, and tell the
agent to run it in a new cloud session instead.

The scripts `/finalize` runs use bash 4 features (`mapfile` among them) and
name `/bin/bash` or the `bash` on `PATH` in their shebangs, so both must be 4 or
newer; macOS ships 3.2 at `/bin/bash`, which no Homebrew bash replaces. Written
in Python because the hook has to run exactly where bash cannot be trusted.

On `PreToolUse` of a `Skill` or `Read` entering `/finalize` it denies the call,
so the skill's body never loads. A typed `/finalize` expands with no tool call
to deny, so on `UserPromptSubmit` the same instruction goes in as context,
telling the agent to set the body aside.

`finalize-bash-gate.py check`, with no payload, runs the check alone for a
harness without hooks: it prints the instruction and exits 1 where the run
would be refused. Fails open on an unreadable payload: stderr and exit 0.
"""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Optional, Sequence

from session_state import project_root
from skill_entry import entering_skill

SKILL = "finalize"
SHELLS = ("/bin/bash", "bash")

INSTRUCTION = """\
/finalize does not run in this session: {why}. The scripts it runs need bash 4 \
at both `/bin/bash` and the `bash` on `PATH`, since their shebangs name one or \
the other. Run it in a new cloud session instead, and none of it here:

1. The cloud session clones the branch from GitHub, not this checkout. \
Uncommitted changes → stop and ask the operator what becomes of them; unpushed \
commits → `git push -u origin HEAD`.
2. Start it on the argument this /finalize was given, the current branch put \
first when that names no target: `claude --cloud "/finalize <branch> <the \
rest>"` from the checkout — or, with `create_session` from the Claude Code \
Remote tools, the way `.claude/skills/relay/SKILL.md` § "Step 3 — Start the \
successor" starts one on the web.
3. Report the session's link and stop."""

TYPED_SUFFIX = (
    "\n\nThe /finalize body in this prompt expanded before this check could stop "
    "it: set it aside, and follow the steps above instead."
)


def say(message: str) -> None:
    print(f"finalize-bash-gate: {message}", file=sys.stderr)


def why_refused(shells: Sequence[str] = SHELLS) -> Optional[str]:
    """What rules this machine's bash out, or None when every shell is bash 4+."""
    for shell in shells:
        try:
            result = subprocess.run(
                [shell, "-c", 'printf %s "$BASH_VERSION"'],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            return f"`{shell}` does not run ({error})"
        version = result.stdout.strip()
        major = version.split(".", 1)[0]
        if result.returncode != 0 or not major.isdigit():
            return f"`{shell}` is not bash (it printed no `$BASH_VERSION`)"
        if int(major) < 4:
            return f"`{shell}` is bash {version}"
    return None


def emit(event: str, why: str) -> None:
    text = INSTRUCTION.format(why=why)
    if event == "PreToolUse":
        output = {
            "hookEventName": event,
            "permissionDecision": "deny",
            "permissionDecisionReason": text,
        }
    else:
        output = {"hookEventName": event, "additionalContext": text + TYPED_SUFFIX}
    json.dump({"hookSpecificOutput": output}, sys.stdout)


def hook() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except ValueError:
        say("unreadable payload; /finalize not checked.")
        return 0
    if not isinstance(payload, dict):
        return 0
    root = project_root(payload)
    if root is None or entering_skill(payload, root) != SKILL:
        return 0
    why = why_refused()
    if why is not None:
        emit(payload["hook_event_name"], why)
    return 0


def check() -> int:
    why = why_refused()
    if why is None:
        return 0
    print(INSTRUCTION.format(why=why))
    return 1


def main(argv: Sequence[str]) -> int:
    if list(argv) == ["check"]:
        return check()
    if argv:
        say(f"unknown arguments {list(argv)}; the one argument is `check`.")
        return 2
    return hook()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
