#!/usr/bin/env python3
"""Write operator-attached images out of a Claude Code session transcript.

Usage:
  python3 scripts/extract-session-images.py <transcript.jsonl> [--out DIR] [--verbose]

Each image goes to `tmp/session-images/` (overridable with `--out`), and a row
to `index.md` there carrying the prompt it arrived with — the text is what makes
the image legible to a session that was not present for it. `tmp/` is gitignored,
so an image reaches the repo only when someone puts it there deliberately.
`.claude/hooks/session-images.sh` is the caller, and carries why this runs
without being invoked.

Idempotent: filenames derive from the record's own timestamp and uuid, and the
manifest's SHA-256 column is the dedupe state, so a re-run over the same
transcript writes nothing and there is no second state file to drift.

Exit status is non-zero only when the transcript cannot be read or the output
directory cannot be written. A transcript holding no attachments is success.

`--verbose` reports what was seen and why each record was rejected. The record
shape belongs to the client and is not documented, so when it changes the filter
matches nothing and this exits 0 — that flag is how the silence is diagnosed.

Running this file as `python3 scripts/extract-session-images.py` puts `scripts/`
on `sys.path[0]`, so `lib.media` resolves as a PEP 420 namespace package from any
working directory — no `__init__.py`, no `sys.path` manipulation.

Stdlib only — no third-party deps. Python 3.9+.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterator, List, NamedTuple, NoReturn, Optional

from lib.media import extension_for_bytes

DEFAULT_OUT = Path("tmp") / "session-images"
MANIFEST_NAME = "index.md"
PROMPT_EXCERPT_CHARS = 200

MANIFEST_HEADER = """# Session images

Images the operator attached to a session, pulled out of the transcript by
`scripts/extract-session-images.py`. This directory is gitignored scratch space
that dies with the machine, so an image worth keeping moves into the repo proper
and is committed there.

| File | Captured (UTC) | Size | Branch | Prompt | SHA-256 |
| --- | --- | --- | --- | --- | --- |
"""

# Anchored at the row's end, which is what keeps a pipe inside the prompt excerpt
# from being read as a column boundary.
SHA_CELL_RE = re.compile(r"`([0-9a-f]{64})`\s*\|\s*$")


class Attachment(NamedTuple):
    data: bytes
    media_type: Optional[str]
    timestamp: str
    uuid: str
    branch: str
    prompt: str
    ordinal: int  # 1-based position among the images of its own record
    of: int  # how many images that record carried


def _die(message: str) -> NoReturn:
    print(f"extract-session-images: {message}", file=sys.stderr)
    raise SystemExit(1)


def _text_of(content: List[object]) -> str:
    parts = [
        block["text"]
        for block in content
        if isinstance(block, dict)
        and block.get("type") == "text"
        and isinstance(block.get("text"), str)
    ]
    return " ".join(" ".join(parts).split())


def _compact_timestamp(raw: str) -> str:
    """`2026-09-11T12:43:55.599Z` -> `20260911T124355Z`, unparseable -> `undated`."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})", raw or "")
    if not m:
        return "undated"
    return "{}{}{}T{}{}{}Z".format(*m.groups())


def _human_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def _cell(text: str) -> str:
    """Make text safe for one Markdown table cell."""
    return text.replace("|", "\\|") or "—"


def _human(origin: object) -> bool:
    return isinstance(origin, dict) and origin.get("kind") == "human"


def _operator_message(record: dict) -> Optional[tuple[List[object], str]]:
    """An operator's message as its content blocks and timestamp, or None.

    A prompt that starts a turn is a `user` record; one sent mid-turn is folded
    into the running turn as a `queued_command` attachment, whose `prompt` is a
    plain string when it carries no image.
    """
    if record.get("type") == "user":
        if not _human(record.get("origin")):
            return None
        content = record.get("message", {}).get("content")
        timestamp = record.get("timestamp")
    elif record.get("type") == "attachment":
        attachment = record.get("attachment")
        if not isinstance(attachment, dict):
            return None
        if attachment.get("type") != "queued_command":
            return None
        if not _human(attachment.get("origin")):
            return None
        content = attachment.get("prompt")
        timestamp = attachment.get("timestamp") or record.get("timestamp")
    else:
        return None
    if not isinstance(content, list):
        return None
    return content, str(timestamp or "")


def iter_attachments(transcript: Path, verbose: bool) -> Iterator[Attachment]:
    """Yield every operator-attached image in the transcript, in order.

    Three things look like one and are not, so the filter is narrower than
    "a record carrying an image": the agent's own `Read` of an image file
    also lands under `type: "user"`, but nests the image in a `tool_result` and
    carries no `origin` key — extracting those would re-commit files the repo
    already has. Subagent turns carry `isSidechain: true`. `queue-operation`
    records carry the prompt text but never the image data.
    """
    seen = matched = 0

    def rejected(why: str) -> None:
        if verbose:
            print(f"  line {seen}: {why}, skipped", file=sys.stderr)

    with transcript.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            seen += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                # A transcript is appended to while this reads it, so the last
                # line can be half-written. The next firing catches the record.
                rejected("unparseable")
                continue
            if not isinstance(record, dict):
                continue
            if record.get("isSidechain"):
                continue
            message = _operator_message(record)
            if message is None:
                continue
            content, timestamp = message

            images = [
                block
                for block in content
                if isinstance(block, dict) and block.get("type") == "image"
            ]
            if not images:
                continue

            prompt = _text_of(content)[:PROMPT_EXCERPT_CHARS]
            for ordinal, block in enumerate(images, start=1):
                source = block.get("source")
                if not isinstance(source, dict) or source.get("type") != "base64":
                    rejected("image source is not base64")
                    continue
                try:
                    data = base64.b64decode(source.get("data", ""), validate=True)
                except (binascii.Error, ValueError):
                    rejected("image data is not valid base64")
                    continue
                if not data:
                    continue
                matched += 1
                yield Attachment(
                    data=data,
                    media_type=source.get("media_type"),
                    timestamp=timestamp,
                    uuid=str(record.get("uuid") or ""),
                    branch=str(record.get("gitBranch") or ""),
                    prompt=prompt,
                    ordinal=ordinal,
                    of=len(images),
                )
    if verbose:
        print(
            f"extract-session-images: {seen} records read, {matched} attachments matched",
            file=sys.stderr,
        )


def known_hashes(manifest: Path) -> set[str]:
    if not manifest.exists():
        return set()
    found: set[str] = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        m = SHA_CELL_RE.search(line)
        if m:
            found.add(m.group(1))
    return found


def filename_for(attachment: Attachment, digest: str) -> str:
    stamp = _compact_timestamp(attachment.timestamp)
    tag = (attachment.uuid or digest)[:8]
    suffix = f"-{attachment.ordinal}" if attachment.of > 1 else ""
    ext = extension_for_bytes(attachment.data, attachment.media_type) or ".bin"
    return f"{stamp}-{tag}{suffix}{ext}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write operator-attached images out of a session transcript."
    )
    parser.add_argument("transcript", type=Path, help="path to the session .jsonl")
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"output directory (default: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="report what was read and what was rejected, on stderr",
    )
    args = parser.parse_args()

    transcript: Path = args.transcript
    if not transcript.is_file():
        _die(f"transcript not found: {transcript}")

    out: Path = args.out
    manifest = out / MANIFEST_NAME
    try:
        attachments = list(iter_attachments(transcript, args.verbose))
    except OSError as exc:
        _die(f"cannot read {transcript}: {exc}")

    if not attachments:
        return 0

    written = known_hashes(manifest)
    rows = []
    for attachment in attachments:
        digest = hashlib.sha256(attachment.data).hexdigest()
        if digest in written:
            continue
        written.add(digest)
        name = filename_for(attachment, digest)
        try:
            out.mkdir(parents=True, exist_ok=True)
            (out / name).write_bytes(attachment.data)
        except OSError as exc:
            _die(f"cannot write {out / name}: {exc}")
        rows.append(
            "| [{name}]({name}) | {stamp} | {size} | {branch} | {prompt} | `{digest}` |".format(
                name=name,
                stamp=_cell(attachment.timestamp),
                size=_human_size(len(attachment.data)),
                branch=_cell(attachment.branch),
                prompt=_cell(attachment.prompt),
                digest=digest,
            )
        )
        print(out / name)

    if not rows:
        return 0

    try:
        with manifest.open("a", encoding="utf-8") as fh:
            if manifest.stat().st_size == 0:
                fh.write(MANIFEST_HEADER)
            fh.write("\n".join(rows) + "\n")
    except OSError as exc:
        _die(f"cannot write {manifest}: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
