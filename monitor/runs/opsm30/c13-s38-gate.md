# OPS-M cycle 30 — do c13 and s38 add gate red of their own?

Started 2026-07-30T10:32:46Z (`date -u +%Y-%m-%dT%H:%M:%SZ`).
Question: for each of `origin/agent/c13-certificate-bridge-two-halves` and
`origin/agent/s38-append-only-probe-branch-blind`, does merging it into current
`origin/master` add ANY monitor-gate failure beyond what clean current master
already fails?

## Fixed points

| thing | sha | committed |
|---|---|---|
| `origin/master` (base of every arm) | `46ba6e34f43a55e40b6acef3e2164b1ec878f302` | 2026-07-30T18:30:38+08:00 |
| `origin/agent/c13-certificate-bridge-two-halves` | `21c88bc5ab5723164d1c051856dab6bef4e6a580` | 2026-07-30T13:10:00+08:00 |
| `origin/agent/s38-append-only-probe-branch-blind` | `9f8d94e3754d40be773fe05563f9b7e572bd6c13` | 2026-07-30T11:47:38+08:00 |
| alleged root cause of master's own red | `873d62eee6d0e4fb48f65f89474f425df5e878ff` | 2026-07-30T12:55:40+08:00 |

## Arms — four, not three

Two **separate** control worktrees, not one shared one, on purpose: if the two
controls disagree the measurement is not reproducible and no verdict about
either branch is worth anything. That disagreement is a finding in its own
right and cannot be seen with a single control.

```
git worktree add --detach .worktrees/opsm30-c13-ctl origin/master
git worktree add --detach .worktrees/opsm30-c13-mrg origin/master
git worktree add --detach .worktrees/opsm30-s38-ctl origin/master
git worktree add --detach .worktrees/opsm30-s38-mrg origin/master
cd .worktrees/opsm30-c13-mrg && git merge --no-ff --no-edit origin/agent/c13-certificate-bridge-two-halves
cd .worktrees/opsm30-s38-mrg && git merge --no-ff --no-edit origin/agent/s38-append-only-probe-branch-blind
```

Merge results (both clean, rc 0, no conflict):

* c13 merge commit `afcdd38ad2f8a34777e560844254c09ea0de8a40`; 20 files,
  +2544/-9. Touches `CONTRACTS/`, `engine-rig/`, `monitor/inbox/`.
* s38 merge commit `808ce63711e036fb679e47c2efa50dd6b6c5b340`; 7 files,
  +619/-4. Touches `PARTNER_SYNC.md`, `monitor/scan.py`,
  `monitor/tests/test_append_only_probe_anchor.py`, `monitor/runs/…S38/`.

## How the gate is run

`.worktrees/opsm30_arms.py`. It replicates `ci_merge.py` and deliberately does
**not** call `gates.run()`:

* `ci_merge.py:92-101` `sh()` — env is
  `dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")` updated with
  `extra_env`; `subprocess.run(..., encoding="utf-8", errors="replace")`.
* `ci_merge.py:526,543-544` — `row = gate_for(wt, d)`, then
  `sh(row["cmd"], cwd=os.path.join(wt, d), timeout=1800, extra_env=gates.gate_env(wt))`.
* `gates.gate_env(wt)` prepends the **merged tree's own root** to `PYTHONPATH`.
* `gates.run()` builds the same `cmd` and the same `cwd` but calls its own
  `sh()` with no `env=` at all, so `PYTHONPATH` is never set. Its docstring
  ("A gate runs at its own territory with the repository root importable")
  describes a contract it does not implement. Any verdict taken from
  `gates.run()` is a verdict about a different environment than the one the
  merge rig uses.
* `gates.gate_for` was resolved against each arm's own tree, and the path
  `<wt>/monitor` is asserted to exist first — `gate_for` returns the identical
  `kind: "none"` answer for "no gate here" and "this directory is not on the
  tree", so "no verify script" is only meaningful after the path is proven.
  All paths are Windows-native absolute (`C:\...`); a git-bash `/tmp/...` path
  handed to Windows Python becomes `C:\tmp\...`.

`gate_for` resolves monitor to `kind=verify`, `name=verify.sh`, run through the
pinned Git Bash (`gates.GIT_BASH_CANDIDATES`), never PATH `bash` (WSL).

Failing test ids come from a second run of exactly the command the gate's own
`_tests()` stage uses (`python -m pytest -q -p no:cacheprovider <wt>/monitor/tests`,
cwd `<wt>/monitor`, same env) plus `-rf`, because `verify.py` stores only
`detail[-2000:]` per stage and truncates the list.

## Results

### Arm `c13-ctl` (control: clean `origin/master`, no merge) — 2026-07-30T10:44Z

```
cmd: ['C:\\Program Files\\Git\\bin\\bash.exe',
      'C:/Users/user/Desktop/theoria/.worktrees/opsm30-c13-ctl/monitor/verify.sh']
cwd: C:\Users\user\Desktop\theoria\.worktrees\opsm30-c13-ctl\monitor
PYTHONPATH[0] = the arm's own root;  PYTHONIOENCODING=utf-8  PYTHONUTF8=1
rc: 1
```

Gate stages: `tests FAILED(1)`, `board states disjoint ok`, `real run ok`,
`artifact fields ok`. So the whole of monitor's red is in the `tests` stage.

Failing set (6):

```
tests/test_scan_failure_exit.py::test_a_blinded_conflict_probe_does_not_report_green
tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk
tests/test_scan_no_third_value.py::test_all_files_present_still_reads_green
tests/test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes
tests/test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
tests/test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero
```

Corroborates the 873d62ee story for three of the six: `git show
origin/master:monitor/reflex.py | grep -c 'SUPPLY-UNKNOWN:\|loop-skipped'`
returns **0** — both guard strings the reflex tests assert on are absent from
master's own `reflex.py`. 873d62ee is `+69/-115` on that one file.

Why each of the six is red, read off the transcript (all three causes are
properties of master's own tree, none of a pending branch):

* the three `test_standing_reflex_no_third_value` cases assert on strings in
  `monitor/reflex.py` — `events.append("revive:GIT-EXIT-%d(loop-skipped)"` and
  `SUPPLY-UNKNOWN:` — that 873d62ee removed.
* `test_a_blinded_conflict_probe_does_not_report_green` blinds `git_or_none`
  and demands `missing`; it gets `risk`, because `probe_conflicts` part (a)
  walks the tree for conflict markers and the tree itself contains files that
  hold them (`monitor/ci/CONFLICT-*.md` quote merge output). Tree content, not
  branch content.
* both `test_scan_no_third_value` append-only cases get
  `PARTNER_SYNC.md（删除 3 行，超出已裁决豁免 1 行）` — 3 published deletions
  against a `BASELINE` of 1, on master's own first-parent history.

### Arm `c13-mrg` (origin/master + merge c13) — 2026-07-30T11:00Z

Merge clean (`afcdd38a`). `rc: 1`. Stages identical: `tests FAILED(1)`,
`board states disjoint ok`, `real run ok`, `artifact fields ok`.

Failing set: **byte-identical to `c13-ctl`, same six ids in the same order.**

* MERGED \ CONTROL = ∅
* CONTROL \ MERGED = ∅

**VERDICT c13: INNOCENT (identical failure sets).**

c13 touches `monitor/` only by adding one file to `monitor/inbox/`, and
`probe_inbox` returns `partial`, never a gate failure, for a non-empty inbox.

Confirmed twice over for this arm pair: the standalone `pytest -rf` run gives
the same six ids, and `diff` of the two sorted lists is empty.

### Arm `s38-ctl` (second, independent control on clean `origin/master`)

`rc: 1`. Stages `tests FAILED(1)` / `board states disjoint ok` /
`real run ok` / `artifact fields ok`. Failing set: **the same six ids as
`c13-ctl`.**

**The two controls agree.** Same rc, same stage pattern, same six failing ids.
The measurement is reproducible across two separately created worktrees at the
same commit, so a difference in either merged arm would have been attributable
to the branch.

(s38-mrg pending)
