#!/usr/bin/env python3
"""UserPromptSubmit probe: block the first prompt of each session, let every
later one through, and log each event to tmp/cache-guard/ so what the client
sent is inspectable afterwards. Blocking every prompt would lock the session."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE = Path(__file__).resolve().parents[2] / "tmp" / "cache-guard"
STATE.mkdir(parents=True, exist_ok=True)

event = json.load(sys.stdin)
with (STATE / "probe-events.jsonl").open("a", encoding="utf-8") as log:
    log.write(json.dumps({"at": datetime.now(timezone.utc).isoformat(), **event}, ensure_ascii=False) + "\n")

STOP_WORD = "!pass"

marker = STATE / f"{event['session_id']}.blocked-once"
if STOP_WORD not in event.get("prompt", "") and not marker.exists():
    marker.touch()
    print(json.dumps({
        "decision": "block",
        "reason": f"cache-guard probe: this prompt was blocked on purpose. Send anything again and it goes through; a prompt containing {STOP_WORD} always does.",
    }))
