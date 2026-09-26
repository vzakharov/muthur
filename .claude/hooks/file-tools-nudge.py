#!/usr/bin/env python3
"""`PreToolUse` hook on `Bash`: deny the first command that edits or writes a
file through the shell, and let the identical command through when it comes
again in the same session. Reads pass: they leave nothing to review.

CLAUDE.md § "Key principles" asks for `Edit`/`Write` in every permission mode,
while the harness's own prompt, in some modes, says the shell is fine. One
refusal at the moment of the call is the reminder; running the same command
again is the agent saying it means it, which keeps a mass substitution across
dozens of files one retry away.

Fails open: a command that cannot be tokenised, a payload that cannot be read or
a refusal that cannot be recorded is allowed, since an unrecorded refusal would
refuse the retry too.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Iterator, Optional

PUNCTUATION = "();<>|&\n"
HEREDOC = re.compile(r"<<(?!<)-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
NOT_FILES = ("/dev/", "/proc/", "/sys/")

# Commands that run the next word as a command, and the options of theirs that
# take the following word as their argument.
WRAPPERS = {
    "command": set(),
    "env": {"-u", "-C", "-S"},
    "nice": {"-n"},
    "nohup": set(),
    "sudo": {"-u", "-g", "-C", "-D", "-h", "-p", "-U"},
    "time": set(),
    "timeout": {"-k", "-s"},
    "xargs": {"-a", "-d", "-E", "-I", "-L", "-n", "-P", "-s"},
}
TOOL = {"edit": "`Edit`", "write": "`Write` (or `Edit`)"}
VERB = {"edit": "edits a file in place", "write": "writes a file"}


def strip_heredocs(command: str) -> str:
    # A heredoc body is data, and routinely carries an apostrophe that would
    # leave `shlex` with an unterminated quote.
    kept: list[str] = []
    pending: list[str] = []
    for line in command.split("\n"):
        if pending:
            if line.strip() == pending[0]:
                pending.pop(0)
            continue
        kept.append(line)
        pending = [m.group(2) for m in HEREDOC.finditer(line)]
    return "\n".join(kept)


def tokens(command: str) -> list[str]:
    lexer = shlex.shlex(strip_heredocs(command), posix=True, punctuation_chars=PUNCTUATION)
    lexer.whitespace = " \t\r"
    return list(lexer)


def is_punctuation(token: str) -> bool:
    return bool(token) and all(c in PUNCTUATION for c in token)


class Simple:
    """One simple command: its words, and the files it redirects output into."""

    def __init__(self) -> None:
        self.words: list[str] = []
        self.outputs: list[str] = []


def simple_commands(toks: list[str]) -> Iterator[Simple]:
    current = Simple()
    i = 0
    while i < len(toks):
        token = toks[i]
        if token == "$" or not is_punctuation(token):
            if token != "$":
                current.words.append(token)
        elif "<" in token or ">" in token:
            target = toks[i + 1] if i + 1 < len(toks) else ""
            i += 1
            if ">" in token and not token.endswith("&"):
                current.outputs.append(target)
        else:
            yield current
            current = Simple()
        i += 1
    yield current


def is_file(word: str) -> bool:
    # A bare number is the fd of a split `2>` redirection, never a file anyone named.
    return (
        bool(word)
        and not word.startswith("-")
        and not word.isdigit()
        and not word.startswith(NOT_FILES)
    )


def unwrap(name: str, args: list[str]) -> list[str]:
    takes_argument = WRAPPERS[name]
    i = 0
    while i < len(args) and (args[i].startswith("-") or ASSIGNMENT.match(args[i])):
        i += 2 if args[i] in takes_argument else 1
    if name == "timeout" and i < len(args):
        i += 1
    return args[i:]


def in_place(args: list[str], argument_flags: str, options_end_at_operand: bool) -> bool:
    """Whether a `-i` sits among the short-option clusters, stopping each cluster
    at the first flag that takes the rest of it as its argument."""
    for arg in args:
        if arg == "--":
            return False
        if not arg.startswith("-") or arg == "-":
            if options_end_at_operand:
                return False
        elif arg.startswith("--"):
            if arg.startswith("--in-place"):
                return True
        else:
            for c in arg[1:]:
                if c == "i":
                    return True
                if c in argument_flags:
                    break
    return False


def classify(words: list[str], outputs: list[str]) -> Optional[tuple[str, str]]:
    """The kind of file change and the command making it, or None."""
    while words and ASSIGNMENT.match(words[0]):
        words = words[1:]
    if not words:
        return None
    name, args = os.path.basename(words[0]), words[1:]
    writes_a_file = any(is_file(f) for f in outputs)

    if name in WRAPPERS:
        return classify(unwrap(name, args), outputs)
    if name == "find":
        for start, word in enumerate(args):
            if word in ("-exec", "-execdir", "-ok", "-okdir"):
                segment = args[start + 1 :]
                end = next((j for j, w in enumerate(segment) if w in (";", "+")), len(segment))
                found = classify(segment[:end], [])
                if found:
                    return found
        return None
    if name in ("sed", "gsed"):
        # GNU sed takes options after the script and files too.
        return ("edit", f"{name} -i") if in_place(args, "efl", False) else None
    if name in ("perl", "ruby"):
        return ("edit", f"{name} -i") if in_place(args, "eEMmIdDx", True) else None
    if name in ("awk", "gawk"):
        for i, arg in enumerate(args):
            if arg in ("-i", "--include") and args[i + 1 : i + 2] == ["inplace"]:
                return "edit", f"{name} -i inplace"
            if arg in ("-iinplace", "--include=inplace"):
                return "edit", f"{name} -i inplace"
        return None
    if name in ("cat", "echo", "printf"):
        return ("write", f"{name} >") if writes_a_file else None
    if name == "tee":
        return ("write", name) if any(is_file(a) for a in args) else None
    return None


def detect(command: str) -> Optional[tuple[str, str]]:
    for simple in simple_commands(tokens(command)):
        found = classify(simple.words, simple.outputs)
        if found:
            return found
    return None


def reason(kind: str, via: str) -> str:
    return (
        "Did you forget? CLAUDE.md § \"Key principles\" asks for the Edit/Write tools "
        "to change files in every permission mode, and it outranks any harness text "
        f"saying the shell is fine. This command {VERB[kind]} with `{via}`: use "
        f"{TOOL[kind]} instead. If the shell is genuinely the better tool here — one "
        "mechanical substitution across dozens of files, say — run the identical "
        "command again and it goes through."
    )


def say(message: str) -> None:
    print(f"file-tools-nudge: {message}", file=sys.stderr)


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
        command = payload["tool_input"]["command"]
        session = payload["session_id"]
    except (ValueError, KeyError, TypeError):
        say("unreadable payload; command allowed.")
        return 0
    if payload.get("tool_name") != "Bash" or not isinstance(command, str):
        return 0
    if not isinstance(session, str) or not session or "/" in session or session.startswith("."):
        return 0

    try:
        found = detect(command)
    except ValueError:
        return 0
    if found is None:
        return 0

    root = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ""
    if not root or not Path(root).is_dir():
        return 0
    state = Path(root) / "tmp" / "file-tools-nudge" / session
    digest = hashlib.sha256(command.encode()).hexdigest()
    try:
        if state.is_file() and digest in state.read_text().split():
            return 0
        state.parent.mkdir(parents=True, exist_ok=True)
        with state.open("a") as f:
            f.write(digest + "\n")
    except OSError as error:
        say(f"cannot record the refusal in {state} ({error}); command allowed.")
        return 0

    kind, via = found
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason(kind, via),
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
