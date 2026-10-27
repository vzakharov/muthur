"""Where a Python hook keeps per-session state: `tmp/<hook>/<session_id>` under
the project root.

The session id becomes a file name, so one that could name a path elsewhere — a
`/` in it, or a leading `.` — gets no state file, and the hook stays out of the
turn rather than writing outside its directory.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def project_root(payload: dict) -> Optional[Path]:
    root = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd")
    if not isinstance(root, str) or not root or not Path(root).is_dir():
        return None
    return Path(root)


def state_file(root: Path, hook: str, payload: dict) -> Optional[Path]:
    session = payload.get("session_id")
    if not isinstance(session, str) or not session or "/" in session or session.startswith("."):
        return None
    return root / "tmp" / hook / session
