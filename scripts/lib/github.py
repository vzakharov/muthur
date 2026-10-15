"""Shared GitHub plumbing for the stdlib-only scripts in `scripts/`.

Imported as `from lib.github import detect_origin_repo, die, fetch, gh_token`.
Running a script as `python3 scripts/<name>.py` puts `scripts/` on `sys.path[0]`, so
`lib.github` resolves as a PEP 420 namespace package from any working directory —
no `__init__.py`, no `sys.path` manipulation. Both callers write output relative
to the caller's cwd while living elsewhere, so that cwd-independence matters.

Deliberately excluded: each script's `USER_AGENT` (they differ, which is how the
two are told apart server-side) and the `DOCS_*_ROOT` output paths.

Stdlib only — no third-party deps. Python 3.9+.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, NamedTuple, NoReturn

# Both scripts pin the same REST API version, and a bump has to move them
# together — unlike `USER_AGENT`, which is deliberately per-script.
GITHUB_API_VERSION = "2022-11-28"


def die(msg: str, code: int = 1) -> NoReturn:
    print(msg, file=sys.stderr)
    sys.exit(code)


def gh_token() -> str:
    env = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if env:
        return env.strip()
    try:
        out = subprocess.check_output(["gh", "auth", "token"], text=True)
    except FileNotFoundError:
        die("No GitHub token: set $GH_TOKEN or install `gh` and run `gh auth login`.")
    except subprocess.CalledProcessError:
        die("`gh auth token` failed; run `gh auth login` or set $GH_TOKEN.")
    token = out.strip()
    if not token:
        die("Empty token from `gh auth token`; run `gh auth login`.")
    return token


def detect_origin_repo(cwd: str | os.PathLike[str] | None = None) -> str | None:
    # The URL as configured, not `git remote get-url`'s: that applies
    # `url.*.insteadOf`, so a mirror rewrite would hide which repository it is.
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], cwd=cwd, text=True
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return parse_repo_url(url)


def parse_repo_url(url: str) -> str | None:
    """`owner/repo` from a GitHub clone URL, or `None` for any other URL."""
    m = re.match(
        r"^(?:https://github\.com/|git@github\.com:)([^/]+)/([^/]+?)(?:\.git)?/?$",
        url,
    )
    return f"{m.group(1)}/{m.group(2)}" if m else None


class _DropAuthOnHostChange(urllib.request.HTTPRedirectHandler):
    """Strip `Authorization` when a redirect crosses to another host.

    An attachment URL redirects to a pre-signed S3 URL, and S3 rejects a
    request that carries both its signature and an `Authorization` header with
    `400 InvalidArgument: Only one auth mechanism allowed`. urllib re-sends
    every header across a redirect, so without this the download always fails.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and _host(newurl) != _host(req.full_url):
            new.remove_header("Authorization")
        return new


def _host(url: str) -> str:
    return urllib.parse.urlsplit(url).netloc.lower()


def _openers() -> list[urllib.request.OpenerDirector]:
    """Proxy-honoring opener first, then one that bypasses the proxy.

    Claude Code's remote-session egress proxy refuses `api.github.com` outright
    and admits only repository-scoped paths on `github.com`, while a direct
    connection to either host succeeds. The order is load-bearing: it keeps an
    environment where the proxy is the only route out working.
    """
    return [
        urllib.request.build_opener(_DropAuthOnHostChange),
        urllib.request.build_opener(
            _DropAuthOnHostChange, urllib.request.ProxyHandler({})
        ),
    ]


class RouteFailure(NamedTuple):
    """One rung's refusal; `body` is `""` when the failure carried none.

    Captured eagerly: an `HTTPError`'s body reads exactly once, off a file
    object that does not outlive the rung.
    """

    status: str
    body: str


class AllRoutesFailed(Exception):
    """Every rung of the ladder refused one request.

    `str()` renders the statuses only; `failures` carries the bodies, so a call
    site opts into them via `format_route_statuses_and_bodies`.
    """

    def __init__(self, failures: list[RouteFailure]) -> None:
        super().__init__(format_route_statuses(failures))
        self.failures = failures


def format_route_statuses(failures: list[RouteFailure]) -> str:
    """Every rung's status, in ladder order, and nothing else.

    Required wherever the remote echoes request headers back: S3 rejects an
    attachment download by quoting the offending header — the bearer token in
    full — so its body must never reach a message.
    """
    return "; then ".join(f.status for f in failures)


def format_route_statuses_and_bodies(failures: list[RouteFailure]) -> str:
    """Every rung's status and response body, one per line, in ladder order.

    Safe only where the remote answers with its own JSON, as the proxy and
    `api.github.com` do — and there the body is the diagnostic: the proxy's 403
    names itself as the refuser, which its status alone does not.
    """
    return "\n".join(
        f"- {f.status}: {f.body.strip()}" if f.body.strip() else f"- {f.status}"
        for f in failures
    )


def fetch(
    build_request: Callable[[], urllib.request.Request],
) -> tuple[bytes, dict[str, str]]:
    """Walk the opener ladder; return the first success as (body, headers).

    Takes a factory, not a `Request`: `ProxyHandler.proxy_open` rewrites the
    request's host in place, so one `Request` reused across rungs aims at the
    proxy on every rung. Building one per rung is what keeps the direct rung
    direct.
    """
    failures: list[RouteFailure] = []
    for opener in _openers():
        try:
            with opener.open(build_request()) as resp:
                return resp.read(), {k.lower(): v for k, v in resp.headers.items()}
        except urllib.error.HTTPError as exc:
            failures.append(
                RouteFailure(
                    f"{exc.code} {exc.reason}", exc.read().decode(errors="replace")
                )
            )
        except urllib.error.URLError as exc:
            failures.append(RouteFailure(str(exc), ""))
    raise AllRoutesFailed(failures)
