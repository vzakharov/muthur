"""The repositories a Claude Code session has attached.

A cloud session with one repository starts in its clone; one with several starts
in their common parent (`/home/user`), with a clone per repository beneath it,
and loads none of their hooks. Everything that has to tell the two apart, or
enumerate the clones, asks here, so the hook generator and the target resolver
never disagree about which repositories a session holds.

Outside a cloud session (`$CLAUDE_CODE_REMOTE` unset) a session is always the one
repository the calling script lives in: a developer's `~/code` holding many
clones is not a multi-repo session, and treating it as one would write settings
into a directory nobody asked us to touch.

Imported as `from lib.session import Session`; see `lib/github.py` for why that
resolves from any working directory.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def is_work_tree(path: Path) -> bool:
    # `.git` is a directory in a clone and a file in a linked worktree.
    return (path / ".git").exists()


@dataclass(frozen=True)
class Session:
    root: Path
    repos: tuple[Path, ...]

    @property
    def multi_repo(self) -> bool:
        return len(self.repos) > 1

    @property
    def names(self) -> str:
        return ", ".join(r.name for r in self.repos)

    @classmethod
    def detect(cls, anchor: Path) -> Session:
        """The session around `anchor`, the repository the calling script lives in.

        The root is `$CLAUDE_PROJECT_DIR` when the caller is a hook, which
        Claude Code runs with it set; a Bash tool call has it unset, and then
        the root is the anchor's parent — where a cloud session puts every clone.
        """
        anchor = anchor.resolve()
        if os.environ.get("CLAUDE_CODE_REMOTE") != "true":
            return cls(anchor, (anchor,))
        env_root = os.environ.get("CLAUDE_PROJECT_DIR")
        root = Path(env_root).resolve() if env_root else anchor.parent
        if is_work_tree(root):
            return cls(root, (root,))
        repos = tuple(
            sorted(p for p in root.iterdir() if p.is_dir() and is_work_tree(p))
        )
        return cls(root, repos or (anchor,))

    def repo_named(self, name: str) -> Path:
        """The attached repo whose directory is `name` — how `--primary` arrives."""
        for repo in self.repos:
            if repo.name == name or str(repo) == name:
                return repo
        raise ValueError(
            f"no attached repository named {name!r}; attached: {self.names}"
        )
