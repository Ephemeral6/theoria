"""The environment proxy: an arm's only route to the ARC environment.

An arm points its ARC base URL at this process and changes nothing else -- no
adapter, no code change, one environment variable. In exchange, four things
become true by construction rather than by anyone's care:

  * **The arm holds no credential.** `ARC_API_KEY` is read here and injected
    here. An arm cannot reach the environment by going around the proxy,
    because going around it means going without a key.
  * **Every bit is recorded.** Request and response, whole, into the ledger.
  * **Sealed games are unreachable.** The guard refuses before the upstream
    socket opens, and records the refusal.
  * **Variants are deterministic rewrites**, applied here, on the wire.

Run it standalone:

    python -m proxy.env_proxy --port 8711 --arm theoria --run-id r-001

or embed it (the runner and the tests do):

    with EnvProxy(EnvProxyConfig(...)) as p:
        arm_env = {"ARC_BASE_URL": p.base_url}
"""

import argparse
import json
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

from . import forward as fwd
from .guard import SealedPileGuard
from .ledger import Ledger, RunLedger, canonical, sha256
from .paths import LEDGER_PATH, UPSTREAM_ARC
from .redact import VAULT, looks_like_credential, read_secret, scrub_outbound
from .spend_gate import (Reservation, SpendGate, SpendGateError,
                         attach_reservation, default_campaign, default_gate)
from .variants import (DEGENERATE_NOTE, Refusal, Variant, VariantRuntime,
                       _Remap)

COMMAND = re.compile(r"^/api/cmd/(RESET|ACTION([1-9][0-9]?))/?$")

#: Headers an arm may send that we pass upstream. Everything else -- above all
#: anything carrying a credential -- is dropped at this boundary.
PASSTHROUGH_REQUEST_HEADERS = ("content-type", "accept")

#: Header names that would mean the arm is carrying a key of its own.
CREDENTIAL_HEADERS = ("x-api-key", "authorization", "api-key", "x-api-token")


class EnvProxyConfig:
    def __init__(self, *, run_id: str, arm: str,
                 upstream: str = UPSTREAM_ARC,
                 api_key: Optional[str] = None,
                 require_key: bool = True,
                 ledger_path: str = LEDGER_PATH,
                 ledger: Optional[Ledger] = None,
                 run: Optional[RunLedger] = None,
                 guard: Optional[SealedPileGuard] = None,
                 variant: Optional[Variant] = None,
                 campaign: Optional[str] = None,
                 spend_gate: Optional[SpendGate] = None,
                 spend_reservation: Optional[Reservation] = None,
                 host: str = "127.0.0.1", port: int = 0,
                 timeout: float = 60.0,
                 max_attempts: int = 5):
        self.run_id = run_id
        self.arm = arm
        self.upstream = upstream.rstrip("/")
        self.host = host
        self.port = port
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.variant = variant

        # The credential enters the process here and nowhere else.
        self.api_key = api_key if api_key is not None else read_secret(
            "ARC_API_KEY", required=require_key)
        VAULT.register(self.api_key, force=True)

        self.ledger = ledger or Ledger(ledger_path)
        # The runner shares one RunLedger across both proxies, so step and call
        # counters for a run come from a single source.
        self.run = run or RunLedger(self.ledger, run_id, arm)
        self.guard = guard if guard is not None else SealedPileGuard()

        # The spend gate, on the same footing as the sealed-pile guard: not a
        # flag, not optional, and constructed here if the caller did not hand
        # one in. `spend_reservation=None` means "I did not declare a budget",
        # which is answered with the policy's small default caps rather than
        # with a shrug -- see `attach_reservation`.
        self.campaign = campaign or default_campaign(arm, run_id)
        self.spend_gate = spend_gate if spend_gate is not None else default_gate()
        self.spend_reservation_owned = spend_reservation is None
        self.spend_reservation = attach_reservation(
            self.spend_gate, self.campaign, spend_reservation,
            holder={"proxy": "env", "run_id": run_id, "arm": arm})


class _State:
    """What the proxy learns while a run happens. Counters only -- everything
    substantive is in the ledger."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.card_ids: list = []
        self.guids: Dict[str, str] = {}
        #: guid -> game_id. The inverse of `guids`, and the one the guard needs:
        #: a command that names only a session has to be attributable to a game.
        self.session_games: Dict[str, str] = {}
        self.runtimes: Dict[str, VariantRuntime] = {}
        #: game_ids whose `win_tighten` degeneracy has already been recorded as
        #: an incident. One per session, not one per WIN.
        self.degeneracy_reported: set = set()
        self.commands = 0
        self.meta_calls = 0
        self.denials = 0
        self.incidents = 0

    def runtime_for(self, game_id: str, variant: Optional[Variant]) -> VariantRuntime:
        with self.lock:
            if game_id not in self.runtimes:
                self.runtimes[game_id] = VariantRuntime(variant)
            return self.runtimes[game_id]


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "theoria-env-proxy/1.0"

    # -- plumbing ----------------------------------------------------------
    def log_message(self, fmt, *args):        # the ledger is the log
        pass

    @property
    def cfg(self) -> EnvProxyConfig:
        return self.server.cfg                                    # type: ignore[attr-defined]

    @property
    def state(self) -> _State:
        return self.server.state                                  # type: ignore[attr-defined]

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_PUT(self):
        self._handle("PUT")

    def do_DELETE(self):
        self._handle("DELETE")

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def _respond(self, status: int, payload: Any,
                 headers: Optional[Dict[str, str]] = None) -> None:
        if isinstance(payload, (bytes, bytearray)):
            body = bytes(payload)
        else:
            body = json.dumps(payload).encode("utf-8")

        # Nothing leaves for the arm carrying a credential -- not from us, and
        # not from an upstream that echoed one back.
        body, headers, leaked = scrub_outbound(body, dict(headers or {}), VAULT)
        if leaked:
            self.state.incidents += 1
            self.cfg.run.incident(
                "credential_reflected",
                "the upstream returned a registered credential to the arm in "
                "%s; it was removed before the arm saw it" % ", ".join(leaked),
                path=self.path.partition("?")[0], places=leaked)

        self.send_response(status)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        if not headers or "Content-Type" not in headers:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # -- the request -------------------------------------------------------
    def _handle(self, method: str) -> None:
        path, _, query = self.path.partition("?")
        raw = self._read_body()
        try:
            body = json.loads(raw.decode("utf-8")) if raw else None
        except (json.JSONDecodeError, UnicodeDecodeError):
            body = None

        # The keyless check runs before the internal-endpoint branch, not
        # after: `/__proxy/health` used to be a route on which an arm could
        # present a credential and have nobody notice (RED-09).
        self._check_arm_is_keyless(path, body, raw)

        if path.startswith("/__proxy/"):
            return self._internal(path)

        match = COMMAND.match(path)
        known_game = self._game_for_session(body)
        verdict = self.cfg.guard.check_request(
            path, query, body, raw=raw, headers=self.headers,
            known_game=known_game, is_command=bool(match))
        if verdict["decision"] == "deny":
            return self._deny(method, path, query, body, verdict)

        if match:
            return self._command(method, path, query, body, raw, match)
        return self._meta(method, path, query, body, raw)

    def _game_for_session(self, body: Any) -> Optional[str]:
        """Which game a `guid` belongs to, if this proxy opened the session.

        A `guid` is only obtainable through a RESET, and a RESET is guarded --
        so a session this proxy opened is a session for a game it allowed. A
        `guid` it has never seen belongs to a session opened somewhere else,
        which is exactly the shape of playing a sealed game through a
        side-channel; `check_request` refuses a command it cannot attribute.
        """
        if not isinstance(body, dict):
            return None
        guid = body.get("guid")
        if not isinstance(guid, str):
            return None
        with self.state.lock:
            return self.state.session_games.get(guid)

    # -- sealing checks ----------------------------------------------------
    def _check_arm_is_keyless(self, path: str, body: Any, raw: bytes) -> None:
        """An arm that sends a credential has one, and a sealed arm has none.
        Either way the credential never goes upstream from here: we inject our
        own. What is recorded is that the arm had something to send."""
        for name in CREDENTIAL_HEADERS:
            value = self.headers.get(name)
            if value:
                self.state.incidents += 1
                self.cfg.run.incident(
                    "bypass_attempt",
                    "the arm supplied its own %s header; the arm is not sealed" % name,
                    path=path, header=name, header_len=len(value))
        if raw and looks_like_credential(raw.decode("utf-8", "replace")):
            self.state.incidents += 1
            self.cfg.run.incident(
                "credential_in_body",
                "a key-shaped string appeared in a request body",
                path=path, request_sha256=sha256(raw))

    def _deny(self, method: str, path: str, query: str, body: Any,
              verdict: Dict[str, Any]) -> None:
        self.state.denials += 1
        self.cfg.run.guard_block(
            game_id=verdict.get("game_id"), rule=verdict.get("rule"),
            reason=verdict.get("reason"), path=path, query=query,
            method=method, peer=self.client_address[0],
            cut_sha256=verdict.get("cut_sha256"))
        self.cfg.run.incident(
            "sealed_pile_request",
            verdict.get("reason"), game_id=verdict.get("game_id"),
            rule=verdict.get("rule"), path=path)

        if COMMAND.match(path):
            # A refused command is still a step: a refusal is evidence, not an
            # absence (LEDGER_FORMAT.md §3).
            name = COMMAND.match(path).group(1)
            self.cfg.run.env_step(
                game_id=(body or {}).get("game_id") or verdict.get("game_id") or "?",
                action={"name": name, "id": _action_id(name), "data": (body or {}).get("data")},
                frames=None,
                card_id=(body or {}).get("card_id"),
                guid=(body or {}).get("guid"),
                guard={"decision": "deny", "rule": verdict.get("rule"),
                       "reason": verdict.get("reason")},
                http={"method": method, "path": path, "status": 403,
                      "elapsed_ms": 0, "forwarded": False,
                      "request_sha256": sha256(body if body is not None else "")})
        self._respond(403, {
            "error": "refused by the sealed-pile guard",
            "rule": verdict.get("rule"),
            "game_id": verdict.get("game_id"),
            "detail": verdict.get("reason"),
        })

    # -- traffic -----------------------------------------------------------
    def _upstream_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        for name in PASSTHROUGH_REQUEST_HEADERS:
            value = self.headers.get(name)
            if value:
                headers[name.title()] = value
        if self.cfg.api_key:
            headers["X-API-Key"] = self.cfg.api_key
        return headers

    def _forward(self, method: str, path: str, query: str, raw: bytes) -> fwd.Response:
        """The only route to a socket in this proxy, and so the only place the
        spend gate has to sit.

        The pool's action unit is one outbound ARC HTTP request
        (`spend_policy.json`), which is what `forward` counts as an attempt, so
        the permit is minted for one action and `forward` re-checks it before
        every retry. The *record* is written afterwards, against the attempts
        that actually happened -- check prevents, record accounts, and a retry
        storm is charged for the requests it really made.
        """
        url = self.cfg.upstream + path + (("?" + query) if query else "")
        permit = self.cfg.spend_gate.permit(self.cfg.spend_reservation,
                                            usd=0.0, actions=1)
        try:
            response = fwd.forward(url, method, self._upstream_headers(),
                                   raw or None, timeout=self.cfg.timeout,
                                   max_attempts=self.cfg.max_attempts,
                                   permit=permit)
        except BaseException as exc:
            # The requests that DID happen are recorded even though the call
            # failed. Two ways the naive version under-counts: a permit refused
            # on attempt 3 raises, so there is no Response to read `attempts`
            # from -- while attempts 1 and 2 opened real sockets against the
            # real rate limit; and any exception between the socket and the
            # return would drop the whole request from the pool.
            self._charge(permit, path, original=exc)
            raise
        self._charge(permit, path)
        self._note_redirect(url, response)
        return response

    def _charge(self, permit, path: str, original=None) -> None:
        """Record the sockets this permit actually opened.

        `record` appends first and raises afterwards if the append breached a
        cap, so the money is on disk either way. What this adds is that a
        breach becomes a *ledger incident* rather than only a 500 the arm sees:
        INC-BA-003's whole complaint was that a budget stop left no trace anyone
        else could read.

        When an exception is already in flight, a breach raised from here is
        swallowed -- the refusal that stopped the request is the more
        informative one, and replacing it would hide why the call died.
        """
        if not permit.attempts_made:
            return
        try:
            self.cfg.spend_gate.record(
                self.cfg.spend_reservation, usd=0.0,
                actions=permit.attempts_made,
                detail={"proxy": "env", "run_id": self.cfg.run_id, "path": path})
        except SpendGateError as exc:
            self.state.incidents += 1
            self.cfg.run.incident(
                "spend_gate_refused",
                "the shared spend pool refused after %d request(s) on %s: %s"
                % (permit.attempts_made, path, exc),
                path=path, rule=getattr(exc, "rule", None),
                campaign=self.cfg.campaign)
            if original is None:
                raise

    def _note_redirect(self, url: str, response: fwd.Response) -> None:
        """A refused redirect is a record, for the same reason a refused
        command is: "nobody tried" and "somebody tried and was stopped" must
        not look the same in the ledger."""
        if response.redirect_to or fwd.crossed_hosts(url, response.final_url):
            self.state.incidents += 1
            self.cfg.run.incident(
                "redirect_refused",
                "the upstream answered %s with a redirect; it was not followed, "
                "because following it would replay the injected credential to "
                "the host it named" % response.status,
                intended=url, location=response.redirect_to,
                final_url=response.final_url)

    def _command(self, method: str, path: str, query: str, body: Any,
                 raw: bytes, match) -> None:
        name = match.group(1)
        body = body or {}
        game_id = body.get("game_id") or "?"
        runtime = self.state.runtime_for(game_id, self.cfg.variant)

        decision = runtime.before(name)
        applied: Optional[Dict[str, Any]] = None
        forwarded_path = path

        if isinstance(decision, Refusal):
            # The variant declines to forward. Nothing leaves this process.
            response_body = decision.body
            status, elapsed, attempts, attempt_log = decision.status, 0, 0, []
            applied = decision.applied
            forwarded = False
        else:
            if isinstance(decision, _Remap):
                applied = decision.applied
                forwarded_path = "/api/cmd/" + decision.action_name
            response = self._forward(method, forwarded_path, query, raw)
            status = response.status
            elapsed = response.elapsed_ms
            attempts = response.attempts
            attempt_log = response.attempt_log
            response_body = response.json()
            if response_body is None:
                response_body = {"raw": response.text}
            response_body, after_applied = runtime.after(response_body)
            if after_applied is not None:
                applied = after_applied if applied is None else {
                    "op": "multiple", "applied": [applied, after_applied]}
            forwarded = True

        with self.state.lock:
            self.state.commands += 1
            card_id = body.get("card_id")
            if card_id and card_id not in self.state.card_ids:
                self.state.card_ids.append(card_id)
            guid = (response_body or {}).get("guid") or body.get("guid")
            if guid:
                self.state.guids[game_id] = guid
                self.state.session_games[guid] = game_id

        frames = response_body.get("frame") if isinstance(response_body, dict) else None
        if frames is not None and not isinstance(frames, list):
            frames = [frames]

        http: Dict[str, Any] = {
            "method": method, "path": path, "status": status,
            "elapsed_ms": elapsed, "attempts": attempts,
            "forwarded": forwarded,
            "request_sha256": sha256(body),
        }
        if getattr(response, "final_url", None) if forwarded else None:
            http["final_url"] = response.final_url
        if forwarded and getattr(response, "redirect_to", None):
            http["redirect_refused_to"] = response.redirect_to
        if forwarded_path != path:
            http["forwarded_path"] = forwarded_path
        if attempts > 1:
            http["attempt_log"] = attempt_log

        # The rest of the response body, minus the frames it already stored
        # whole. The live API returns `win_levels`, `available_actions`,
        # `full_reset` and `action_input` on every command, and a record that
        # dropped them would not be the complete record Phase 1 claims.
        rest = None
        if isinstance(response_body, dict):
            rest = {k: v for k, v in response_body.items() if k != "frame"}

        self.cfg.run.env_step(
            game_id=game_id,
            action={"name": name, "id": _action_id(name), "data": body.get("data")},
            frames=frames,
            card_id=body.get("card_id"),
            guid=(response_body or {}).get("guid") or body.get("guid"),
            state=(response_body or {}).get("state"),
            score=(response_body or {}).get("score"),
            levels_completed=(response_body or {}).get("levels_completed"),
            variant=self.cfg.variant.reference(applied) if self.cfg.variant else None,
            response=rest,
            http=http,
        )
        self._note_degeneracy(runtime, game_id)
        self._respond(status if status > 0 else 502, response_body)

    def _note_degeneracy(self, runtime: VariantRuntime, game_id: str) -> None:
        """Once per session, when `win_tighten` first rewrote a WIN because the
        game reported no score at all.

        The `degenerate` bit on the `applied` record is the decision (D-032);
        this is one of the two things that read it. It is written after the
        `env_step` it refers to, so the incident always points at a record that
        already exists, and it fires once because a scoreless game produces the
        same rewrite on every WIN and a per-WIN incident would bury the first
        one under copies of itself."""
        if runtime.degenerate_wins != 1 or game_id in self.state.degeneracy_reported:
            return
        with self.state.lock:
            if game_id in self.state.degeneracy_reported:
                return
            self.state.degeneracy_reported.add(game_id)
            self.state.incidents += 1
        first = runtime.first_degenerate or {}
        self.cfg.run.incident(
            "variant_degenerate",
            first.get("note") or DEGENERATE_NOTE,
            game_id=game_id,
            variant_id=(self.cfg.variant.variant_id if self.cfg.variant else None),
            require_score=first.get("require_score"),
            reason=first.get("reason"))

    def _meta(self, method: str, path: str, query: str, body: Any, raw: bytes) -> None:
        """Everything that is not a game command: scorecard open/close, the game
        list. Recorded as `env_meta` so `env_step` keeps exactly one shape."""
        response = self._forward(method, path, query, raw)
        parsed = response.json()

        with self.state.lock:
            self.state.meta_calls += 1
            if isinstance(parsed, dict):
                card_id = parsed.get("card_id")
                if card_id and card_id not in self.state.card_ids:
                    self.state.card_ids.append(card_id)

        self.cfg.run.env_meta(
            request=body if body is not None else (raw.decode("utf-8", "replace") or None),
            response=parsed if parsed is not None else response.text,
            http={"method": method, "path": path, "query": query or None,
                  "status": response.status, "elapsed_ms": response.elapsed_ms,
                  "attempts": response.attempts, "forwarded": True,
                  "final_url": response.final_url,
                  "redirect_refused_to": response.redirect_to,
                  "request_sha256": sha256(body if body is not None else "")})
        self._respond(response.status if response.status > 0 else 502,
                      response.body, response.passthrough_headers())

    def _internal(self, path: str) -> None:
        if path == "/__proxy/health":
            return self._respond(200, {"ok": True, "run_id": self.cfg.run_id,
                                       "arm": self.cfg.arm})
        if path == "/__proxy/state":
            return self._respond(200, self.server.summary())            # type: ignore
        self._respond(404, {"error": "no such proxy endpoint"})


def _action_id(name: str) -> Optional[int]:
    return None if name == "RESET" else int(name.replace("ACTION", ""))


class EnvProxy:
    def __init__(self, config: EnvProxyConfig):
        self.cfg = config
        self.httpd = ThreadingHTTPServer((config.host, config.port), _Handler)
        self.httpd.cfg = config                                    # type: ignore[attr-defined]
        self.httpd.state = _State()                                # type: ignore[attr-defined]
        self.httpd.summary = self.summary                          # type: ignore[attr-defined]
        self.httpd.daemon_threads = True
        self._thread: Optional[threading.Thread] = None

    @property
    def port(self) -> int:
        return self.httpd.server_address[1]

    @property
    def base_url(self) -> str:
        return "http://%s:%d" % (self.cfg.host, self.port)

    def summary(self) -> Dict[str, Any]:
        state: _State = self.httpd.state                            # type: ignore[attr-defined]
        return {"run_id": self.cfg.run_id, "arm": self.cfg.arm,
                "upstream": self.cfg.upstream,
                "commands": state.commands, "meta_calls": state.meta_calls,
                "denials": state.denials, "incidents": state.incidents,
                "card_ids": list(state.card_ids), "guids": dict(state.guids),
                "variant": self.cfg.variant.fingerprint() if self.cfg.variant else None,
                "guard": self.cfg.guard.fingerprint(),
                "key_injected": bool(self.cfg.api_key)}

    def start(self) -> "EnvProxy":
        self._thread = threading.Thread(target=self.httpd.serve_forever,
                                        name="env-proxy", daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread:
            self._thread.join(timeout=5)
        # Give the unspent remainder back, but only if this proxy is the thing
        # that claimed it. A reservation the caller handed in belongs to the
        # caller's run, which may outlive this proxy; releasing it here would
        # hand back headroom the run still needs. Spend already recorded is
        # untouched either way -- release returns the hold, never the money.
        if self.cfg.spend_reservation_owned:
            self.cfg.spend_gate.release(self.cfg.spend_reservation,
                                        reason="env proxy stopped")

    def __enter__(self) -> "EnvProxy":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8711)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--arm", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--upstream", default=UPSTREAM_ARC)
    ap.add_argument("--ledger", default=LEDGER_PATH)
    ap.add_argument("--variant", default=None, help="variant_id from proxy/variants/")
    args = ap.parse_args(argv)

    variant = Variant.find(args.variant) if args.variant else None
    cfg = EnvProxyConfig(run_id=args.run_id, arm=args.arm, upstream=args.upstream,
                         ledger_path=args.ledger, variant=variant,
                         host=args.host, port=args.port)
    proxy = EnvProxy(cfg)
    print("env proxy on %s -> %s" % (proxy.base_url, cfg.upstream))
    print("  ledger : %s" % cfg.ledger.path)
    print("  guard  : %s" % canonical(cfg.guard.fingerprint()))
    print("  key    : injected here; the arm never sees it")
    try:
        proxy.httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        proxy.httpd.server_close()
        # The claim goes back on the way out. Without this, a Ctrl-C'd
        # standalone proxy holds its share of the shared pool for the full TTL
        # with nothing spent -- 40 of them take the pool offline for an hour
        # and the only recovery is to wait.
        if cfg.spend_reservation_owned:
            cfg.spend_gate.release(cfg.spend_reservation,
                                   reason="standalone proxy exited")
    return 0


if __name__ == "__main__":
    sys.exit(main())
