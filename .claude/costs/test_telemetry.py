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
from datetime import datetime, timedelta, timezone
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


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class UnderClaude(unittest.TestCase):
    """The hook over a `python3` stub that records its arguments, on a port of
    the test's own so the session's receiver on 4318 is no obstacle, and under a
    shell named `claude` that holds the exporter's variables and strips `OTEL_*`
    from the hook, as Claude Code does."""

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
        self.transcript = Path(base.name) / "transcript.jsonl"
        self.transcript.touch()
        self.events = self.root / "tmp" / "telemetry"
        self.pending = self.events / f"{SESSION}.unconfirmed"
        self.port = free_port()
        self.export = {
            "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
            "OTEL_LOGS_EXPORTER": "otlp",
            "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
            "OTEL_EXPORTER_OTLP_ENDPOINT": f"http://127.0.0.1:{self.port}",
        }

    def run_hook(self, event: str = "SessionStart", late: str = "", **env: str) -> str:
        """`late` is assignments the hook gets and `claude`'s `/proc` environ
        does not, as a `claude` exec'd from a preloaded spare hands them on."""
        inherited = {
            k: v
            for k, v in os.environ.items()
            if not (k.startswith("OTEL_") or k == "CLAUDE_CODE_ENABLE_TELEMETRY")
        }
        # The trailing `:` keeps `claude` from exec'ing into the hook, which
        # would leave it no such ancestor.
        strip_otel = f'env $(env | sed -n "s/^\\(OTEL_[A-Z_]*\\)=.*/-u \\1/p") {late} bash "$0"; :'
        ran = subprocess.run(
            [str(self.claude), "-c", strip_otel, str(HOOK)],
            input=json.dumps(
                {"hook_event_name": event, "session_id": SESSION, "transcript_path": str(self.transcript)}
            ),
            capture_output=True,
            text=True,
            check=True,
            env={
                **inherited,
                "PATH": self.path,
                "CLAUDE_PROJECT_DIR": str(self.root),
                "MUTHUR_TELEMETRY_RECEIVER_PORT": str(self.port),
                **env,
            },
        )
        return ran.stdout


class WhenTheHookStartsTheReceiver(UnderClaude):
    def test_names_what_to_set_and_starts_nothing_when_the_variables_are_unset(self) -> None:
        notice = self.run_hook(**{**self.export, "OTEL_EXPORTER_OTLP_ENDPOINT": "http://collector:4318"})
        self.assertIn("listens for: OTEL_EXPORTER_OTLP_ENDPOINT.", notice)
        for name, value in self.export.items():
            self.assertIn(f"    {name}={value}\n", notice)
        self.assert_nothing_started()

    def assert_nothing_started(self) -> None:
        time.sleep(0.2)
        self.assertFalse(self.started.exists())

    def assert_started(self, event: str, late: str = "") -> None:
        self.assertEqual(self.run_hook(event, late, **({} if late else self.export)), "")
        for _ in range(50):
            if self.started.exists():
                break
            time.sleep(0.1)
        self.assertIn(f"--out {self.root}/tmp/telemetry --port {self.port}", self.started.read_text())

    def test_starts_the_receiver_into_tmp_when_they_are_set(self) -> None:
        self.assert_started("SessionStart")
        self.assertFalse(self.pending.exists())

    def test_starts_a_missing_receiver_after_a_tool_call_too(self) -> None:
        self.assert_started("PostToolUse")

    def test_starts_on_its_own_telemetry_flag_when_claudes_environ_predates_it(self) -> None:
        self.assert_started("SessionStart", late="CLAUDE_CODE_ENABLE_TELEMETRY=1")
        self.assertTrue(self.pending.exists())

    def test_says_nothing_after_a_tool_call_when_the_variables_are_unset(self) -> None:
        self.assertEqual(self.run_hook("PostToolUse"), "")
        self.assert_nothing_started()


def stamp(seconds_ago: float) -> str:
    moment = datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)
    return moment.isoformat(timespec="milliseconds").replace("+00:00", "Z")


class WhenTheReceiverRunsOnTheFlagAlone(UnderClaude):
    """After a tool call, with a receiver listening that was started on
    `CLAUDE_CODE_ENABLE_TELEMETRY` a minute ago and has no event yet."""

    def setUp(self) -> None:
        super().setUp()
        listener = socket.socket()
        self.addCleanup(listener.close)
        listener.bind(("127.0.0.1", self.port))
        listener.listen()
        self.events.mkdir(parents=True)
        self.pending.write_text(stamp(60)[:19] + "Z\n")

    def responses(self, *seconds_ago: float) -> None:
        """One main-thread response per age, the last the current one, each
        written as two records the way a response with a tool call is, and
        compact, as Claude Code writes its transcript."""
        with self.transcript.open("w", encoding="utf-8") as transcript:
            for n, age in enumerate(seconds_ago):
                for block_age in (age + 5, age):
                    record = {"type": "assistant", "timestamp": stamp(block_age), "message": {"id": f"msg_{n}"}}
                    transcript.write(json.dumps(record, separators=(",", ":")) + "\n")

    def confirm(self) -> str:
        return self.run_hook("PostToolUse")

    def test_settles_quietly_on_the_sessions_first_event(self) -> None:
        self.responses(30, 0)
        (self.events / f"{SESSION}.jsonl").write_text('{"cost_usd": 0.01}\n')
        self.assertEqual(self.confirm(), "")
        self.assertFalse(self.pending.exists())

    def test_waits_while_only_the_current_response_has_run(self) -> None:
        self.responses(30)
        self.assertEqual(self.confirm(), "")
        self.assertTrue(self.pending.exists())

    def test_waits_while_a_finished_responses_event_may_be_in_flight(self) -> None:
        self.responses(2, 0)
        self.assertEqual(self.confirm(), "")
        self.assertTrue(self.pending.exists())

    def test_ignores_responses_from_before_the_receiver_started(self) -> None:
        self.responses(120, 0)
        self.assertEqual(self.confirm(), "")
        self.assertTrue(self.pending.exists())

    def test_says_once_that_capture_looks_off_when_a_finished_response_brought_no_event(self) -> None:
        self.responses(30, 0)
        context = json.loads(self.confirm())["hookSpecificOutput"]
        self.assertEqual(context["hookEventName"], "PostToolUse")
        self.assertIn("telemetry capture looks off", context["additionalContext"])
        self.assertIn(f"    OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:{self.port}\n", context["additionalContext"])
        self.assertFalse(self.pending.exists())
        self.assertEqual(self.confirm(), "")


if __name__ == "__main__":
    unittest.main()
