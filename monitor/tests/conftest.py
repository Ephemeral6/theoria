"""Put `monitor/` on the path and give every test its own state files.

Nothing here touches the live `monitor/quota_state.json` or the live
`dispatch-logs/`. The fleet is running while these tests run; a test that wrote
to the real state file could hold the whole fleet, which is the exact failure
these tests exist to prevent.

## The one expensive thing, run once (S44)

Measured 2026-07-31 with `pytest --durations=50` on this box: the suite took
**460.8s wall**, and **six tests accounted for 338.7s of it (74%)**. Every one of
the six was doing the same thing -- one real `scan.build(False, out_dir=…)`,
about 55 seconds each -- and then reading a different field out of the same
output. Nothing else in the suite reached 3.4 seconds.

That is what `real_scan` below fixes. The scan is genuinely necessary (it is the
only thing that proves `build()` writes what the page and the gate read, and the
whole S30 ticket exists because a *broken* scan and a *healthy* one wrote the
same files), so it is not mocked and not marked slow and not moved out of the
gate -- **it is run once**. Six times 55 seconds becomes one, and the checks all
survive intact. Removing checks to make a gate fast is the failure this repairs,
not the repair.

The fixture is session-scoped and read-only by contract: the six consumers only
read `state`, list the directory, and read `index.html`. Do not write into
`real_scan.dir`; `test_gate_budget.py` will notice a seventh real scan appearing
and say so.
"""

import json
import os
import sys
from types import SimpleNamespace

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
MONITOR = os.path.dirname(HERE)
if MONITOR not in sys.path:
    sys.path.insert(0, MONITOR)

import quota                                           # noqa: E402


@pytest.fixture(scope="session")
def real_scan(tmp_path_factory):
    """One real `scan.build()` for the whole session; ~55s paid once, not six times.

    Returns a handle rather than a path because the six consumers want three
    different things off the same run -- the returned state dict, the set of
    files on disk, and the rendered `index.html`.

    `out_dir=` is not optional and not a style choice: `scan.build()` with no
    argument writes `state.json`, `index.html` and `history.jsonl` **into the
    repository**, which would make `monitor/verify.py` report its own test stage
    as a dirty tree and could turn the *next* territory's gate red for a reason
    that has nothing to do with the branch being merged.

    Session scope means the run happens outside any `monkeypatch`. That is a
    requirement, not a coincidence: several tests in this suite replace
    `scan.build` with a crashing stub, and a fixture that materialised inside one
    of them would capture the crash instead of the healthy run.
    """
    import scan                                          # noqa: PLC0415

    out = tmp_path_factory.mktemp("real-scan")
    state = scan.build(False, out_dir=str(out))
    return SimpleNamespace(
        dir=str(out),
        path=out,
        state=state,
        files=sorted(os.listdir(str(out))),
        page=(out / "index.html").read_text(encoding="utf-8"),
    )


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
