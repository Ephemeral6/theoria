# arm-a3 — `origin/agent/a3-campaign-devpile`

Measurement only. No adjudication, no fix, no commit.

Base pinned: `ea4f6af6` (per `monitor/runs/opsm33/METHOD.md`).
Branch tip: `1e29578a58ce1dc398c5830b7be6f6e6b78dd03d`
Merge commit produced in worktree: `44a7bdfeefb94479e605bb5dd7b447dfa7df88bc`

---

## 1. Merge status

**CLEAN.** `git merge --no-ff --no-edit origin/agent/a3-campaign-devpile` → rc 0,
no conflicted paths (`git diff --name-only --diff-filter=U` empty).

Note: the first invocation was killed by a 120 s harness timeout with HEAD still
at `ea4f6af6` and no `MERGE_HEAD` — i.e. it had not begun applying. Re-run with a
longer timeout completed in well under the limit. `ci_merge.py` (pid 32352) is
running concurrently and contends for the object store; this is a plausible
explanation for the first stall but was not instrumented.

Diffstat: **203 files changed, 109632 insertions(+), 256 deletions(-)**

Top-level paths touched:

| path | files |
|---|---|
| `theoria-arm/` | 201 |
| `monitor/` | 1 |
| `PARTNER_SYNC.md` | 1 |

So the gated territories in play are **`monitor`** and **`theoria-arm`**
(`PARTNER_SYNC.md` is a root file, not a territory). `ci_merge.py:525` walks
`sorted(dirs)` and `:548` returns on the first *verify* red — `monitor` sorts
before `theoria-arm`, so a red monitor gate masks whatever theoria-arm would say.

Gate resolution in the merged tree (`gates.gate_for`):

* `monitor` → kind `verify`, `verify.sh` (bash)
* `theoria-arm` → kind `verify`, `verify.py` (python)

---

## 2. The 30-attempt history — the failure mode migrated four times

Reconstructed from `monitor/ci/merge.log` (`grep a3-campaign-devpile`). Every
`FLAG` line for this branch, in order:

| # | UTC | reason recorded |
|---|---|---|
| — | 2026-07-29T00:25:10Z | **MERGED** (dirs: PARTNER_SYNC.md, monitor, theoria-arm; gates: verify:monitor(verify.sh), pytest:theoria-arm) |
| 1 | 2026-07-29T01:55:33Z | tests red in **theoria-arm** |
| 2 | 2026-07-29T01:59:03Z | tests red in theoria-arm |
| 3 | 2026-07-29T02:08:53Z | tests red in theoria-arm |
| 4 | 2026-07-29T02:18:57Z | tests red in theoria-arm |
| 5 | 2026-07-29T02:32:58Z | verify gate red in **monitor** (verify.sh) |
| 6 | 2026-07-29T02:37:58Z | verify gate red in monitor (verify.sh) |
| 7 | 2026-07-29T02:47:57Z | verify gate red in monitor (verify.sh) |
| 8 | 2026-07-29T02:54:58Z | verify gate red in monitor (verify.sh) |
| 9 | 2026-07-29T03:04:19Z | verify gate red in monitor (verify.sh) |
| 10 | 2026-07-29T03:14:00Z | verify gate red in monitor (verify.sh) |
| 11 | 2026-07-29T03:28:02Z | verify gate red in monitor (verify.sh) |
| 12 | 2026-07-29T03:37:53Z | verify gate red in monitor (verify.sh) |
| 13 | 2026-07-29T03:53:01Z | verify gate red in monitor (verify.sh) |
| 14 | 2026-07-29T04:14:01Z | verify gate red in monitor (verify.sh) ← **`first_seen` on the current flag** |
| 15 | 2026-07-29T05:25:48Z | verify gate red in **theoria-arm** (verify.py) ← theoria-arm has *acquired a verify.py*; it was `pytest` at 00:25 |
| 16 | 2026-07-29T10:29:35Z | verify gate red in theoria-arm (verify.py) [NEEDS-HUMAN: 3 attempts] |
| 17 | 2026-07-29T15:07:43Z | verify gate red in **monitor** (verify.sh) [4 attempts] |
| 18 | 2026-07-29T17:21:59Z | verify gate red in **theoria-arm** (verify.py) [5] |
| 19 | 2026-07-29T18:38:18Z | theoria-arm (verify.py) [6] |
| 20 | 2026-07-29T18:55:10Z | theoria-arm (verify.py) [7] |
| 21 | 2026-07-29T19:10:52Z | theoria-arm (verify.py) [8] |
| 22 | 2026-07-29T21:03:38Z | theoria-arm (verify.py) [9] |
| 23 | 2026-07-29T21:27:48Z | theoria-arm (verify.py) [10] |
| 24 | 2026-07-29T21:49:03Z | theoria-arm (verify.py) [11] |
| 25 | 2026-07-29T22:21:20Z | theoria-arm (verify.py) [12] |
| 26 | 2026-07-29T22:41:45Z | theoria-arm (verify.py) [13] |
| 27 | 2026-07-29T23:08:14Z | theoria-arm (verify.py) [14] |
| 28 | 2026-07-29T23:33:44Z | theoria-arm (verify.py) [15] |
| 29 | 2026-07-30T00:12:46Z | theoria-arm (verify.py) [16] |
| 30 | 2026-07-30T00:39:17Z | theoria-arm (verify.py) [17] |
| 31 | 2026-07-30T01:22:50Z | theoria-arm (verify.py) [18] |
| 32 | 2026-07-30T02:30:39Z | theoria-arm (verify.py) [19] |
| 33 | 2026-07-30T02:52:18Z | theoria-arm (verify.py) [20] |
| 34 | 2026-07-30T04:03:14Z | theoria-arm (verify.py) [21] |
| 35 | 2026-07-30T05:40:33Z | **monitor** (verify.sh) [22] ← switches back and stays |
| 36 | 2026-07-30T07:03:05Z | monitor (verify.sh) [23] |
| 37 | 2026-07-30T07:51:14Z | monitor (verify.sh) [24] |
| 38 | 2026-07-30T08:52:31Z | monitor (verify.sh) [25] |
| 39 | 2026-07-30T09:42:45Z | monitor (verify.sh) [26] |
| 40 | 2026-07-30T10:34:32Z | monitor (verify.sh) [27] |
| 41 | 2026-07-30T11:36:27Z | monitor (verify.sh) [28] |
| 42 | 2026-07-30T12:41:15Z | monitor (verify.sh) [29] |
| 43 | 2026-07-30T13:09:49Z | monitor (verify.sh) [30] ← `last_seen` on the live flag |

**Sequence in five segments** (raw, no interpretation beyond reading the log):

1. `01:55:33Z – 02:18:57Z` — **theoria-arm, kind `pytest`** (4 flags). At this
   point theoria-arm had no `verify.py`; the gate was the bare suite.
2. `02:32:58Z – 04:14:01Z` — **monitor `verify.sh`** (10 flags). Territory
   changes with no branch change in between.
3. `05:25:48Z – 10:29:35Z` — **theoria-arm `verify.py`** (2 flags). The gate
   *kind* for theoria-arm has changed from `pytest` to `verify` between
   segments 1 and 3 — theoria-arm gained a `verify.py` on master.
4. `15:07:43Z` — **monitor `verify.sh`** (1 flag), then
5. `17:21:59Z – 04:03:14Z` — **theoria-arm `verify.py`** (17 flags), then
6. `05:40:33Z – 13:09:49Z` — **monitor `verify.sh`** (9 flags, current).

So: 3 distinct gate identities (theoria-arm/pytest, theoria-arm/verify.py,
monitor/verify.sh) and **5 territory switches** across 43 log flags. The
`attempts:` counter on the flag file (30) and the `NEEDS-HUMAN: N attempts since
2026-07-29T04:14:01Z` string aggregate all of them into one number.

**Prior OPS-M note in the log itself**, `2026-07-29T16:01:59Z`
(`merge.log:1876`), verbatim on this point:

> `NOTE-BY-OPS-M a3-campaign-devpile: its flag is NOT cleared, but the reason
> recorded on it is wrong and the NEEDS-HUMAN counter overstates it. The 'verify
> gate red in monitor' of 15:07:43Z was master's, as above; a3's own red is in
> theoria-arm -- tests/test_arm.py::test_the_archive_stays_accountable, manifest
> re-derivation drift on leg 20260729T004020Z-leg01 -- which is green on clean
> master and red with a3 merged. ci_merge walks sorted(dirs) and returns on the
> first red, so monitor was masking theoria-arm. The '4 attempts' aggregate at
> least three distinct causes across the day (tests red in theoria-arm
> 01:55-02:18Z; an older monitor red 02:32-04:14Z; theoria-arm's verify red
> 05:25Z and 10:29Z; p16's stale assertion 15:07Z). Escalation is a semantic call
> for theoria-arm's owner, not a merge; inbox item written.`

That note was written at attempt 4. The pattern it describes continued for 26
more attempts.

---

## 3. The tracked-memo rewind — **CONFIRMED**

Cycle 32's claim: `monitor/ci/CONFLICT-*.md` is a **tracked** file, so checking
out / committing a tree rewinds the queue's memory of the flag.

`git ls-files --error-unmatch monitor/ci/CONFLICT-origin_agent_a3-campaign-devpile.md`
→ tracked. `git check-ignore` → not ignored.

At `ea4f6af6` (committed) vs the live working tree, same path:

| field | committed @ `ea4f6af6` | live working tree |
|---|---|---|
| `reason` | `verify gate red in theoria-arm (verify.py)` | `verify gate red in monitor (verify.sh)` |
| `tip` | `a5812063b9a6b7b699bd8acb58f96dd770c298f8` | `1e29578a58ce1dc398c5830b7be6f6e6b78dd03d` |
| `base` | `3d59d0a63cffeb0e1f865c2bacc8508c5232087b` | `d1da2c9ceb4309e602d654e4b2a74dcb8a5ee599` |
| `last_seen` | `2026-07-30T04:03:14Z` | `2026-07-30T13:09:49Z` |
| `attempts` | **21** | **30** |

Cycle 32 recorded committed 21 / live 29; the live counter has since advanced to
30 (one more flag at 13:09:49Z), and the base it names has moved from `cc7e414e`
to `d1da2c9c`. The *substance* of the claim — committed 21 vs live 21+, i.e. a
9-attempt rewind — is **confirmed**, with the committed side matching exactly.

`git log -p --follow` on the flag file shows the tracked file has only ever been
committed at these five points, and the recorded `attempts` at each:

| commit | date (local) | `attempts` written |
|---|---|---|
| `43b29a56` | 2026-07-29 12:15:07 | 1 (file created; `last_seen` 04:14:01Z) |
| `69938a08` | 2026-07-29 18:08:17 | 1 → 2 |
| `0d6d4ea4` | 2026-07-29 22:25:50 | 2 → 3 |
| `0749a84f` | 2026-07-29 23:11:08 | 3 → 4 |
| `ab85017d` | 2026-07-30 12:45:32 | 4 → 21, and `base:` first appears |

The committed series is `1, 2, 3, 4, 21` against a live series that reached 30.
The commits are snapshots of whatever the live file happened to say at commit
time, and 26 of the 43 log flags never got a commit at all. Anyone who checks out
a commit and reads the flag file gets the counter as of that snapshot, not the
queue's actual state — which is what "commits rewind the queue's memory" means
here. Also worth naming: `base:` did not exist as a field until `ab85017d`, so
the first four committed snapshots record no base at all.

---

## 4. Pile-cut compliance (hard constraint, checked before running anything)

`theoria-arm/verify.py` was audited before being run. It is compliant:

* `verify.py:169` builds `argv = ["--mock", "--slug", SLUG, "--game", GAME,
  "--budget", BUDGET]` and `:170` asserts `"--mock" in argv and "--desk" not in
  argv, "offline only"`.
* `:85` `GAME = "g50t-5849a774"` — a **development-pile** game — and `dev_pile()`
  (`:217`) reads `arc-recon/data/piles.json` and refuses the run if the pinned
  game is not in the dev pile.
* `:194-195` the child is launched with `ARC_API_KEY` and `ANTHROPIC_API_KEY`
  popped from its environment.
* The gate's own docstring: "**This gate never spends, never reaches the
  network, and never needs `ARC_API_KEY`.**" The only socket is a loopback bind
  to an in-process mock.

So the theoria-arm gate is safe to run and was run. **Nothing else was run**: no
`harness.run` without `--mock`, no `--desk`, no `make play-local` /
`verify-local` / `list-games`, no swarm runner, no `environment_files/` access.
No sealed-pile game content was opened, read, or summarised — the only game id
that appears anywhere in this measurement is `g50t-5849a774`, which is in the
development pile.

Nothing was skipped on pile-cut grounds, because nothing in the gated path
reaches the live API.

## 5. Gate results

### 5.1 `monitor` gate — **rc 1, but it did not reach a verdict**

Invoked exactly as `ci_merge.py:543-544`: cwd `<wt>/monitor`, cmd
`["C:/Program Files/Git/bin/bash.exe", "<wt>/monitor/verify.sh"]`, PYTHONPATH
prepended with the worktree root, no timeout imposed by me short of 1800.

**Dying stage: `[1/4] tests` — and it did not fail, it timed out.** The whole
output was a traceback:

```
subprocess.TimeoutExpired: Command '['D:\\Miniforge3\\python.exe', '-m',
'pytest', '-q', '-p', 'no:cacheprovider',
'C:\\Users\\user\\Desktop\\theoria\\.worktrees\\opsm33-a3\\monitor\\tests']'
timed out after 900 seconds
```

raised out of `monitor/verify.py:141` (`_tests()`, `timeout=900`), unhandled,
through `verify()` at `:276` and `main()` at `:313`. **rc 1.**

This is a different rc-1 from the one the flag records. The flag's transcript
shows the gate completing all four stages and printing `RED: tests` with a
6-item failing list; here the gate never produced a single `== <stage>` banner,
never ran stages 2/3/4, and never printed `RED:`. `ci_merge.py:545-547` cannot
tell these apart — it reads `returncode != 0` and writes
`verify gate red in monitor (verify.sh)` either way, then attaches whatever
`r.stdout + r.stderr` happened to be, which in this case is a `TimeoutExpired`
traceback rather than a test verdict.

Caveats that belong on this number, since a timeout is a wall-clock measurement
and not a property of the tree:

* `ci_merge.py` (pid 32352) was running concurrently throughout, by design of
  cycle 33's method note.
* Cycle 33 dispatched **six** measurement agents in parallel, each running gates
  on this same machine. The 900 s budget was consumed under that load.
* `monitor/verify.py:141`'s inner `timeout=900` is *half* of `ci_merge`'s outer
  `timeout=1800` (`ci_merge.py:543`), so the inner one binds first and the
  territory is reported as failing its own check rather than as having run out
  of time. Same failure shape `gates.gate_env`'s docstring warns about, one
  layer up.

The `python -m pytest -q -rf` run below is therefore the load-bearing
measurement of what is actually red in `monitor` on this tree.

### 5.2 `monitor` — `python -m pytest -q -rf`

(running)
