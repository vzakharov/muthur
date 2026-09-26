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
import tempfile
import threading
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


if __name__ == "__main__":
    unittest.main()
