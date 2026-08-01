"""Conjunct one, measured: the bare_cc arm process does not hold the game key.

`Theoria.md` Phase 1 states the seal as two things at once -- no credential
inside the arm, **and** egress around the proxy must fail. `STATUS.md` GAP-5
registered on 2026-07-31 that this track satisfied neither: `load_api_key()`
opened `.env` inside the arm, `ArcClient.__init__` parked the value in
`self._key` for the whole run, and every call went straight to ARC. That was
not a leak -- the value was simply resident, in the interpreter that also runs
`claude -p`.

The property is now a process boundary (`harness/key_proxy.py` supervising
`harness/key_proxy_server.py`) and this file is the instrument that says so.
Five things are checked, deliberately apart, because they fail apart:

1. **Absence, positively.** A whole mock game -- scorecard open, RESET, three
   model-driven ACTIONs, scorecard close -- is played in a *fresh interpreter*
   from which `ARC_API_KEY` has been removed, and it completes. Asserting
   `"ARC_API_KEY" not in os.environ` inside pytest would prove nothing, since
   pytest's environment is whatever the shell had.
2. **Presence, in the child.** With a sentinel handed to the run, the mock
   upstream receives `X-API-Key: <sentinel>` -- injection really happens --
   while the sentinel appears nowhere in the parent's environment and nowhere
   in a recursive walk of the client or the supervisor. A test that only
   asserted absence would pass on a proxy that injects nothing at all, so the
   negative control (a proxy started with no key) is here too.
3. **The removed path is removed.** `arc_client.load_api_key()` raises, and a
   keyless client refuses to reach the real upstream at all rather than
   sending an unauthenticated request and paying an action for the 401.
4. **The proxy does not launder.** A client that *does* hold a key is refused
   by the child rather than forwarded -- otherwise this proxy would be the
   thing that hides GAP-5 instead of the thing that closes it.
5. **Nothing measured moved.** The cookie jar still works across the extra hop
   (arc-recon INC-007: 20/20 first-attempt RESETs with a jar, 0/20 without),
   the probe log still names the upstream rather than the loopback, and a
   transport failure is still `-1` rather than the proxy's own status.

Zero network and zero spend: the "upstream" is a loopback stub in this process
and `bare_cc.call_model` is replaced by a canned envelope, so no `claude -p`
runs. No sentinel here is shaped like a credential, and no assertion prints
one -- every check is `not in`, so a failure reports the absence it wanted
rather than the value it found.

    cd baseline-arms && python -m pytest tests/test_seal_process.py -q
"""

import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.dirname(HERE)
sys.path.insert(0, TRACK)

from harness import arc_client, bare_cc, key_proxy, ledger, spend  # noqa: E402

#: Not shaped like a credential: this test is about *where a value lives*, not
#: about any detector, and a key-shaped literal in a tracked test file is the
#: thing CLAUDE.md forbids outright.
SENTINEL = "sentinel-key-for-the-seal-test-do-not-use"

#: Development pile. Naming a sealed game here would be an incident.
DEV_GAME = "ar25-0c556536"

CANNED_FRAME = [[[0, 0], [0, 0]]]


# --------------------------------------------------------------- mock upstream
class _Recorder(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):                       # silence
        return

    def do_GET(self):                                        # noqa: N802
        self._handle("GET")

    def do_POST(self):                                       # noqa: N802
        self._handle("POST")

    def _handle(self, method: str) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        first = self.server.record(method, self.path, self.headers, raw)  # type: ignore[attr-defined]

        if self.path.startswith("/api/scorecard/open"):
            payload: Any = {"card_id": "card-mock-0001"}
        elif self.path.startswith("/api/scorecard/close"):
            payload = {"card_id": "card-mock-0001", "score": 0, "total_actions": 3}
        elif self.path.startswith("/api/games"):
            payload = [{"game_id": DEV_GAME}]
        else:                                                # RESET / ACTIONn
            payload = {"guid": "mock-session-0000", "frame": CANNED_FRAME,
                       "state": "NOT_FINISHED", "score": 0, "win_score": 1,
                       "available_actions": [1, 2, 3, 4, 5],
                       "action_input": {"id": 0},
                       "levels_completed": 0, "win_levels": 1}

        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if first:
            # Shaped like the real ALB's, including the two attributes that
            # would otherwise strand the jar one hop away: `Domain` for a host
            # the arm is no longer talking to, and `Secure` on a loopback hop
            # that is plain http. `key_proxy_server.rewrite_set_cookie` is what
            # makes these survive, and the jar test below is what proves it.
            self.send_header("Set-Cookie",
                             "AWSALBAPP-0=ROUTINGVALUE; Domain=three.arcprize.org; "
                             "Path=/; Secure; HttpOnly")
            self.send_header("Set-Cookie",
                             "GAMESESSION=SESSIONVALUE; Domain=three.arcprize.org; "
                             "Path=/; Secure; HttpOnly")
        self.end_headers()
        self.wfile.write(body)


class Upstream:
    """A loopback stand-in for the ARC host. Records; never judges."""

    def __init__(self) -> None:
        self.hits: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def __enter__(self) -> "Upstream":
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Recorder)
        server.daemon_threads = True
        server.record = self._record                         # type: ignore[attr-defined]
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

    def _record(self, method: str, path: str, headers, raw: bytes) -> bool:
        with self._lock:
            first = not self.hits
            self.hits.append({
                "method": method, "path": path,
                "headers": {k.lower(): v for k, v in headers.items()},
                "body": raw.decode("utf-8", "replace"),
            })
            return first

    def blob(self) -> str:
        with self._lock:
            return json.dumps(self.hits)

    def key_headers(self) -> List[Optional[str]]:
        with self._lock:
            return [hit["headers"].get("x-api-key") for hit in self.hits]


# --------------------------------------------------------------------- helpers
@pytest.fixture(autouse=True)
def no_ledger_writes(monkeypatch):
    """Replace the writer, do not redirect it.

    `ledger.probe(kind, detail, path=PROBE_PATH)` binds its default at
    definition time, so monkeypatching the module attribute is ignored and the
    call lands in this track's real, append-only `probe_log.jsonl`. Test noise
    in a tracked append-only file cannot be tidied afterwards. `_append` is the
    single funnel every writer goes through, so replacing it cannot write
    anywhere by construction.
    """
    monkeypatch.setattr(ledger, "_append", lambda path, entry: None)


def walk_repr(root: Any, needle: str, limit: int = 4000) -> List[str]:
    """Every path in an object graph whose string form contains `needle`.

    A recursive walk rather than one `repr(obj)`: `repr` on an `ArcClient` is
    the default `<ArcClient object at 0x...>` and would find nothing whatever
    the object held, which is the shape of a test that passes because it never
    looked. Returns paths only -- never the matched value.

    Its own copy rather than an import from `theoria-arm`: that is another
    territory, and this track may not depend on its test helpers.
    """
    seen: set = set()
    found: List[str] = []
    stack = [("root", root, 0)]
    while stack and len(seen) < limit:
        path, node, depth = stack.pop()
        if depth > 6 or id(node) in seen:
            continue
        seen.add(id(node))
        if isinstance(node, str):
            if needle in node:
                found.append(path)
            continue
        if isinstance(node, (bytes, bytearray)):
            if needle.encode() in bytes(node):
                found.append(path)
            continue
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(key, str) and needle in key:
                    found.append("%s[key %s]" % (path, key))
                stack.append(("%s[%r]" % (path, key), value, depth + 1))
            continue
        if isinstance(node, (list, tuple, set, frozenset)):
            for index, value in enumerate(node):
                stack.append(("%s[%d]" % (path, index), value, depth + 1))
            continue
        attrs = getattr(node, "__dict__", None)
        if isinstance(attrs, dict):
            for key, value in attrs.items():
                stack.append(("%s.%s" % (path, key), value, depth + 1))
    return found


def sealed_client(proxy, binding, **kwargs):
    return arc_client.ArcClient(base_url=proxy.base_url, spend_binding=binding,
                                **kwargs)


# ============================ 1. absence, in a fresh interpreter ==============
DRIVER = r'''
"""Play a whole mock game in a process that has no key and cannot read one."""
import json, os, sys, threading, tempfile

TRACK = sys.argv[1]
sys.path.insert(0, TRACK)
sys.path.insert(0, os.path.join(TRACK, "tests"))

# (i) the documented way the key gets into a shell -- undone, before anything
#     in this track is imported.
os.environ.pop("ARC_API_KEY", None)

from harness import arc_client, bare_cc, key_proxy, ledger, spend
from test_seal_process import DEV_GAME, SENTINEL, Upstream

# (ii) nothing is written to the tracked append-only ledgers, and no `claude -p`
#      is ever started: the model is a canned envelope, so this costs nothing.
ledger._append = lambda path, entry: None
bare_cc.call_model = lambda prompt, model, cwd, timeout=300: {
    "result": "ACTION 1", "is_error": False, "total_cost_usd": 0.0,
    "usage": {"input_tokens": 10, "output_tokens": 5},
    "_elapsed_ms": 1,
}

# (iii) the reader is not merely unused here, it is unreachable: the arm's own
#       entry point raises, and the module that *can* read was never imported
#       by the supervisor the arm uses.
read_path_raises = False
try:
    arc_client.load_api_key()
except arc_client.CredentialInArmError:
    read_path_raises = True

supervisor_imported_the_reader = "harness.key_proxy_server" in sys.modules

from proxy.spend_gate import SpendPolicy

tmp = tempfile.mkdtemp()
gate = spend.SpendGate(policy=SpendPolicy({
    "pool": "a19-seal-driver",
    "usd_ceiling": 10.0,
    "action_ceiling": 500,
    "ledger": os.path.join(tmp, "spend_gate.jsonl"),
    "default_run_caps": {"usd": 1.0, "actions": 10},
    "default_ttl_seconds": 600,
}))
binding = spend.SpendBinding(gate, gate.reserve("a19-seal", 5.0, 200))

with Upstream() as upstream:
    with key_proxy.sealed_upstream(run_id="a19-driver",
                                   upstream=upstream.base_url,
                                   env_key=SENTINEL) as proxy:
        summary = bare_cc.play(DEV_GAME, "claude-haiku-4-5-20251001", 3,
                               spend_binding=binding, verbose=False,
                               base_url=proxy.base_url)
        key_headers = [h["headers"].get("x-api-key") for h in upstream.hits]
        paths = [h["path"] for h in upstream.hits]

print("RESULT " + json.dumps({
    "outcome": summary.get("outcome"),
    "actions_ok": summary.get("actions_ok"),
    "model_calls": summary.get("model_calls"),
    "had_key_in_env": "ARC_API_KEY" in os.environ,
    "read_path_raises": read_path_raises,
    "supervisor_imported_the_reader": supervisor_imported_the_reader,
    "sentinel_in_parent_env": SENTINEL in os.environ.values(),
    "stub_channel_in_parent_env": key_proxy.STUB_KEY_ENV in os.environ,
    "upstream_hits": len(key_headers),
    "every_hit_carried_the_sentinel": bool(key_headers) and all(
        h == SENTINEL for h in key_headers),
    "reset_was_reached": any(p.endswith("/api/cmd/RESET") for p in paths),
    "actions_were_reached": sum(1 for p in paths if "/api/cmd/ACTION" in p),
}))
'''


def test_a_whole_mock_game_is_played_by_a_process_that_holds_no_key(tmp_path):
    """The core assertion, and the only honest way to make it.

    A fresh interpreter with `ARC_API_KEY` removed plays the game end to end:
    scorecard, RESET, three ACTIONs, close. Green means the arm completed a
    game it could not have read a key during -- the credential was in the
    child, one hop away, the whole time.
    """
    driver = tmp_path / "keyless_driver.py"
    driver.write_text(DRIVER, encoding="utf-8")

    env = dict(os.environ)
    env.pop("ARC_API_KEY", None)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run([sys.executable, str(driver), TRACK],
                          cwd=TRACK, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)

    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    lines = [l for l in proc.stdout.splitlines() if l.startswith("RESULT ")]
    assert lines, proc.stdout + "\n" + proc.stderr
    result = json.loads(lines[-1][len("RESULT "):])

    # It played.
    assert result["outcome"] == "budget_exhausted", result
    assert result["actions_ok"] == 3, result
    assert result["model_calls"] == 3, result
    assert result["reset_was_reached"] is True, result
    assert result["actions_were_reached"] == 3, result

    # And it could not have held a key while doing so.
    assert result["had_key_in_env"] is False
    assert result["read_path_raises"] is True
    assert result["supervisor_imported_the_reader"] is False, (
        "harness.key_proxy imported the module that reads .env; the whole "
        "point of the two-module split is that the arm's supervisor cannot")
    assert result["sentinel_in_parent_env"] is False
    assert result["stub_channel_in_parent_env"] is False

    # The positive half: injection happened, in the child, on every call.
    assert result["upstream_hits"] >= 5, result
    assert result["every_hit_carried_the_sentinel"] is True, result


# ==================== 2. presence in the child, absence in the parent =========
def test_the_key_is_injected_by_the_child_and_is_not_in_this_process(scratch_binding):
    """Injection happens; it just does not happen here."""
    with Upstream() as upstream:
        with key_proxy.KeyProxyProcess(run_id="a19-sentinel",
                                       upstream=upstream.base_url,
                                       env_key=SENTINEL) as proxy:
            api = sealed_client(proxy, scratch_binding)
            status, _ = api.reset(DEV_GAME, "card-1")
            assert status == 200

            # The child injected it.
            assert upstream.key_headers() == [SENTINEL]

            # This process never held it.
            assert SENTINEL not in os.environ.values()
            assert key_proxy.STUB_KEY_ENV not in os.environ, (
                "the stub channel belongs to the child's environment; finding "
                "it here means this process's environment was mutated")
            assert api._key is None
            for name, obj in (("client", api), ("supervisor", proxy)):
                where = walk_repr(obj, SENTINEL)
                assert where == [], (
                    "the sentinel is reachable from the %s object graph at: %s"
                    % (name, ", ".join(where)))


def test_a_proxy_with_no_key_injects_nothing(scratch_binding):
    """The negative control for the test above.

    Without it, "the sentinel is nowhere in the parent" would also be satisfied
    by a proxy that injects nothing whatsoever -- which is not a seal, it is a
    broken proxy that would 401 against the real upstream.

    It is also the test that caught `resolve_key`'s first version, which read
    `.env` and only fell back to keyless when that failed. On this machine
    `.env` exists, so a control meant to demonstrate *absence* was starting a
    child holding the live credential. `--no-require-key` now means keyless
    outright, and this assertion is what says so on a machine that has a
    `.env` sitting right there.
    """
    with Upstream() as upstream:
        with key_proxy.KeyProxyProcess(run_id="a19-nokey",
                                       upstream=upstream.base_url,
                                       require_key=False) as proxy:
            assert proxy.handshake["key_injected"] is False
            api = sealed_client(proxy, scratch_binding)
            api.reset(DEV_GAME, "card-1")
            assert upstream.key_headers() == [None]


def test_no_require_key_does_not_fall_back_to_the_env_file():
    """The regression the control above caught, pinned where it cannot hide.

    Machine-independent on purpose: the integration control only demonstrates
    this on a host that *has* a `.env` to be wrongly picked up, and CI may not.
    `resolve_key` is where the decision lives, so that is where it is asserted.
    """
    from harness import key_proxy_server                     # noqa: PLC0415

    assert key_proxy_server.resolve_key(None, require_key=False) is None
    # And the stub channel is still optional in the same way.
    assert key_proxy_server.resolve_key("A_VARIABLE_THAT_IS_NOT_SET",
                                        require_key=False) is None
    with pytest.raises(key_proxy_server.KeyUnavailable):
        key_proxy_server.resolve_key("A_VARIABLE_THAT_IS_NOT_SET",
                                     require_key=True)


def test_the_supervisor_drops_the_stub_once_the_child_has_it(scratch_binding):
    """The mechanism the two tests above rest on: `KeyProxyProcess` holds the
    stub between construction and `start()` and not one statement longer."""
    with Upstream() as upstream:
        proxy = key_proxy.KeyProxyProcess(run_id="a19-drop",
                                          upstream=upstream.base_url,
                                          env_key=SENTINEL)
        assert proxy._env_key == SENTINEL              # before start
        with proxy:
            assert proxy._env_key is None              # after


# =========================== 3. the removed path is removed ===================
def test_the_old_direct_read_path_raises():
    """`STATUS.md` GAP-5 names `arc_client.py:137 load_api_key()` as the defect.

    It is still there, and it raises -- a reader following that pointer lands
    on the explanation rather than on a missing name.
    """
    with pytest.raises(arc_client.CredentialInArmError):
        arc_client.load_api_key()
    # Even pointed at a file that exists and is well formed: there is no
    # argument that turns this function back into a reader.
    with pytest.raises(arc_client.CredentialInArmError):
        arc_client.load_api_key(env_path=os.path.join(TRACK, "STATUS.md"))


def test_the_reader_still_exists_but_lives_in_the_child_module(tmp_path):
    """The negative control for the test above.

    A `load_api_key` that raised because the whole capability had been deleted
    would pass that test and break every live run. The capability moved; this
    is where it went, and it is not imported by anything the arm imports.
    """
    from harness import key_proxy_server                     # noqa: PLC0415

    env = tmp_path / ".env"
    env.write_text("# comment\nARC_API_KEY=not-a-real-key-for-this-test\n",
                   encoding="utf-8")
    assert key_proxy_server.read_api_key(env_path=str(env)) \
        == "not-a-real-key-for-this-test"

    with pytest.raises(key_proxy_server.KeyUnavailable):
        key_proxy_server.read_api_key(env_path=str(tmp_path / "absent.env"))

    empty = tmp_path / "empty.env"
    empty.write_text("OTHER=1\n", encoding="utf-8")
    with pytest.raises(key_proxy_server.KeyUnavailable):
        key_proxy_server.read_api_key(env_path=str(empty))


def test_a_keyless_client_refuses_the_real_upstream_before_the_socket(
        scratch_gate, monkeypatch):
    """Phase 1's second conjunct, made local and made cheap.

    Unproxied, this request would leave the machine unauthenticated, come back
    401, and cost an action against the shared pool on the way. It fails here
    instead: no socket, no charge.
    """
    binding = spend.SpendBinding(scratch_gate, scratch_gate.reserve("c", 5.0, 50))
    api = arc_client.ArcClient(spend_binding=binding)         # no key, real host
    assert api.proxied is False
    opened = []

    class Watching:
        def open(self, request, timeout=None):
            opened.append(1)
            raise OSError("should never be reached")

    monkeypatch.setattr(api, "_opener", Watching())
    with pytest.raises(arc_client.UnproxiedEgressError):
        api.request("GET", "/api/games", raise_on_error=False)

    assert opened == [], "the socket was opened before the refusal"
    assert scratch_gate.totals().actions == 0, "an action was charged for a call "\
        "that never happened"


def test_the_same_client_pointed_at_the_proxy_is_allowed(scratch_binding):
    """Negative control: the refusal above must be about the *destination*, not
    a client that can no longer make any request at all."""
    with Upstream() as upstream:
        with key_proxy.KeyProxyProcess(run_id="a19-allowed",
                                       upstream=upstream.base_url,
                                       env_key=SENTINEL) as proxy:
            api = sealed_client(proxy, scratch_binding)
            assert api.proxied is True
            status, _ = api.request("GET", "/api/games")
            assert status == 200
            assert len(upstream.hits) == 1


# ========================= 4. the proxy does not launder ======================
def test_a_client_that_holds_a_key_is_refused_not_forwarded(scratch_binding):
    """If the arm still has a credential, the proxy must not be the thing that
    makes that invisible."""
    with Upstream() as upstream:
        with key_proxy.KeyProxyProcess(run_id="a19-launder",
                                       upstream=upstream.base_url,
                                       env_key=SENTINEL) as proxy:
            api = sealed_client(proxy, scratch_binding, api_key="an-arm-held-key")
            status, body = api.request("GET", "/api/games", raise_on_error=False)
            assert status == 400
            assert body["error"] == "ARM_SENT_A_KEY"
            assert upstream.hits == [], "the arm's key reached the upstream"
            assert proxy.state()["denied_arm_key"] == 1


# ======================= 5. nothing that was measured moved ===================
def test_the_cookie_jar_survives_the_extra_hop(scratch_binding):
    """arc-recon INC-007, still holding one hop further away.

    The jar is the transport every figure in `BUDGET_REPORT.md` will be
    re-derived on: 20/20 first-attempt RESETs with it, 0/20 without. The
    upstream issues its cookies with `Domain=three.arcprize.org` and `Secure`,
    neither of which is true of the loopback hop, so without the child's
    rewrite the arm's jar would hold nothing and nothing would fail loudly.
    """
    with Upstream() as upstream:
        with key_proxy.KeyProxyProcess(run_id="a19-jar",
                                       upstream=upstream.base_url,
                                       env_key=SENTINEL) as proxy:
            api = sealed_client(proxy, scratch_binding)
            api.reset(DEV_GAME, "card-1")
            assert api.cookies_held() == ["AWSALBAPP-0", "GAMESESSION"], \
                "the jar did not survive the loopback hop"

            api.action(DEV_GAME, "card-1", "guid", 1)
            echoed = upstream.hits[1]["headers"].get("cookie") or ""
            assert "AWSALBAPP-0" in echoed and "GAMESESSION" in echoed, \
                "the second request did not echo the session back upstream"

            # And the redraw still does what D-005's envelope needs.
            api.clear_routing_cookies()
            assert api.cookies_held() == ["GAMESESSION"]


def test_the_rewrite_drops_only_the_two_attributes_it_must():
    """The unit behind the jar test, with its negative control.

    A rewrite that dropped more would silently widen a cookie's scope; one that
    dropped less would strand the jar. Both directions are asserted.
    """
    from harness.key_proxy_server import rewrite_set_cookie   # noqa: PLC0415

    raw = ("GAMESESSION=SESSIONVALUE; Domain=three.arcprize.org; Path=/; "
           "Secure; HttpOnly; Expires=Tue, 04 Aug 2026 00:00:00 GMT")
    out = rewrite_set_cookie(raw)

    assert "Domain=" not in out and "Secure" not in out
    assert out.startswith("GAMESESSION=SESSIONVALUE")
    for kept in ("Path=/", "HttpOnly", "Expires=Tue, 04 Aug 2026 00:00:00 GMT"):
        assert kept in out, kept
    # Negative control: the attributes really were in the input, so the
    # assertions above are not vacuously true of any string.
    assert "Domain=" in raw and "Secure" in raw
    # A header with neither is passed through untouched.
    assert rewrite_set_cookie("A=B; Path=/") == "A=B; Path=/"


def test_the_probe_log_names_the_upstream_not_the_loopback(scratch_binding,
                                                            monkeypatch):
    """`probe_log.jsonl` is append-only and spans the change.

    If `url` started pointing at an ephemeral `127.0.0.1:<port>`, every line
    written after this ticket would be incomparable with every line written
    before it -- and the port would be different on every run.
    """
    records = []
    monkeypatch.setattr(ledger, "probe",
                        lambda kind, detail, **kw: records.append(
                            {"kind": kind, **detail}) or records[-1])

    with Upstream() as upstream:
        with key_proxy.KeyProxyProcess(run_id="a19-probe",
                                       upstream=upstream.base_url,
                                       env_key=SENTINEL) as proxy:
            api = sealed_client(proxy, scratch_binding)
            api.reset(DEV_GAME, "card-1")

    entry = records[0]
    assert entry["url"] == "https://three.arcprize.org/api/cmd/RESET"
    assert entry["wire_url"].startswith("http://127.0.0.1:")
    assert entry["proxied"] is True
    assert "X-API-Key" not in entry["request_headers"], \
        "the arm still built a credential header"
    # The sentinel is not in the record either -- by any route.
    assert SENTINEL not in json.dumps(entry)


def test_a_transport_failure_is_still_minus_one(scratch_binding):
    """The taxonomy `probe_log.jsonl` has always used, preserved.

    The child answers 599 when it cannot reach the upstream at all, because
    "the upstream said something" and "the upstream could not be reached" are
    different facts. The arm maps it back, so no historical reader has to learn
    a new status.
    """
    # A port nothing listens on: the child comes up, the upstream does not exist.
    with key_proxy.KeyProxyProcess(run_id="a19-transport",
                                   upstream="http://127.0.0.1:1",
                                   env_key=SENTINEL) as proxy:
        api = sealed_client(proxy, scratch_binding)
        status, _ = api.request("GET", "/api/games", raise_on_error=False)
        assert status == -1, "a proxy-side transport failure changed status"
        assert proxy.state()["upstream_errors"] == 1


def test_the_track_ledgers_are_not_written_by_this_file(scratch_binding):
    """The guard for the fixture above: if it ever stops intercepting, this
    notices before a tracked append-only file grows test noise."""
    sizes = {}
    for name in ("ledger.jsonl", "probe_log.jsonl"):
        path = os.path.join(TRACK, name)
        sizes[path] = os.path.getsize(path) if os.path.exists(path) else 0

    with Upstream() as upstream:
        with key_proxy.KeyProxyProcess(run_id="a19-noledger",
                                       upstream=upstream.base_url,
                                       env_key=SENTINEL) as proxy:
            sealed_client(proxy, scratch_binding).request("GET", "/api/games")

    for path, before in sizes.items():
        after = os.path.getsize(path) if os.path.exists(path) else 0
        assert after == before, path


# ------------------------------------------------------------------ lifecycle
def test_the_handshake_arrives_and_the_child_is_reaped():
    with Upstream() as upstream:
        with key_proxy.KeyProxyProcess(run_id="a19-life",
                                       upstream=upstream.base_url,
                                       env_key=SENTINEL) as proxy:
            child = proxy.proc
            assert child is not None and child.poll() is None
            assert proxy.handshake["port"] == proxy.port
            assert proxy.handshake["pid"] == child.pid
            assert proxy.handshake["key_injected"] is True
            # The handshake reports a boolean, never a value.
            assert SENTINEL not in json.dumps(proxy.handshake)

        # Windows has no SIGTERM, so this is the assertion that
        # `POST /__keyproxy/shutdown` stopped a process rather than leaving one
        # holding a port and a credential.
        assert child.poll() is not None


def test_stopping_twice_is_not_an_error():
    with Upstream() as upstream:
        proxy = key_proxy.KeyProxyProcess(run_id="a19-stop2",
                                          upstream=upstream.base_url,
                                          env_key=SENTINEL)
        with proxy:
            pass
        proxy.stop()
        proxy.stop()


def test_a_child_that_cannot_start_raises_with_its_log_tail(monkeypatch):
    """The failure path, so a broken start is a message rather than a hang."""
    proxy = key_proxy.KeyProxyProcess(run_id="a19-badstart",
                                      upstream="http://127.0.0.1:1",
                                      env_key=SENTINEL, startup_timeout=20.0)
    monkeypatch.setattr(
        proxy, "_argv",
        lambda port_file: [sys.executable, "-c",
                           "import sys; print('deliberate A19 start failure'); "
                           "sys.exit(3)"])
    started = time.time()
    with pytest.raises(key_proxy.KeyProxyStartupError) as exc:
        proxy.start()
    assert "deliberate A19 start failure" in str(exc.value), str(exc.value)
    assert time.time() - started < 60
    assert proxy.proc is None


def test_sealed_upstream_restores_the_base_url_variable():
    """A helper that leaked a stale ephemeral port into the environment would
    send the next run at a closed socket."""
    previous = os.environ.get(key_proxy.BASE_URL_ENV)
    try:
        os.environ.pop(key_proxy.BASE_URL_ENV, None)
        with Upstream() as upstream:
            with key_proxy.sealed_upstream(run_id="a19-env",
                                           upstream=upstream.base_url,
                                           env_key=SENTINEL) as proxy:
                assert os.environ[key_proxy.BASE_URL_ENV] == proxy.base_url
                # And a client that is given nothing picks it up.
                assert arc_client.ArcClient().base_url == proxy.base_url
            assert key_proxy.BASE_URL_ENV not in os.environ

        os.environ[key_proxy.BASE_URL_ENV] = "http://127.0.0.1:9"
        with Upstream() as upstream:
            with key_proxy.sealed_upstream(run_id="a19-env2",
                                           upstream=upstream.base_url,
                                           env_key=SENTINEL):
                pass
            assert os.environ[key_proxy.BASE_URL_ENV] == "http://127.0.0.1:9"
    finally:
        if previous is None:
            os.environ.pop(key_proxy.BASE_URL_ENV, None)
        else:
            os.environ[key_proxy.BASE_URL_ENV] = previous
