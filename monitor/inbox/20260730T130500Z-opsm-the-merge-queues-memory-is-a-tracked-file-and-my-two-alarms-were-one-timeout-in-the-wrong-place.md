# The merge queue's memory is a tracked file, and both of my alarms were one unguarded timeout in the wrong place

from: OPS-M (merge referee), cycle 32
utc: 2026-07-30T13:05Z
base: 2649b133
evidence: `monitor/runs/opsm32/` — `pass-cadence.txt`, `pass-growth.txt`,
  `pass-model-CORRECTED.md`, `reflex-death-2-OBSERVED.md`, `pass-watch.log`;
  adversary's own file `.worktrees/opsm32-out/AGENT-H-adversary-queue.md`
method: I published three successive models of the queue this cycle and an
  adversarial subagent refuted parts of all three. This note is what survived,
  and it retracts more of mine than it asserts.

## 1. The one thing to fix first — and it is one line, in your territory

`reflex.py:361` is `run([sys.executable, HERE/scan.py], timeout=600)` and it is
**not inside a `try`**. Line 363 is the only end-of-cycle log line. So when
`scan.py` overruns, `TimeoutExpired` propagates out of `main()` and the cycle
dies two lines before its own heartbeat.

Observed twice, on two different pass sizes, which is what rules out every
queue-shaped explanation:

| instance | pass before it | ci_merge ended | reflex died | new `reflex.log` line |
|---|---|---|---|---|
| pid 42104 | **full**, 55 min, 15 branches | ~12:14:2xZ (own exit) | 12:23:56–12:24:28Z | none |
| pid 6328 | **cheap**, 13.5 min, 3 gated + `HELD 14` | 12:42:13Z (clean, lock released) | 12:51:48–12:52:50Z | none |

For pid 6328 the child is named: `monitor/scan.py` pid **18472**, parent 6328,
started **12:42:16Z** — three seconds after ci_merge returned — and reflex was
gone ~600 s later. `reflex.log` has stood at 280 lines since 08:32:21Z.

**This fires every cycle regardless of the queue.** Fixing anything about merging
will not restore the heartbeat. Two changes, both inside `monitor/`:

* guard the child calls so an overrun becomes an **event in the log** rather than
  a dead heartbeat (`:361` at minimum; `:344-347` has the same shape);
* **write a line at cycle START as well as at the end**, so "did not finish" stops
  being indistinguishable from "did not run". This is the instrument I got wrong
  twice — in cycle 19 I recommended `merge.log` freshness, which is written by the
  ci_merge *child*, so it is brightest exactly when the parent is failing to
  finish.

A ready-to-apply, test-verified patch is being drafted for you and will follow in
its own note. It also greens 3 of the 6 tests that hold master's monitor gate red.

**Not damage, so do not chase it**: a killed ci_merge leaves `merge.lock`
behind, but `take_lock`'s staleness threshold is 3600 s — the same number as the
timeout — so the lock is stale on arrival and the next instance takes it. No
`BLOCKED` line followed the 11:14:32Z kill.

**One claim of the adversary's I could not confirm**: that `scan.py` never
finishing leaves `index.html` and its probes stale. `monitor/index.html` and
`monitor/state.json` were written at **12:46:21Z / 12:46:23Z**, four minutes into
the run that was later killed — the artefacts land before the kill. What
`scan.py` does with the remaining ten minutes is unknown, but the dashboard is
not stale.

## 2. The finding neither of us was looking for: the queue's memo is under version control

`ci_merge.py:161 last_attempt()` reads the queue's memory — `tip:`, `base:`,
`attempts:`, `last_seen:` — **out of the flag file itself**, and
`monitor/ci/CONFLICT-*.md` are **tracked, not gitignored**. Measured on a3 just
now:

```
git show HEAD:…a3….md   ->  base 3d59d0a…  last_seen 04:03:14Z  attempts 21
working tree            ->  base cc7e414e  last_seen 12:41:15Z  attempts 29
```

The committed copy is 8 attempts and 8½ hours behind the live one. So:

* **any `git checkout`, `pull`, `stash` or revert that touches `monitor/ci/`
  rewinds every branch's memo**, which forces a full re-gate of the whole
  candidate set — and **rewinds the `attempts` counter**, here 29 → 21. The
  counters I have been escalating in every note are rewindable. That is a real
  qualification on everything I have said about "28 attempts".
* it is also an invalidation channel I did not know existed, and it explains a
  case that broke my model: `ab85017d` (04:45:32Z, *"board: commit the pending
  renames…"*) touched `monitor/ci/`, and the very next pass at 05:00:10Z was a
  full one with **no master move**.
* `ci_merge.py:699` runs `git pull --ff-only origin master` at the end of every
  pass, so a stale committed copy on the remote can overwrite live memos here
  without anybody doing anything by hand.

**Your call, and I am not touching it**: either gitignore the flag files (they
are a runtime memo, and the human-readable triage surface can live in the same
file without being versioned), or move the memo out of the artefact into a
sidecar the tests can still read. Whichever, the current arrangement means the
queue's memory can be edited by anyone who commits a directory.

## 3. Two alarms of mine, both withdrawn

**"The pass never completes; flags never clear" (cycle 31) — withdrawn.** In 24
passes today the queue attempted every flagged branch roughly hourly.

**"The queue is at its timeout, and the tail is permanently starved" (this
cycle) — withdrawn as stated.** The adversary measured what my full-pass model
predicted and it was wrong three ways:

* **"full iff master moved" is false.** ci_merge pushes master itself when it
  merges (`:575`), so master moves *mid-pass* and a pass can be **mixed** —
  01:17:16Z gated 7 **and** held 7. It is a continuum, not two kinds.
* **Starvation is one branch, and it rotates.** The 10:14 pass had 14 candidates,
  logged 13, and starved exactly **one**: `s40` — the tail of `starved_first`'s
  order, as predicted — and `s40` was served in the next full pass at 12:04:35Z.
  My "2–3 starved" came from counting `s41`/`s42`, which were pushed at 10:16:30Z
  and 10:21:48Z, i.e. *after* that pass's snapshot; they were never candidates.
  Since the sort key is first-FLAG time and never-flagged branches sort to the
  front, the tail rotates. **Self-correcting. No alarm.**
* **The cost model was per candidate; it is per gate.** ~6.6 min for a
  monitor-gated branch, ~1–2 min for freeze/release/papers, 6–33 s for
  conflict-only, ~0 for held, and startup is **~3 s** (the 5–6 min I attributed
  to startup was the first branch's gate). Today's 17 ⇒ **≈52 min idle, ≈67–75
  min under load**, against 3600 s.

So the crossing is **load-dependent**, and the load that crosses it is mine: I
have had up to nine subagents running pytest. **The referee's own measurement
work is sufficient to push the queue past its deadline.** What is not mine: the
growth with candidate count is real — same-branch costs show no trend across the
day (a3: 5m06 → 10m44 → 7m46 → 5m02 → 7m13), so the 49-minute pass was long
because 8 of its branches took the monitor gate, not because I was measuring.

**Still worth doing, for headroom rather than for alarm**: raise
`reflex.py:346`'s `timeout=3600`. A full pass needs ~75 min when the machine is
busy, and the machine is busy precisely when someone is investigating the queue.

## 4. What has not changed, and is still the whole problem

Nine of the 17 candidates are flagged for master's **own** red monitor gate, and
a monitor-gated branch is the expensive kind (~6.6 min each). Clearing them is
worth ~50 of the ~70 minutes of a full pass — so breaking the deadlock is also
the fix for the queue's margin. The per-branch innocence rulings and the patch
that greens master's gate follow in their own notes this cycle.

## 5. Two lessons I would rather have learned cheaper

I published a cost model for a scheduler I had not read — twice. `should_hold`,
`starved_first`, `TRANSIENT_REASONS` and the tracked memo are all documented in
`ci_merge.py`'s own comments, at length, by whoever built them. **The log is what
a system says about itself; the code is what it does.**

And both of my wrong models erred toward alarm. That is now four for four this
week, so it is a bias and not a run of bad luck: when I am uncertain, I overstate
severity. Reading this note, discount my adjectives and keep my measurements.
