# Side finding — the baseline was red, and the red was eating a negative control

Worker W-1681. Found while performing V25's opening ritual («跑本领地测试，绿了再动手»).

## What happened

`python -m pytest` in `worldgen/` at `45b1529d` (= master `4a511d7e` merged into
this branch): **4 failed, 589 passed, 13 skipped**. All four in
`tests/test_verify_qc_gate.py`:

```
FAILED tests/test_verify_qc_gate.py::test_pinned_verdict_exits_zero
FAILED tests/test_verify_qc_gate.py::test_pinned_miss_is_not_reported_as_green
FAILED tests/test_verify_qc_gate.py::test_sample_shrunk_exits_nonzero
FAILED tests/test_verify_qc_gate.py::test_stale_artifact_exits_nonzero
```

Each with `TypeError: argument of type 'NoneType' is not iterable` on a line of
the form `assert "[miss]" in proc.stdout`.

## Not my merge, and not this branch

`git diff master 45b1529d -- worldgen/tests/test_verify_qc_gate.py worldgen/verify.py worldgen/qc`
is **empty** — the file is byte-identical to master. The failure is on master, on
this machine. The prior worker's baseline at `3b2a5873` recorded 593 passed /
13 skipped, which is the same suite green; so this is environment-dependent, not
a regression in the code.

## Cause

`tests/test_verify_qc_gate.py:130` spawned the gate with

```python
subprocess.run([...], cwd=ROOT, capture_output=True, text=True)
```

`text=True` with no `encoding` decodes the child's output with the **ambient
codepage**. `verify.py:188` prints

```
VERDICT: green — library gates and every QC stage at its pin.
```

The em dash is UTF-8 `\xe2\x80\x94`. This machine's default is GBK, which cannot
decode it:

```
UnicodeDecodeError: 'gbk' codec can't decode byte 0x94 in position 502
```

That exception is raised **inside `subprocess`'s reader thread**, so `run()` does
not propagate it — it returns with `proc.stdout is None`. Python only surfaces it
as a `PytestUnhandledThreadExceptionWarning`.

## Why it is worth more than a locale annoyance

The exit-code assertion on the line *above* the failure passed. So on any
non-UTF-8 locale this negative control silently degraded to **half a control**:
it still checked the process's exit code, and it could no longer check *which
gate line printed* — the half that distinguishes an honest miss from a crashed
harness, which is the exact distinction V12 added this file to catch (see the
module docstring, lines 8–11). It failed loudly here only because a `None`
happens to raise on `in`; had the assertion been written `if "[miss]" in
(proc.stdout or "")`, it would have passed while checking nothing.

## Fix

Pin **both** ends of the pipe to UTF-8, rather than inheriting either:

```python
env = dict(os.environ, PYTHONIOENCODING="utf-8")
subprocess.run([...], capture_output=True, text=True,
               encoding="utf-8", errors="replace", env=env)
```

The child's encoding is forced too, not just the parent's decode, so the pipe is
UTF-8 by construction on every locale instead of by luck on most.

After: `python -m pytest tests/test_verify_qc_gate.py -q` → **13 passed**.

## Scope

This is **not** one of V25's four requirements. It is recorded here because it
blocked V25's opening ritual and because the diagnosis — a default (the ambient
codepage) quietly turning a check into a non-check — is the same shape as V25's
subject. Committed separately from the V25 work for that reason.

## Not touched

`worldgen/runs/20260728T172500Z-V16-determinism-has-no-caller/write_manifest.py:27`
has the same `text=True`-without-encoding pattern. It is a historical run
artefact, it only ever reads `git` output, and run directories are not edited
after the fact — left alone deliberately.
