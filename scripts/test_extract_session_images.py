#!/usr/bin/env python3
"""Tests for which transcript records `extract-session-images.py` writes out.

The records are built to the shapes Claude Code writes, since the shape is the
client's and undocumented: an image sent with a prompt that starts a turn, and
one sent while a turn was running.

Run by path, as `scripts/check-muthur.sh` does — see the note there on why never
through `unittest discover`.
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "extract-session-images.py"

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


def image_block(data: bytes) -> dict:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": base64.b64encode(data).decode(),
        },
    }


def prompt_record(data: bytes, **extra: object) -> dict:
    return {
        "type": "user",
        "uuid": "aaaaaaaa-0000-0000-0000-000000000000",
        "timestamp": "2026-10-09T14:00:00.000Z",
        "gitBranch": "feature",
        "origin": {"kind": "human"},
        "message": {
            "role": "user",
            "content": [{"type": "text", "text": "the cover"}, image_block(data)],
        },
        **extra,
    }


def mid_turn_record(prompt: object, origin: str = "human") -> dict:
    return {
        "type": "attachment",
        "uuid": "bbbbbbbb-0000-0000-0000-000000000000",
        "timestamp": "2026-10-09T14:05:00.000Z",
        "gitBranch": "feature",
        "attachment": {
            "type": "queued_command",
            "prompt": prompt,
            "commandMode": "prompt",
            "origin": {"kind": origin},
            "timestamp": "2026-10-09T14:04:59.000Z",
        },
    }


class ExtractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp())
        self.out = self.dir / "out"

    def extract(self, *records: dict) -> list[str]:
        transcript = self.dir / "session.jsonl"
        transcript.write_text("".join(json.dumps(r) + "\n" for r in records))
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(transcript), "--out", str(self.out)],
            capture_output=True,
            text=True,
            check=True,
        )
        return [Path(line).name for line in result.stdout.splitlines()]

    def test_prompt_image(self) -> None:
        self.assertEqual(self.extract(prompt_record(PNG)), ["20261009T140000Z-aaaaaaaa.png"])

    def test_mid_turn_image(self) -> None:
        record = mid_turn_record([{"type": "text", "text": "here"}, image_block(PNG + b"1")])
        self.assertEqual(self.extract(record), ["20261009T140459Z-bbbbbbbb.png"])
        self.assertIn("| here |", (self.out / "index.md").read_text())

    def test_mid_turn_text_only(self) -> None:
        self.assertEqual(self.extract(mid_turn_record("just text")), [])

    def test_mid_turn_not_from_the_operator(self) -> None:
        record = mid_turn_record([image_block(PNG)], origin="task-notification")
        self.assertEqual(self.extract(record), [])

    def test_sidechain(self) -> None:
        self.assertEqual(self.extract(prompt_record(PNG, isSidechain=True)), [])

    def test_same_image_twice_is_written_once(self) -> None:
        written = self.extract(prompt_record(PNG), mid_turn_record([image_block(PNG)]))
        self.assertEqual(len(written), 1)
        self.assertEqual(self.extract(prompt_record(PNG)), [])


if __name__ == "__main__":
    unittest.main()
