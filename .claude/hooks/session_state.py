"""Where a Python hook keeps per-session state: `tmp/<hook>/<session_id>` under
the project root.

The session id becomes a file name, so one that could name a path elsewhere — a
`/` in it, or a leading `.` — gets no state file, and the hook stays out of the
turn rather than writing outside its directory.
"""

from __future__ import annotations

import hashlib
import os
import sys
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


def first_sighting(state: Path, call: str) -> bool:
    """Whether `call` is new to the session's `state` file, recording it when it
    is — the record behind a hook that refuses a call once and lets the identical
    retry through. A record that cannot be read or written counts as a repeat,
    said on stderr, since an unrecorded refusal would refuse the retry too."""
    digest = hashlib.sha256(call.encode()).hexdigest()
    try:
        if state.is_file() and digest in state.read_text().split():
            return False
        state.parent.mkdir(parents=True, exist_ok=True)
        with state.open("a") as f:
            f.write(digest + "\n")
    except OSError as error:
        print(
            f"{state.parent.name}: cannot record the refusal in {state} ({error}); call allowed.",
            file=sys.stderr,
        )
        return False
    return True
