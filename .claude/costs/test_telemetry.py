#!/usr/bin/env python3
"""Posts an OTLP/HTTP-JSON payload to the telemetry receiver, as Claude Code's
exporter does, and reads back what reached disk. What it protects is the
filter: the numbers and the few named fields kept, the account's email and ids
never written.

The payload follows the shape Claude Code documents for its `api_request`
event, counts sent as strings, rather than one a session recorded.

Run by path (`python3 .claude/costs/test_telemetry.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `hooks`.
"""

from __future__ import annotations

import contextlib
import gzip
import io
import json
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

from hooks.telemetry_receiver import serve

SESSION = "36e8edad-f0fb-5cea-8fa6-d7453a2cd5cb"


def attribute(key: str, value: Any) -> Dict[str, Any]:
    if isinstance(value, int):
        return {"key": key, "value": {"intValue": str(value)}}
    return {"key": key, "value": {"stringValue": value}}


def event(name: str, **attributes: Any) -> Dict[str, Any]:
    identity = {
        "session.id": SESSION,
        "user.email": "someone@example.com",
        "user.account_uuid": "0b3c5a8e-1f2d-4e6a-9b7c-2d4e6f8a0b1c",
        "user.id": "5f1d7e8c9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d",
        "organization.id": "a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6",
        "prompt.id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "terminal.type": "non-interactive",
    }
    return {
        "timeUnixNano": "1790380800000000000",
        "body": {"stringValue": f"claude_code.{name}"},
        "attributes": [
            attribute(key, value)
            for key, value in {
                **identity,
                "event.name": name,
                "event.timestamp": "2026-09-26T00:00:00.000Z",
                "event.sequence": 12,
                **attributes,
            }.items()
        ],
    }


PAYLOAD = {
    "resourceLogs": [
        {
            "resource": {"attributes": [attribute("service.name", "claude-code")]},
            "scopeLogs": [
                {
                    "scope": {"name": "com.anthropic.claude_code.events"},
                    "logRecords": [
                        event(
                            "api_request",
                            model="claude-opus-5-5",
                            cost_usd="0.2213",
                            duration_ms="5231",
                            input_tokens="3",
                            output_tokens="1200",
                            cache_read_tokens="229000",
                            cache_creation_tokens="1040",
                            request_id="req_011CaBcDeFgHiJkLmNoPqRsT",
                            speed="normal",
                            query_source="compact",
                        ),
                        event("user_prompt", prompt_length="42"),
                    ],
                }
            ],
        }
    ]
}


class WhatTheReceiverKeeps(unittest.TestCase):
    def setUp(self) -> None:
        base = tempfile.TemporaryDirectory()
        self.addCleanup(base.cleanup)
        self.out = Path(base.name)
        self.server = serve(self.out, 0)
        self.addCleanup(self.server.server_close)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.shutdown)

    def post(self, body: bytes, path: str = "/v1/logs", **headers: str) -> int:
        port = self.server.server_address[1]
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}{path}",
            data=body,
            headers={"Content-Type": "application/json", **headers},
        )
        # No proxy: the exporter reaches the receiver directly, and so does this.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(request) as reply:
                return int(reply.status)
        except urllib.error.HTTPError as error:
            return error.code

    def written(self) -> List[Dict[str, Any]]:
        lines = (self.out / f"{SESSION}.jsonl").read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines]

    def test_keeps_the_numbers_and_named_fields_of_an_api_request_only(self) -> None:
        self.assertEqual(self.post(json.dumps(PAYLOAD).encode()), 200)
        self.assertEqual(
            self.written(),
            [
                {
                    "timestamp": "2026-09-26T00:00:00.000Z",
                    "model": "claude-opus-5-5",
                    "request_id": "req_011CaBcDeFgHiJkLmNoPqRsT",
                    "speed": "normal",
                    "query_source": "compact",
                    "cost_usd": 0.2213,
                    "duration_ms": 5231,
                    "input_tokens": 3,
                    "output_tokens": 1200,
                    "cache_read_tokens": 229000,
                    "cache_creation_tokens": 1040,
                    "event.sequence": 12,
                }
            ],
        )

    def test_reads_a_gzipped_body(self) -> None:
        body = gzip.compress(json.dumps(PAYLOAD).encode())
        self.assertEqual(self.post(body, **{"Content-Encoding": "gzip"}), 200)
        self.assertEqual(len(self.written()), 1)

    def test_appends_across_exports(self) -> None:
        self.post(json.dumps(PAYLOAD).encode())
        self.post(json.dumps(PAYLOAD).encode())
        self.assertEqual(len(self.written()), 2)

    def test_refuses_a_body_that_is_not_json(self) -> None:
        # The receiver logs the refusal, which is its job and this test's noise.
        with contextlib.redirect_stderr(io.StringIO()) as logged:
            self.assertEqual(self.post(b"not json"), 400)
        self.assertIn("not JSON", logged.getvalue())
        self.assertEqual(list(self.out.iterdir()), [])

    def test_answers_nothing_but_logs(self) -> None:
        self.assertEqual(self.post(b"{}", path="/v1/metrics"), 404)


HOOK = Path(__file__).resolve().parent / "hooks" / "start-telemetry-receiver.sh"
EXPORT = {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://127.0.0.1:4318",
}


class WhenTheHookStartsTheReceiver(unittest.TestCase):
    """Over a `python3` stub that records its arguments, so no test binds the
    receiver's port, and under a shell named `claude` that holds the exporter's
    variables and strips `OTEL_*` from the hook, as Claude Code does."""

    def setUp(self) -> None:
        base = tempfile.TemporaryDirectory()
        self.addCleanup(base.cleanup)
        self.root = Path(base.name) / "repo"
        self.root.mkdir()
        stubs = Path(base.name) / "bin"
        stubs.mkdir()
        self.started = Path(base.name) / "started"
        stub = stubs / "python3"
        stub.write_text(f'#!/bin/sh\necho "$@" > {self.started}\n')
        stub.chmod(0o755)
        self.claude = stubs / "claude"
        self.claude.symlink_to(shutil.which("bash") or "/bin/bash")
        self.path = f"{stubs}:{os.environ['PATH']}"

    def run_hook(self, **env: str) -> str:
        inherited = {
            k: v
            for k, v in os.environ.items()
            if not (k.startswith("OTEL_") or k == "CLAUDE_CODE_ENABLE_TELEMETRY")
        }
        # The trailing `:` keeps `claude` from exec'ing into the hook, which
        # would leave it no such ancestor.
        strip_otel = 'env $(env | sed -n "s/^\\(OTEL_[A-Z_]*\\)=.*/-u \\1/p") bash "$0"; :'
        ran = subprocess.run(
            [str(self.claude), "-c", strip_otel, str(HOOK)],
            input="{}",
            capture_output=True,
            text=True,
            check=True,
            env={**inherited, "PATH": self.path, "CLAUDE_PROJECT_DIR": str(self.root), **env},
        )
        return ran.stdout

    def test_names_what_to_set_and_starts_nothing_when_the_variables_are_unset(self) -> None:
        notice = self.run_hook(**{**EXPORT, "OTEL_EXPORTER_OTLP_ENDPOINT": "http://collector:4318"})
        self.assertIn("listens for: OTEL_EXPORTER_OTLP_ENDPOINT.", notice)
        for name, value in EXPORT.items():
            self.assertIn(f"    {name}={value}\n", notice)
        time.sleep(0.2)
        self.assertFalse(self.started.exists())

    def test_starts_the_receiver_into_tmp_when_they_are_set(self) -> None:
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", 4318)) == 0:
                self.skipTest("something already listens on 4318, so the hook starts nothing")
        self.assertEqual(self.run_hook(**EXPORT), "")
        for _ in range(50):
            if self.started.exists():
                break
            time.sleep(0.1)
        self.assertIn(f"--out {self.root}/tmp/telemetry --port 4318", self.started.read_text())


if __name__ == "__main__":
    unittest.main()
