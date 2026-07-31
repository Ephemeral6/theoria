"""The environment proxy as a **child process**, supervised from the arm.

## What this is for

`Theoria.md` Phase 1 states the seal as a conjunction: no credential inside the
arm, *and* egress that bypasses the two proxies must fail. The second conjunct
has held since the proxy was written -- `harness/arc.py` has no code path that
builds a credential header, and the upstream refuses an unauthenticated
request. The first did not.

`Run` used to build an `EnvProxyConfig` in its own `__init__`, and that
constructor's second statement is `read_secret("ARC_API_KEY")`. So the live
credential was resident at `run._cfg.api_key` and in the process-wide `VAULT`,
inside the same interpreter that runs the inner loop, the engines, and every
line of model-facing code. Nothing was leaking it; it was simply *there*, and
"the arm holds no credential" was false as written. A11's report and
`runs/20260730T1020Z-A3-SEAL-CONJUNCT-ONE/` measured it with a sentinel key.

The fix is a process boundary rather than more care. `python -m proxy.env_proxy`
is a complete standalone proxy; this module starts one, hands the arm a
`http://127.0.0.1:<port>` URL, and never learns the key. The child reads `.env`
itself. **The parent does not pass the credential and does not read it**, which
is why this is a seal and not a discipline: an arm-side bug cannot leak a value
its process never held.

## What did NOT change, on purpose

`proxy/env_proxy.py`'s in-process `EnvProxy` class stays exactly as it was.
`proxy/runner.py` runs the env proxy, the model proxy and a mock arm in one
interpreter, and the proxy track's own tests assert against the handler objects
directly. There is nothing to seal in either case -- the "arm" there is the
test -- and forking those flows onto a subprocess would buy nothing and cost
the ability to poke at internals. The seal is about *this* arm, so the change
is here.

## Windows, which is where this runs

* **No fork.** The child re-imports everything, so `cwd` is the repository root
  and `-m proxy.env_proxy` resolves from there. Nothing is inherited except the
  environment and the two log handles.
* **No SIGTERM.** `stop()` asks over HTTP first (`POST /__proxy/shutdown`),
  waits, and only then falls back to `terminate()`/`kill()`, which on Windows
  are both `TerminateProcess`.
* **The handshake is a file, not stdout.** The console encoding on this host is
  cp936 and mangles the child's banner; a parent that parsed stdout would be
  parsing mojibake. The child writes `{"port": ...}` by atomic rename and the
  parent polls for it.
* **A hard-killed parent must not strand the child.** An `atexit` hook covers a
  parent that raises; `--parent-pid` gives the child its own watchdog for the
  parent that does not get to run one.

## The ledger, written by two processes

The child writes `env_step` / `env_meta` / `guard_block` / `incident`; the
parent writes `run_start` / `run_end` / `model_call`. One file, one hash chain:
`proxy/ledger.py`'s `_ChainLock` is a cross-process lock on a sidecar file and
every append re-reads the tail inside it, so the chain is correct with two
writers. The step and call counters are disjoint by writer -- `_step_idx` is
consumed only by `env_step`, `_call_idx` only by `model_call` -- so nothing is
double-assigned either. `tests/test_seal_process.py` verifies the chain of a
real two-writer run rather than taking that on trust.
"""

import atexit
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

import _bootstrap                                     # noqa: F401  (sys.path)

#: The repository root, taken from `_bootstrap` rather than counted out in
#: `dirname` calls here. It is the child's working directory, and it is what
#: makes `-m proxy.env_proxy` resolve: there is no fork on Windows, so the
#: child imports from scratch and inherits none of this process's `sys.path`.
REPO = _bootstrap.REPO

#: The environment variable the child reads a *stub* key from.
#:
#: Mocks and offline proofs need the proxy to inject something, so they can tell
#: the proxy's header apart from an arm-supplied one. It travels as a variable
#: in the child's environment and never as a command-line argument: on Windows
#: any user can read another process's command line (`wmic process get
#: commandline`), and the arm's own tests would then be publishing a
#: key-shaped string to the whole machine every time they ran.
#:
#: It is a different name from `ARC_API_KEY` so that a stub run cannot fall
#: back to the real credential -- see `EnvProxyConfig.api_key_env`.
STUB_KEY_ENV = "ENV_PROXY_TEST_KEY"


class EnvProxyStartupError(RuntimeError):
    """The child never came up. Carries the tail of its log."""


class EnvProxyProcess:
    """One `python -m proxy.env_proxy` child, and the surface `Run` uses.

    `start()`, `stop()`, `base_url` and `summary()` are the same four names the
    in-process `EnvProxy` offers, so `harness/run.py` swaps one for the other
    without learning a new vocabulary.
    """

    def __init__(self, *, run_id: str, arm: str, upstream: str,
                 ledger_path: str,
                 campaign: Optional[str] = None,
                 reservation: Any = None,
                 spend_gate: Any = None,
                 max_attempts: int = 3,
                 timeout: float = 60.0,
                 env_key: Optional[str] = None,
                 require_key: bool = True,
                 variant_id: Optional[str] = None,
                 host: str = "127.0.0.1",
                 work_dir: Optional[str] = None,
                 startup_timeout: float = 30.0,
                 python: Optional[str] = None):
        self.run_id = run_id
        self.arm = arm
        self.upstream = upstream.rstrip("/")
        self.ledger_path = os.path.abspath(ledger_path)
        self.campaign = campaign
        self.reservation = reservation
        self.spend_gate = spend_gate
        self.max_attempts = max_attempts
        self.timeout = timeout
        self.require_key = require_key
        self.variant_id = variant_id
        self.host = host
        self.startup_timeout = startup_timeout
        self.python = python or sys.executable

        #: Held only until `start()` has handed it to the child, then dropped.
        #:
        #: This is not tidiness. `tests/test_seal_process.py` walks the whole
        #: `Run` object graph for a sentinel and asserts it is not there; a
        #: supervisor that kept the value would put a key back inside the arm
        #: by a shorter route than the one this class exists to close. A run is
        #: started once, so there is nothing to keep it for.
        self._env_key = env_key

        #: Where the child's log goes: the run directory, so a failure is
        #: diagnosable from the archive rather than from a temp path nobody
        #: kept. The handshake and the policy hand-off go somewhere else --
        #: they are transient, and a run directory is walked into a MANIFEST.
        self._work_dir = work_dir
        self._handshake_dir: Optional[str] = None
        self.port_file: Optional[str] = None
        self.proc: Optional[subprocess.Popen] = None
        self.port: Optional[int] = None
        self.handshake: Dict[str, Any] = {}
        self._log_path: Optional[str] = None
        self._log_handle = None
        self._atexit_hook = None
        self._last_summary: Dict[str, Any] = {}

    # -- addresses ---------------------------------------------------------
    @property
    def base_url(self) -> str:
        if self.port is None:
            raise RuntimeError("the environment proxy child is not started")
        return "http://%s:%d" % (self.host, self.port)

    @property
    def log_path(self) -> Optional[str]:
        return self._log_path

    # -- lifecycle ---------------------------------------------------------
    def start(self) -> "EnvProxyProcess":
        handshake_dir = tempfile.mkdtemp(prefix="env-proxy-")
        self._handshake_dir = handshake_dir
        port_file = os.path.join(handshake_dir, "env_proxy.port.json")
        self.port_file = port_file

        log_dir = self._work_dir or handshake_dir
        os.makedirs(log_dir, exist_ok=True)
        self._log_path = os.path.join(log_dir, "env_proxy.log")

        argv = self._argv(port_file, handshake_dir)
        env = self._child_env()
        # Dropped here rather than in `stop()`: the value is in the child's
        # environment from this line onwards and this object has no further use
        # for it.
        self._env_key = None

        self._log_handle = open(self._log_path, "ab")
        creation = 0
        if os.name == "nt":                                  # pragma: no cover
            creation = (getattr(subprocess, "CREATE_NO_WINDOW", 0)
                        | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        self.proc = subprocess.Popen(
            argv, cwd=REPO, env=env,
            stdin=subprocess.DEVNULL,
            stdout=self._log_handle, stderr=subprocess.STDOUT,
            creationflags=creation)

        self._atexit_hook = self._kill_quietly
        atexit.register(self._atexit_hook)

        try:
            self.handshake = self._await_handshake(port_file)
        except BaseException:
            self._kill_quietly()
            raise
        self.port = int(self.handshake["port"])
        self._await_health()
        return self

    def _argv(self, port_file: str, work: str) -> list:
        argv = [self.python, "-m", "proxy.env_proxy",
                "--host", self.host, "--port", "0",
                "--port-file", port_file,
                "--parent-pid", str(os.getpid()),
                "--arm", self.arm, "--run-id", self.run_id,
                "--upstream", self.upstream,
                "--ledger", self.ledger_path,
                "--max-attempts", str(self.max_attempts),
                "--timeout", str(self.timeout)]
        if self.variant_id:
            argv += ["--variant", self.variant_id]
        if self.campaign:
            argv += ["--campaign", self.campaign]
        if self.reservation is not None:
            argv += ["--reservation-id", self.reservation.reservation_id,
                     "--usd-cap", "%r" % float(self.reservation.usd_cap),
                     "--action-cap", str(int(self.reservation.action_cap))]
        policy_file = self._policy_file(work)
        if policy_file:
            argv += ["--spend-policy", policy_file]
        if self._env_key is not None:
            # A stub. The real key is never passed -- the child reads `.env`.
            argv += ["--api-key-env", STUB_KEY_ENV]
        if not self.require_key:
            argv += ["--no-require-key"]
        return argv

    def _policy_file(self, work: str) -> Optional[str]:
        """Where the child should read its spend policy from.

        `None` when the parent is on the tracked pool: the child's
        `default_gate()` finds the same file, and copying it would only create
        a second thing that can go stale.

        A test or an offline proof builds its policy in memory (a scratch pool
        in a temp directory), so there is no file for the child to load. The
        spec is written out here -- it is a handful of numbers and a path, no
        secrets -- and the child loads that. Without it the child would draw on
        the **real shared pool** while the parent drew on the scratch one, which
        is a fictional dollar landing in the fleet's money ledger.
        """
        gate = self.spend_gate
        if gate is None:
            return None
        policy = getattr(gate, "policy", None)
        spec = getattr(policy, "spec", None)
        if spec is None:
            return None
        source = getattr(policy, "source", None)
        if source and os.path.exists(source):
            return source
        path = os.path.join(work, "spend_policy.json")
        spec = dict(spec)
        # The child resolves a relative ledger against the pool root, which is
        # the same constant here and there -- but a scratch policy's path is
        # already absolute and this keeps it that way.
        spec["ledger"] = os.path.abspath(policy.ledger_path)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(spec, fh, indent=2, sort_keys=True)
            fh.write("\n")
        return path

    def _child_env(self) -> Dict[str, str]:
        """What the child inherits.

        The parent's environment, plus the stub-key channel when there is one.
        `ARC_API_KEY` is **not** added: for a live run the parent does not have
        it to add, and the child reads `.env` for itself.

        `PYTHONIOENCODING=utf-8` because the child's banner is read back out of
        a log file when startup fails, and the host console encoding is cp936;
        pinning both ends is what makes that tail legible.
        """
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        if self._env_key is not None:
            env[STUB_KEY_ENV] = self._env_key
        return env

    def _await_handshake(self, port_file: str) -> Dict[str, Any]:
        deadline = time.time() + self.startup_timeout
        while True:
            if os.path.exists(port_file):
                try:
                    with open(port_file, encoding="utf-8") as fh:
                        payload = json.load(fh)
                except (OSError, json.JSONDecodeError):
                    payload = None                  # mid-rename; poll again
                if isinstance(payload, dict) and payload.get("port"):
                    return payload
            code = self.proc.poll() if self.proc else None
            if code is not None:
                raise EnvProxyStartupError(
                    "the environment proxy child exited with %s before it "
                    "published a port. Its log tail:\n%s"
                    % (code, self._log_tail()))
            if time.time() >= deadline:
                raise EnvProxyStartupError(
                    "the environment proxy child did not publish a port within "
                    "%.0fs. Its log tail:\n%s"
                    % (self.startup_timeout, self._log_tail()))
            time.sleep(0.05)

    def _await_health(self) -> None:
        """One round trip, so `start()` returning means the socket answers.

        The port file says the server bound; it does not say a request will be
        served. The difference matters to the caller immediately after this,
        which is about to hand the URL to an arm.
        """
        try:
            self._get("/__proxy/health", timeout=10)
        except (urllib.error.URLError, OSError) as exc:
            # The tail is read *before* the child is killed: `_kill_quietly`
            # takes the log handle and the temp directory with it, and an error
            # message that says "(no log)" because the error path deleted the
            # log is worse than no error message.
            tail = self._log_tail()
            self._kill_quietly()
            raise EnvProxyStartupError(
                "the environment proxy child published port %s but did not "
                "answer /__proxy/health: %s. Its log tail:\n%s"
                % (self.port, exc, tail))

    def summary(self) -> Dict[str, Any]:
        """What the child has seen. Goes into `run_end` and `run.json`.

        Cached, because both readers can run after `stop()` on an error path
        and a summary that turns into `None` when the run failed is exactly the
        record the failure most needs.
        """
        try:
            self._last_summary = self._get("/__proxy/state", timeout=10)
        except (urllib.error.URLError, OSError, ValueError):
            pass
        return dict(self._last_summary)

    def stop(self) -> None:
        """Ask, wait, then insist. Idempotent.

        Hard-killing is safe by construction: the reservation is attached and
        not owned, so the claim is the parent's to release (`Run.__exit__`
        does), and a torn final ledger line is a case `verify_chain` reports
        rather than one that corrupts what came before it.
        """
        proc, self.proc = self.proc, None
        if proc is None:
            self._close_log()
            return
        if proc.poll() is None:
            try:
                self._post("/__proxy/shutdown", timeout=5)
            except (urllib.error.URLError, OSError):
                pass                                # it is going down anyway
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:   # pragma: no cover
                    proc.kill()
                    proc.wait(timeout=5)
        if self._atexit_hook is not None:
            atexit.unregister(self._atexit_hook)
            self._atexit_hook = None
        self._close_log()
        self._clear_handshake_dir()

    # -- plumbing ----------------------------------------------------------
    def _get(self, path: str, timeout: float) -> Dict[str, Any]:
        request = urllib.request.Request(self.base_url + path, method="GET")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _post(self, path: str, timeout: float) -> Dict[str, Any]:
        request = urllib.request.Request(self.base_url + path, data=b"",
                                         method="POST")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _log_tail(self, limit: int = 2000) -> str:
        if not self._log_path or not os.path.exists(self._log_path):
            return "(no log)"
        if self._log_handle is not None:
            try:
                self._log_handle.flush()
            except ValueError:                      # pragma: no cover
                pass
        with open(self._log_path, "rb") as fh:
            try:
                fh.seek(-limit, os.SEEK_END)
            except OSError:
                fh.seek(0)
            return fh.read().decode("utf-8", "replace")

    def _kill_quietly(self) -> None:
        """The `atexit` path: a parent that died must not strand a child that
        is holding a bound port and a credential."""
        proc = self.proc
        if proc is None:
            return
        if proc.poll() is None:
            try:
                proc.kill()
                proc.wait(timeout=5)
            except Exception:                       # noqa: BLE001
                pass
        self.proc = None
        self._close_log()
        self._clear_handshake_dir()

    def _clear_handshake_dir(self) -> None:
        """The port file and the policy hand-off are read once, at startup.

        Removed rather than left behind because the log they sit beside is the
        only one of the three worth keeping, and because a run directory is
        walked whole into `MANIFEST.json`: a transient file with an ephemeral
        port number in it would appear there as though it were an artefact of
        the experiment.
        """
        import shutil                                       # noqa: PLC0415

        directory, self._handshake_dir = self._handshake_dir, None
        if directory and directory != self._work_dir:
            shutil.rmtree(directory, ignore_errors=True)

    def _close_log(self) -> None:
        handle, self._log_handle = self._log_handle, None
        if handle is not None:
            try:
                handle.close()
            except Exception:                       # noqa: BLE001
                pass

    # -- context manager ---------------------------------------------------
    def __enter__(self) -> "EnvProxyProcess":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()
