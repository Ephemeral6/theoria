"""Conjunct one, measured: the arm process does not hold the game credential.

`Theoria.md` Phase 1 states the seal as two things at once -- no credential
inside the arm, and egress around the two proxies must fail. The second half has
been tested since `test_bypass_negative.py` was written. The first had **no test
anywhere in this arm**, and when A11 finally measured it with a sentinel key the
answer was that the credential was resident at `run._cfg.api_key` for the whole
run, because `Run.__init__` built an `EnvProxyConfig` and that constructor reads
`.env`.

So the property is now a process boundary (`harness/proxy_process.py`), and this
file is the instrument that says so. Four things are checked and they are
deliberately separate:

1. **Absence, positively.** A whole `--mock` game is played in a fresh
   interpreter in which `ARC_API_KEY` has been removed from the environment
   *and* `read_secret` has been replaced with something that raises. Green means
   the arm played a game it could not have read a key during.
2. **Presence, in the child.** With a sentinel key handed to the run, the
   instrumented upstream receives `X-API-Key: <sentinel>` -- so injection
   really happens, in the child -- while the sentinel appears nowhere in the
   parent's environment and nowhere in a recursive walk of the `Run` object
   graph. A test that only asserted absence would pass on a proxy that injects
   nothing at all.
3. **Lifecycle.** The handshake arrives, `stop()` leaves no process behind,
   `stop()` twice is not an error, and a child that cannot start raises with
   its own log tail instead of hanging.
4. **One chain, two writers.** After a real run the ledger holds the parent's
   `run_start`/`run_end` and the child's `env_step`, and `verify_chain` says
   PASS. Two processes appending to one hash chain is the thing this design
   asks the cross-process lock to do, so it is checked rather than argued.

Zero network and zero API calls: the "upstream" is a loopback stub, or
`proxy/mock`. No sentinel used here is shaped like a real credential, and no
assertion prints one -- every check is `not in`, so a failure reports the
absence it wanted rather than the value it found.

Phase 1's seal is a conjunction and this file is only half of it: the other
half -- that no game identifier reaches *model* context -- is the desk's pile
screen, pinned in `test_desk_pile_screen.py`. The two live apart because they
fail apart: this one goes red when the process boundary is undone, that one
when the cut is widened or the scanner is bypassed.
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
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                          # noqa: E402,F401

from harness import budget as budget_mod                   # noqa: E402
from harness import run as run_mod                         # noqa: E402
from harness import spend as spend_mod                     # noqa: E402
from harness.arc import ArcThroughProxy                    # noqa: E402
from harness.proxy_process import (STUB_KEY_ENV,           # noqa: E402
                                   EnvProxyProcess,
                                   EnvProxyStartupError)
from harness.run import FIXTURE_RUNS_DIR, Run              # noqa: E402
from proxy.ledger import read_ledger                       # noqa: E402
from proxy.paths import PILES                              # noqa: E402
from proxy.spend_gate import SpendGate                     # noqa: E402

#: Not shaped like a credential -- `proxy/redact.py:looks_like_credential`
#: would raise an incident on a 32-character alphanumeric run, and this test is
#: about where a value lives, not about the detector.
SENTINEL = "sentinel-key-for-the-seal-test-do-not-use"

CANNED = {
    "guid": "stub-session-0000",
    "frame": [[[0, 0], [0, 0]]],
    "state": "NOT_FINISHED",
    "score": 0,
    "win_score": 1,
    "available_actions": [1, 2, 3, 4, 5],
    "action_input": {"id": 0},
}


# ------------------------------------------------------------- the stub host
class _Recorder(BaseHTTPRequestHandler):
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
        payload = json.dumps(CANNED).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class Upstream:
    """A loopback stand-in for the ARC host. Records; never judges.

    Its own copy rather than an import from `test_bypass_negative.py`: pytest
    puts the tests directory on `sys.path`, so importing one test module from
    another happens to work and makes the two files a package that is not one.
    """

    def __init__(self) -> None:
        self.hits: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def __enter__(self) -> "Upstream":
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

    def _record(self, method: str, path: str, headers, raw: bytes) -> None:
        with self._lock:
            self.hits.append({
                "method": method, "path": path,
                "headers": {k.lower(): v for k, v in headers.items()},
                "body": raw.decode("utf-8", "replace"),
            })

    def blob(self) -> str:
        with self._lock:
            return json.dumps(self.hits)


# ------------------------------------------------------------------- helpers
def _cut() -> Dict[str, Any]:
    with open(PILES, encoding="utf-8") as fh:
        return json.load(fh)


def dev_id() -> str:
    return sorted(_cut()["dev_pile"])[0]


def _own_pool(tmp_path):
    """A scratch pool. Never the fleet's shared one -- see test_arm.py."""
    policy = run_mod._scratch_policy(str(tmp_path / "scratch-pool.jsonl"))
    gate = SpendGate(policy)
    return gate, {"pool": policy.pool,
                  "ledger_abspath": os.path.abspath(policy.ledger_path)}


def arm_run(upstream: Upstream, tmp_path, slug: str, *,
            env_key: Optional[str] = SENTINEL) -> Run:
    gate, expect = _own_pool(tmp_path)
    return Run(dev_id(), slug,
               env_upstream=upstream.base_url,
               env_key=env_key, require_key=False,
               env_max_attempts=1,
               runs_root=FIXTURE_RUNS_DIR,
               spend_gate=gate, expect_pool=expect,
               ledger_path=str(tmp_path / "ledger.jsonl"))


def walk_repr(root: Any, needle: str, limit: int = 4000) -> List[str]:
    """Every path in an object graph whose string form contains `needle`.

    A recursive walk rather than one `repr(run)`: `repr` on a `Run` is the
    default `<Run object at 0x...>` and would find nothing whatever the object
    held, which is the shape of a test that passes because it never looked.
    Returns paths only -- never the matched value.
    """
    seen: set = set()
    found: List[str] = []
    stack = [("run", root, 0)]
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


# ------------------------------------------- 1. absence, in a fresh interpreter
DRIVER = r'''
"""Play one whole mock game with no way to read a secret. Prints JSON."""
import json, os, sys, tempfile

ARM = sys.argv[1]
sys.path.insert(0, ARM)

# (i) the documented way the key gets into a shell -- undone.
os.environ.pop("ARC_API_KEY", None)

import _bootstrap                                          # noqa: F401

# (ii) and the way it gets into a process -- made impossible. Both the
# definition and the name `proxy.env_proxy` bound at import time, because
# rebinding only one of them proves only that one of them was unused.
import proxy.redact as redact
import proxy.env_proxy as env_proxy


def forbidden(*args, **kwargs):
    raise AssertionError("the arm process tried to read a secret: %r" % (args,))


redact.read_secret = forbidden
env_proxy.read_secret = forbidden

from harness import run as run_mod, spend as spend_mod
from proxy.mock.arc_mock import DEFAULT_KEY, MockArc
from proxy.spend_gate import SpendGate

tmp = tempfile.mkdtemp()
policy = run_mod._scratch_policy(os.path.join(tmp, "pool.jsonl"))
gate = SpendGate(policy)
expect = {"pool": policy.pool,
          "ledger_abspath": os.path.abspath(policy.ledger_path)}
game = sys.argv[2]

from harness import budget as budget_mod
from harness.arc import ArcThroughProxy


class TinyArm:
    def __init__(self, env_base, game_id):
        self.client = ArcThroughProxy(env_base, game_id,
                                      budget_mod.Budget(actions=4))
        self.steps = 0

    def play(self):
        status, body = self.client.reset()
        self.steps += 1
        for action in (1, 2):
            status, body = self.client.act(action)
            self.steps += 1
        return {"outcome": "ok", "steps": self.steps, "status": status}

    def summary(self):
        return {"steps": self.steps}


with MockArc(api_key=DEFAULT_KEY, games=[game]) as arc:
    caps = spend_mod.plan_caps(actions=8, commands=50, cost_ceiling_usd=None,
                               gate=gate)
    outcome = run_mod.play(
        game, "pytest-keyless-" + os.path.basename(tmp),
        lambda env_base, run: TinyArm(env_base, game),
        env_upstream=arc.base_url, env_key=DEFAULT_KEY, require_key=False,
        caps=caps, spend_gate=gate, expect_pool=expect,
        ledger_path=os.path.join(tmp, "ledger.jsonl"),
        runs_root=run_mod.FIXTURE_RUNS_DIR)
    upstream_hits = len(arc.requests) if hasattr(arc, "requests") else None

print("RESULT " + json.dumps({
    "outcome": outcome.get("outcome"),
    "steps": outcome.get("steps"),
    "ledger": os.path.join(tmp, "ledger.jsonl"),
    "had_key_in_env": "ARC_API_KEY" in os.environ,
}))
'''


def test_a_whole_game_is_played_by_a_process_that_cannot_read_a_secret(tmp_path):
    """The core assertion, and the only honest way to make it.

    Asserting `"ARC_API_KEY" not in os.environ` inside this interpreter would
    prove nothing: pytest's environment is whatever the shell had. So the run
    happens in a child of its own with the variable removed and `read_secret`
    replaced by something that raises -- and it still completes a game. The
    environment proxy that served it read a key of its own, in *its* process,
    which is the whole architecture in one sentence.
    """
    driver = tmp_path / "keyless_driver.py"
    driver.write_text(DRIVER, encoding="utf-8")

    env = dict(os.environ)
    env.pop("ARC_API_KEY", None)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(driver), ARM, dev_id()],
        cwd=ARM, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300)

    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    line = [l for l in proc.stdout.splitlines() if l.startswith("RESULT ")]
    assert line, proc.stdout + "\n" + proc.stderr
    result = json.loads(line[-1][len("RESULT "):])

    assert result["outcome"] == "ok", result
    assert result["steps"] >= 3, result
    assert result["had_key_in_env"] is False


# ------------------------------------------ 2. presence in the child, not here
def test_the_key_is_injected_by_the_child_and_is_not_in_the_parent(tmp_path):
    """Injection happens; it just does not happen here.

    The positive half is the upstream's received header. Without it, "the
    sentinel is nowhere in the parent" would be satisfied by a proxy that
    injects nothing, which is not a seal -- it is a broken proxy.
    """
    with Upstream() as upstream:
        with arm_run(upstream, tmp_path, "pytest-sentinel-"
                     + os.path.basename(str(tmp_path))) as run:
            client = ArcThroughProxy(run.env_base, dev_id(),
                                     budget_mod.Budget(actions=2))
            status, _ = client.reset()
            assert status == 200

            # The child injected it.
            assert upstream.hits, "the stub upstream was never reached"
            assert upstream.hits[0]["headers"].get("x-api-key") == SENTINEL

            # This process did not hold it.
            assert SENTINEL not in os.environ.values()
            assert STUB_KEY_ENV not in os.environ, (
                "the stub channel belongs to the child's environment; finding "
                "it here means the parent's own environment was mutated")
            where = walk_repr(run, SENTINEL)
            assert where == [], (
                "the sentinel is reachable from the Run object graph at: %s"
                % ", ".join(where))


def test_the_supervisor_drops_the_stub_key_once_the_child_has_it(tmp_path):
    """Stated as its own test because it is the mechanism the one above relies
    on: `EnvProxyProcess` holds the value between construction and `start()`
    and not one statement longer."""
    with Upstream() as upstream:
        run = arm_run(upstream, tmp_path,
                      "pytest-drop-" + os.path.basename(str(tmp_path)))
        assert run.proxy._env_key == SENTINEL          # before start
        try:
            with run:
                assert run.proxy._env_key is None      # after
        finally:
            run.spend.release("test over")


# --------------------------------------------------------------- 3. lifecycle
def test_the_handshake_arrives_and_the_child_is_reaped(tmp_path):
    with Upstream() as upstream:
        with arm_run(upstream, tmp_path, "pytest-life-"
                     + os.path.basename(str(tmp_path))) as run:
            proxy = run.proxy
            child = proxy.proc
            assert child is not None and child.poll() is None
            assert proxy.handshake["port"] == proxy.port
            assert proxy.handshake["pid"] == child.pid
            assert proxy.handshake["key_injected"] is True
            # The handshake carries the cut the child is enforcing, so the
            # parent does not have to take the child's guard on trust.
            assert proxy.handshake["guard"]["n_sealed"] == 21

        # Out of the `with`: Windows has no SIGTERM, so this is the assertion
        # that `POST /__proxy/shutdown` actually stopped a process rather than
        # leaving one holding a port and a credential.
        assert child.poll() is not None


def test_stopping_twice_is_not_an_error(tmp_path):
    with Upstream() as upstream:
        with arm_run(upstream, tmp_path, "pytest-stop2-"
                     + os.path.basename(str(tmp_path))) as run:
            proxy = run.proxy
        proxy.stop()
        proxy.stop()


def test_a_child_that_cannot_start_raises_with_its_log_and_frees_the_claim(tmp_path):
    """The failure path, and the reason `Run.__enter__` keeps its try/except.

    A run whose proxy never came up must not leave a claim on the shared pool
    for the lease's whole duration -- 43 crashed runs did exactly that once and
    the recovery was to wait an hour. The child is made to fail deterministically
    by naming a variant that does not exist, which raises in `Variant.find`
    before the socket is bound.
    """
    gate, expect = _own_pool(tmp_path)
    caps = spend_mod.plan_caps(actions=4, commands=20, cost_ceiling_usd=None,
                               gate=gate)
    run = Run(dev_id(), "pytest-badstart-" + os.path.basename(str(tmp_path)),
              env_upstream="http://127.0.0.1:1", env_key=SENTINEL,
              require_key=False, caps=caps, spend_gate=gate,
              expect_pool=expect, runs_root=FIXTURE_RUNS_DIR,
              ledger_path=str(tmp_path / "ledger.jsonl"))
    run.proxy.variant_id = "no-such-variant-anywhere"
    run.proxy.startup_timeout = 30.0

    with pytest.raises(EnvProxyStartupError) as exc:
        run.__enter__()

    assert "no-such-variant-anywhere" in str(exc.value), str(exc.value)
    assert gate.totals().live == [], "a failed start stranded the claim"


def test_the_supervisor_reports_a_timeout_rather_than_hanging(tmp_path):
    """A child that comes up too slowly is a failure with a message, not a
    wedged run. Driven with an interpreter argument that cannot serve anything,
    so no port is ever published."""
    proxy = EnvProxyProcess(
        run_id="r-timeout", arm="theoria", upstream="http://127.0.0.1:1",
        ledger_path=str(tmp_path / "ledger.jsonl"),
        env_key=SENTINEL, require_key=False,
        work_dir=str(tmp_path), startup_timeout=20.0)
    proxy.variant_id = "no-such-variant-anywhere"
    started = time.time()
    with pytest.raises(EnvProxyStartupError):
        proxy.start()
    assert time.time() - started < 60
    assert proxy.proc is None


# -------------------------------------------------- 4. one chain, two writers
def test_one_ledger_two_processes_one_unbroken_chain(tmp_path):
    """The cross-process lock, exercised rather than cited.

    The parent writes `run_start` and `run_end`; the child writes `env_step`.
    Both append to the same file, interleaved in real time, each re-reading the
    tail inside a lock on a sidecar file. If that were wrong the chain would
    fork and `verify_chain` would say so.
    """
    from proxy.tools.verify_chain import verify              # noqa: PLC0415

    ledger = str(tmp_path / "ledger.jsonl")
    with Upstream() as upstream:
        with arm_run(upstream, tmp_path, "pytest-chain-"
                     + os.path.basename(str(tmp_path))) as run:
            run.start_record()
            client = ArcThroughProxy(run.env_base, dev_id(),
                                     budget_mod.Budget(actions=3))
            client.reset()
            client.act(1)
            run.end_record(outcome="ok", steps=2)

    events = [r["event"] for r in read_ledger(ledger)]
    assert events[0] == "run_start", events
    assert events[-1] == "run_end", events
    assert events.count("env_step") == 2, events

    report = verify(ledger)
    assert report["verdict"] == "PASS", report

    # And the two writers really are two processes: the child's records carry
    # its pid nowhere, so the evidence is that this interpreter never called
    # `env_step` -- the counter it would have used is untouched.
    assert run.run._step_idx == -1, (
        "the parent assigned a step index, so the env proxy ran in-process")
