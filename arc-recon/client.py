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

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple

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


def load_api_key(env_path: Optional[str] = None) -> str:
    """Read ARC_API_KEY from the gitignored .env. Never returned to a log."""
    path = env_path or os.path.join(REPO, ".env")
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


class ArcClient:
    """Every call goes through `request`, so every call lands in the ledger."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = BASE_URL,
                 ledger_path: str = LEDGER_PATH, timeout: int = 30,
                 dry_run: bool = False):
        self._key = api_key or load_api_key()
        self.base_url = base_url.rstrip("/")
        self.ledger_path = ledger_path
        self.timeout = timeout
        self.dry_run = dry_run
        self.calls = 0

    # -- ledger ------------------------------------------------------------
    def _record(self, entry: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.ledger_path)), exist_ok=True)
        with open(self.ledger_path, "a", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps(entry, sort_keys=True, ensure_ascii=True))
            fh.write("\n")

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
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                status = response.status
                text = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            status = exc.code
            text = exc.read().decode("utf-8", "replace")
        self.calls += 1

        try:
            parsed: Any = json.loads(text)
        except json.JSONDecodeError:
            parsed = None

        self._record(
            {
                "t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
                "elapsed_ms": int((time.time() - started) * 1000),
                "note": note,
                "method": method,
                "url": url,
                # the key is never written, in any form
                "request_headers": {k: (REDACTED if k == "X-API-Key" else v)
                                    for k, v in headers.items()},
                "request_body": body,
                "status": status,
                "response_body": parsed if parsed is not None else text,
            }
        )

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
