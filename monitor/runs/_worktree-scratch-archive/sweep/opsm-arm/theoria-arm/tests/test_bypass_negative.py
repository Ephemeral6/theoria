"""The negative sample: build the bypass, then show it is refused *and* recorded.

Everything else in this suite asks whether the arm does its job. This file asks
the opposite question -- what happens when the arm misbehaves -- because a seal
that has only ever been tested from the well-behaved side has not been tested.

Three properties are pinned here, and **they are separate on purpose**:

1. **Refusal, before the socket.** A sealed-pile id sent down the arm's own
   environment path (`harness.run.Run` -> `EnvProxy` -> upstream) gets a 403
   and the upstream records **zero** requests. The positive control is half the
   test: a development-pile id through the identical path *does* open the
   socket. A guard that refuses everything proves nothing.

2. **Recording.** The refusal reaches the ledger as a `guard_block` plus an
   `incident`, carrying the game id, the rule and the sha256 of the cut it was
   decided under.

3. **Credential stripping, asserted as an outcome.** `proxy/env_proxy.py`'s
   `_check_arm_is_keyless` only *logs* a `bypass_attempt` -- there is no
   `return` and no `_respond`, so control falls straight through to the guard
   and then to `_forward`. What actually holds the property is a different
   mechanism entirely: `_upstream_headers` **rebuilds** the outbound headers
   from the `PASSTHROUGH_REQUEST_HEADERS` allowlist, which contains no
   credential header. Recording is the observation point; the allowlist is the
   enforcement point, and they can drift apart silently.

   So the assertion here is on what the **upstream received**, not on what the
   ledger says. If anybody ever adds `authorization` to that allowlist, the
   incident record will look exactly as it does today and this test will go red
   anyway. That is the whole reason it is written this way.

Zero network: the "upstream" is a `http.server` on 127.0.0.1 that records every
request it is handed and answers from a canned envelope. Sealed-pile games are
touched by **identifier only** -- the id is read out of the cut, never any
content about the game.
"""

import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                          # noqa: E402,F401

from harness import budget as budget_mod                   # noqa: E402
from harness.arc import ArcThroughProxy                    # noqa: E402
from harness.run import FIXTURE_RUNS_DIR, Run              # noqa: E402
from proxy.ledger import read_ledger                       # noqa: E402
from proxy.paths import PILES                              # noqa: E402

#: Not a real credential and not shaped like one -- it stands in for the key the
#: proxy injects, so the test can tell the proxy's header apart from the arm's.
PROXY_KEY = "upstream-key-for-the-instrumented-stub"

#: What a rogue arm would put in its own header. Deliberately unmistakable: the
#: test greps the whole recorded upstream request for it.
ARM_SUPPLIED = "an-arm-supplied-credential-value-0123456789"

CANNED_RESET = {
    "guid": "stub-session-0000",
    "frame": [[[0, 0], [0, 0]]],
    "state": "NOT_FINISHED",
    "score": 0,
    "win_score": 1,
    "available_actions": [1, 2, 3, 4, 5],
    "action_input": {"id": 0},
}


# ------------------------------------------------------- the instrumented host
class _Recorder(BaseHTTPRequestHandler):
    """Answers everything 200 and remembers exactly what it was handed.

    It is deliberately permissive. The mock ARC in `proxy/mock` refuses an
    unauthenticated request, which would make "the sealed game was not played"
    ambiguous between *the guard stopped it* and *the upstream rejected it*.
    This one would happily serve any id it is asked for, so a game that does not
    appear in `hits` was stopped on this side of the wire and nowhere else.
    """

    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):                     # silence
        return

    def do_GET(self):                                      # noqa: N802
        self._handle("GET")

    def do_POST(self):                                     # noqa: N802
        self._handle("POST")

    def _handle(self, method: str) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        self.server.record(method, self.path, self.headers, raw)   # type: ignore[attr-defined]
        payload = json.dumps(CANNED_RESET).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class InstrumentedUpstream:
    """A local stand-in for `https://three.arcprize.org`. Records, never judges."""

    def __init__(self) -> None:
        self.hits: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    # -- lifecycle ---------------------------------------------------------
    def __enter__(self) -> "InstrumentedUpstream":
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Recorder)
        server.daemon_threads = True
        server.record = self._record                       # type: ignore[attr-defined]
        self._server = server
        self._thread = threading.Thread(target=server.serve_forever,
                                        kwargs={"poll_interval": 0.05},
                                        daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)

    @property
    def base_url(self) -> str:
        assert self._server is not None
        host, port = self._server.server_address[:2]
        return "http://%s:%d" % (host, port)

    # -- what it saw -------------------------------------------------------
    def _record(self, method: str, path: str, headers, raw: bytes) -> None:
        with self._lock:
            self.hits.append({
                "method": method,
                "path": path,
                # Every header, exactly as received, plus a case-folded view.
                "header_items": [(k, v) for k, v in headers.items()],
                "headers": {k.lower(): v for k, v in headers.items()},
                "body": raw.decode("utf-8", "replace"),
            })

    def blob(self) -> str:
        """Everything that crossed the wire, as one string to search."""
        with self._lock:
            return json.dumps(self.hits)


# ------------------------------------------------------------------- helpers
def _cut() -> Dict[str, Any]:
    with open(PILES, encoding="utf-8") as fh:
        return json.load(fh)


def sealed_id() -> str:
    """One sealed-pile **identifier**, read from the cut.

    Read rather than hard-coded so the test follows the cut if it is ever
    widened deliberately; and it is an id and nothing else -- no game content is
    opened here or anywhere downstream, because the upstream is a stub that
    never had any.
    """
    return sorted(_cut()["sealed_pile"])[0]


def dev_id() -> str:
    return sorted(_cut()["dev_pile"])[0]


def arm_run(upstream: InstrumentedUpstream, tmp_path, slug: str) -> Run:
    """A `Run` exactly as `harness.run.play` builds one, pointed at the stub.

    This is the arm's real environment path -- the same `EnvProxy`, the same
    `SealedPileGuard()` constructed inside `Run.__init__` with no way for a
    caller to swap or disable it -- with only the upstream host replaced.

    The spend pool is the one exception, and it has to be: `spend_gate=None`
    resolves to the *tracked* pool, and `harness.spend` refuses that from
    inside pytest because 59% of its recorded action count turned out to have
    been written by tests. A pool this test owns keeps the environment path
    identical while leaving the fleet's ceiling alone -- what is under test
    here is `SealedPileGuard` and the credential header, neither of which reads
    the pool.
    """
    from proxy.spend_gate import SpendGate             # noqa: PLC0415
    from harness.run import _scratch_policy            # noqa: PLC0415

    policy = _scratch_policy(str(tmp_path / "scratch-pool.jsonl"))
    gate = SpendGate(policy)
    return Run(dev_id(), slug,
               env_upstream=upstream.base_url,
               env_key=PROXY_KEY, require_key=False,
               env_max_attempts=1,
               runs_root=FIXTURE_RUNS_DIR,
               spend_gate=gate,
               expect_pool={"pool": policy.pool,
                            "ledger_abspath": os.path.abspath(
                                policy.ledger_path)},
               ledger_path=str(tmp_path / "ledger.jsonl"))


def post(base: str, path: str, body: Dict[str, Any],
         headers: Optional[Dict[str, str]] = None):
    """A raw POST at the proxy: an arm that has stopped using its own client.

    `harness.arc.ArcThroughProxy` cannot send a credential header -- it has no
    code path that builds one, which `test_arm.py` already pins at the source.
    A bypass attempt is by definition an arm that is not using that client, so
    the credential half of this file goes around it.
    """
    request = urllib.request.Request(
        base.rstrip("/") + path, data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"error": raw}


def records(tmp_path, event: str) -> List[Dict[str, Any]]:
    return [r for r in read_ledger(str(tmp_path / "ledger.jsonl"))
            if r["event"] == event]


# ------------------------------------------------ 1. refusal, before the socket
def test_a_sealed_id_through_the_arms_environment_path_never_reaches_a_socket(tmp_path):
    """The negative sample. Sealed id in, 403 out, and the upstream saw nothing.

    "Saw nothing" is the load-bearing half. A 403 alone would be satisfied by a
    proxy that forwards the request and then decides it did not like it -- and
    by then the sealed game has been touched, which is the harm the cut exists
    to prevent. The stub would have served the id happily; the count of what it
    received is therefore a direct measurement of whether the guard runs before
    the socket or after it.
    """
    game = sealed_id()
    with InstrumentedUpstream() as upstream:
        with arm_run(upstream, tmp_path, "pytest-sealed-" + os.path.basename(str(tmp_path))) as run:
            client = ArcThroughProxy(run.env_base, game, budget_mod.Budget())
            status, body = client.reset()

        assert status == 403, body
        assert body["rule"] == "sealed_pile"
        assert body["game_id"] == game

        # Zero. Not "no gameplay request" -- zero requests of any kind.
        assert upstream.hits == [], upstream.hits
        # And the id itself never crossed the wire in any form.
        assert game not in upstream.blob()
        assert game.split("-")[0] not in upstream.blob()


def test_a_development_id_through_the_identical_path_does_open_the_socket(tmp_path):
    """The positive control, and the reason the test above means anything.

    Same `Run`, same guard object, same stub, same client, same call -- only the
    id differs. If this one ever fails, the file above is proving that the proxy
    is broken rather than that the guard is working.
    """
    game = dev_id()
    with InstrumentedUpstream() as upstream:
        with arm_run(upstream, tmp_path, "pytest-dev-" + os.path.basename(str(tmp_path))) as run:
            client = ArcThroughProxy(run.env_base, game, budget_mod.Budget())
            status, body = client.reset()

        assert status == 200, body
        assert [h["path"] for h in upstream.hits] == ["/api/cmd/RESET"]
        assert json.loads(upstream.hits[0]["body"])["game_id"] == game


# ------------------------------------------------------------- 2. the recording
def test_the_refusal_is_written_to_the_ledger_with_the_cut_it_was_decided_under(tmp_path):
    """A refusal nobody can read afterwards is indistinguishable from nobody
    having tried (LEDGER_FORMAT.md's rule that a refusal is evidence, not an
    absence). So: the record exists, and it carries the fields that make it
    auditable -- which game, which rule, and the sha256 of the cut in force.
    """
    game = sealed_id()
    with InstrumentedUpstream() as upstream:
        with arm_run(upstream, tmp_path, "pytest-record-" + os.path.basename(str(tmp_path))) as run:
            run_id = run.run_id
            ArcThroughProxy(run.env_base, game, budget_mod.Budget()).reset()

    blocks = [r for r in records(tmp_path, "guard_block") if r["run_id"] == run_id]
    assert len(blocks) == 1
    block = blocks[0]
    assert block["game_id"] == game
    assert block["rule"] == "sealed_pile"
    assert block["path"] == "/api/cmd/RESET"
    assert block["method"] == "POST"
    assert block["arm"] == "theoria"
    assert game in block["reason"]
    # Which cut said so. Without this the record cannot be re-decided later.
    assert block["cut_sha256"] == _cut()["sha256"]

    incidents = [r for r in records(tmp_path, "incident") if r["run_id"] == run_id]
    assert [i["kind"] for i in incidents] == ["sealed_pile_request"]
    assert incidents[0]["game_id"] == game
    assert incidents[0]["rule"] == "sealed_pile"

    # A refused command is still a step, and it says so: forwarded is False.
    steps = [r for r in records(tmp_path, "env_step") if r["run_id"] == run_id]
    assert len(steps) == 1
    assert steps[0]["http"]["status"] == 403
    assert steps[0]["http"]["forwarded"] is False
    assert steps[0]["guard"]["decision"] == "deny"


# ------------------------------------- 3. credential stripping, as an outcome
@pytest.mark.parametrize("header", ["Authorization", "X-API-Key"])
def test_a_credential_header_the_arm_sends_never_reaches_the_upstream(tmp_path, header):
    """The property, checked where it is enforced rather than where it is logged.

    `_check_arm_is_keyless` writes a `bypass_attempt` and falls through; the
    request is then forwarded like any other. Nothing is stopped. What keeps the
    arm's credential out of the world is `_upstream_headers` rebuilding the
    outbound headers from `PASSTHROUGH_REQUEST_HEADERS` -- and that allowlist is
    an ordinary tuple in an ordinary module that anybody can extend.

    Hence the assertion below is `ARM_SUPPLIED not in <what the upstream got>`,
    over the whole recorded request, headers and body alike. Asserting that an
    incident was written would pass unchanged on the day the allowlist grows --
    verified, not assumed: with `authorization` added to the allowlist the
    outcome assertion goes red while every `bypass_attempt` assertion below it
    stays green.

    The two parameters are not protected by the same mechanism, which is worth
    knowing before trusting either. `authorization` is held out by the allowlist
    alone. `x-api-key` is held out twice: by the allowlist, and -- were it ever
    allowlisted -- by `urllib.request.Request.add_header` capitalising header
    names, so a passed-through `X-Api-Key` collides with the `X-API-Key` the
    proxy injects and is overwritten by it. That second mechanism is incidental
    to a transport detail and must not be counted on; the allowlist is the one
    to keep.
    """
    game = dev_id()
    with InstrumentedUpstream() as upstream:
        with arm_run(upstream, tmp_path, "pytest-cred-" + os.path.basename(str(tmp_path))) as run:
            run_id = run.run_id
            status, _ = post(run.env_base, "/api/cmd/RESET", {"game_id": game},
                             headers={header: ARM_SUPPLIED})

    # It was forwarded -- the header did not stop it, which is exactly the
    # point being made: the incident is an observation, not an intervention.
    assert status == 200
    assert len(upstream.hits) == 1
    hit = upstream.hits[0]

    # The outcome. Nowhere in what the upstream received.
    assert ARM_SUPPLIED not in upstream.blob()
    assert hit["headers"].get("authorization") is None
    # ...and the key the upstream *did* see is the one the proxy injected, so
    # this is not passing merely because no credential travelled at all.
    assert hit["headers"].get("x-api-key") == PROXY_KEY

    # Recording, which is a separate mechanism and is asserted separately.
    incidents = [r for r in records(tmp_path, "incident")
                 if r["run_id"] == run_id and r["kind"] == "bypass_attempt"]
    assert len(incidents) == 1
    assert incidents[0]["header"] == header.lower()
    assert incidents[0]["header_len"] == len(ARM_SUPPLIED)
    # The ledger records that a value existed, never the value.
    assert ARM_SUPPLIED not in open(str(tmp_path / "ledger.jsonl"),
                                    encoding="utf-8").read()


def test_a_sealed_id_carrying_the_arms_own_credential_is_still_refused_first(tmp_path):
    """The two failures composed: the guard runs whether or not the arm brought
    a key, and the socket still never opens."""
    game = sealed_id()
    with InstrumentedUpstream() as upstream:
        with arm_run(upstream, tmp_path, "pytest-both-" + os.path.basename(str(tmp_path))) as run:
            run_id = run.run_id
            status, body = post(run.env_base, "/api/cmd/RESET", {"game_id": game},
                                headers={"Authorization": ARM_SUPPLIED})

    assert status == 403 and body["rule"] == "sealed_pile"
    assert upstream.hits == []
    kinds = sorted(r["kind"] for r in records(tmp_path, "incident")
                   if r["run_id"] == run_id)
    assert kinds == ["bypass_attempt", "sealed_pile_request"]
