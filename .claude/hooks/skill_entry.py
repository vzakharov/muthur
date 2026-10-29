"""Which skill a hook payload enters, for hooks that act when a skill's body
arrives. It arrives three ways, each its own registration in
`.claude/settings.json`:

- `PostToolUse` on `Skill`, naming it;
- `PostToolUse` on `Read` of `.claude/skills/<name>/SKILL.md` — how one skill
  reaches another;
- `UserPromptSubmit` opening with `/<name>`, since a typed slash command expands
  without any tool call.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

TYPED = re.compile(r"^\s*/([\w-]+)(\s|$)")
SKILLS_DIR = Path(".claude") / "skills"


def entered_skill(payload: dict, root: Path) -> Optional[str]:
    event = payload.get("hook_event_name")
    if event == "UserPromptSubmit":
        prompt = payload.get("prompt")
        match = TYPED.match(prompt) if isinstance(prompt, str) else None
        return match.group(1) if match else None
    if event != "PostToolUse":
        return None
    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    if tool == "Skill":
        skill = tool_input.get("skill")
        return skill.lstrip("/") if isinstance(skill, str) else None
    if tool == "Read":
        path = tool_input.get("file_path")
        if not isinstance(path, str):
            return None
        resolved = Path(path).resolve()
        if resolved.name != "SKILL.md" or resolved.parent.parent != (root / SKILLS_DIR).resolve():
            return None
        return resolved.parent.name
    return None
