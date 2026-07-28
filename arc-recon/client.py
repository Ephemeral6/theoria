"""Minimal ARC-AGI-3 API client with a complete, append-only call ledger.

Two disciplines from Theoria.md Phase 1 are structural here rather than
advisory:

  * **The credential never leaves this module.** It is read from the gitignored
    `.env`, sent only in the `X-API-Key` header, and redacted in every ledger
    entry. Nothing that touches disk or stdout can carry it.
  * **Every bit in and out is recorded.** Each call appends one line to
    `data/recon_ledger.jsonl`: method, url, redacted headers, request body,
    status, response body, wall-clock time. "Conclusions may only come from the
    ledger" needs the ledger to be complete by construction.

This is the reconnaissance client, not the Phase 1 environment proxy. The proxy
(which the three arms point at, and which is what makes "arms never see the
credential" a physical fact rather than a promise) is a separate build; this is
the read-only instrument used to survey the API before that is designed.
"""

import http.cookiejar
import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA_DIR = os.path.join(HERE, "data")
LEDGER_PATH = os.path.join(DATA_DIR, "recon_ledger.jsonl")

BASE_URL = "https://three.arcprize.org"
REDACTED = "<redacted>"


class ArcApiError(Exception):
    def __init__(self, status: int, body: str, path: str):
        super().__init__("HTTP %s on %s: %s" % (status, path, body[:300]))
        self.status = status
        self.body = body
        self.path = path


def main_checkout(start: str) -> Optional[str]:
    """The main worktree's root, if `start` is a linked worktree of one.

    A linked worktree has a `.git` **file** holding `gitdir: <path>`, and that
    path is `<main>/.git/worktrees/<name>`. `.env` is gitignored, so it exists
    only in the main checkout -- which makes every network-facing tool here
    unusable from a worktree, and the working agreement requires worktrees.
    Returns None for a normal checkout or anything unrecognised; the caller
    treats that as "no fallback", never as an error.
    """
    marker = os.path.join(start, ".git")
    if not os.path.isfile(marker):
        return None
    try:
        line = open(marker, encoding="utf-8").readline().strip()
    except OSError:
        return None
    if not line.startswith("gitdir:"):
        return None
    gitdir = os.path.abspath(os.path.join(start, line[len("gitdir:"):].strip()))
    parts = gitdir.replace("\\", "/").split("/")
    if len(parts) < 4 or parts[-3] != ".git" or parts[-2] != "worktrees":
        return None
    return os.path.dirname(os.path.dirname(os.path.dirname(gitdir)))


def load_api_key(env_path: Optional[str] = None) -> str:
    """Read ARC_API_KEY from the gitignored .env. Never returned to a log."""
    path = env_path or os.path.join(REPO, ".env")
    if not os.path.exists(path) and env_path is None:
        main = main_checkout(REPO)
        if main:
            candidate = os.path.join(main, ".env")
            if os.path.exists(candidate):
                path = candidate
    if not os.path.exists(path):
        raise RuntimeError(
            "%s not found. Copy .env.example to .env and set ARC_API_KEY." % path
        )
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == "ARC_API_KEY" and value.strip():
            return value.strip()
    raise RuntimeError("ARC_API_KEY is not set in %s" % path)


def mask(key: str) -> str:
    """A stable, non-reversible handle for the key, safe to print."""
    return "%s...%s (len %d)" % (key[:4], key[-4:], len(key)) if key else "<unset>"


# RFC 6265 cookie-name is a token: no separators, no whitespace.
_COOKIE_TOKEN = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


def cookie_names(set_cookie_header: str) -> List[str]:
    """The name at the head of ONE Set-Cookie header. At most one, by design.

    A cookie value is a credential. `GAMESESSION` is a bearer token for a live
    game session and the ALB pins identify a backend, so the rule that keeps
    `X-API-Key` out of the tracked ledger applies to these too (INC-008).

    This deliberately does NOT split on commas, and that is the whole point. The
    first version did, on the theory that one header can carry several cookies --
    and a value containing a comma then produced a *fragment of the value* as if
    it were a name: `GAMESESSION=v1,eyJndWlkIjoi...` yielded
    `['GAMESESSION', 'eyJndWlkIjoi...']`. The redaction leaked through the
    redactor. A response carries one `Set-Cookie` header per cookie anyway, so
    reading only the head of each header is both correct and safe; where a caller
    has already collapsed several headers into one string, this under-reports
    rather than over-reports, which is the direction a redactor must fail in.

    Returns a list (0 or 1 entries) because callers concatenate across headers.
    """
    head = (set_cookie_header or "").split(";", 1)[0].strip()
    if "=" not in head:
        return []
    name = head.split("=", 1)[0].strip()
    return [name] if _COOKIE_TOKEN.match(name) else []


def _issued_cookie_names(headers: Any) -> List[str]:
    """Names from EVERY Set-Cookie header, not just the first.

    A response carries one `Set-Cookie` header per cookie, and this server sends
    five. `headers.get("Set-Cookie")` returns only the first of them, and
    `dict(headers)` keeps only the last -- either way the log would under-report
    what the server issued while the jar (which reads them all) quietly held
    more. The jar is unaffected by this; only the record was at risk.

    `get_all` is also case-insensitive on an `email.message.Message`, which
    matters because HTTP header names are.
    """
    raw: List[str] = []
    getter = getattr(headers, "get_all", None)
    if callable(getter):
        raw = list(getter("Set-Cookie") or [])
    else:                                        # a plain mapping
        for key, value in getattr(headers, "items", lambda: [])():
            if str(key).lower() == "set-cookie" and value:
                raw.append(value)
    names: List[str] = []
    for header in raw:
        names.extend(cookie_names(header))
    return names


class ArcClient:
    """Every call goes through `request`, so every call lands in the ledger."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = BASE_URL,
                 ledger_path: str = LEDGER_PATH, timeout: int = 30,
                 dry_run: bool = False, cookies: bool = True):
        self._key = api_key or load_api_key()
        self.base_url = base_url.rstrip("/")
        self.ledger_path = ledger_path
        self.timeout = timeout
        self.dry_run = dry_run
        self.calls = 0

        # INC-007. The server sits behind an AWS ALB and issues AWSALBAPP-*
        # routing cookies plus a GAMESESSION cookie. Without a jar every request
        # is load-balanced afresh, lands on a replica that does not hold the
        # session, and comes back `400 game <id> not found` -- which this
        # directory spent two incidents reading as an intermittent server fault.
        # Measured: 20/20 first-attempt RESETs with a jar, 0/20 without.
        #
        # ONE jar per client, shared across games. That is not an assumption: the
        # cross-game probe walked all four development games out and back on a
        # single jar and every RESET succeeded first try, so game A's
        # GAMESESSION does not poison game B's.
        #
        # `cookies=False` is kept deliberately. Every figure measured before this
        # change -- the determinism verdicts, the canary baseline, both tracks'
        # cost models -- was taken on a cookie-less transport, and an instrument
        # you cannot put back the way it was is one you cannot re-verify.
        self.cookies = cookies
        self.jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            *([urllib.request.HTTPCookieProcessor(self.jar)] if cookies else []))
        self.transport = {
            "cookies": cookies,
            "description": ("cookie jar shared across games (INC-007 fix)"
                            if cookies else
                            "bare urllib, no cookie jar (pre-INC-007 behaviour, "
                            "kept for reproducing old measurements)"),
        }

    def cookies_held(self) -> List[str]:
        """Names only. Values are credentials and never leave this object."""
        return sorted(c.name for c in self.jar)

    def clear_cookies(self) -> None:
        self.jar.clear()

    def clear_routing_cookies(self) -> None:
        """Drop the ALB pins, keep the session identity.

        The retry envelope was designed against a transport that was re-routed
        on every attempt: 40 identical retries worked because each was an
        independent draw at a replica that might hold the session. A pinned jar
        removes that -- all 40 now go to the same replica, so if THAT replica is
        the broken one, retrying is just waiting. Dropping `AWSALB*` between
        attempts restores the draw; `GAMESESSION` stays, because the session
        identity is the thing we are trying to reach, not the thing that is
        wrong.
        """
        for cookie in list(self.jar):
            if cookie.name.upper().startswith("AWSALB"):
                self.jar.clear(cookie.domain, cookie.path, cookie.name)

    # -- ledger ------------------------------------------------------------
    def _record(self, entry: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.ledger_path)), exist_ok=True)
        # ONE write call, newline included. Two writes on a buffered stream can
        # be flushed as separate chunks, and this file has a second appender
        # (probe_stickiness.py) plus, at times, a second process -- a record
        # split across flushes is a corrupted append-only ledger, and 148 of the
        # current records are larger than the default 8 KiB buffer.
        line = json.dumps(entry, sort_keys=True, ensure_ascii=True) + "\n"
        with open(self.ledger_path, "a", encoding="utf-8", newline="") as fh:
            fh.write(line)

    # -- transport ---------------------------------------------------------
    def request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None,
                note: str = "") -> Tuple[int, Any]:
        url = self.base_url + path
        headers = {"X-API-Key": self._key, "Accept": "application/json"}
        payload = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if self.dry_run:
            return 0, {"dry_run": True, "method": method, "url": url, "body": body}

        started = time.time()
        request = urllib.request.Request(url, data=payload, headers=headers, method=method)
        # Snapshot the jar BEFORE the call. HTTPCookieProcessor absorbs the
        # response's Set-Cookie during `open()`, so a snapshot taken afterwards
        # describes the jar the call produced, not the jar that produced the
        # call -- and the first request of every session, which provably sent no
        # Cookie header, would be logged as though it had. "Which cookies did we
        # echo" is the INC-007 discriminator; it has to be recorded in the right
        # tense.
        sent = self.cookies_held()
        transport_error = None
        final_url = url
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                status = response.status
                text = response.read().decode("utf-8", "replace")
                issued = _issued_cookie_names(response.headers)
                # build_opener follows redirects. The ledger recorded only the
                # URL we aimed at, so a call that landed elsewhere looked
                # identical to one that did not.
                final_url = response.geturl() or url
        except urllib.error.HTTPError as exc:
            status = exc.code
            text = exc.read().decode("utf-8", "replace")
            issued = _issued_cookie_names(exc.headers)
            final_url = exc.geturl() or url
        except Exception as exc:
            # A timeout, a reset connection, a DNS failure, a body that dies
            # mid-read: the request LEFT THIS PROCESS, so it must leave a row.
            # Previously it escaped before `calls += 1` and before `_record`,
            # which broke the module's own promise that the ledger is complete
            # by construction -- and, worse, made contamination.py's
            # "zero sealed-pile contact" audit blind to exactly those calls,
            # since it can only see what the ledger holds.
            status, text, issued = -1, str(exc), []
            transport_error = "%s: %s" % (type(exc).__name__, exc)
        self.calls += 1

        try:
            parsed: Any = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            parsed = None

        self._record(
            {
                "t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
                "elapsed_ms": int((time.time() - started) * 1000),
                "note": note,
                "method": method,
                "url": url,
                # Where it actually landed. Equal to `url` unless a redirect was
                # followed, which the ledger previously could not show at all.
                "final_url": final_url,
                "redirected": final_url != url,
                # the key is never written, in any form
                "request_headers": {k: (REDACTED if k == "X-API-Key" else v)
                                    for k, v in headers.items()},
                "request_body": body,
                "status": status,
                "response_body": parsed if parsed is not None else text,
                # Cookie NAMES only -- never values (INC-008). Recording these
                # makes "the cookie jar was actually on for this call" an
                # auditable fact rather than a claim about which build ran.
                # Two tenses, because they answer different questions:
                # `cookies_sent` is what this request carried (the INC-007
                # discriminator), `cookies_held_after` is the jar the response
                # left behind. Note the Cookie header itself is attached by
                # HTTPCookieProcessor inside `open()`, so it never appears in
                # `request_headers` -- `cookies_sent` is the record of it.
                "cookies_enabled": self.cookies,
                "set_cookie_names": sorted(set(issued)),
                "cookies_sent": sent,
                "cookies_held_after": self.cookies_held(),
                "transport_error": transport_error,
            }
        )

        if transport_error is not None:
            # Recorded first, then re-raised: callers (precheck.send_command)
            # already treat this as retryable, and the retry accounting stays
            # exactly as it was.
            raise urllib.error.URLError(transport_error)
        if status >= 400:
            raise ArcApiError(status, text, path)
        return status, parsed if parsed is not None else text

    # -- read-only surface (costs no action quota) -------------------------
    def list_games(self):
        return self.request("GET", "/api/games", note="list available games")[1]

    def open_scorecard(self, **metadata):
        return self.request(
            "POST", "/api/scorecard/open", body=dict(metadata) or {},
            note="open scorecard",
        )[1]

    def close_scorecard(self, card_id: str):
        return self.request(
            "POST", "/api/scorecard/close", body={"card_id": card_id},
            note="close scorecard",
        )[1]

    def get_scorecard(self, card_id: str):
        return self.request(
            "GET", "/api/scorecard/%s" % card_id, note="retrieve scorecard"
        )[1]
