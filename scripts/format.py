#!/usr/bin/env python3
"""Format each file an agent edits, and check every tracked one, by the list in
`.claude/format.json`.

    format.py hook    PostToolUse on Edit|Write|MultiEdit: format the file the
                      tool just touched, with every entry whose globs match it
    format.py check   vet: run each entry's check over the tracked files its
                      globs match

The list is the repo's own: an array of entries, each

    {"name": "markdown wrap",
     "files": ["*.md"],
     "format": ["scripts/prettier.sh", "--write"],
     "check": ["scripts/prettier.sh", "--check"]}

`files` are `fnmatch` globs against the repo-relative path, so `*` crosses `/`,
as in git's default pathspec. `format` and `check` are argv lists run from the
repo root with the file paths appended. Every matching entry runs, in list
order. No list means nothing to format, and both modes exit 0.

The hook formats what the check would check: a file inside the project that git
does not ignore. It exits 2 with the formatter's output when one fails, which
Claude Code shows the agent — an edit that went through unformatted in silence
would surface only at the vet run, far from the edit that caused it. A
malformed list fails both modes rather than turning formatting off.

The check reads a staged always-loaded file through its staged copy
(`scripts/staged.sh`), since that is the text the branch will land.
"""

from __future__ import annotations

import fnmatch
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

CONFIG = Path(".claude/format.json")
STAGED = Path("scripts/staged.sh")


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Entry:
    name: str
    files: List[str]
    format: List[str]
    check: List[str]

    def matches(self, rel: str) -> bool:
        return any(fnmatch.fnmatchcase(rel, pattern) for pattern in self.files)


def _strings(raw: dict, key: str, where: str) -> List[str]:
    value = raw.get(key)
    if not (isinstance(value, list) and value and all(isinstance(v, str) and v for v in value)):
        raise ConfigError(f"{where}: `{key}` must be a non-empty list of non-empty strings")
    return value


def load(root: Path) -> List[Entry]:
    path = root / CONFIG
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigError(f"{CONFIG} is not valid JSON: {error}") from error
    if not isinstance(raw, list):
        raise ConfigError(f"{CONFIG} must be an array of entries")
    entries = []
    for index, item in enumerate(raw):
        where = f"{CONFIG} entry {index}"
        if not isinstance(item, dict):
            raise ConfigError(f"{where} must be an object")
        unknown = set(item) - {"name", "files", "format", "check"}
        if unknown:
            raise ConfigError(f"{where}: unknown key(s) {', '.join(sorted(unknown))}")
        name = item.get("name")
        if not (isinstance(name, str) and name):
            raise ConfigError(f"{where}: `name` must be a non-empty string")
        entries.append(
            Entry(
                name=name,
                files=_strings(item, "files", where),
                format=_strings(item, "format", where),
                check=_strings(item, "check", where),
            )
        )
    return entries


def run(argv: List[str], root: Path) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(argv, cwd=root, capture_output=True, text=True)
    except OSError as error:
        return subprocess.CompletedProcess(argv, 127, "", f"{argv[0]}: {error}\n")


def output(result: subprocess.CompletedProcess) -> str:
    return (result.stdout + result.stderr).strip()


def ignored(rel: str, root: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", "--", rel], cwd=root).returncode == 0


def hook(root: Path, payload: dict) -> int:
    file_path = (payload.get("tool_input") or {}).get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return 0
    path = Path(file_path).resolve()
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return 0
    if not path.is_file() or ignored(rel, root):
        return 0
    failures = []
    for entry in load(root):
        if entry.matches(rel):
            result = run(entry.format + [str(path)], root)
            if result.returncode != 0:
                failures.append(f"{entry.name} could not format {path}:\n{output(result)}")
    if failures:
        print("\n\n".join(failures), file=sys.stderr)
        return 2
    return 0


def staged_copies(root: Path) -> dict:
    if not (root / STAGED).is_file():
        return {}
    listing = subprocess.run(
        [str(STAGED), "list"], cwd=root, capture_output=True, text=True, check=True
    ).stdout
    return dict(line.split("\t", 1) for line in listing.splitlines() if "\t" in line)


def check(root: Path) -> int:
    entries = load(root)
    tracked = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.split("\0")
    copies = staged_copies(root)
    failures = 0
    for entry in entries:
        matched = [rel for rel in tracked if rel and entry.matches(rel)]
        files = sorted({copies.get(rel, rel) for rel in matched if (root / rel).is_file()})
        if not files:
            continue
        result = run(entry.check + files, root)
        if result.returncode != 0:
            failures += 1
            print(f"format: {entry.name} — check failed:\n{output(result)}", file=sys.stderr)
    if failures:
        return 1
    print(f"format: OK — {len(entries)} entr{'y' if len(entries) == 1 else 'ies'}")
    return 0


def main(argv: List[str]) -> int:
    if argv not in (["hook"], ["check"]):
        print("usage: format.py hook|check", file=sys.stderr)
        return 2
    try:
        if argv == ["check"]:
            return check(Path(__file__).resolve().parent.parent)
        payload = json.load(sys.stdin)
        root: Optional[str] = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd")
        if not root or not Path(root).is_dir():
            return 0
        return hook(Path(root).resolve(), payload)
    except (ConfigError, json.JSONDecodeError) as error:
        print(f"format: {error}", file=sys.stderr)
        return 2 if argv == ["hook"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
