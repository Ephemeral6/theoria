"""Is the credential resident in the arm's own process?

`Theoria.md:305`'s Phase 1 acceptance line is a conjunction:

    密封测试通过（臂内无任何凭据，绕开双代理的出网必须失败）

Two conjuncts. The second one has a test and it is green
(`tests/test_bypass_negative.py`: a sealed id through `Run` -> `EnvProxy` ->
upstream is refused before a socket opens). The first one -- *no credential
inside the arm* -- has no test anywhere in this arm. I have asserted three
times in three heartbeats that it is false, each time by reading code
(`harness/run.py`'s `__enter__` builds `EnvProxy` in-process;
`proxy/env_proxy.py`'s `__init__` calls `read_secret`). A reading is an
argument. This is the measurement.

It is run with a **sentinel** key, never the real one: `Run(env_key=...)` takes
the value, so nothing here reads `.env` and nothing here can print the real
credential. What the sentinel measures is the *structure* -- whether a
credential handed to a live `Run` is reachable from the arm process's own
objects -- and that structure does not depend on which string the credential is.

The probe answers three separate questions, because they have different fixes:

  Q1  Is the value reachable from the live `Run` object graph?
  Q2  Is the value in the process-wide `VAULT`?
  Q3  Is the value in this process's `os.environ`?

Exit code 0 means "not resident anywhere" (the conjunct holds). Exit code 1
means at least one of the three found it, and the report says which.
"""

import gc
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: F401,E402  (sys.path)

from harness.run import Run                           # noqa: E402
from proxy.redact import VAULT                        # noqa: E402

#: Not key-shaped on purpose. `proxy/redact.py:_KEYISH` raises a
#: `credential_in_body` incident on 32+ char alphanumerics and on UUIDs, and a
#: probe that trips the arm's own detector would be measuring the detector.
SENTINEL = "sentinel-not-a-real-credential-A3"

#: An upstream that is syntactically valid and refuses to resolve. The probe
#: never opens a socket -- it constructs the run and looks at memory -- but if a
#: future edit made it try, this fails closed rather than reaching the real API.
DEAD_UPSTREAM = "http://127.0.0.1:9"


def _reachable(root, needle, max_depth=6):
    """Walk the object graph from `root` and report every path that holds
    `needle` as a string value.

    Deliberately not `gc.get_referents` over the whole heap: the question is
    not "does this string exist somewhere in a CPython process" (it does, it
    was just constructed) but "can the arm's own live objects hand it over".
    The first question has no fix; the second one does -- move the proxy out of
    the process.
    """
    hits, seen = [], set()

    def walk(obj, path, depth):
        if depth > max_depth or id(obj) in seen:
            return
        seen.add(id(obj))
        if isinstance(obj, str):
            if obj == needle:
                hits.append(path)
            return
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                walk(v, "%s[%r]" % (path, k), depth + 1)
            return
        if isinstance(obj, (list, tuple, set, frozenset)):
            for i, v in enumerate(list(obj)):
                walk(v, "%s[%d]" % (path, i), depth + 1)
            return
        slots = getattr(obj, "__dict__", None)
        if isinstance(slots, dict):
            for k, v in list(slots.items()):
                walk(v, "%s.%s" % (path, k), depth + 1)

    walk(root, "run", 0)
    return hits


def main():
    report = {"sentinel_is_the_real_key": False, "questions": {}}

    run = Run(
        game_id="g50t-5849a774",
        slug="_probe-seal-conjunct-one",
        env_upstream=DEAD_UPSTREAM,
        env_key=SENTINEL,
        require_key=True,
        runs_root=os.path.join(ARM, ".pytest-runs"),
    )
    try:
        with run:
            q1 = _reachable(run, SENTINEL)
            q2 = [k for k in getattr(VAULT, "_secrets", ()) if k == SENTINEL]
            q3 = [k for k, v in os.environ.items() if v == SENTINEL]
    finally:
        gc.collect()

    report["questions"]["Q1_reachable_from_run_object_graph"] = {
        "resident": bool(q1), "paths": q1[:12], "path_count": len(q1)}
    report["questions"]["Q2_in_process_wide_vault"] = {"resident": bool(q2)}
    report["questions"]["Q3_in_os_environ"] = {"resident": bool(q3)}

    resident = bool(q1) or bool(q2) or bool(q3)
    report["conjunct_one_holds"] = not resident
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if resident else 0


if __name__ == "__main__":
    sys.exit(main())
