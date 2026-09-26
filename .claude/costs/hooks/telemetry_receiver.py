#!/usr/bin/env python3
"""Receive Claude Code's OpenTelemetry log events over OTLP/HTTP-JSON and append
each `api_request` to `<out>/<session-id>.jsonl`.

Usage:
  python3 .claude/costs/hooks/telemetry_receiver.py --out <dir> [--port 4318]

An event keeps its numeric attributes, `request_id`, `model`, `speed`,
`query_source` and its timestamp, and nothing else: the rest carry the
account's email and ids, which have no business on disk. The session id names
the file and is not written into it.

Started detached by `start-telemetry-receiver.sh`. Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple

KEPT = ("request_id", "model", "speed", "query_source")
DECIMAL = re.compile(r"-?\d+(\.\d+)?")
SAFE_ID = re.compile(r"[A-Za-z0-9_-]+")


def _value(wrapped: Any) -> Any:
    """An OTLP `AnyValue`, whose int64 arrives as a JSON string."""
    if not isinstance(wrapped, dict):
        return None
    if "intValue" in wrapped:
        return int(wrapped["intValue"])
    if "doubleValue" in wrapped:
        return float(wrapped["doubleValue"])
    return wrapped.get("stringValue")


def _number(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    # Claude Code sends its counts as strings. A decimal string is a count; an
    # id or an address is not, which is what keeps them off disk.
    if isinstance(value, str) and DECIMAL.fullmatch(value):
        return float(value) if "." in value else int(value)
    return None


def _records(payload: Any) -> Iterator[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Each log record with its attributes flattened, beside its resource's."""
    for resource_logs in payload.get("resourceLogs") or []:
        resource = {
            a.get("key"): _value(a.get("value"))
            for a in (resource_logs.get("resource") or {}).get("attributes") or []
        }
        for scope_logs in resource_logs.get("scopeLogs") or []:
            for record in scope_logs.get("logRecords") or []:
                attributes = {
                    a.get("key"): _value(a.get("value")) for a in record.get("attributes") or []
                }
                attributes.setdefault("_time_unix_nano", record.get("timeUnixNano"))
                yield attributes, resource


def kept_events(payload: Any) -> Iterator[Tuple[str, Dict[str, Any]]]:
    """`(session id, what is written)` for each `api_request` in a payload."""
    for attributes, resource in _records(payload):
        if attributes.get("event.name") != "api_request":
            continue
        session = attributes.get("session.id") or resource.get("session.id")
        kept: Dict[str, Any] = {"timestamp": _timestamp(attributes)}
        for key in KEPT:
            if isinstance(attributes.get(key), str):
                kept[key] = attributes[key]
        for key, value in attributes.items():
            number = _number(value)
            if key not in kept and not key.startswith("_") and number is not None:
                kept[key] = number
        yield (session if isinstance(session, str) and SAFE_ID.fullmatch(session) else "unknown"), kept


def _timestamp(attributes: Dict[str, Any]) -> Optional[str]:
    stamped = attributes.get("event.timestamp")
    if isinstance(stamped, str):
        return stamped
    nanos = attributes.get("_time_unix_nano")
    if isinstance(nanos, (str, int)) and str(nanos).isdigit():
        moment = datetime.fromtimestamp(int(nanos) / 1e9, tz=timezone.utc)
        return moment.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    return None


def make_handler(out: Path) -> type:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if self.path.rstrip("/") != "/v1/logs":
                self._reply(404)
                return
            body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
            if self.headers.get("Content-Encoding") == "gzip":
                body = gzip.decompress(body)
            try:
                payload = json.loads(body)
            except json.JSONDecodeError as error:
                # Answered as the client's error, and logged: the exporter
                # does not retry a 400, so the log is where a shape change shows.
                self.log_error("not JSON: %s", error)
                self._reply(400)
                return
            out.mkdir(parents=True, exist_ok=True)
            for session, event in kept_events(payload):
                with (out / f"{session}.jsonl").open("a", encoding="utf-8") as sink:
                    sink.write(json.dumps(event, sort_keys=True) + "\n")
            self._reply(200)

        def _reply(self, status: int) -> None:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"{}")

        def log_request(self, code: Any = "-", size: Any = "-") -> None:
            # A line per request would grow the log by one a second; errors
            # still reach it through `log_error`.
            pass

    return Handler


def serve(out: Path, port: int) -> HTTPServer:
    return HTTPServer(("127.0.0.1", port), make_handler(out))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--port", type=int, default=4318)
    args = parser.parse_args()
    serve(args.out, args.port).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
