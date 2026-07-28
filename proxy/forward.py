"""Upstream HTTP, shared by both proxies.

Nothing here knows about ARC or about model providers. It opens the socket, it
retries the retryable, and it reports what happened -- including the per-attempt
statuses, which the ledger records when there was more than one.

**It does not follow redirects.** `urllib`'s default handler does, and its
redirect handler copies every request header except `Content-Length` and
`Content-Type` onto the new request -- so a `302` from the upstream would
replay the injected credential to whatever host the redirect named. The red
team landed exactly that (RED-01) and it is the one attack that breaks sealing
without the arm doing anything: the whole double-proxy argument is that the key
exists only inside this process, and a courier that carries it to a third party
on request ends the argument.

A redirect is therefore returned to the caller as-is, with the `Location`
recorded, so the refusal is visible rather than silent (RED-02).
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

#: Retried: rate limits, gateway-class failures, and transport errors. A 4xx
#: that is not 429 is the upstream telling us something true; retrying it would
#: only burn quota.
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
TRANSPORT_STATUS = -1

HOP_BY_HOP = frozenset({
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "content-length",
    "content-encoding", "host",
})


class _NoRedirects(urllib.request.HTTPRedirectHandler):
    """Hand the 3xx back instead of chasing it.

    `redirect_request` returning `None` makes `urllib` stop and surface the
    response, which is what we want: the caller sees the redirect, records it,
    and nothing leaves this process for the host the redirect named.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


#: Built once. `urlopen` uses the global opener chain, which follows redirects;
#: this one does not.
_OPENER = urllib.request.build_opener(_NoRedirects)


class Response:
    def __init__(self, status: int, headers: Dict[str, str], body: bytes,
                 elapsed_ms: int, attempts: int, attempt_log: List[Dict[str, Any]],
                 final_url: Optional[str] = None,
                 redirect_to: Optional[str] = None):
        self.status = status
        self.headers = headers
        self.body = body
        self.elapsed_ms = elapsed_ms
        self.attempts = attempts
        self.attempt_log = attempt_log
        #: Where the transport actually finished. The ledger used to record the
        #: URL the proxy *intended*; those are the same thing only as long as
        #: nothing redirects, which is precisely what was not being checked.
        self.final_url = final_url
        #: The `Location` of a refused redirect, if there was one.
        self.redirect_to = redirect_to

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", "replace")

    def json(self) -> Optional[Any]:
        try:
            return json.loads(self.text)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    def passthrough_headers(self) -> Dict[str, str]:
        return {k: v for k, v in self.headers.items() if k.lower() not in HOP_BY_HOP}


def forward(url: str, method: str, headers: Dict[str, str],
            body: Optional[bytes] = None, timeout: float = 60.0,
            max_attempts: int = 5, backoff: float = 0.25,
            sleep=time.sleep, *, permit) -> Response:
    """Open a socket to `url`. Requires a live spend permit.

    `permit` is keyword-only and has **no default**, so a caller that forgot the
    gate gets a `TypeError` here rather than a line in the next incident report.
    That is the whole difference between a gate and a convention: INC-BA-003's
    second session obeyed every rule it knew about, and the rule it needed did
    not exist to be known.

    The permit is checked before **every attempt**, not once per call. One
    `forward()` can open up to `max_attempts` sockets, the pool's action unit is
    one outbound request (`spend_policy.json`), and a retry storm is precisely
    the shape that reaches the 600 rpm limit -- so a gate that charged a retry
    loop as one request would be blind to the case it was built for.

    `permit.check()` raises to refuse; it is not caught here. A refusal must
    reach the caller as an exception, because the alternative -- returning a
    Response that looks like an upstream error -- would let a budget breach be
    retried as though it were weather.
    """
    attempt_log: List[Dict[str, Any]] = []
    started = time.time()
    status, response_headers, raw = TRANSPORT_STATUS, {}, b""
    final_url: Optional[str] = None

    for attempt in range(1, max_attempts + 1):
        permit.check()                     # every socket, not once per call
        permit.attempts_made += 1          # counted before, so a throw is counted
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        attempt_started = time.time()
        try:
            with _OPENER.open(request, timeout=timeout) as response:
                status = response.status
                response_headers = dict(response.headers.items())
                raw = response.read()
                final_url = getattr(response, "url", None)
        except urllib.error.HTTPError as exc:
            status = exc.code
            response_headers = dict(exc.headers.items()) if exc.headers else {}
            raw = exc.read()
            final_url = getattr(exc, "url", None)
        except Exception as exc:                       # transport-level failure
            status = TRANSPORT_STATUS
            response_headers = {}
            final_url = None
            raw = json.dumps({"error": "%s: %s" % (type(exc).__name__, exc)}).encode()

        attempt_log.append({"attempt": attempt, "status": status,
                            "ms": int((time.time() - attempt_started) * 1000)})
        if status not in RETRY_STATUSES and status != TRANSPORT_STATUS:
            break
        if attempt < max_attempts:
            sleep(backoff * attempt)

    redirect_to = None
    if 300 <= status < 400:
        redirect_to = response_headers.get("Location") or response_headers.get("location")

    return Response(status, response_headers, raw,
                    int((time.time() - started) * 1000),
                    len(attempt_log), attempt_log,
                    final_url=final_url, redirect_to=redirect_to)


def crossed_hosts(intended: str, final: Optional[str]) -> bool:
    """Whether the transport finished somewhere other than where it was aimed.

    With redirects refused this should never be true. It is checked anyway,
    because "should never" is the state a security property is in right before
    it stops holding.
    """
    if not final:
        return False
    a, b = urllib.parse.urlsplit(intended), urllib.parse.urlsplit(final)
    return (a.scheme, a.netloc) != (b.scheme, b.netloc)
