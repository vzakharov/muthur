"""A Bash command split into the simple commands it runs, for the `PreToolUse`
hooks that judge a command by the programs in it.

Approximate by design: `shlex` with shell punctuation, heredoc bodies dropped,
and only as much of the grammar as tells one simple command from the next and
whether its output feeds another command. A command it cannot tokenise raises
`ValueError`, which its callers take as a reason to let the command through.
"""

from __future__ import annotations

import os
import re
import shlex
from typing import Iterator, Optional

PUNCTUATION = "();<>|&\n"
HEREDOC = re.compile(r"<<(?!<)-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

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
    """One simple command; `consumed` when its output feeds another command
    rather than the agent."""

    def __init__(self) -> None:
        self.words: list[str] = []
        self.outputs: list[str] = []
        self.inputs: list[str] = []
        self.consumed = False


def simple_commands(toks: list[str]) -> Iterator[Simple]:
    current = Simple()
    # One entry per open parenthesis: whether it opened a `$(…)`.
    substitutions: list[bool] = []
    previous = ""
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
            elif token == "<":
                current.inputs.append(target)
        else:
            current.consumed = any(substitutions) or token.strip("()") in ("|", "|&")
            yield current
            current = Simple()
            for c in token:
                if c == "(":
                    substitutions.append(previous.endswith("$"))
                elif c == ")" and substitutions:
                    substitutions.pop()
        previous = token
        i += 1
    current.consumed = any(substitutions)
    yield current


def unwrap(name: str, args: list[str]) -> list[str]:
    takes_argument = WRAPPERS[name]
    i = 0
    while i < len(args) and (args[i].startswith("-") or ASSIGNMENT.match(args[i])):
        i += 2 if args[i] in takes_argument else 1
    if name == "timeout" and i < len(args):
        i += 1
    return args[i:]


def program(words: list[str]) -> Optional[tuple[str, list[str]]]:
    """The program a simple command runs and its arguments, past any leading
    variable assignments, or None when there is no program."""
    while words and ASSIGNMENT.match(words[0]):
        words = words[1:]
    return (os.path.basename(words[0]), words[1:]) if words else None
