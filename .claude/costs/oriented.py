#!/usr/bin/env python3
"""Mark the end of a session's orientation, or check for the mark.

Usage:
  python3 .claude/costs/oriented.py
  python3 .claude/costs/oriented.py check <transcript>

Run bare, it records nothing itself: the Bash call that ran it, in the
transcript, is the mark, and the ledger reads it there. `check` prints `marked`
or `unmarked` for the stretch since the transcript's latest compaction, so that
`hooks/estimate-notice.sh` asks for a mark only where there is none.
`.claude/costs/CLAUDE.md` § "Orientation" carries what the mark ends.

Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import sys
from pathlib import Path

from lib.orientation import marked
from lib.shape import ShapeError


def main(argv: list[str]) -> int:
    if not argv:
        print("Orientation marked: the ledger ends this phase here.")
        return 0
    if len(argv) == 2 and argv[0] == "check":
        path = Path(argv[1])
        try:
            found = marked(path.read_text(encoding="utf-8"), str(path))
        except (OSError, ShapeError) as error:
            print(f"oriented.py: {error}", file=sys.stderr)
            return 1
        print("marked" if found else "unmarked")
        return 0
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
