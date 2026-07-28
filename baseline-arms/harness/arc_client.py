"""ARC-AGI-3 client for the baseline-arms track, with a sealed-pile guard.

Two things are structural here, not advisory:

  * **The credential never leaves this module.** Read from the gitignored
    `.env`, sent only as `X-API-Key`, redacted in everything written to disk.
  * **Sealed-pile games cannot be reached.** `piles.json` is loaded at import
    and any call naming a sealed game raises before the socket is opened.
    Reading a sealed game's first frame teaches its mechanics as surely as
    playing it, and would poison the future Theoria arm's exam on that game.

This deliberately does not import `arc-recon/client.py`: that file belongs to
another track and this track may not modify it, so duplicating ~60 lines is
cheaper than coupling to something we cannot fix.

COOKIE JAR (arc-recon INC-007 / INC-007a / INC-009; ported here 2026-07-28).
The API sits behind an AWS ALB that issues `AWSALBAPP-*` routing cookies and a
`GAMESESSION` cookie. A client that does not echo them is load-balanced afresh
on every request, lands on a replica that does not hold the session, and gets
back `400 game <id> not found` -- which both tracks read as an intermittent
server fault for two days. arc-recon measured it: **20/20 first-attempt RESETs
with a jar, 0/20 without**, arms interleaved and placed on different games so
neither could starve the other, plus 8/8 walking all four development games out
and back on one jar. Its paired canary sweep went from 190 HTTP calls to 20 for
the same 20 commands -- zero retries -- with identical frame hashes, so the fix
is behaviour-preserving and not merely faster.

That is where D-005's 5.07x amplification and the `[400x7, 200]` storm come
from.

**The jar is ON by default, and this paragraph used to say the opposite.** It
read "`cookies=False` is kept: an instrument you cannot put back the way it was
is one you cannot re-verify, and BUDGET_REPORT's numbers should be re-derived,
not quietly reinterpreted." That was a good intention and it was never true of
the code: `__init__` has defaulted to `cookies=True` since the jar landed, and
no caller except `transport_ab` passes anything else -- so `bare_cc`, and with
it the whole variance campaign, silently changed transport. An adversarial audit
of the g50t cells found it (D-019); nothing in the harness would have.

The measurement is unambiguous, from this track's own probe logs:

    jar off  (M4 pilot + the ar25 envelope, all history)  1922 calls
             200: 249   400: 1315   404: 147   500: 208   transport error: 3
    jar on   (g50t, this campaign)                          99 calls
             200: 99

So the honest statement, replacing the one above: **BUDGET_REPORT's section 2.1
unit prices and every extrapolation built on them were measured on a transport
that no longer exists.** `http_per_action` is not 7.11 any more; on the jar it
is 1.0. They are not to be reinterpreted, and they are also not to be compared
against anything measured after 2026-07-28 -- they must be re-derived. The jar
stays on because it is a real fix that arc-recon measured (20/20 vs 0/20) and
because turning it off now would make the campaign's own games incomparable with
each other, which is the one thing a variance envelope cannot survive.

Three details that cost arc-recon an incident each, honoured here rather than
rediscovered:

  * **Cookie NAMES only, never values.** `GAMESESSION` is a bearer token for a
    live session; the probe log is tracked and Phase 4 publishes every tracked
    file. arc-recon's INC-008 happened because its redaction lived inside one
    function and a second writer went around it -- and this module is a second
    writer by design (`ledger.probe`, not that function).
  * **The right tense.** `HTTPCookieProcessor` absorbs the response's cookies
    *during* `open()`, so a jar snapshot taken afterwards describes the call's
    result, not what the call sent. `cookies_sent` is captured before.
  * **The retry envelope changes meaning.** Retries used to be independent
    routing draws; with a pinned jar they all hit the same replica, so
    `clear_routing_cookies()` exists and the retry loops in `bare_cc.py` call it.
"""

import http.cookiejar
import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from . import ledger, spend

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.dirname(HERE)
REPO = os.path.dirname(TRACK)

PILES_PATH = os.path.join(REPO, "arc-recon", "data", "piles.json")
BASE_URL = "https://three.arcprize.org"
REDACTED = "<redacted>"


class SealedGameError(RuntimeError):
    """Raised before any network call that would touch the sealed pile."""


class ArcApiError(RuntimeError):
    def __init__(self, status: int, body: str, path: str):
        super().__init__("HTTP %s on %s: %s" % (status, path, body[:300]))
        self.status = status
        self.body = body
        self.path = path


def load_piles(path: str = PILES_PATH) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def dev_pile(path: str = PILES_PATH):
    return list(load_piles(path)["dev_pile"])


def sealed_pile(path: str = PILES_PATH):
    return set(load_piles(path)["sealed_pile"])


def env_file() -> str:
    """Where `.env` lives, from a checkout or from a linked worktree of one.

    `.env` is gitignored, so it does not travel with a branch -- and CLAUDE.md
    instructs every agent to work in `.worktrees/<id>/`, where the file
    therefore does not exist. Resolving only against the importing checkout made
    the credential unreachable from exactly the place the conventions say to
    work, so a worktree falls back to the main checkout, which is the same
    resolution `proxy/spend_gate.py` uses for the pool ledger and for the same
    reason. The key is still read, still only from a gitignored file, and still
    never copied anywhere.
    """
    here = os.path.join(REPO, ".env")
    if os.path.exists(here):
        return here
    from proxy.spend_gate import main_checkout
    main = main_checkout(REPO)
    return os.path.join(main, ".env") if main else here


def load_api_key(env_path: Optional[str] = None) -> str:
    path = env_path or env_file()
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


# RFC 6265 cookie-name is a token: no separators, no whitespace.
_COOKIE_TOKEN = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


def cookie_names(set_cookie_header: str) -> List[str]:
    """The name at the head of ONE Set-Cookie header. At most one, by design.

    Deliberately does not split on commas. arc-recon's first version did, and a
    value containing a comma then produced a fragment of the VALUE dressed as a
    name -- the redactor leaking through itself. A response carries one
    `Set-Cookie` header per cookie, so reading only each header's head is both
    correct and safe; if a caller has already collapsed several into one string
    this under-reports, which is the only direction a redactor may fail in.
    """
    head = (set_cookie_header or "").split(";", 1)[0].strip()
    if "=" not in head:
        return []
    name = head.split("=", 1)[0].strip()
    return [name] if _COOKIE_TOKEN.match(name) else []


def issued_cookie_names(headers: Any) -> List[str]:
    """Names from EVERY Set-Cookie header. This server sends five.

    `headers.get("Set-Cookie")` returns only the first and `dict(headers)` keeps
    only the last, so either would under-report what the server issued while the
    jar quietly held more.
    """
    raw: List[str] = []
    getter = getattr(headers, "get_all", None)
    if callable(getter):
        raw = list(getter("Set-Cookie") or [])
    else:
        for key, value in getattr(headers, "items", lambda: [])():
            if str(key).lower() == "set-cookie" and value:
                raw.append(value)
    names: List[str] = []
    for header in raw:
        names.extend(cookie_names(header))
    return names


class ArcClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = BASE_URL,
                 timeout: int = 30, cookies: bool = True,
                 spend_binding: Optional["spend.SpendBinding"] = None):
        self._key = api_key or load_api_key()
        #: The claim on the shared pool this client spends against. There is no
        #: default and no way to switch it off: `request()` refuses without one.
        #: See `harness/spend.py` and `proxy/SPEND_GATE.md`.
        self.spend = spend_binding
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.sealed = sealed_pile()
        self.calls = 0

        # See the module docstring. One jar per client, shared across games --
        # arc-recon's cross-game probe established that game A's GAMESESSION
        # does not poison game B's, so this needs no per-game bookkeeping.
        self.cookies = cookies
        self.jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            *([urllib.request.HTTPCookieProcessor(self.jar)] if cookies else []))
        self.transport = {
            "cookies": cookies,
            "description": ("cookie jar shared across games (arc-recon INC-007)"
                            if cookies else
                            "bare urllib, no cookie jar -- the transport every "
                            "figure in BUDGET_REPORT.md was measured on"),
        }

    def cookies_held(self) -> List[str]:
        """Names only. Values are credentials and never leave this object."""
        return sorted(c.name for c in self.jar)

    def clear_routing_cookies(self) -> None:
        """Drop the ALB pins, keep the session identity.

        D-005's envelope retried an identical request up to 30 times, and that
        worked because the jar-less transport re-drew a replica every time. A
        pinned jar sends all 30 to the same one, so if that replica is the
        broken one, retrying is only waiting. `GAMESESSION` stays: the session
        is what we are trying to reach, not what is wrong.
        """
        for cookie in list(self.jar):
            if cookie.name.upper().startswith("AWSALB"):
                self.jar.clear(cookie.domain, cookie.path, cookie.name)

    # -- the guard ---------------------------------------------------------
    def assert_playable(self, game_id: str) -> None:
        """Refuse sealed games before opening a socket. Prefix-matched, because
        a caller may pass a bare id without the version suffix."""
        for sealed_id in self.sealed:
            if game_id == sealed_id or game_id.split("-")[0] == sealed_id.split("-")[0]:
                raise SealedGameError(
                    "%s is in the sealed pile (piles.json). Touching it would "
                    "contaminate the future exam on that game." % game_id
                )

    # -- transport ---------------------------------------------------------
    def request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None,
                note: str = "", raise_on_error: bool = True) -> Tuple[int, Any]:
        # The gate, on the first line of the path that spends. Not a convention
        # a caller has to remember: a client with no claim on the shared pool
        # cannot open a socket at all. INC-BA-003's second session obeyed every
        # rule it knew about; the rule it needed did not exist to be known, so
        # this one is a function that raises rather than a paragraph.
        if self.spend is None:
            raise spend.NoSpendBinding(
                "this ArcClient has no claim on the shared spend pool, so an "
                "outbound request to %s would be money nobody can total. "
                "Construct it with `ArcClient(spend_binding=...)` -- see "
                "harness/spend.py and proxy/SPEND_GATE.md." % path)
        self.spend.check_action(1)                # refuses before the socket

        url = self.base_url + path
        headers = {"X-API-Key": self._key, "Accept": "application/json"}
        payload = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        started = time.time()
        request = urllib.request.Request(url, data=payload, headers=headers, method=method)
        # Snapshot the jar BEFORE the call: HTTPCookieProcessor absorbs the
        # response's cookies during `open()`, so a snapshot taken afterwards
        # would describe what the call produced, not what it sent -- and the
        # first call of a session, which provably echoed nothing, would be
        # logged as though it had.
        sent = self.cookies_held()
        final_url = url
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                status = response.status
                text = response.read().decode("utf-8", "replace")
                issued = issued_cookie_names(response.headers)
                final_url = response.geturl() or url
        except urllib.error.HTTPError as exc:
            status = exc.code
            text = exc.read().decode("utf-8", "replace")
            issued = issued_cookie_names(exc.headers)
            final_url = exc.geturl() or url
        except Exception as exc:                       # transport-level failure
            status = -1
            text = "%s: %s" % (type(exc).__name__, exc)
            issued = []
        self.calls += 1

        try:
            parsed: Any = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            parsed = None

        ledger.probe("arc_api_call", {
            "note": note,
            "method": method,
            "url": url,
            # Equal to `url` unless a redirect was followed. build_opener
            # follows them, and the log previously could not show that at all.
            "final_url": final_url,
            "redirected": final_url != url,
            "request_headers": {k: (REDACTED if k == "X-API-Key" else v)
                                for k, v in headers.items()},
            "request_body": body,
            "status": status,
            "elapsed_ms": int((time.time() - started) * 1000),
            "response_summary": _summarise(parsed if parsed is not None else text),
            # Cookie NAMES only, never values. Two tenses because they answer
            # different questions: what this request carried, and what the
            # response left behind. The `Cookie` header itself is attached by
            # HTTPCookieProcessor inside `open()`, so it never appears in
            # `request_headers` -- `cookies_sent` is the only record of it.
            "cookies_enabled": self.cookies,
            "set_cookie_names": sorted(set(issued)),
            "cookies_sent": sent,
            "cookies_held_after": self.cookies_held(),
        })

        # Charged after the probe line is on disk, and charged whatever the
        # status was. A 400 crossed the wire, counted against the rate limit and
        # happened; a pool that only counts successes is a pool that undercounts
        # itself by exactly D-005's 5-11x retry amplification. If this raises,
        # the cap was reached -- the spend is already recorded, and the refusal
        # is the point.
        self.spend.record_action(1, detail={"path": path, "status": status,
                                            "note": note})

        if status >= 400 or status < 0:
            if raise_on_error:
                raise ArcApiError(status, text, path)
        return status, parsed if parsed is not None else text

    # -- read-only ---------------------------------------------------------
    def list_games(self):
        return self.request("GET", "/api/games", note="list games")[1]

    def open_scorecard(self, **metadata):
        return self.request("POST", "/api/scorecard/open", body=dict(metadata) or {},
                            note="open scorecard")[1]

    def close_scorecard(self, card_id: str, tries: int = 8):
        """Close a scorecard, retrying the transient 404 the way D-005 retries
        the transient 400 on gameplay.

        This is the only moment the authoritative scores are obtainable. A
        closed card cannot be re-fetched -- `GET /api/scorecard/<id>` and a
        second close both return 404 permanently -- so a close that is allowed
        to fail destroys that run's reconciliation data for good. In the M4
        pilot 22 of 23 closes returned `404 scorecard <id> not found` and none
        were retried, which is why only one of fourteen cells can be checked
        against `Theoria.md` Phase 1's obligation that ledger-derived scores
        equal API scorecard scores.

        The 404 has the same shape and the same cause as the gameplay 400 (only
        some backend instances hold the session), so it gets the same treatment.
        """
        status, body = -1, None
        for k in range(tries):
            status, body = self.request("POST", "/api/scorecard/close",
                                        body={"card_id": card_id},
                                        note="close scorecard", raise_on_error=False)
            if status == 200:
                return body
            time.sleep(0.4 * (k + 1))
        ledger.probe("scorecard_close_failed", {
            "card_id": card_id, "tries": tries, "last_status": status,
            "consequence": "no authoritative scores for this run; "
                           "reconciliation impossible (a closed card cannot be re-fetched)",
        })
        return body

    # -- gameplay (guarded) ------------------------------------------------
    def reset(self, game_id: str, card_id: str, raise_on_error: bool = True):
        self.assert_playable(game_id)
        return self.request("POST", "/api/cmd/RESET",
                            body={"game_id": game_id, "card_id": card_id},
                            note="RESET %s" % game_id, raise_on_error=raise_on_error)

    def action(self, game_id: str, card_id: str, guid: str, action_id: int,
               data: Optional[Dict[str, Any]] = None, raise_on_error: bool = True):
        self.assert_playable(game_id)
        body: Dict[str, Any] = {"game_id": game_id, "card_id": card_id, "guid": guid}
        if data:
            body["data"] = data
        return self.request("POST", "/api/cmd/ACTION%d" % action_id, body=body,
                            note="ACTION%d %s" % (action_id, game_id),
                            raise_on_error=raise_on_error)


def _summarise(body: Any) -> Any:
    """Frames are 64x64 grids; the probe log records shape, not pixels. Full
    frames belong in ledger.jsonl as env_step records, once, not duplicated
    into every diagnostic line."""
    if isinstance(body, dict):
        out = {}
        for k, v in body.items():
            if k == "frame" and isinstance(v, list):
                out[k] = "<%d frame(s)>" % len(v)
            else:
                out[k] = v
        return out
    if isinstance(body, list):
        return "<list of %d>" % len(body)
    return body
