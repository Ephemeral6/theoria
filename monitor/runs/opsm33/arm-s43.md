# Arm — `origin/agent/s43-three-guards-reverted`

> **EPILOGUE, written at 22:58 local — the branch landed while I was measuring.**
> `origin/master` moved off the pinned base during this run. As of now:
> ```
> 8a5a83f9 verify: a gate that times out is not a red gate, and this one had outgrown its own patience
> 6b953a60 Merge remote-tracking branch 'origin/agent/s43-three-guards-reverted'
> 954eb44c fleet: a pause switch that everything can see, and claim stops taking flags for workers
> 5ad83b31 OPS-M cycle 33: the push that broke a gate-passing merge was mine, ...
> 58dcafa8 S43: RUN_STATE, and a fixture split ...
> 83a7b02a monitor: seven guards were deleted in place, ...
> ```
> Three things this measurement said turned out to be checkable against what
> then happened, and all three checked out:
> 1. **The live-tree collision I flagged in §(f) was real.** `6b953a60`'s message
>    carries `# Conflicts: monitor/reflex.py`. The uncommitted live edit landed
>    first as `954eb44c`, and s43 then had to be conflict-resolved against it by
>    hand — exactly the six blocks I named.
> 2. **The resolution kept s43's shape.** On `origin/master` now:
>    `merge_events` at `:84`, `scan_events` at `:114`,
>    `except subprocess.TimeoutExpired:` at `:133`, the English SCAN FAILED
>    string at `:144`, all six guards (`sweep:EXIT` `:201`, `reap:EXIT` `:254`,
>    `BOARD-QUERY-FAILED` `:311`, `revive:GIT-EXIT` `:375`, `SUPPLY-UNKNOWN`
>    `:442`, `scan_events(` `:455`), **and** the live edit's `PAUSE =
>    os.path.join(HERE, "FLEET_PAUSE")` at `:29`. Nothing was lost either way.
> 3. **My gate finding was found independently and fixed.** `8a5a83f9`
>    (22:51:59) raises `verify.py`'s pytest ceiling 900 → 2400 as
>    `TESTS_TIMEOUT_S` and catches `TimeoutExpired`, returning **exit 124** with
>    "the suite did not finish, so nothing was proved either way. This is NOT a
>    red suite." Its message cites the same measurement I made independently:
>    "monitor/tests reaches 34% in 540 seconds and takes about thirty minutes end
>    to end". So the 900s timeout in §6 below was **not** the arm's fault and not
>    purely load — the suite had genuinely outgrown its own gate.
>
> Still **not** on master: FINDINGS change 3 —
> `git show origin/master:monitor/scan.py | grep base_gates` → no hits. The
> dashboard still cannot see a red master. And `monitor/ci/base_gates.json` does
> not exist yet (nothing has taken the red path since the merge).
>
> Everything below was measured against the pinned base `ea4f6af6` as instructed
> and is left as measured.


Measured per `monitor/runs/opsm33/METHOD.md`. Base pinned `ea4f6af6`.
Worktree: `.worktrees/opsm33-s43` (detached).

* Branch tip: `58dcafa844d5713ce0f1abf3af4faa5f2ddccb32`
  ("S43: RUN_STATE, and a fixture split so the counter test's red is behavioural")
* Second commit: `83a7b02a` ("monitor: seven guards were deleted in place, and
  nothing was gating master")
* Merge commit produced in worktree: `9efa5c0baa4475ffd6f18de417c8cb69ccdd50ea`
* Flag under measurement: 2026-07-30T14:21:14Z, "verify gate red in monitor (verify.sh)"

---

## JOB 2 — the substantive question (written first, per instruction)

### (a) How many guards `873d62ee` removed: **SEVEN**, not three and not four.

`git show 873d62ee` is a single-file diff (`monitor/reflex.py`, +69 −115). Every
removal below is a *reporting* guard: a construct that turned a silent failure
into a named event in `reflex.log`.

| # | Site in `main()` | Removed construct | What it guarded |
|---|---|---|---|
| 1 | sweep (`--include-standing`) | `if sw.returncode != 0: events.append("sweep:EXIT-%d" % sw.returncode)` | a crashed sweep prints no "freed from" lines — identical observation to a sweep with nothing to free. This step decides whether dead sessions' board claims are released. |
| 2 | §1 reap | `reap = run(...)` rebound to `out = run(...).stdout`, deleting `if reap.returncode != 0: events.append("reap:EXIT-%d")` | rc became *unrecoverable*, not merely ignored: a reaper that died reads exactly like a reaper with nothing to reap. |
| 3 | §0b worker headcount | `except Exception as exc: ... events.append("BOARD-QUERY-FAILED:%s(refill-skipped)")` → bare `except Exception: avail, claimed = 0, 0` | a crashed `board.candidates()` becomes indistinguishable from an empty board; `if not hold and avail:` then skips the whole refill loop without a word. |
| 4 | §3 revive loop | `_remote = run([...]); if _remote.returncode != 0: events.append("revive:GIT-EXIT-%d(loop-skipped)") else: <loop>` → inline `.stdout.lower()`, loop unconditional | **the money one.** A failed `git branch -r` yields `remote == ""`, every `in remote` test goes False, every dead session reads "never delivered", and the loop **revives sessions that had already finished** — paid API sessions. |
| 5 | §4 ci merge | `if r.returncode != 0: events.append("merge:EXIT-%d %s" % (rc, first_stderr_line[:120]))` | a crashed merger, a merger killed mid-run, and a clean no-op all logged `quiet`. |
| 6 | §4b supply alarm | `except Exception as exc: events.append("SUPPLY-UNKNOWN:%s")` → `except Exception: pass` | a *broken* board becomes quieter than an *empty* one (an empty board still emits `SUPPLY-LOW:0`). |
| 7 | §5 dashboard refresh (`scan.py`) | the entire `try/except subprocess.TimeoutExpired/except Exception` + `if scan_rc != 0: events.append("SCAN FAILED (rc=%s) ...")` → bare `run([... scan.py], timeout=600)` | both a non-zero scan rc **and** `subprocess.TimeoutExpired` escaping `main()`. This is the one that killed the reflex layer. |

**Guard #5 is on master again, but not because `873d62ee` spared it.** It was
deleted inline like the other six. It came back because `c8061d7b` ("monitor:
four checks that could not go red, including one that tested a copy of itself")
was developing the extracted `merge_events()` in parallel, and the merge commit
`7c1dd89b` resolved in favour of that parent. It survived by merge resolution,
not by intent — which matters, because *the count of guards a reader can see
missing is not the count that was attacked*. **I verified this independently:**

```
$ git log -1 --format=%P 873d62ee
cd048b324c36374a468e90fe9ddbca5ba79909ab          # single parent, direct on master
$ git merge-base --is-ancestor c8061d7b cd048b32; echo $?
1                                                  # merge_events was NOT on 873d62ee's line
$ git show cd048b32:monitor/reflex.py | grep -n "merge:EXIT"
336:                events.append("merge:EXIT-%d %s" % (r.returncode, first[:120]))
```

i.e. the guard was present and *inline* on 873d62ee's parent, so 873d62ee did
delete it. (`git log 873d62ee..ea4f6af6 -- monitor/reflex.py` → exactly
`7c1dd89b`, `c8061d7b`.) It now lives at
`reflex.py:95-116` of the base. So at base `ea4f6af6` **six of the seven are
still absent**.

**Honest qualification, and the branch states it itself** (docstring of
`test_s43_guards_deleted_in_place.py`): of the seven, **only two changed what
the loop does** — #4 (git-query → spurious paid revivals) and #7 (scan timeout →
dead heartbeat). The other five changed only what it *says*. Five are
restorations of the record, not control-flow fixes. A reader should not come
away thinking six control-flow bugs were fixed here.

**Why the deletion went unnoticed for 72 commits, per the branch:** five of the
seven were watched by `test_standing_reflex_no_third_value.py` and went red
immediately and stayed red, visibly. `BOARD-QUERY-FAILED` (#3) and the `scan.py`
guard (#7) were watched by **nothing**, so their deletion produced no signal at
all. #7 is the one that then cost the 131-minute dead heartbeat.

The commit message of `873d62ee` mentions **none** of the seven. It claims to be
about `MIN_FREE_GB` only. The seven deletions are unexplained collateral.

### (b) How many this branch restores: **all six that are still absent at base.**

Post-merge `git diff ea4f6af6 HEAD -- monitor/reflex.py` restores, verbatim
including the S28/S30 rationale comments:

1. `sweep:EXIT-%d` — restored (`reflex.py:196-201` post-merge)
2. `reap:EXIT-%d` — restored, `out =` reverted back to `reap =` (`:250-256`)
3. `BOARD-QUERY-FAILED:%s(refill-skipped)` — restored (`:296-315`)
4. `revive:GIT-EXIT-%d(loop-skipped)` — restored with the whole loop re-nested under `else:` (`:365-407`)
5. `merge:EXIT` — **untouched** (already present at base as `merge_events`; no diff hunk in §4)
6. `SUPPLY-UNKNOWN:%s` — restored (`:429-431`)
7. `SCAN FAILED` + `TimeoutExpired` catch — restored, **and refactored** into a
   module-level `scan_events(run_scan)` function (`:117-149`), by the same
   ADV-2/D12 argument that produced `merge_events`: inline in `main()` it is
   unreachable from a test, and `main()` cannot be driven in a test because that
   tick launches paid sessions.

**Net: 6 restored / 6 outstanding. Nothing left behind.**

The branch *name* says "three". The branch's own commit message says "seven".
The byte evidence says seven removed, one already back, six restored here.
The name is wrong and undersells the change by half.

### (c) Is the `scan.py` call wrapped in something catching `subprocess.TimeoutExpired` after merge? **YES.**

Post-merge call site, `monitor/reflex.py:433-446`:

```python
        # 5. light dashboard refresh
        #
        # S30: the return code used to be thrown away -- not even bound. A scan
        # that crashed therefore left the board frozen on the previous numbers
        # while this line logged the cycle as `quiet`, which is the same
        # sentence a healthy idle cycle writes. The two must not be the same
        # sentence.
        #
        # A timeout raises rather than returning, and it used to take the whole
        # reflex cycle down with it -- so it is caught in `scan_events` and
        # turned into an event, not into silence and not into a dead heartbeat.
        events += scan_events(
            lambda: run([sys.executable, os.path.join(HERE, "scan.py")],
                        timeout=600))
```

The `timeout=600` now lives inside a zero-arg lambda; the lambda is *invoked
inside the try*, so the raise happens within the handler's scope. Post-merge
`monitor/reflex.py:134-149`:

```python
    try:
        scan_rc = run_scan().returncode
    except subprocess.TimeoutExpired:
        scan_rc = "timeout(600s)"
    except Exception as exc:                    # noqa: BLE001 -- reported
        scan_rc = "%s: %s" % (type(exc).__name__, exc)
    if scan_rc == 0:
        return []
    # Deliberately does not change reflex's own exit code: the other four duties
    # in this cycle may all have succeeded, and failing the scheduled task for a
    # dashboard refresh would make *reflex* look dead. The signal lives in the
    # heartbeat line instead, where it reads differently from `quiet` -- which
    # was the whole point.
    return ["SCAN FAILED (rc=%s) -- the board should have been rewritten as a "
            "red failure page; if it was not, the failure exit is down too"
            % scan_rc]
```

Base `ea4f6af6` `monitor/reflex.py` at the same site is the bare one-liner:

```python
        # 5. light dashboard refresh
        run([sys.executable, os.path.join(HERE, "scan.py")], timeout=600)
```

`subprocess.TimeoutExpired` is a subclass of `SubprocessError`/`Exception`, and
at base nothing between this line and `main()`'s `try:` catches it — the only
enclosing handler is the `finally:` that drops the lock. So at base the raise
exits `main()`, the lock is released, and the heartbeat `rlog(...)` on the very
next line never runs. That is the 08:32:21Z silence. **The branch closes it.**

One behavioural note for the record: `scan_events` still does not change
reflex's exit code — deliberately, per its own comment. It converts a dead
heartbeat into a `SCAN FAILED (rc=timeout(600s)) ...` line in the heartbeat.
It does not make the scheduled task fail.

### (d) Wholesale revert, or forward re-application? **Forward re-application. Not a revert.**

Every one of `873d62ee`'s own changes survives the merge intact. Verified in the
post-merge tree:

* `reflex.py:19` — `import socket` still at module level (873d62ee hoisted it out of the `try`).
* `reflex.py:41-43` — the stated purpose of `873d62ee` is fully retained:
  ```python
  HEADROOM_GB = 3.0        # 不动用的余量
  PER_SESSION_GB = 0.6     # 单个会话的保守估计（实测 0.42–0.52）
  MIN_FREE_GB = HEADROOM_GB + PER_SESSION_GB
  ```
  (was `MIN_FREE_GB = 8`), still consumed at `reflex.py:346` (`if free_gb < MIN_FREE_GB:`).
* `reflex.py:227-247` — the serve-restart rewrite is retained in full: the
  `cmd /c start` invocation replaced by a direct `subprocess.Popen([sys.executable,
  "-m", "http.server", "8787", "--bind", "127.0.0.1"], cwd=HERE, ...)`, plus the
  3s wait and a `connect_ex` probe that distinguishes `serve:restarted` from
  `serve:restart-FAILED(port still shut)`, plus `serve:spawn-FAILED:%s`.

**So what else did `873d62ee` do besides deleting seven guards?** Two things,
both legitimate, both preserved:

1. **The stated fix.** `MIN_FREE_GB` 8 → 3.6 (headroom + per-session), aligning
   reflex with `standing.py`'s 2026-07-29 move to headroom-plus-per-session. The
   commit message's evidence: an entire night of `worker-hold:low-memory(7.5GB)`
   / `(7.3GB)` / `(6.7GB)` — a top-up mechanism that existed and had never fired.
2. **An unstated but real improvement — and it *adds* guards.** The serve
   restart previously (i) used `cmd /c start`, which did not actually start the
   server in this environment, and (ii) appended `serve:restarted`
   unconditionally, so success and failure wrote the same line. 873d62ee fixed
   both and added `serve:spawn-FAILED` / `serve:restart-FAILED(port still shut)`.

A `git revert 873d62ee` would have destroyed both. The branch does not revert;
it re-applies the six guards forward on top of them. This is the correct shape
for the change.

### (d-bis) The branch's own adversarial review, and what it concedes

`monitor/runs/20260730T1005Z-S43/ADVERSARIAL.md` records a dedicated
counter-subagent given the negative brief. Its results, verbatim in substance:

* All six absent guards confirmed genuinely absent — not renamed, not moved to
  another file, not covered by an outer mechanism, not `check=True`. It also
  confirmed the *deployed* `reflex.py` is byte-identical to master
  (`git status --porcelain -- monitor/reflex.py` empty in the main checkout), so
  "the running reflex is not the one on master" is closed off.
* It **overturned the branch's own original claim** about `merge:EXIT`: the
  criterion given is `git merge-base --is-ancestor c8061d7b cd048b32` → false,
  i.e. the `merge_events` extraction was never on `873d62ee`'s line of
  development; and `git show cd048b32:monitor/reflex.py | grep merge:EXIT` →
  line 336, still in inline form. Hence seven deleted, not six.
* **Strongest counter-argument it raised, which OPS-M should weigh:** the revive
  loop is not solely defended by guard #4. `reflex.py:331` calls `dispatch.py
  --only` *without* `--force`, and `dispatch.py:347` refuses on its own
  (`if branch_taken(pid, branches) and not args.force`), where `branches` comes
  from `git branch -a` — a superset of reflex's `git branch -r --list`. reflex
  only counts a revival when `"launched" in r.stdout`, so a dispatch-blocked
  attempt costs nothing, adds no death count, and skips the 45s stagger; plus
  `MAX_DEATHS = 3` caps it. The branch's rebuttal: `dispatch.py:49-52`'s own
  `git()` helper **also discards the return code and bare-returns `.stdout`**,
  so a machine-level git fault blinds both layers at once in the same direction.
  The second line of defence only holds for a fault local to reflex's one call.
* **A finding beyond scope, self-declared and deliberately not smuggled in:**
  nothing watches `reflex.log` for freshness. `grep -rn "reflex.log"
  monitor/*.py` hits only `reflex.py` itself, while `probe_standing`
  (`scan.py:1220-1230`) does exactly that job for `standing.log`, and
  `probe_scheduled_tasks` (`scan.py:644-672`) checks only registration/disabled
  state — never last-run time or last result. With `\TheoriaReflex` set to
  `MultipleInstances: IgnoreNew` and `ExecutionTimeLimit: PT72H`, **a tick that
  dies before `rlog()` can stay invisible for up to 72 hours.** The 131-minute
  silence on 07-30 was that mechanism, bounded only by a human happening to
  look. Filed as a separate item per contract, per RUN_STATE's 自供 section.

### (e) Not asked, but material: the branch is not only a guard restore.

The diff is 9 files, +1237 −39. `monitor/ci_merge.py` gets +122 lines
implementing a **base-verdict probe**, which is a change to how the merge referee
attributes blame:

* `base_verdict(wt, directory, row, base_sha)` — on a red gate only, resets the
  worktree to `origin/master` and re-runs the same gate there, memoised in
  `monitor/ci/base_gates.json` keyed `"<master sha>/<territory>"`. Returns
  `0` / non-zero / `None`. It explicitly **never falls back to "base is green"**.
* `blame_the_base(...)` — when the base is red, flags `origin/master` instead of
  the branch, and logs `FLAG origin/master: BASE RED in <dir> -- <branch> adds no
  new failure and is NOT at fault`. Prefix kept as `FLAG` on purpose, because
  `reflex.merge_events` scrapes with a literal `startswith("FLAG")`.
* `flag()` gains a **reason-change reset**: `if prev.get("reason") and
  prev.get("reason") != reason: prev = {}` — so a branch that fails three
  *different* ways no longer accumulates one `attempts` counter across all of
  them. The cited case is `a3-campaign-devpile` wearing
  `NEEDS-HUMAN: 28 attempts since 07-29T04:14` built from three unrelated reasons.

This is a behaviour change to the referee itself and is OPS-M's call, not a
measurement finding. Recorded here because it is in the same merge.

Also added: `monitor/runs/20260730T1005Z-S43/` (ADVERSARIAL.md,
FINDINGS-why-72-commits-landed-red.md, MANIFEST.json, PATCH_PLAN.md,
RUN_STATE.md) and two new test files (see Job 1 §5).

Its own FINDINGS doc proposes **three** changes; the branch ships **two**.
Change 3 — `probe_verify_gates` (`scan.py:915`) reading `base_gates.json` so a
red master reaches the dashboard — is **not implemented**; there is no `scan.py`
hunk in the diffstat. Per that doc, change 3 is "the only one that puts 'master
is red' on the dashboard" and is "almost free". Its absence is a gap, not a
defect.

Self-declared limitations the branch writes down (RUN_STATE §"三件必须写下来的"):

1. The three previously-red grep tests going green **is not proof** — they are
   source-string greps, and the test file says so. The claimed real proof is a
   normalised diff of the branch's `reflex.py` against `1585dd04:monitor/reflex.py`
   (pre-deletion), where the only differences are the four deliberately kept
   items (threshold fix, serve fix, `socket` hoisted to module scope,
   `merge_events` extraction) and zero drift inside the four restored blocks.

   **I ran that diff independently** (`git show 1585dd04:monitor/reflex.py` vs
   `git show origin/agent/s43-three-guards-reverted:monitor/reflex.py`). The
   claim is *substantially* true but not literally "zero drift" — there are two
   textual differences inside restored blocks, both comment/message-level, no
   control-flow effect:
   * In the `BOARD-QUERY-FAILED` block, one comment sentence is dropped:
     `# (EVIDENCE-3-standing-reflex.md). -1 is the third value: not measured.`
     → `# (EVIDENCE-3-standing-reflex.md).`
   * The `SCAN FAILED` event string was Chinese at `1585dd04`
     (`"SCAN FAILED (rc=%s) — 盘面应已改写为红色失败页；若没有，失败出口本身也挂了"`)
     and is English on the branch
     (`"SCAN FAILED (rc=%s) -- the board should have been rewritten as a red
     failure page; if it was not, the failure exit is down too"`). The branch has
     a test for this (`test_the_scan_failure_string_survives_a_cp936_console`),
     so it is deliberate — the em-dash and the CJK are exactly what breaks a
     cp936 pipe. **Anything grepping for the old Chinese string would now miss.**

   Everything else in the diff is accounted for: `import socket` hoisted,
   `MIN_FREE_GB` → `HEADROOM_GB + PER_SESSION_GB`, the serve rewrite,
   `merge_events()` extraction, `scan_events()` extraction. All four restored
   guard bodies are otherwise byte-identical, including the 30-line re-indent of
   the revive loop.
2. **9 of the 11 new `base_verdict` tests are ERROR on master, not FAILED** —
   `AttributeError`, because they exercise symbols this branch introduces. That
   proves the symbol is new and proves nothing about behaviour. Only the counter
   test gives a genuine behavioural red on master (inheriting `attempts=4`), and
   it uses a fixture deliberately touching no new symbol. A first draft mixed
   both into one fixture and made all 11 ERROR on master; that was fixed — this
   is what the tip commit `58dcafa8` ("a fixture split so the counter test's red
   is behavioural") is.
3. **The exit does not stop the next `873d62ee`.** It converts "silently blame
   nine innocents" into "name master within one merge tick". Actual prevention
   needs a pre-push hook running `monitor/verify.sh` at ~500s per push, and this
   repo's own history (`gates.py:19-22`, `scan.py:924-928`) says such a thing
   gets turned off within a day. Detect-and-name is the honest cheap option.

Its FINDINGS doc also asserts, with merge.log timestamps, that `873d62ee` was a
single-parent commit landed **directly on master** (`git log -1 --format=%P
873d62ee` → `cd048b32`), that `unmerged_branches()` (`ci_merge.py:448-457`) only
ever enumerates `origin/agent/*`, and that the green→red boundary brackets it in
a 36-minute window (`04:29:32Z MERGED ... gates: verify:monitor` green →
`04:55:40Z` commit → `05:05:27Z` first FLAG). It counts **nine** branches held on
master's red, longest 6h41m, ~35 monitor-red flag events at ~500s each ≈ 4.8 CPU
hours spent re-deriving master's own red and charging it to branches.

Two of its incidental observations that OPS-M may want independently:
* `ci_merge.py:548`'s return-on-first-red also hides *green* results:
  `a3-campaign-devpile` touches `PARTNER_SYNC.md, monitor, theoria-arm`, and
  `sorted(dirs)` puts `monitor` first, so `theoria-arm`'s gate had not run in 30
  hours — and it measures green.
* `probe_verify_gates` (`scan.py:873-940`) reports "24 territories gated, 22
  never shown able to go red" **by reading filenames**. `gates.run()` exists and
  is well written; no automatic path calls it.

---

### (f) URGENT, found while measuring: the LIVE working tree is being patched right now, in the same lines

At 2026-07-30T22:37Z (local) I ran `git status --porcelain -- monitor/reflex.py`
in the **main checkout** (not a worktree) to re-verify the ADVERSARIAL doc's
claim that the deployed file is byte-identical to master. It is **not**:

```
 M monitor/reflex.py          # 131 insertions(+), 84 deletions(-) vs ea4f6af6
```

`ls --time-style=full-iso`:

```
monitor/FLEET_PAUSE   727 bytes   2026-07-30 22:33:21 +0800
monitor/reflex.py   22254 bytes   2026-07-30 22:34:10 +0800
```

i.e. it was edited **three minutes before I looked**, while this measurement was
running. `monitor/FLEET_PAUSE` (also new, untracked) reads: `paused_by: monitor`,
`reason: 用户 2026-07-30 指示——停止一切派发 ... 由监控全权接手合并队列（18 条卡住，
其中 9 条同挂在 monitor 的闸门上）`. So this is a deliberate, user-directed live
change — not a stray edit. It is recorded here because of what it does to s43,
not as a complaint.

**The uncommitted live edit does five things, and four of them are the same
lines s43 touches:**

1. Restores `sweep:EXIT-`, `reap:EXIT-`, `BOARD-QUERY-FAILED`,
   `revive:GIT-EXIT-(loop-skipped)`, `SUPPLY-UNKNOWN` — **identical intent to
   s43, textually near-identical, but placed inline in `main()`.**
2. Restores the scan guard **inline**, in its original Chinese-message form:
   ```python
           try:
               scan_rc = run([sys.executable, os.path.join(HERE, "scan.py")],
                             timeout=600).returncode
           except subprocess.TimeoutExpired:
               scan_rc = "timeout(600s)"
           except Exception as exc:                    # noqa: BLE001 -- reported
               scan_rc = "%s: %s" % (type(exc).__name__, exc)
           if scan_rc != 0:
               events.append("SCAN FAILED (rc=%s) — 盘面应已改写为红色失败页；"
                             "若没有，失败出口本身也挂了" % scan_rc)
   ```
   **not** via `scan_events()`. So the fourth guard is already closed on the
   running machine — but only in the working tree, uncommitted.
3. **Deletes `merge_events()` and re-inlines it.** That is c8061d7b's extraction
   undone. `merge_events` is the symbol the existing test suite reaches; s43's
   `scan_events` is written by explicit analogy to it and cites it (ADV-2/D12).
4. Moves `import socket` back *inside* the `try:` (undoing 873d62ee's hoist),
   which the live file needs because it drops the module-level import.
5. Adds a genuinely new feature s43 knows nothing about:
   `PAUSE = os.path.join(HERE, "FLEET_PAUSE")` plus
   ```python
           if os.path.exists(PAUSE):
               events.append("PAUSED:no-hiring")
           elif not hold and avail:
   ```

**Consequence for the queue:** s43 and this live edit are two independent
restorations of the same six guards in the same file, in incompatible shapes
(extracted-function vs inline; English vs Chinese SCAN FAILED string; with vs
without `merge_events`). They do not conflict today only because the live edit is
uncommitted and `ci_merge.py` merges into a fresh worktree. The moment the live
edit is committed, every one of the six blocks is a conflict hunk — and s43's new
tests (`test_the_scan_step_is_not_reimplemented_in_the_loop`,
`test_the_scan_failure_string_survives_a_cp936_console`) assert on the *extracted,
English* shape and would go red against the inline Chinese one.

**Also confirmed:** `monitor/reflex.log`'s last line is
`2026-07-30T08:32:21Z quota: window reopened ...`. Nothing since. The heartbeat
has been silent for ~14 hours as of this measurement, not 131 minutes — the
131-minute figure in the branch's docs was measured earlier in the same outage.

---

## JOB 1 — arm measurement

### 1. Worktree

```
git worktree add --detach .worktrees/opsm33-s43 ea4f6af6      # ok
```

### 2. Merge — **CLEAN**

```
git merge --no-ff --no-edit origin/agent/s43-three-guards-reverted
Merge made by the 'ort' strategy.
```

`git diff --name-only --diff-filter=U` → empty. No conflicts.

Diffstat `ea4f6af6..HEAD`:

```
 monitor/ci_merge.py                                          | 122 +++++++++-
 monitor/reflex.py                                            | 155 +++++++++---
 monitor/runs/20260730T1005Z-S43/ADVERSARIAL.md               |  71 ++++++
 monitor/runs/20260730T1005Z-S43/FINDINGS-why-72-commits-landed-red.md | 158 ++++++++++++
 monitor/runs/20260730T1005Z-S43/MANIFEST.json                |  27 +++
 monitor/runs/20260730T1005Z-S43/PATCH_PLAN.md                | 174 +++++++++++++
 monitor/runs/20260730T1005Z-S43/RUN_STATE.md                 | 102 ++++++++
 monitor/tests/test_s43_base_red_is_not_the_branchs_fault.py  | 268 +++++++++++++++++++++
 monitor/tests/test_s43_guards_deleted_in_place.py            | 199 +++++++++++++++
 9 files changed, 1237 insertions(+), 39 deletions(-)
```

Branch commits over base: `83a7b02a`, `58dcafa8`.
Note the branch's own `RUN_STATE.md` records its baseline as `cc7e414e`, i.e. one
cycle behind the pinned `ea4f6af6`; the merge is clean regardless.

### 3. Gate — resolved command

`gates.gate_for(<wt>, "monitor")` →
`kind=verify`, `canonical=true`, `decorative=false`,
`cmd = ["C:\Program Files\Git\bin\bash.exe", "<wt>/monitor/verify.sh"]`

Invoked per `ci_merge.py:653-655`: cwd `<wt>/monitor`, `PYTHONPATH` prepended
with `<wt>`, timeout 1800.

### 5. THIRD CATEGORY CHECK — **IT FIRES.**

The branch adds two test files absent from master:
`monitor/tests/test_s43_guards_deleted_in_place.py` (10 tests) and
`monitor/tests/test_s43_base_red_is_not_the_branchs_fault.py` (11 tests) —
**21 new tests**, so the arm's collected count should exceed the control's by 21.

Method: second worktree `.worktrees/opsm33-s43-base` at `ea4f6af6`, the two test
files copied in *unchanged*, nothing else from the branch. Run against master's
code with the same `PYTHONPATH`:

```
python -m pytest tests/test_s43_guards_deleted_in_place.py \
                 tests/test_s43_base_red_is_not_the_branchs_fault.py --tb=no
→ 7 failed, 5 passed, 9 errors in 0.32s
```

Sorted red set against master's code (7 FAILED):

```
test_s43_base_red_is_not_the_branchs_fault.py::test_a_different_failure_does_not_inherit_the_old_counter
test_s43_guards_deleted_in_place.py::test_a_crashed_board_query_does_not_look_like_an_empty_board_to_refill
test_s43_guards_deleted_in_place.py::test_a_crashed_scan_is_distinguishable_from_a_clean_one
test_s43_guards_deleted_in_place.py::test_a_scan_timeout_is_an_event_and_not_a_dead_heartbeat
test_s43_guards_deleted_in_place.py::test_an_unexpected_exception_is_also_caught_and_named
test_s43_guards_deleted_in_place.py::test_the_scan_failure_string_survives_a_cp936_console
test_s43_guards_deleted_in_place.py::test_the_scan_step_is_not_reimplemented_in_the_loop
```

9 ERROR (all fixture-level `AttributeError: module 'ci_merge' has no attribute
'BASE_MEMO'`):

```
test_s43_base_red_is_not_the_branchs_fault.py::test_a_green_base_is_reported_as_green
test_s43_base_red_is_not_the_branchs_fault.py::test_a_green_base_still_blames_the_branch
test_s43_base_red_is_not_the_branchs_fault.py::test_a_new_master_sha_is_measured_again
test_s43_base_red_is_not_the_branchs_fault.py::test_a_probe_that_could_not_run_is_None_and_never_green
test_s43_base_red_is_not_the_branchs_fault.py::test_a_red_base_is_reported_as_red
test_s43_base_red_is_not_the_branchs_fault.py::test_a_red_base_names_master_and_spares_the_branch
test_s43_base_red_is_not_the_branchs_fault.py::test_an_unmeasurable_base_blames_nobody_silently
test_s43_base_red_is_not_the_branchs_fault.py::test_the_master_flag_line_starts_with_FLAG
test_s43_base_red_is_not_the_branchs_fault.py::test_the_verdict_is_memoised_per_master_sha_and_territory
```

**But the 7 reds are not 7 equal reds.** Failure text, `--tb=line`:

| test | how it fails at base | is this master's defect? |
|---|---|---|
| `test_a_scan_timeout_is_an_event_and_not_a_dead_heartbeat` | `AttributeError: module 'reflex' has no attribute 'scan_events'` (`:72`) | no — tests the branch's own refactor symbol |
| `test_a_crashed_scan_is_distinguishable_from_a_clean_one` | same `AttributeError` (`:80`) | no — same |
| `test_an_unexpected_exception_is_also_caught_and_named` | same `AttributeError` (`:94`) | no — same |
| `test_the_scan_step_is_not_reimplemented_in_the_loop` | `AssertionError: the loop no longer calls scan_events` — source grep for `scan_events(` in `main()` (`:109`) | no — same |
| `test_the_scan_failure_string_survives_a_cp936_console` | `ValueError: substring not found` (`:122`) — greps for the branch's *English* SCAN FAILED string | no — same |
| `test_a_crashed_board_query_does_not_look_like_an_empty_board_to_refill` | `AssertionError: the refill board-query guard is missing` — greps for `BOARD-QUERY-FAILED:%s(refill-skipped)` (`:136`) | **YES** — that literal was on master before `873d62ee` and is gone |
| `test_a_different_failure_does_not_inherit_the_old_counter` | `AssertionError: a brand-new failure inherited the old reason's count (4)`, `assert '4' == '1'` (`:251`) | **YES** — a real behavioural assertion on `ci_merge.flag`, no new symbol touched |

So the honest tally: **2 of the 21 new tests are genuine reds against master's
own behaviour/content**; the other 5 FAILED and all 9 ERROR only demonstrate that
the branch's new symbols do not exist yet. The branch's own RUN_STATE claims 1
(the counter test); by my measurement it is 2 — the `BOARD-QUERY-FAILED` grep is
also a true master regression, because that string was present at `1585dd04` and
deleted by `873d62ee`. Note the three `scan_events` AttributeErrors would fail
against `1585dd04` too, since the guard was inline there, not a function.

Also worth flagging for the third-category rule: five of these reds are **source
grep assertions**, which the test file itself admits are brittle. A behaviourally
wrong rewrite passes them. The branch's own answer to that is the normalised diff
in §(d), which I reproduced above and which holds.

### 6. Gate result — **rc = 1, and it does not die at a test failure**

Started 22:27 local, finished ~22:42 local (~900s). Full captured output, all 25
lines:

```
Traceback (most recent call last):
  File "...\.worktrees\opsm33-s43\monitor\verify.py", line 337, in <module>
    raise SystemExit(main())
  File "...\.worktrees\opsm33-s43\monitor\verify.py", line 313, in main
    result = verify()
  File "...\.worktrees\opsm33-s43\monitor\verify.py", line 276, in verify
    label, code, detail = _tests()
  File "...\.worktrees\opsm33-s43\monitor\verify.py", line 141, in _tests
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         os.path.join(HERE, "tests")],
        cwd=HERE, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=900)
  File "D:\Miniforge3\Lib\subprocess.py", line 556, in run
    stdout, stderr = process.communicate(input, timeout=timeout)
  ...
subprocess.TimeoutExpired: Command '['D:\\Miniforge3\\python.exe', '-m',
'pytest', '-q', '-p', 'no:cacheprovider',
'...\\.worktrees\\opsm33-s43\\monitor\\tests']' timed out after 900 seconds
GATE_RC=1
```

* **rc: 1**
* **stage it dies at: stage 1 of 4, `tests`** — the first stage. Stages
  `board states disjoint`, `real run`, `fields` never ran, so the gate produced
  **no stage table and no failing-test list at all**.
* **It does not die red-because-tests-failed. It dies on
  `subprocess.TimeoutExpired` escaping `verify.py:141`.** `_tests()` passes
  `timeout=900` to `subprocess.run` and nothing catches the raise; it propagates
  through `verify()` → `main()` → module level and Python exits 1 on the
  traceback.

**This is the same defect class as the S43 item itself, one level up.** S43
exists because `reflex.py` called `scan.py` with `timeout=600` and caught
nothing. `verify.py:141` calls pytest with `timeout=900` and catches nothing.
`verify.py:149-158`'s `_real_run` is worse — it calls `scan.build()` in-process
with **no timeout at all**, guarded only by `except Exception`, and
`TimeoutExpired` would not arise there but a hang would be unbounded.
`ci_merge.py` would read this rc=1 as "verify gate red in monitor" and flag the
branch, exactly as the 14:21:14Z flag reads.

**Caveat OPS-M must weigh before reading anything into the 900s.** The machine
was carrying ~39 concurrent python processes during this run (six cycle-33
measurement agents plus the live `ci_merge.py` pid 32352). Master's monitor gate
has been measured at ~500s (`opsm30/adversarial-master-red.md`: `monitor RED
rc=1 507.4s`). 900s is a 1.8x overshoot on a machine under 6-way measurement
load. **I cannot distinguish "the arm's +21 tests pushed the suite past 900s"
from "the parallel measurement load did".** The control arm at `ea4f6af6`,
measured by its own agent under the same load, is the comparison that settles it
— if the control also times out at 900s, this is load, not the branch.

A separate `python -m pytest -q -rf` follows, with no 900s cap, to recover the
failing-id set the gate could not produce.

### 7. Collected counts

```
arm  (merged tree)                              418 tests collected
base ea4f6af6 + the 2 S43 files --ignore'd      397 tests collected
                                                ---
                                                 21  = exactly the S43 additions
```

So the arm adds 21 tests and changes collection **nowhere else** — no test file
is deleted, renamed, or made uncollectable by the merge. **The control at
`ea4f6af6` must collect 397.** If the control agent reports 397, the counts
reconcile and any id present in the arm but not the control is either one of the
21 or a genuine regression.

### 8. Full pytest — failing-id set

<!-- PYTEST RESULT INSERTED BELOW -->
