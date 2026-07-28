"""The arm's only route to the environment: HTTP to the env proxy, nothing else.

This client holds no credential and has no code path that could use one. It
addresses `ARC_BASE_URL`, which is the environment proxy, and the proxy injects
`ARC_API_KEY` on the far side. That is the whole of the sealing story from this
side of the wire.

Two things here are not in `proxy/` and had to be built, both for reasons this
repo already measured:

**The 400 wave.** `arc-recon` established (INC-001b/INC-002a) that
`400 {"message": "game <id> not found"}` from ARC is a *transient* fault
arriving in 1-3 minute waves off a multi-instance backend, not an entitlement
boundary; an envelope of 40 attempts with linear backoff capped at 5s turned
"0 of 8 actions succeed" into "4/4 dev-pile games PASS determinism".
`proxy/forward.py` does not retry 400 -- `RETRY_STATUSES` is
`{429, 500, 502, 503, 504}` -- and `proxy/` belongs to another track, so the
retry has to live on this side of the proxy. The consequence is deliberate and
worth naming: **each retry is its own request through the proxy and therefore
its own `env_step` record.** The ledger will show more steps than the scorecard
shows actions. That is the honest shape -- a refusal is evidence, not an
absence (LEDGER_FORMAT.md §3) -- and `runs/.../MANIFEST.json` records both
counts so nobody has to guess which one they are reading.

**500 is not retried here.** `proxy/forward.py` does retry it. On `tn36` the
nominal ACTION6 returns a deterministic 500 on every one of 88 attempts, so a
retry envelope on 500 burns the full backoff for a certainty. This client
treats 500 as permanent and lets the proxy's own (shorter) envelope be the only
one that fires. `g50t` has no ACTION6, but the rule is the safe one either way.

**Full ids only.** INC-005: a short game id can return HTTP 200 carrying the
pristine initial frame regardless of session progress. A counterfeit 200 is
worse than a 400. Every request body here carries the version-suffixed id, and
`_check_full_id` refuses to send anything else.
"""

import json
import re
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple

from .budget import Budget

#: A full ARC game id: stem, dash, eight hex digits. The suffix is the
#: environment version fingerprint (LEDGER_FORMAT.md §3) and is never dropped.
FULL_ID = re.compile(r"^[A-Za-z0-9]{2,6}-[0-9a-f]{8}$")

#: arc-recon/precheck.py's envelope, which is the one that produced a verdict
#: on all four dev-pile games.
RESET_ATTEMPTS = 40
ACTION_ATTEMPTS = 40
DELAY_BASE = 0.5
DELAY_CAP = 5.0


class ArcError(RuntimeError):
    pass


class ShortIdRefused(ArcError):
    """INC-005. Refusing to send is the whole point."""


def _retryable(status: int, body: Any) -> bool:
    """arc-recon/precheck._retryable, reproduced. Everything not named here is
    permanent, deliberately -- so a deterministic 500 does not burn 40 attempts."""
    if status < 0 or status == 0:
        return True                                   # transport
    if status == 429:
        return True
    if status == 502:
        # The proxy renders an upstream transport failure as 502 after its own
        # envelope is spent. Treat it the way arc-recon treats a transport error.
        return True
    if status == 400:
        message = ""
        if isinstance(body, dict):
            message = str(body.get("message") or body.get("detail") or "")
        return "not found" in message.lower()
    return False


class ArcThroughProxy:
    """One game, one scorecard, one session. Keyless by construction."""

    def __init__(self, env_base: str, game_id: str, budget: Budget,
                 timeout: float = 60.0,
                 on_command: Optional[Callable[[Dict[str, Any]], None]] = None,
                 sleep=time.sleep):
        self._check_full_id(game_id)
        self.env_base = env_base.rstrip("/")
        self.game_id = game_id
        self.budget = budget
        self.timeout = timeout
        self.sleep = sleep
        #: Called with a small dict after every command completes. The run
        #: driver uses it to keep RUN_STATE.md current without this module
        #: knowing anything about files.
        self.on_command = on_command

        self.card_id: Optional[str] = None
        self.guid: Optional[str] = None
        self.available_actions: List[int] = []
        self.win_levels: Optional[int] = None
        self.attempt_log: List[Dict[str, Any]] = []

    # -- sealing -----------------------------------------------------------
    @staticmethod
    def _check_full_id(game_id: str) -> None:
        if not FULL_ID.match(game_id or ""):
            raise ShortIdRefused(
                "%r is not a full game id. INC-005: a short id can return 200 "
                "carrying the pristine initial frame whatever the session has "
                "done, so a short-id 200 is counterfeit and is never sent."
                % (game_id,))

    # -- transport ---------------------------------------------------------
    def _post(self, path: str, body: Dict[str, Any]) -> Tuple[int, Any]:
        payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.env_base + path, data=payload, method="POST",
            headers={"Content-Type": "application/json",
                     "Accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8", "replace")
                status = response.status
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            status = exc.code
        except Exception as exc:                     # transport to our own proxy
            return -1, {"error": "%s: %s" % (type(exc).__name__, exc)}
        try:
            return status, json.loads(raw)
        except json.JSONDecodeError:
            return status, {"raw": raw}

    def _send(self, path: str, body: Dict[str, Any], *, attempts: int,
              note: str, is_reset: bool = False, probe: bool = False
              ) -> Tuple[int, Any, int]:
        """Send until it sticks or the envelope is spent. Returns
        (status, body, attempts_used)."""
        status, parsed = 0, None
        used = 0
        for k in range(attempts):
            self.budget.check(probe=probe, is_reset=is_reset)
            self.budget.command()
            used += 1
            status, parsed = self._post(path, body)
            if not _retryable(status, parsed):
                break
            if k < attempts - 1:
                self.sleep(min(DELAY_BASE * (k + 1), DELAY_CAP))

        ok = status == 200
        if ok:
            self.budget.succeeded(is_reset=is_reset, probe=probe)
        else:
            self.budget.failed(is_reset=is_reset)

        entry = {"note": note, "path": path, "status": status,
                 "attempts": used, "ok": ok}
        self.attempt_log.append(entry)
        if self.on_command:
            self.on_command(entry)
        return status, parsed, used

    # -- the surface -------------------------------------------------------
    def open_scorecard(self, tags: List[str], opaque: Optional[Dict[str, Any]] = None
                       ) -> Optional[str]:
        body: Dict[str, Any] = {"tags": list(tags)}
        if opaque:
            body["opaque"] = opaque
        status, parsed = self._post("/api/scorecard/open", body)
        if status == 200 and isinstance(parsed, dict):
            self.card_id = parsed.get("card_id")
        return self.card_id

    def close_scorecard(self, tries: int = 40) -> Optional[Dict[str, Any]]:
        """D-015: a closed card can never be re-fetched, and close 404s
        transiently. 22 of baseline-arms' 23 pilot closes returned an instant
        404 with no retry, and the score exists *only* in a successful close
        response -- so a close that is not retried loses the score silently.

        **Eight is not enough.** `baseline-arms`' D-015 fix uses `tries=8`, and
        on this run's first card that failed: eight attempts returned 404 and
        the score looked lost. The same card closed cleanly on a retry with
        `tries=40` a minute later. Under an active 400 wave the close endpoint
        needs the same wave-outlasting envelope every other endpoint needs, so
        the default here is 40. Reported to the track that owns D-015 rather
        than fixed there."""
        if not self.card_id:
            return None
        for k in range(tries):
            status, parsed = self._post("/api/scorecard/close",
                                        {"card_id": self.card_id})
            if status == 200 and isinstance(parsed, dict):
                return parsed
            self.sleep(0.4 * (k + 1))
        return None

    def reset(self) -> Tuple[int, Any]:
        body: Dict[str, Any] = {"game_id": self.game_id}
        if self.card_id:
            body["card_id"] = self.card_id
        status, parsed, _ = self._send("/api/cmd/RESET", body,
                                       attempts=RESET_ATTEMPTS, note="RESET",
                                       is_reset=True)
        if status == 200:
            self._absorb(parsed)
        return status, parsed

    def act(self, action_id: int, data: Optional[Dict[str, Any]] = None, *,
            probe: bool = False) -> Tuple[int, Any]:
        if not 1 <= action_id <= 7:
            raise ArcError("ACTION%d is outside the API's 1..7" % action_id)
        body: Dict[str, Any] = {"game_id": self.game_id, "card_id": self.card_id,
                                "guid": self.guid}
        if data is not None:
            body["data"] = data
        status, parsed, _ = self._send(
            "/api/cmd/ACTION%d" % action_id, body,
            attempts=ACTION_ATTEMPTS, note="ACTION%d" % action_id, probe=probe)
        if status == 200:
            self._absorb(parsed)
        return status, parsed

    def _absorb(self, envelope: Any) -> None:
        """Everything this client remembers between commands. Note there is no
        `score` key in an ARC gameplay response -- score exists only on the
        scorecard -- so nothing here tracks one."""
        if not isinstance(envelope, dict):
            return
        if envelope.get("guid"):
            self.guid = envelope["guid"]
        if isinstance(envelope.get("available_actions"), list):
            self.available_actions = list(envelope["available_actions"])
        if envelope.get("win_levels") is not None:
            self.win_levels = envelope["win_levels"]


def frames_of(envelope: Any) -> List[List[List[int]]]:
    """The frame field, always as a list of grids.

    One ARC command can return anything from 1 to 113 grids -- the precheck saw
    7 from a single g50t ACTION2 -- and the cascade ruling turns on that count,
    so it is never collapsed here."""
    if not isinstance(envelope, dict):
        return []
    frame = envelope.get("frame")
    if frame is None:
        return []
    if frame and isinstance(frame[0], list) and frame[0] and isinstance(frame[0][0], list):
        return frame
    return [frame]                                    # a bare grid


def current_grid(envelope: Any) -> Optional[List[List[int]]]:
    """The state after the command: the *last* grid of the cascade."""
    frames = frames_of(envelope)
    return frames[-1] if frames else None
