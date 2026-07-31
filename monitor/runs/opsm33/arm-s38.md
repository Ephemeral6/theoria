# arm-s38 — `origin/agent/s38-append-only-probe-branch-blind`

Measured per `monitor/runs/opsm33/METHOD.md`. Base pinned `ea4f6af6`.
Worktree: `.worktrees/opsm33-s38` (detached).

## 1. Branch identity

* branch tip SHA: `9f8d94e3754d40be773fe05563f9b7e572bd6c13`
  (matches the `tip:` recorded in `monitor/ci/CONFLICT-origin_agent_s38-append-only-probe-branch-blind.md`)
* standing flag: "verify gate red in monitor (verify.sh)", 8 attempts since
  2026-07-30T05:05:27Z.

## 2. Merge — CLEAN

`git merge --no-ff --no-edit origin/agent/s38-append-only-probe-branch-blind`
→ "Merge made by the 'ort' strategy.", rc 0.
`git diff --name-only --diff-filter=U` → empty (no conflicted paths).

Diffstat: **7 files changed, 619 insertions(+), 4 deletions(-)**

```
 PARTNER_SYNC.md                                |   5 +
 monitor/runs/20260730T0410Z-S38/MANIFEST.json  |  22 +++
 monitor/runs/20260730T0410Z-S38/RUN_STATE.md   |  94 +++++++++++
 monitor/runs/20260730T0410Z-S38/measure.json   | 219 +++++++++++++++++++++++++
 monitor/runs/20260730T0410Z-S38/measure.py     |  78 +++++++++
 monitor/scan.py                                |  51 +++++-
 monitor/tests/test_append_only_probe_anchor.py | 154 +++++++++++++++++
```

The only production-code change is `monitor/scan.py` (+47/-4), inside
`probe_append_only`: it re-anchors the append-only deletion sum on
`origin/master` instead of `HEAD`, and adds a `merge-base(origin/master, HEAD)..HEAD`
"own net deletions" term. One new test file is added:
`monitor/tests/test_append_only_probe_anchor.py`.

(sections 3-5 appended below as they were measured)

## 3. Monitor gate, run exactly as `ci_merge.py:539-544`

Discovery via `gates.gate_for(<wt>, "monitor")`:

* kind `verify`, name `verify.sh`
* cmd `['C:\Program Files\Git\bin\bash.exe', '<wt>/monitor/verify.sh']`
* cwd `<wt>/monitor`, env = `gates.gate_env(<wt>)` (PYTHONPATH prepended with the
  worktree ROOT), timeout 1800.

**rc = 1.** Dying stage: **`_tests()` — the FIRST stage of `verify()`**
(`verify.py:276` → `verify.py:141`). It did not die *red*; it died with an
uncaught `subprocess.TimeoutExpired`: `verify.py`'s own inner
`timeout=900` on the pytest child expired, the exception propagated out of
`verify()` and `main()`, and the interpreter exited 1 with a bare traceback.
Full stderr saved at `monitor/runs/opsm33/_s38_gate_raw.txt`; it is the whole
of the gate's output — no stage banner was ever printed, because `verify()`
prints only after collecting all four stages.

```
  File ".../monitor/verify.py", line 141, in _tests
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         os.path.join(HERE, "tests")], ... timeout=900)
subprocess.TimeoutExpired: ... timed out after 900 seconds
```

**This is not the failure mode the standing flag recorded.** The flag's stored
transcript shows the tests stage completing with `== tests FAILED(1)` and six
named failing ids. Here the child never finished inside 900 s. Six OPS-M
measurement agents plus the live `ci_merge.py` (pid 32352) are running the same
suite concurrently on this box, so the 900 s wall is being hit under load rather
than by a hang introduced by the branch — noted as a measurement condition, not
adjudicated. The `-q -rf` run in §4 is the instrument that recovers the real
failing set.
