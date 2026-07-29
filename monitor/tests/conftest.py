"""Put `monitor/` on the path and give every test its own state files.

Nothing here touches the live `monitor/quota_state.json` or the live
`dispatch-logs/`. The fleet is running while these tests run; a test that wrote
to the real state file could hold the whole fleet, which is the exact failure
these tests exist to prevent.
"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
MONITOR = os.path.dirname(HERE)
if MONITOR not in sys.path:
    sys.path.insert(0, MONITOR)

import quota                                           # noqa: E402


@pytest.fixture
def rig(tmp_path, monkeypatch):
    """An isolated quota breaker: its own state file, logs and registry.

    Returns a small handle rather than a bare path, because every test needs
    the same three moves -- write a state, run a command, read the state back.
    """
    logs = tmp_path / "dispatch-logs"
    logs.mkdir()
    state = tmp_path / "quota_state.json"
    monkeypatch.setattr(quota, "LOGS", str(logs))
    monkeypatch.setattr(quota, "STATE", str(state))

    class Rig:
        path = str(state)
        logs_dir = str(logs)

        def write_state(self, **fields):
            base = {"mode": "normal", "requeue": [], "history": []}
            base.update(fields)
            state.write_text(json.dumps(base), encoding="utf-8")
            return base

        def read_state(self):
            return json.loads(state.read_text(encoding="utf-8"))

        def registry(self, entries):
            (logs / "registry.json").write_text(json.dumps(entries),
                                                encoding="utf-8")

        def log(self, name, text):
            (logs / name).write_text(text, encoding="utf-8")

        def dead_session(self, pid_str, log_text, *, pushed=False):
            """A session that died without pushing, with `log_text` in its log."""
            self.registry({pid_str: {"pid": 424242, "log": pid_str + ".log"}})
            self.log(pid_str + ".log", log_text)
            monkeypatch.setattr(quota, "pid_alive", lambda pid: False)
            monkeypatch.setattr(quota, "branch_pushed", lambda p: pushed)

        def window(self, open_):
            """Stub `ping`. The real one shells out to the `claude` CLI."""
            calls = []
            monkeypatch.setattr(quota, "ping",
                                lambda: calls.append(1) or (0 if open_ else 2))
            return calls

        def no_dispatch(self):
            """Catch every relaunch instead of spawning one."""
            spawned = []

            def fake_run(cmd, **kw):
                spawned.append(cmd)
                class Done:
                    returncode = 0
                    stdout = ""
                    stderr = ""
                return Done()

            monkeypatch.setattr(quota.subprocess, "run", fake_run)
            monkeypatch.setattr(quota.time, "sleep", lambda s: None)
            return spawned

    return Rig()
