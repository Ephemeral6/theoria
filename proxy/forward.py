"""Upstream HTTP, shared by both proxies.

Nothing here knows about ARC or about model providers. It opens the socket, it
retries the retryable, and it reports what happened -- including the per-attempt
statuses, which the ledger records when there was more than one.
"""

import json
import time
import urllib.error
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


class Response:
    def __init__(self, status: int, headers: Dict[str, str], body: bytes,
                 elapsed_ms: int, attempts: int, attempt_log: List[Dict[str, Any]]):
        self.status = status
        self.headers = headers
        self.body = body
        self.elapsed_ms = elapsed_ms
        self.attempts = attempts
        self.attempt_log = attempt_log

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
            sleep=time.sleep) -> Response:
    attempt_log: List[Dict[str, Any]] = []
    started = time.time()
    status, response_headers, raw = TRANSPORT_STATUS, {}, b""

    for attempt in range(1, max_attempts + 1):
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        attempt_started = time.time()
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status = response.status
                response_headers = dict(response.headers.items())
                raw = response.read()
        except urllib.error.HTTPError as exc:
            status = exc.code
            response_headers = dict(exc.headers.items()) if exc.headers else {}
            raw = exc.read()
        except Exception as exc:                       # transport-level failure
            status = TRANSPORT_STATUS
            response_headers = {}
            raw = json.dumps({"error": "%s: %s" % (type(exc).__name__, exc)}).encode()

        attempt_log.append({"attempt": attempt, "status": status,
                            "ms": int((time.time() - attempt_started) * 1000)})
        if status not in RETRY_STATUSES and status != TRANSPORT_STATUS:
            break
        if attempt < max_attempts:
            sleep(backoff * attempt)

    return Response(status, response_headers, raw,
                    int((time.time() - started) * 1000),
                    len(attempt_log), attempt_log)
