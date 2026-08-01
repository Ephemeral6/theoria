"""Supervising the credential child from the arm, without ever holding a key.

`harness/key_proxy_server.py` is the process that reads `.env`. This module is
the process that does not: it starts one child, receives a
`http://127.0.0.1:<port>` URL by file handshake, hands that URL to `ArcClient`
as its base URL, and stops the child afterwards.

**There is deliberately no credential reader in this file.** That is the whole
mechanism. `harness/arc_client.py` no longer has one either -- `load_api_key()`
raises now -- so after this change the only code in `baseline-arms` that can
obtain `ARC_API_KEY` lives in a module the arm process does not import. An
arm-side bug cannot leak a value its process never held; that is a seal rather
than a discipline, which is what `STATUS.md` GAP-5 asked for.

The Windows shapes here are `theoria-arm/harness/proxy_process.py`'s, because
they were already paid for on this host:

* **No fork.** The child re-imports from scratch, so it is started with `cwd`
  set to the track root and `-m harness.key_proxy_server` resolves from there.
* **No SIGTERM.** `stop()` asks over HTTP first, waits, and only then falls
  back to `terminate()`/`kill()` -- both `TerminateProcess` on Windows.
* **The handshake is a file, not stdout.** The console encoding on this host is
  cp936 and mangles a child's banner; a parent parsing stdout would be parsing
  mojibake. The child publishes `{"port": ...}` by atomic rename.
* **A hard-killed parent must not strand the child.** An `atexit` hook covers a
  parent that raises; `--parent-pid` gives the child its own watchdog for the
  parent that never gets to run one. A stranded child holds a bound port and a
  credential, which is why it is worth the lines.

Typical use, from a runner:

    with sealed_upstream(run_id="pilot-ar25") as proxy:
        summary = bare_cc.play(game, model, budget,
                               spend_binding=binding,
                               base_url=proxy.base_url)
"""

import atexit
import contextlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Iterator, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.dirname(HERE)

#: Re-exported so a test can name the stub channel without importing the child
#: module (which does contain a reader) into the process under test.
STUB_KEY_ENV = "BASELINE_ARMS_TEST_KEY"

#: The environment variable `ArcClient` reads its base URL from when a caller
#: does not pass one. `sealed_upstream()` sets it for the duration, so
#: `bare_cc.play()`'s internally-constructed client is routed too without every
#: call site having to thread a parameter through.
BASE_URL_ENV = "ARC_BASE_URL"


class KeyProxyStartupError(RuntimeError):
    """The child never came up. Carries the tail of its log."""


class KeyProxyProcess:
    """One `python -m harness.key_proxy_server` child, supervised.

    `start()`, `stop()`, `base_url` and `state()` are the whole surface a
    runner needs.
    """

    def __init__(self, *, run_id: str,
                 upstream: Optional[str] = None,
                 host: str = "127.0.0.1",
                 timeout: float = 60.0,
                 work_dir: Optional[str] = None,
                 env_key: Optional[str] = None,
                 require_key: bool = True,
                 startup_timeout: float = 30.0,
                 python: Optional[str] = None):
        self.run_id = run_id
        # Imported lazily and by name only: this module must not import the
        # child module, which is where the reader lives.
        from . import arc_client                             # noqa: PLC0415

        self.upstream = (upstream or arc_client.BASE_URL).rstrip("/")
        self.host = host
        self.timeout = timeout
        self.require_key = require_key
        self.startup_timeout = startup_timeout
        self.python = python or sys.executable

        #: A **stub**, held only until `start()` has handed it to the child.
        #:
        #: Not tidiness: `tests/test_seal_process.py` walks this object graph
        #: for a sentinel and asserts it is not there. A supervisor that kept
        #: the value would put a key back inside the arm by a shorter route
        #: than the one this class exists to close. The live credential never
        #: comes through here at all -- the child reads `.env` itself.
        self._env_key = env_key

        self._work_dir = work_dir
        self._handshake_dir: Optional[str] = None
        self.port_file: Optional[str] = None
        self.proc: Optional[subprocess.Popen] = None
        self.port: Optional[int] = None
        self.handshake: Dict[str, Any] = {}
        self._log_path: Optional[str] = None
        self._log_handle = None
        self._atexit_hook = None
        self._last_state: Dict[str, Any] = {}

    # -- addresses ---------------------------------------------------------
    @property
    def base_url(self) -> str:
        if self.port is None:
            raise RuntimeError("the key proxy child is not started")
        return "http://%s:%d" % (self.host, self.port)

    @property
    def log_path(self) -> Optional[str]:
        return self._log_path

    # -- lifecycle ---------------------------------------------------------
    def start(self) -> "KeyProxyProcess":
        handshake_dir = tempfile.mkdtemp(prefix="arc-key-proxy-")
        self._handshake_dir = handshake_dir
        self.port_file = os.path.join(handshake_dir, "key_proxy.port.json")

        log_dir = self._work_dir or handshake_dir
        os.makedirs(log_dir, exist_ok=True)
        self._log_path = os.path.join(log_dir, "key_proxy.log")

        argv = self._argv(self.port_file)
        env = self._child_env()
        # Dropped here rather than in `stop()`: the value is in the child's
        # environment from this line onwards and this object has no further
        # use for it.
        self._env_key = None

        self._log_handle = open(self._log_path, "ab")
        creation = 0
        if os.name == "nt":                                  # pragma: no cover
            creation = (getattr(subprocess, "CREATE_NO_WINDOW", 0)
                        | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        self.proc = subprocess.Popen(
            argv, cwd=TRACK, env=env,
            stdin=subprocess.DEVNULL,
            stdout=self._log_handle, stderr=subprocess.STDOUT,
            creationflags=creation)

        self._atexit_hook = self._kill_quietly
        atexit.register(self._atexit_hook)

        try:
            self.handshake = self._await_handshake(self.port_file)
        except BaseException:
            self._kill_quietly()
            raise
        self.port = int(self.handshake["port"])
        self._await_health()
        return self

    def _argv(self, port_file: str) -> list:
        argv = [self.python, "-m", "harness.key_proxy_server",
                "--host", self.host, "--port", "0",
                "--port-file", port_file,
                "--parent-pid", str(os.getpid()),
                "--upstream", self.upstream,
                "--timeout", str(self.timeout)]
        if self._env_key is not None:
            # A stub, named -- never the value. The real key is never passed
            # at all: the child reads `.env`.
            argv += ["--api-key-env", STUB_KEY_ENV]
        if not self.require_key:
            argv += ["--no-require-key"]
        return argv

    def _child_env(self) -> Dict[str, str]:
        """What the child inherits.

        This process's environment, plus the stub channel when there is one.
        `ARC_API_KEY` is **not** added: for a live run this process does not
        have it to add, and the child reads `.env` for itself.

        `PYTHONIOENCODING=utf-8` because the child's banner is read back out of
        a log file when startup fails and the console encoding here is cp936;
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
                    payload = None                           # mid-rename; poll again
                if isinstance(payload, dict) and payload.get("port"):
                    return payload
            code = self.proc.poll() if self.proc else None
            if code is not None:
                raise KeyProxyStartupError(
                    "the key proxy child exited with %s before it published a "
                    "port. Its log tail:\n%s" % (code, self._log_tail()))
            if time.time() >= deadline:
                raise KeyProxyStartupError(
                    "the key proxy child did not publish a port within %.0fs. "
                    "Its log tail:\n%s" % (self.startup_timeout, self._log_tail()))
            time.sleep(0.05)

    def _await_health(self) -> None:
        """One round trip, so `start()` returning means the socket answers.

        The port file says the server bound; it does not say a request will be
        served. The difference matters to the caller immediately after this,
        which is about to hand the URL to an arm.
        """
        try:
            self._get("/__keyproxy/health", timeout=10)
        except (urllib.error.URLError, OSError) as exc:
            # Read the tail *before* killing: `_kill_quietly` takes the log
            # with it, and "(no log)" because the error path deleted the log is
            # worse than no message at all.
            tail = self._log_tail()
            self._kill_quietly()
            raise KeyProxyStartupError(
                "the key proxy child published port %s but did not answer "
                "/__keyproxy/health: %s. Its log tail:\n%s"
                % (self.port, exc, tail))

    def state(self) -> Dict[str, Any]:
        """Counts the child has kept. Goes into a run summary.

        Cached, because a caller can ask after `stop()` on an error path and a
        state that turns into `None` when the run failed is exactly the record
        the failure most needs.
        """
        try:
            self._last_state = self._get("/__keyproxy/state", timeout=10)
        except (urllib.error.URLError, OSError, ValueError):
            pass
        return dict(self._last_state)

    def stop(self) -> None:
        """Ask, wait, then insist. Idempotent."""
        proc, self.proc = self.proc, None
        if proc is None:
            self._close_log()
            return
        if proc.poll() is None:
            try:
                self._post("/__keyproxy/shutdown", timeout=5)
            except (urllib.error.URLError, OSError):
                pass                                         # it is going down anyway
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:            # pragma: no cover
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
            except ValueError:                               # pragma: no cover
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
            except Exception:                                # noqa: BLE001
                pass
        self.proc = None
        self._close_log()
        self._clear_handshake_dir()

    def _clear_handshake_dir(self) -> None:
        """The port file is read once, at startup, and then is only clutter --
        and a run directory is walked whole into `MANIFEST.json`, so a
        transient file with an ephemeral port in it would appear there as
        though it were an artefact of the experiment."""
        import shutil                                        # noqa: PLC0415

        directory, self._handshake_dir = self._handshake_dir, None
        if directory and directory != self._work_dir:
            shutil.rmtree(directory, ignore_errors=True)

    def _close_log(self) -> None:
        handle, self._log_handle = self._log_handle, None
        if handle is not None:
            try:
                handle.close()
            except Exception:                                # noqa: BLE001
                pass

    # -- context manager ---------------------------------------------------
    def __enter__(self) -> "KeyProxyProcess":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()


@contextlib.contextmanager
def sealed_upstream(*, run_id: str, **kwargs) -> Iterator[KeyProxyProcess]:
    """Start the child and point this track's clients at it for the duration.

    `ARC_BASE_URL` is set here as well as being available as an explicit
    `base_url=` argument, because `bare_cc.play()` constructs an `ArcClient` of
    its own when the caller does not supply one -- and a seal that depends on
    every call site remembering to pass a parameter is the kind of discipline
    GAP-5 was raised about. The previous value is restored on the way out, so
    a nested or repeated run cannot leave a stale port behind.

    A URL is not a secret; this sets a base URL and never a credential.
    """
    proxy = KeyProxyProcess(run_id=run_id, **kwargs)
    proxy.start()
    missing = object()
    previous: Any = os.environ.get(BASE_URL_ENV, missing)
    os.environ[BASE_URL_ENV] = proxy.base_url
    try:
        yield proxy
    finally:
        if previous is missing:
            os.environ.pop(BASE_URL_ENV, None)
        else:
            os.environ[BASE_URL_ENV] = previous
        proxy.stop()
