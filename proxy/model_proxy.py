"""The model proxy: the same trick, applied a second time.

An arm points its model base URL here and changes nothing else. The provider
credential is injected inside this process, so an arm holds neither of the two
keys it would need to leave the recorded path. With both proxies running, an
arm sees exactly two hosts on the network, and the ledger is generated at the
proxy rather than by each arm -- which is why three arms could not produce
three different ledger formats even if they tried.

What is recorded, per LEDGER_FORMAT.md §4:

  * the request body, whole, and the response body, whole -- because a model
    call is not replayable, so the full text is the substitute for replay;
  * the provider's `usage` block **verbatim**, not reshaped or summed;
  * a `pricing_ref` naming the price table. No dollar figure is written.

Run it standalone:

    python -m proxy.model_proxy --port 8712 --arm theoria --run-id r-001
"""

import argparse
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple

from . import forward as fwd
from .cost import DEFAULT_TABLE, PriceTable
from .ledger import Ledger, RunLedger, sha256
from .paths import LEDGER_PATH, UPSTREAM_MODEL
from .guard import SealedPileGuard
from .redact import VAULT, read_secret, scrub_outbound
from .spend_gate import (Reservation, SpendGate, SpendGateError,
                         attach_reservation, default_campaign, default_gate)

ANTHROPIC_VERSION = "2023-06-01"

PASSTHROUGH_REQUEST_HEADERS = ("content-type", "accept", "anthropic-version",
                               "anthropic-beta")

CREDENTIAL_HEADERS = ("x-api-key", "authorization", "api-key")


class ModelProxyConfig:
    def __init__(self, *, run_id: str, arm: str,
                 upstream: str = UPSTREAM_MODEL,
                 provider: str = "anthropic",
                 api_key: Optional[str] = None,
                 key_env: str = "ANTHROPIC_API_KEY",
                 require_key: bool = True,
                 ledger_path: str = LEDGER_PATH,
                 ledger: Optional[Ledger] = None,
                 run: Optional[RunLedger] = None,
                 pricing_table: str = DEFAULT_TABLE,
                 game_id: Optional[str] = None,
                 guard: Optional[SealedPileGuard] = None,
                 campaign: Optional[str] = None,
                 spend_gate: Optional[SpendGate] = None,
                 spend_reservation: Optional[Reservation] = None,
                 host: str = "127.0.0.1", port: int = 0,
                 timeout: float = 300.0,
                 max_attempts: int = 3):
        self.run_id = run_id
        self.arm = arm
        self.provider = provider
        self.upstream = upstream.rstrip("/")
        self.host = host
        self.port = port
        self.timeout = timeout
        self.max_attempts = max_attempts

        self.api_key = api_key if api_key is not None else read_secret(
            key_env, required=require_key)
        VAULT.register(self.api_key, force=True)

        self.ledger = ledger or Ledger(ledger_path)
        # A runner shares one RunLedger across both proxies so `call_idx` and
        # `step_idx` come from a single counter per run.
        # `game_id` here rather than only on the runner's shared RunLedger:
        # the standalone path builds its own, and every `model_call` it wrote
        # carried `game_id: null` -- the exact gap the Phase 2 battery raised.
        self.game_id = game_id
        self.run = run or RunLedger(self.ledger, run_id, arm, game_id=game_id)
        # The sealed-pile guard reads model traffic too. The cut's rule 2
        # counts *reading about* a sealed game as contamination, and a prompt
        # that names one teaches the model exactly that (RED-32).
        self.guard = guard if guard is not None else SealedPileGuard()
        try:
            self.pricing = PriceTable.load(pricing_table)
        except KeyError:
            self.pricing = None

        # Same footing as the guard: constructed here if not handed in, never
        # a flag, never absent. This is the proxy that spends dollars, so it is
        # the one whose `record` carries a price -- and an unpriced call is
        # recorded as unpriced rather than as zero, which is what stops the
        # pool's dollar total from silently becoming a lower bound.
        self.campaign = campaign or default_campaign(arm, run_id)
        self.spend_gate = spend_gate if spend_gate is not None else default_gate()
        self.spend_reservation_owned = spend_reservation is None
        self.spend_reservation = attach_reservation(
            self.spend_gate, self.campaign, spend_reservation,
            holder={"proxy": "model", "run_id": run_id, "arm": arm})


class _State:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.calls = 0
        self.errors = 0
        self.step_idx: Optional[int] = None       # set by the arm via a header


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "theoria-model-proxy/1.0"

    def log_message(self, fmt, *args):
        pass

    @property
    def cfg(self) -> ModelProxyConfig:
        return self.server.cfg                                     # type: ignore[attr-defined]

    @property
    def state(self) -> _State:
        return self.server.state                                   # type: ignore[attr-defined]

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def _respond(self, status: int, body: bytes,
                 headers: Optional[Dict[str, str]] = None) -> None:
        # The arm holds no credential, and a provider that echoes ours back in
        # a body or a header is a way for it to acquire one (RED-12).
        body, headers, leaked = scrub_outbound(bytes(body), dict(headers or {}),
                                               VAULT)
        if leaked:
            self.cfg.run.incident(
                "credential_reflected",
                "the provider returned a registered credential to the arm in "
                "%s; it was removed before the arm saw it" % ", ".join(leaked),
                path=self.path.partition("?")[0], places=leaked)
        self.send_response(status)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        if not headers or not any(k.lower() == "content-type" for k in headers):
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle(self, method: str) -> None:
        path, _, query = self.path.partition("?")
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw.decode("utf-8")) if raw else None
        except (json.JSONDecodeError, UnicodeDecodeError):
            body = None

        if path.startswith("/__proxy/"):
            if path == "/__proxy/health":
                return self._respond(200, json.dumps(
                    {"ok": True, "run_id": self.cfg.run_id, "arm": self.cfg.arm}).encode())
            if path == "/__proxy/state":
                return self._respond(200, json.dumps(
                    self.server.summary()).encode())                # type: ignore[attr-defined]
            return self._respond(404, b'{"error":"no such proxy endpoint"}')

        for name in CREDENTIAL_HEADERS:
            if self.headers.get(name):
                self.cfg.run.incident(
                    "bypass_attempt",
                    "the arm supplied its own %s header to the model proxy" % name,
                    path=path, header=name)

        # The arm may declare which env_step this call is deciding. It is the
        # only thing an arm gets to add to the ledger, and it is metadata, not
        # content -- the battery needs a per-turn axis for cost.
        verdict = self.cfg.guard.check_request(path, query, body, raw=raw,
                                               headers=self.headers)
        if verdict["decision"] == "deny":
            self.cfg.run.guard_block(
                game_id=verdict.get("game_id"), rule=verdict.get("rule"),
                reason=verdict.get("reason"), path=path, query=query or None,
                method=method, peer=self.client_address[0],
                cut_sha256=verdict.get("cut_sha256"), surface="model_proxy")
            self.cfg.run.incident(
                "sealed_pile_in_prompt", verdict.get("reason"),
                game_id=verdict.get("game_id"), rule=verdict.get("rule"),
                path=path)
            return self._respond(403, json.dumps({
                "error": "refused by the sealed-pile guard",
                "rule": verdict.get("rule"),
                "game_id": verdict.get("game_id"),
                "detail": verdict.get("reason")}).encode())

        declared_step = self.headers.get("X-Theoria-Step")
        step_idx: Optional[int] = None
        if declared_step is not None:
            try:
                step_idx = int(declared_step)
            except ValueError:
                step_idx = None

        # What this call could cost, BEFORE the socket opens. `cost()` prices a
        # call after the fact, which is the only way to know what it really
        # cost and therefore useless as a gate -- an adversarial pass put $600
        # through a $10 ceiling in one call for exactly that reason. A call
        # with no computable ceiling is refused rather than sent: it is
        # unbounded, and the pool has no way to notice it going by.
        ceiling = (self.cfg.pricing.ceiling_for(body) if self.cfg.pricing
                   else {"usd": None, "why": "no pricing table is loaded"})
        if ceiling.get("usd") is None:
            self.cfg.run.incident(
                "spend_gate_refused",
                "this request has no computable cost ceiling, so it was not "
                "sent: %s" % ceiling.get("why"),
                path=path, campaign=self.cfg.campaign)
            return self._respond(402, json.dumps({
                "error": "refused by the shared spend gate",
                "rule": "NO_COST_CEILING",
                "detail": ceiling.get("why")}).encode())

        try:
            response = self._forward(method, path, query, raw,
                                     usd=ceiling["usd"])
        except BaseException:
            # The request may or may not have reached the provider. It is
            # charged at its ceiling either way and flagged unpriced, because
            # the alternative -- assume it cost nothing -- is the assumption
            # that lets a provider decide whether it gets billed.
            self._charge(ceiling["usd"], unpriced=True, path=path,
                         why="the call raised before a price could be computed",
                         swallow=True)
            raise
        parsed = response.json()
        streamed = "text/event-stream" in (
            response.headers.get("Content-Type", "").lower())

        if streamed:
            usage, events, assembled = _parse_sse(response.text)
            recorded_response: Any = {"stream": True, "assembled": assembled,
                                      "stream_events": events}
        else:
            usage = (parsed or {}).get("usage") if isinstance(parsed, dict) else None
            recorded_response = parsed if parsed is not None else response.text

        with self.state.lock:
            self.state.calls += 1
            if response.status >= 400 or response.status < 0:
                self.state.errors += 1

        http: Dict[str, Any] = {
            "method": method, "path": path, "status": response.status,
            "elapsed_ms": response.elapsed_ms, "attempts": response.attempts,
            "stream": streamed, "request_sha256": sha256(body if body is not None else ""),
        }
        if response.attempts > 1:
            http["attempt_log"] = response.attempt_log

        # The real price, or the ceiling if the real price cannot be had.
        #
        # Three ways the naive version under-recorded, all found adversarially
        # and all resolved the same way -- **charge the ceiling and flag it**:
        #   * cost() raises on a usage value json.loads accepts but int() does
        #     not (1e999, "1e5"), and five real calls produced no record at all;
        #   * a missing or empty usage block priced to $0.00 with the unpriced
        #     flag OFF, so the pool did not even know it was blind;
        #   * an SSE stream cut before message_delta loses output_tokens, which
        #     is the expensive half of the bill at 5x the input rate.
        # In every one of those, the provider's response decided whether the
        # call was billed. It does not any more.
        model_name = (body or {}).get("model") if isinstance(body, dict) else None
        try:
            priced = self.cfg.pricing.cost(model_name or "?", usage or {})
        except Exception as exc:                            # noqa: BLE001
            priced = {"usd": None,
                      "unpriced": "pricing raised on the response: %s: %s"
                                  % (type(exc).__name__, exc)}
        # A price is usable only if the usage block carries **both** halves of
        # the bill. Not `usd > 0`: a model legitimately priced at $0.00 with a
        # complete usage block is *priced*, not blind, and flagging it would
        # jam the pool on nothing. What this does catch is the case a stream
        # produces -- `input_tokens` arrives in `message_start` and
        # `output_tokens` only in `message_delta`, so an SSE response cut short
        # yields a plausible, positive, and badly wrong figure that misses the
        # expensive half at 5x the input rate.
        required = ("input_tokens", "output_tokens")
        usable = (priced.get("usd") is not None
                  and isinstance(usage, dict)
                  and all(key in usage for key in required))
        if usable:
            self._charge(priced["usd"], unpriced=False, path=path, why=None,
                         model=model_name, status=response.status)
        else:
            self._charge(ceiling["usd"], unpriced=True, path=path,
                         why=(priced.get("unpriced")
                              or "the response carried no usable usage block, "
                                 "so the call is charged at its pre-flight "
                                 "ceiling"),
                         model=model_name, status=response.status)

        self.cfg.run.model_call(
            provider=self.cfg.provider,
            model=(body or {}).get("model") if isinstance(body, dict) else None,
            request=body if body is not None else (raw.decode("utf-8", "replace") or None),
            response=recorded_response,
            usage=usage or {},
            pricing_ref=self.cfg.pricing.reference() if self.cfg.pricing else None,
            step_idx=step_idx,
            http=http,
        )
        self._respond(response.status if response.status > 0 else 502,
                      response.body, response.passthrough_headers())

    def _charge(self, usd: float, *, unpriced: bool, path: str,
                why, model=None, status=None, swallow: bool = False) -> None:
        """Put the money on disk, and make a refusal visible to more than the arm."""
        try:
            self.cfg.spend_gate.record(
                self.cfg.spend_reservation, usd=float(usd), actions=0,
                unpriced=unpriced,
                detail={"proxy": "model", "run_id": self.cfg.run_id,
                        "model": model, "status": status, "path": path,
                        "unpriced": why})
        except SpendGateError as exc:
            self.cfg.run.incident(
                "spend_gate_refused",
                "the shared spend pool refused after a model call on %s: %s"
                % (path, exc),
                path=path, rule=getattr(exc, "rule", None),
                campaign=self.cfg.campaign)
            if not swallow:
                raise

    def _forward(self, method: str, path: str, query: str, raw: bytes,
                 usd: float = 0.0) -> fwd.Response:
        headers = {"Accept": "application/json",
                   "anthropic-version": ANTHROPIC_VERSION}
        for name in PASSTHROUGH_REQUEST_HEADERS:
            value = self.headers.get(name)
            if value:
                headers[name] = value
        if self.cfg.api_key:
            headers["x-api-key"] = self.cfg.api_key
        url = self.cfg.upstream + path + (("?" + query) if query else "")
        # The dollar cost is not knowable until the response's `usage` comes
        # back, so the pre-flight can only assert that *some* headroom exists.
        # `_handle` records the real price the moment it can compute it.
        permit = self.cfg.spend_gate.permit(self.cfg.spend_reservation,
                                            usd=usd, actions=0)
        return fwd.forward(url, method, headers, raw or None,
                           timeout=self.cfg.timeout,
                           max_attempts=self.cfg.max_attempts, permit=permit)


def _parse_sse(text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
    """Pull the usage block and the assembled message out of an SSE stream.

    Usage arrives in two places: `message_start` carries the input side,
    `message_delta` the output side. Merging them is the only reshaping done
    anywhere in this file, and it is a merge of the provider's own keys -- no
    key is renamed, no total is invented.
    """
    events: List[Dict[str, Any]] = []
    usage: Dict[str, Any] = {}
    text_parts: List[str] = []
    stop_reason = None
    model = None

    for block in text.split("\n\n"):
        for line in block.splitlines():
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if not payload or payload == "[DONE]":
                continue
            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                continue
            events.append(event)
            kind = event.get("type")
            if kind == "message_start":
                message = event.get("message") or {}
                model = message.get("model", model)
                usage.update(message.get("usage") or {})
            elif kind == "message_delta":
                usage.update(event.get("usage") or {})
                stop_reason = (event.get("delta") or {}).get("stop_reason", stop_reason)
            elif kind == "content_block_delta":
                delta = event.get("delta") or {}
                if delta.get("type") == "text_delta":
                    text_parts.append(delta.get("text", ""))

    assembled = {"model": model, "stop_reason": stop_reason,
                 "text": "".join(text_parts)}
    return usage, events, assembled


class ModelProxy:
    def __init__(self, config: ModelProxyConfig):
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
                "provider": self.cfg.provider, "upstream": self.cfg.upstream,
                "calls": state.calls, "errors": state.errors,
                "pricing": self.cfg.pricing.reference() if self.cfg.pricing else None,
                "key_injected": bool(self.cfg.api_key)}

    def start(self) -> "ModelProxy":
        self._thread = threading.Thread(target=self.httpd.serve_forever,
                                        name="model-proxy", daemon=True)
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
                                        reason="model proxy stopped")

    def __enter__(self) -> "ModelProxy":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8712)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--arm", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--game", default=None,
                    help="the game this run plays; goes on every model_call")
    ap.add_argument("--upstream", default=UPSTREAM_MODEL)
    ap.add_argument("--provider", default="anthropic")
    ap.add_argument("--ledger", default=LEDGER_PATH)
    args = ap.parse_args(argv)

    cfg = ModelProxyConfig(run_id=args.run_id, arm=args.arm, game_id=args.game, upstream=args.upstream,
                           provider=args.provider, ledger_path=args.ledger,
                           host=args.host, port=args.port)
    proxy = ModelProxy(cfg)
    print("model proxy on %s -> %s" % (proxy.base_url, cfg.upstream))
    print("  ledger : %s" % cfg.ledger.path)
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
