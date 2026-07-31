# arm-s39 — `origin/agent/s39-writes-into-the-live-master-tree`

Measurement only. No adjudication, no fixes, no commits.

* base (pinned): `ea4f6af6`
* branch tip: `a03fde2fa1ef5a023ebd6005988bea91b398b709` (matches the flag file's `tip:`)
* merge commit in the throwaway worktree: `b3a7559b9ddf51f6f2727b8ca9a9ccd7878295fe`
* worktree: `.worktrees/opsm33-s39` (detached, removed after this file was written)
* standing flag: `verify gate red in monitor (verify.sh)`, 8 attempts since 2026-07-30T05:10:24Z

## 1. Merge — CLEAN

`git merge --no-ff --no-edit` → rc 0, "Merge made by the 'ort' strategy",
`PARTNER_SYNC.md` auto-merged. `git diff --name-only --diff-filter=U` is empty.

Note on procedure: the first `git merge` invocation was killed by a 120 s tool
timeout mid-checkout (`ORIG_HEAD` written, no `MERGE_HEAD`, HEAD still at base).
The worktree was `git reset --hard ea4f6af6`'d and the merge re-run with a
600 s budget; it then completed in seconds. Nothing outside the throwaway
worktree was touched.

Diffstat `ea4f6af6..HEAD`:

```
 PARTNER_SYNC.md                                    |   5 +
 monitor/master_tree_guard.py                       | 816 +++++++++++++++++++++
 monitor/runs/20260730T0440Z-S39/FINDINGS.md        | 122 +++
 monitor/runs/20260730T0440Z-S39/MANIFEST.json      |  41 ++
 monitor/runs/20260730T0440Z-S39/RUN_STATE.md       | 232 ++++++
 .../20260730T0440Z-S39/master-tree-status-raw.txt  | 212 ++++++
 monitor/scan.py                                    |  74 ++
 monitor/tests/test_master_tree_guard.py            | 808 ++++++++++++++++++++
 8 files changed, 2310 insertions(+)
```

All adds except `PARTNER_SYNC.md` (+5) and `monitor/scan.py` (+74). The scan.py
change adds `probe_master_tree()` and registers it in `PROBES`. Nothing existing
is modified or deleted.

## 2. Live-tree-write check — NO WRITE FOUND (one read, flagged)

The branch adds exactly one test file, `monitor/tests/test_master_tree_guard.py`
(808 lines, 45 tests). Read in full.

**Every constructive test builds a throwaway git repo under `tmp_path`** via the
`repo` fixture (lines 44-80): `git init` in `tmp_path/repo`, source and fleet
state written there, `git worktree add` targets are also under `tmp_path`. No
test writes to any path outside `tmp_path`. The file says so itself in its
module docstring and gives the reason ("a test that dirtied master's working
tree to prove the guard notices dirty working trees would be the exact defect
S39 exists to stop").

**One test does touch the live repo, read-only.**
`test_live_master_tree_is_judgeable` (line 786) resolves
`g.main_worktree(<dir of the test file>)`. Because `.worktrees/opsm33-s39` is a
*linked* worktree of `C:\Users\user\Desktop\theoria`, that resolves to the real
checkout, and `g.report(main)` runs against it. Verified read-only by reading
`master_tree_guard.py`: `report()` only shells out to
`git status --porcelain -z` (plus a per-path `-uall` refinement) and
`git worktree list --porcelain`. `install_hook()` — the only writing function in
the module — is never called on the live tree by any test; every
`install_hook` call site passes the `tmp_path` fixture repo.

Two second-order effects worth naming, neither a content mutation:

* `git status` on the live checkout refreshes `.git/index`'s stat cache and
  briefly takes `index.lock`. `ci_merge.py` is running concurrently against the
  same repo. Contention is benign (git degrades to not refreshing) but it is a
  real shared-resource touch.
* The same is true of the *gate*: the new `probe_master_tree()` in `scan.py`
  deliberately calls `mtg.main_worktree(ROOT)` so that it judges the shared tree
  no matter which worktree scan runs from. So `verify.sh` inside a throwaway
  worktree reads the live master tree's dirty-path set. That makes this probe's
  colour a function of live fleet state at the instant of the run — a moving
  target across the six cycle-33 arms. Measurement note, not a verdict.

Conclusion: **the branch's name describes the defect it detects, not a defect it
commits.** Safe to run the full suite. Proceeding.

## 3. Gate — `verify.sh`, exactly as ci_merge.py:539-544

cwd `<wt>/monitor`, `PYTHONPATH` prepended with the worktree root, timeout 1800.

Resolved command (via `gates.find_gate`, same call ci_merge makes):
`['C:\Program Files\Git\bin\bash.exe', '<wt>/monitor/verify.sh']`.

**rc = 1. Dying stage: `tests` — and it does not FAIL, it CRASHES.**

The gate produced no stage output at all. Whole output:

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
         os.path.join(HERE, "tests")],
        cwd=HERE, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=900)
  ...
subprocess.TimeoutExpired: Command '[... '-m', 'pytest', ... 'monitor\\tests']'
    timed out after 900 seconds
```

Three things follow, and they matter more than the rc:

1. **`verify.py:141`'s `timeout=900` is unguarded.** `subprocess.TimeoutExpired`
   propagates out of `_tests()`, past `verify()`, out of `main()`. The gate
   never reaches its own error path, never writes a stage row, never prints
   `RED:`. `ci_merge` sees rc 1 and flags "verify gate red in monitor
   (verify.sh)" — the same wording it would use for a genuinely failing suite.
   A gate that cannot finish and a gate that failed are indistinguishable from
   outside. This is the same shape as the repo's standing "crash is not a
   finding" lesson, applied to the enforcer itself.

2. **The flag file's recorded stderr cannot be reproduced from this tree.** The
   flag transcript shows a completed run — `== tests FAILED(1)`, six named
   failures, then `== board states disjoint ok`, `== real run ok`,
   `== artifact fields ok`, `RED: tests`. That is a run where the suite fit
   inside 900 s. It no longer does. So the 8 recorded attempts are not
   necessarily all the same event, and the newest ones may be timeouts wearing
   the older ones' label.

3. **The runtime is coupled to live fleet state.** The gate's inner cap is 900 s,
   well inside ci_merge's 1800 s outer timeout, so the outer budget never
   protects it. The branch's `probe_master_tree()` and
   `test_live_master_tree_is_judgeable` both resolve and read the *main*
   worktree; `git worktree list --porcelain` now enumerates **309** registered
   worktrees (the branch's own source comment cites 221 and 0.85 s per probe
   call), and `master_tree_guard.report()` additionally issues a per-collapsed-
   directory `git status -uall -- <path>` against a live tree carrying ~200
   dirty paths. Whether this arm's gate finishes is therefore a function of how
   many worktrees and dirty paths exist at the moment it runs — not a property
   of the merged tree alone.

## 4. `python -m pytest -q -rf` in `<wt>/monitor`

## 4. `python -m pytest -q -rf` in `<wt>/monitor`

PENDING

## 5. Third category

PENDING
