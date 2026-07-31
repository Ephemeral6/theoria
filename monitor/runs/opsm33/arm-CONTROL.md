# opsm33 — arm CONTROL (no branch merged)

**Status: IN PROGRESS** — this file is written as measurement proceeds.

## Setup

* Base commit: `ea4f6af68611df19c6657ba553e72e61d9cdb84a` (pinned by
  `monitor/runs/opsm33/METHOD.md`).
* Worktree: `C:\Users\user\Desktop\theoria\.worktrees\opsm33-control`, created
  `git worktree add --detach`. **Note:** the first `git worktree add` was killed
  by a 2-minute tool timeout mid-checkout and left a stale
  `.git/worktrees/opsm33-control/index.lock`; the lock was removed and
  `git reset --hard ea4f6af6` re-materialised the tree. `git status --porcelain`
  is empty afterwards, so the tree measured is pristine at the base commit.
* Merge: **none**. This is the control arm.

## Gate resolution (`monitor/gates.py: find_gate` / `gate_for`)

`CANONICAL = ("verify.sh", "verify.py")`, first hit wins.

| territory | gate file present | resolved gate |
|---|---|---|
| `monitor` | `verify.sh`, `verify.py`, `verify_quota_exit.sh` | `verify.sh` (canonical, first) |
| `freeze`  | `verify.sh` | `verify.sh` |
| `release` | `verify.sh` | `verify.sh` |

`monitor/verify.sh` is a two-line shim: `exec python "$HERE/verify.py"`.

Invocation replicates `ci_merge.py:537-544` exactly:

* `cmd` = `gates._runner(path)` = `["C:\Program Files\Git\bin\bash.exe", "<wt>/<terr>/verify.sh"]`
* `cwd` = `<wt>/<territory>`
* env = `os.environ` + `gates.gate_env(<wt>)` i.e. `PYTHONPATH` prepended with the
  **worktree root**
* `timeout` = 1800

## 1. `monitor` gate — **RED, rc = 1**, dies at stage 1 (`tests`)

```
CMD  ['C:\Program Files\Git\bin\bash.exe',
      'C:/Users/user/Desktop/theoria/.worktrees/opsm33-control/monitor/verify.sh']
CWD  <wt>\monitor
RC   1
STDOUT  (empty)
```

It does **not** die with a red test summary. It dies with an uncaught
`subprocess.TimeoutExpired` inside `verify.py::_tests`:

```
Traceback (most recent call last):
  File "<wt>\monitor\verify.py", line 337, in <module>
    raise SystemExit(main())
  File "<wt>\monitor\verify.py", line 313, in main
    result = verify()
  File "<wt>\monitor\verify.py", line 276, in verify
    label, code, detail = _tests()
  File "<wt>\monitor\verify.py", line 141, in _tests
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         os.path.join(HERE, "tests")], cwd=HERE, ..., timeout=900)
subprocess.TimeoutExpired: Command '['D:\Miniforge3\python.exe', '-m', 'pytest',
  '-q', '-p', 'no:cacheprovider',
  'C:\Users\user\Desktop\theoria\.worktrees\opsm33-control\monitor\tests']'
  timed out after 900 seconds
```

Consequences worth naming, because they change what "gate red" means here:

* `verify.py` has **four** stages — `tests`, `board states disjoint`,
  `real run`, `artifact fields` (`verify.py:272-298`). Stage 1 raising means
  stages 2-4 **never ran** and stdout is empty. The gate produced no stage
  table at all.
* `_tests()`'s 900 s timeout is not caught, so what `ci_merge.py` sees is
  `returncode 1` and a traceback — i.e. `ci_merge` records this as
  `verify gate red in monitor (verify.sh)` and stores a Python traceback as the
  "excerpt". That is `gates.py`'s own "broken, not red" distinction failing to
  apply, because the timeout is *inside* the gate rather than around it.
* Caveat on this particular run: `freeze` and `release` gates were started
  ~5 min into the monitor gate's 900 s window, so there was CPU contention for
  part of it. The standalone pytest run in §2 is the uncontended measurement
  and settles whether 900 s is genuinely exceeded.

Raw: `.worktrees/opsm33-ctl-monitor-gate.txt`.

## 2. `monitor` — standalone `python -m pytest -q -rf`

(pending — see below)

## 3. `freeze` gate — **GREEN, rc = 0**

`freeze/verify.sh`, 15 stages `[0]`..`[14]`, zero `FAIL` lines. Verdict banner:
`DRAFT COMPLETE -- all 13 items landed or annotated`.

Raw: `.worktrees/opsm33-ctl-freeze-gate.txt`.

## 4. `release` gate — **GREEN, rc = 0**

`release/verify.sh`, all five steps `-- ok`, final line `VERIFY: green`:

| step | result |
|---|---|
| red-line negative controls (`python -m pytest -q`) | ok |
| red lines clear, every tracked file read (`--mode generate`) | ok |
| every tracked file is classified | ok |
| no checklist item rests on an unclassified file | ok |
| the S23 before/after archive still reproduces | ok |

Mode was `generate`, i.e. the credential *was* reachable, so the strict path ran.

**Side finding (not a gate failure):** the release gate leaves the tree dirty.
After it ran, `git status --porcelain` reported two modified tracked files:

```
 M release/runs/20260728T234923Z-S23/after/contamination.planted.txt
 M release/runs/20260728T234923Z-S23/before/contamination.planted.txt
```

That is `gates.run`'s `drift` outcome — logged, non-blocking, and `ci_merge`
does not check for it at all since it calls the gate directly. They were
restored with `git checkout --` before the pytest run below, so §2 measures a
pristine tree.

## Standing-flag bearing

The standing flags of the form *"verify gate red in freeze/release"* are **not
reproduced by the control at `ea4f6af6`**: both territories are rc 0 green on a
pristine base with no branch merged. Whatever makes them red is not the base
tree. (Adjudication is not mine — this is the control datum.)
