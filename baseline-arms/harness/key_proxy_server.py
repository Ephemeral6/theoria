"""The ARC credential, in a process the arm is not.

## What this is and why it exists

`Theoria.md` Phase 1 states the seal as a conjunction: the arm process does not
hold the environment credential, **and** egress that goes around the proxy
fails. `STATUS.md` GAP-5 (2026-07-31) registered that this track satisfied
neither half -- `arc_client.load_api_key()` opened `.env` inside the arm and
`ArcClient.__init__` parked the value in `self._key` for the whole run, and
every call went straight to `https://three.arcprize.org` with no proxy in
between. That was not a leak; the value was simply *resident*, in the same
interpreter that runs `claude -p`, the retry envelope and every line of
model-facing code.

This module is the other side of the boundary. It is a **transparent
forwarder**: it reads `.env` itself, injects `X-API-Key`, and passes everything
else -- method, path, query, body, cookies, status, response body -- through
unaltered. The arm talks to `http://127.0.0.1:<port>` and never learns a key,
because its process never reads one.

It is started as `python -m harness.key_proxy_server` by
`harness/key_proxy.py`, which is the parent-side supervisor and which contains
no credential reader at all. That split is the point: an arm-side bug cannot
leak a value its process never held.

## Why not `proxy/env_proxy.py`

The ticket allowed either. `theoria-arm` routes through the fleet environment
proxy and that is right for it; for this track it would have changed three
measured things at once (DECISIONS.md D-026):

  * `proxy/env_proxy.py` charges `proxy/spend_gate.py` itself, and
    `ArcClient.request()` already charges the same shared pool through
    `harness/spend.py`. Routing bare_cc through it would bill every ARC action
    to the fleet pool twice.
  * It writes `env_step` records in the proxy's canon format. This track's
    accounting reads `ledger.jsonl` and `probe_log.jsonl`; one campaign would
    have ended up with two incompatible ledgers.
  * It is not transparent -- it re-implements ARC command semantics and applies
    variants. The cookie jar that `arc_client` owns is the transport every
    figure in `BUDGET_REPORT.md` will be re-derived on (arc-recon INC-007,
    20/20 first-attempt RESETs with a jar against 0/20 without), and putting a
    second, differently-behaved HTTP client in the path would silently change
    it again -- which is exactly the D-019 failure this track has already had
    once.

So the credential moves and nothing else does. The jar, the probe log, the
spend gate and the sealed-pile guard all stay in the arm, where they were
measured.

## Two details that would otherwise bite

* **Set-Cookie is rewritten, minimally.** The arm's jar now sees `127.0.0.1`
  rather than `three.arcprize.org`, so a cookie carrying `Domain=` for the real
  host would be rejected by the arm's own jar, and a `Secure` cookie would not
  be sent back over the loopback hop's `http://`. Both attributes are stripped
  on the way out; the name, the value, `Path`, `HttpOnly` and the expiry are
  untouched. Nothing else about the jar changes, so `cookies_sent` and
  `cookies_held_after` still describe the real session.
* **An arm that sends a key is refused, not laundered.** A request arriving
  here with an `X-API-Key` header means the arm held a credential after all.
  Forwarding it would make this proxy the thing that hides GAP-5 rather than
  the thing that closes it, so it is answered `400 ARM_SENT_A_KEY` and never
  forwarded.

The handshake, the atomic port file and the parent watchdog follow
`proxy/env_proxy.py`'s proven Windows shapes (no fork, no SIGTERM, a file
rather than stdout, `ctypes` rather than `os.kill(pid, 0)`). They are written
out here rather than imported for the reason the top of `arc_client.py` already
gives about `arc-recon/client.py`: that module belongs to another territory and
this one may not modify it, so sixty duplicated lines are cheaper than a
coupling this track cannot fix.
"""

import argparse
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.dirname(HERE)
REPO = os.path.dirname(TRACK)
for _path in (TRACK, REPO):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from harness import arc_client                                  # noqa: E402

#: The variable name -- never a value -- of the live credential.
KEY_ENV = "ARC_API_KEY"

#: The header the upstream authenticates with.
KEY_HEADER = "X-API-Key"

#: Where a *stub* key arrives from for offline proofs, so a test can tell this
#: proxy's injected header apart from an arm-supplied one. It travels as an
#: environment variable and never as a command-line argument: on Windows any
#: user can read another process's command line, and this track's own tests
#: would then publish a key-shaped string to the whole machine on every run.
#: A different name from `ARC_API_KEY` so a stub run cannot fall back to the
#: real credential.
STUB_KEY_ENV = "BASELINE_ARMS_TEST_KEY"

#: Status used to report a failure *reaching* the upstream, as opposed to a
#: failure the upstream reported. `ArcClient` maps it back to the `-1` its
#: probe log has always used for a transport-level fault, so the taxonomy in
#: `probe_log.jsonl` is unchanged by the split.
TRANSPORT_ERROR_STATUS = 599
#: Defined in `arc_client` and imported here, not the other way round: the arm
#: has to read these header names, and it must not import this module -- this
#: is where the reader lives.
TRANSPORT_ERROR_HEADER = arc_client.UPSTREAM_TRANSPORT_ERROR_HEADER
FINAL_URL_HEADER = arc_client.UPSTREAM_FINAL_URL_HEADER

#: Request headers the arm is allowed to have forwarded. A whitelist, so a
#: future header cannot travel by accident -- and `X-API-Key` is not on it by
#: construction.
FORWARDED_REQUEST_HEADERS = ("Content-Type", "Accept", "Cookie")

INTERNAL_PREFIX = "/__keyproxy/"


class KeyUnavailable(RuntimeError):
    """No credential could be found where the child was told to look."""


# --------------------------------------------------------------- the reader
def read_api_key(env_name: str = KEY_ENV,
                 env_path: Optional[str] = None) -> str:
    """The **only** `.env` reader left in this track, and it runs here.

    `arc_client.load_api_key()` used to be this function. It now raises, and
    this is where its body went: into the process that the arm is not.

    Never logged, never returned to the parent, never written to disk. The
    handshake reports the boolean `key_injected` and nothing else.
    """
    path = env_path or arc_client.env_file()
    if not os.path.exists(path):
        raise KeyUnavailable(
            "%s not found. Copy .env.example to .env and set %s." % (path, env_name))
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() == env_name and value.strip():
                return value.strip()
    raise KeyUnavailable("%s is not set in %s" % (env_name, path))


# ------------------------------------------------------------ cookie plumbing
def rewrite_set_cookie(header: str) -> str:
    """Drop `Domain=` and `Secure` from one Set-Cookie header.

    The arm's jar is now talking to `127.0.0.1` over `http://`. A cookie
    scoped `Domain=three.arcprize.org` would be refused by that jar, and one
    marked `Secure` would be held but never sent back -- so the session would
    silently stop being pinned and this track would re-acquire the exact
    five-to-ten-calls-per-command defect arc-recon's INC-007 removed, with
    nothing failing.

    Only those two attributes are touched. The name, the value, `Path`,
    `HttpOnly`, `Expires` and `Max-Age` pass through, so what the jar holds is
    still what the upstream issued.
    """
    parts = header.split(";")
    kept = [parts[0]]
    for attribute in parts[1:]:
        name = attribute.strip().split("=", 1)[0].strip().lower()
        if name in ("domain", "secure"):
            continue
        kept.append(attribute)
    return ";".join(kept)


# ------------------------------------------------------------------- the state
class _Counters:
    """What the child has seen. Names and counts; never a value."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.forwarded = 0
        self.denied_arm_key = 0
        self.upstream_errors = 0
        self.statuses: Dict[str, int] = {}

    def note(self, status: int) -> None:
        with self.lock:
            self.forwarded += 1
            key = str(status)
            self.statuses[key] = self.statuses.get(key, 0) + 1

    def note_denied(self) -> None:
        with self.lock:
            self.denied_arm_key += 1

    def note_error(self) -> None:
        with self.lock:
            self.upstream_errors += 1

    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            return {"forwarded": self.forwarded,
                    "denied_arm_key": self.denied_arm_key,
                    "upstream_errors": self.upstream_errors,
                    "statuses": dict(self.statuses)}


# ----------------------------------------------------------------- the handler
class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):                       # noqa: A003
        return                                               # the counters are the log

    # -- verbs -------------------------------------------------------------
    def do_GET(self):                                        # noqa: N802
        self._handle("GET")

    def do_POST(self):                                       # noqa: N802
        self._handle("POST")

    def do_PUT(self):                                        # noqa: N802
        self._handle("PUT")

    def do_DELETE(self):                                     # noqa: N802
        self._handle("DELETE")

    # -- plumbing ----------------------------------------------------------
    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def _send(self, status: int, body: bytes, content_type: str = "application/json",
              extra: Optional[List[Tuple[str, str]]] = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in (extra or []):
            self.send_header(name, value)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _send_json(self, status: int, payload: Any,
                   extra: Optional[List[Tuple[str, str]]] = None) -> None:
        self._send(status, json.dumps(payload, sort_keys=True).encode("utf-8"),
                   extra=extra)

    def _handle(self, method: str) -> None:
        raw = self._read_body()
        path, _, query = self.path.partition("?")

        if path.startswith(INTERNAL_PREFIX):
            self._internal(method, path)
            return

        # The guard. An inbound credential means the arm held one, which is the
        # condition this whole module exists to make impossible; forwarding it
        # would turn the proxy into the thing that hides GAP-5.
        if self.headers.get(KEY_HEADER) is not None:
            self.server.counters.note_denied()               # type: ignore[attr-defined]
            self._send_json(400, {
                "error": "ARM_SENT_A_KEY",
                "message": ("the arm process sent an %s header. The arm must "
                            "hold no credential -- see baseline-arms/harness/"
                            "key_proxy_server.py and STATUS.md GAP-5."
                            % KEY_HEADER),
            })
            return

        self._forward(method, path, query, raw)

    def _forward(self, method: str, path: str, query: str, raw: bytes) -> None:
        server = self.server                                 # type: ignore[assignment]
        url = server.upstream + path + (("?" + query) if query else "")

        headers = {}
        for name in FORWARDED_REQUEST_HEADERS:
            value = self.headers.get(name)
            if value is not None:
                headers[name] = value
        if server.api_key is not None:
            headers[KEY_HEADER] = server.api_key

        request = urllib.request.Request(
            url, data=raw if raw else None, headers=headers, method=method)
        try:
            with server.opener.open(request, timeout=server.timeout) as response:
                status = response.status
                body = response.read()
                out_headers = response.headers
                final_url = response.geturl() or url
        except urllib.error.HTTPError as exc:
            status = exc.code
            body = exc.read()
            out_headers = exc.headers
            final_url = exc.geturl() or url
        except Exception as exc:                             # noqa: BLE001
            # A failure to *reach* the upstream, which is a different fact from
            # a status the upstream returned. Reported as such so the arm can
            # keep recording it as `-1`, the way it always has.
            server.counters.note_error()
            self._send_json(TRANSPORT_ERROR_STATUS,
                            {"error": "UPSTREAM_TRANSPORT",
                             "detail": "%s: %s" % (type(exc).__name__, exc)},
                            extra=[(TRANSPORT_ERROR_HEADER, "1"),
                                   (FINAL_URL_HEADER, url)])
            return

        extra: List[Tuple[str, str]] = [(FINAL_URL_HEADER, final_url)]
        for raw_cookie in _all_set_cookie(out_headers):
            extra.append(("Set-Cookie", rewrite_set_cookie(raw_cookie)))

        content_type = "application/json"
        getter = getattr(out_headers, "get", None)
        if callable(getter):
            content_type = out_headers.get("Content-Type") or content_type

        server.counters.note(status)
        self._send(status, body, content_type=content_type, extra=extra)

    def _internal(self, method: str, path: str) -> None:
        server = self.server                                 # type: ignore[assignment]
        name = path[len(INTERNAL_PREFIX):]
        if name == "health":
            self._send_json(200, {"ok": True,
                                  "key_injected": server.api_key is not None})
            return
        if name == "state":
            payload = server.counters.snapshot()
            payload["key_injected"] = server.api_key is not None
            payload["upstream"] = server.upstream
            self._send_json(200, payload)
            return
        if name == "shutdown" and method == "POST":
            self._send_json(200, {"stopping": True})
            threading.Thread(target=server.shutdown, daemon=True).start()
            return
        self._send_json(404, {"error": "no such internal endpoint", "path": path})


def _all_set_cookie(headers: Any) -> List[str]:
    """Every Set-Cookie header. This server sends five.

    `headers.get()` returns the first and `dict(headers)` keeps the last, so
    either would drop cookies on the floor between the upstream and the arm's
    jar -- the pin would be partial and nothing would say so.
    """
    getter = getattr(headers, "get_all", None)
    if callable(getter):
        return list(getter("Set-Cookie") or [])
    out = []
    for key, value in getattr(headers, "items", lambda: [])():
        if str(key).lower() == "set-cookie" and value:
            out.append(value)
    return out


# ------------------------------------------------------------ the handshake
def write_port_file(path: str, payload: Dict[str, Any]) -> None:
    """Publish the handshake by atomic rename.

    The parent polls this file, so a half-written one would be read as invalid
    JSON -- and the obvious repair (retry until it parses) cannot tell a
    half-written file from a child that published nonsense. `os.replace` is
    atomic on NTFS and on POSIX: the file is either absent or complete.

    The shape follows `proxy/env_proxy.write_port_file`, deliberately.
    """
    tmp = path + ".tmp"
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def parent_is_alive(pid: int) -> bool:
    """Whether the process that started us still exists.

    `os.kill(pid, 0)` is the POSIX idiom and is actively dangerous on Windows:
    CPython implements `os.kill` there by opening the process and calling
    `TerminateProcess` for any signal that is not a console event, so the
    liveness probe would kill the parent it is asking about.
    """
    if os.name == "nt":                                      # pragma: no cover
        import ctypes                                        # noqa: PLC0415

        SYNCHRONIZE = 0x00100000
        QUERY_LIMITED = 0x1000
        WAIT_TIMEOUT = 0x102
        kernel32 = ctypes.windll.kernel32                    # type: ignore[attr-defined]
        handle = kernel32.OpenProcess(SYNCHRONIZE | QUERY_LIMITED, False, pid)
        if not handle:
            return False
        try:
            return kernel32.WaitForSingleObject(handle, 0) == WAIT_TIMEOUT
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:                                  # alive, not ours
        return True
    return True


def watch_parent(pid: int, httpd, interval: float = 2.0) -> threading.Thread:
    """Stop serving once the parent is gone.

    The supervisor stops this child explicitly and also kills it from an
    `atexit` hook, which covers a parent that raises. Neither covers a parent
    that is hard-killed, and what would be left behind is a process holding a
    bound port **and a credential**. Two consecutive readings, because one
    failed probe is not evidence.
    """
    def loop() -> None:
        misses = 0
        while True:
            time.sleep(interval)
            if parent_is_alive(pid):
                misses = 0
                continue
            misses += 1
            if misses >= 2:
                httpd.shutdown()
                return

    thread = threading.Thread(target=loop, name="key-proxy-parent-watch",
                              daemon=True)
    thread.start()
    return thread


# ------------------------------------------------------------------ the server
def build_argument_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=0,
                    help="0 lets the OS choose; the port file publishes it")
    ap.add_argument("--port-file", default=None,
                    help="where to publish {port, pid, key_injected}")
    ap.add_argument("--parent-pid", type=int, default=None,
                    help="stop serving if this process goes away")
    ap.add_argument("--upstream", default=arc_client.BASE_URL)
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--api-key-env", default=None,
                    help=("read a STUB key from this environment variable "
                          "instead of .env. Offline proofs only."))
    ap.add_argument("--no-require-key", dest="require_key",
                    action="store_false",
                    help=("serve without a credential. The negative control: "
                          "the upstream then sees no %s at all." % KEY_HEADER))
    ap.set_defaults(require_key=True)
    return ap


def resolve_key(api_key_env: Optional[str], require_key: bool) -> Optional[str]:
    """Where the credential comes from, in the child and nowhere else.

    Exactly three cases, and the third one is the one that matters:

      * `--api-key-env NAME` -- a stub, from the child's own environment.
      * nothing, and a key is required -- the live path, `.env`.
      * `--no-require-key` -- **serve with no credential at all**, without
        looking at `.env`.

    That last line was written the other way round first, as "read `.env` and
    fall back to keyless if it is missing", and A19's own negative control
    caught it within the hour: this machine *has* a `.env`, so the test whose
    entire purpose was to show a keyless proxy injecting nothing started a
    child holding the live credential. Nothing was printed and nothing was
    written -- the assertion failed before any request was made -- but a test
    designed to prove absence had quietly arranged presence, on every developer
    machine where the file exists and on no CI box where it does not.

    An optional credential is not a credential policy. `require_key=False` is
    a positive statement that this proxy runs without one.
    """
    if api_key_env:
        value = os.environ.get(api_key_env)
        if value:
            return value
        if require_key:
            raise KeyUnavailable(
                "--api-key-env named %s but that variable is not set in this "
                "process's environment" % api_key_env)
        return None
    if not require_key:
        return None
    return read_api_key()


def main(argv=None) -> int:
    args = build_argument_parser().parse_args(argv)

    try:
        api_key = resolve_key(args.api_key_env, args.require_key)
    except KeyUnavailable as exc:
        # The message names variables and paths, never values.
        print("key proxy: %s" % exc, flush=True)
        return 3

    httpd = ThreadingHTTPServer((args.host, args.port), _Handler)
    httpd.daemon_threads = True
    httpd.upstream = args.upstream.rstrip("/")               # type: ignore[attr-defined]
    httpd.timeout_seconds = args.timeout                     # type: ignore[attr-defined]
    httpd.timeout = args.timeout                             # type: ignore[attr-defined]
    httpd.api_key = api_key                                  # type: ignore[attr-defined]
    httpd.counters = _Counters()                             # type: ignore[attr-defined]
    # No cookie processor here on purpose: the jar stays in the arm, which is
    # where every transport figure this track publishes was measured.
    httpd.opener = urllib.request.build_opener()             # type: ignore[attr-defined]

    port = httpd.server_address[1]
    handshake = {"port": int(port), "pid": os.getpid(),
                 "key_injected": api_key is not None,
                 "upstream": httpd.upstream}                 # type: ignore[attr-defined]
    if args.port_file:
        write_port_file(args.port_file, handshake)
    print("key proxy listening on http://%s:%d -> %s (key_injected=%s)"
          % (args.host, port, httpd.upstream,                # type: ignore[attr-defined]
             api_key is not None), flush=True)

    if args.parent_pid:
        watch_parent(args.parent_pid, httpd)

    try:
        httpd.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:                                # pragma: no cover
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    sys.exit(main())
