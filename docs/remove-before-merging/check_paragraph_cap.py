#!/usr/bin/env python3
"""Prototype: flag Markdown prose blocks longer than N physical lines.

Relies on the file already being prettier-formatted (check-markdown-wrap holds
that), so blocks are separated by blank lines and list items start at a marker.
Stdlib only.
"""

import re
import sys

MARKER = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
SKIP_LINE = re.compile(r"^\s*(#{1,6}\s|>|\||<)")


def blocks(lines):
    """Yield (start_line, length) for each paragraph or list item's own text."""
    fence = None
    start, length = None, 0
    in_front = bool(lines) and lines[0].strip() == "---"
    in_comment = False

    def flush():
        nonlocal start, length
        if start is not None:
            yield start, length
        start, length = None, 0

    for n, line in enumerate(lines, 1):
        if in_front:
            if n > 1 and line.strip() == "---":
                in_front = False
            continue
        if in_comment:
            in_comment = "-->" not in line
            continue
        m = FENCE.match(line)
        if m:
            run = m.group(1)
            if fence is None:
                yield from flush()
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        if line.lstrip().startswith("<!--"):
            yield from flush()
            in_comment = "-->" not in line
            continue
        if not line.strip() or SKIP_LINE.match(line):
            yield from flush()
            continue
        if MARKER.match(line):
            yield from flush()
        if start is None:
            start = n
        length += 1
    yield from flush()


def main():
    cap = int(sys.argv[1])
    over = 0
    for path in sys.argv[2:]:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
        for start, length in blocks(lines):
            if length > cap:
                over += 1
                print(f"{path}:{start}: {length} lines")
    print(f"{over} block(s) over {cap} lines", file=sys.stderr)
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
