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
"""

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple

from . import ledger

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


def load_api_key(env_path: Optional[str] = None) -> str:
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


class ArcClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = BASE_URL,
                 timeout: int = 30):
        self._key = api_key or load_api_key()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.sealed = sealed_pile()
        self.calls = 0

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
        url = self.base_url + path
        headers = {"X-API-Key": self._key, "Accept": "application/json"}
        payload = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        started = time.time()
        request = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                status = response.status
                text = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            status = exc.code
            text = exc.read().decode("utf-8", "replace")
        except Exception as exc:                       # transport-level failure
            status = -1
            text = "%s: %s" % (type(exc).__name__, exc)
        self.calls += 1

        try:
            parsed: Any = json.loads(text)
        except json.JSONDecodeError:
            parsed = None

        ledger.probe("arc_api_call", {
            "note": note,
            "method": method,
            "url": url,
            "request_headers": {k: (REDACTED if k == "X-API-Key" else v)
                                for k, v in headers.items()},
            "request_body": body,
            "status": status,
            "elapsed_ms": int((time.time() - started) * 1000),
            "response_summary": _summarise(parsed if parsed is not None else text),
        })

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

    def close_scorecard(self, card_id: str):
        return self.request("POST", "/api/scorecard/close", body={"card_id": card_id},
                            note="close scorecard", raise_on_error=False)[1]

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
