# E2 — the FD ladder, priced

**What was asked.** P-13 connected a real Fast Downward behind the three-rung
ladder. E2 asks what that is worth: a nodes / wall-clock / optimality table across
the rungs on one batch; the M9 deadlock theorems wired in as pruning, before and
after, against Theoria 1.9's promise that *每证一个死锁，规划器同时提速*; and the
reproducibility hole `.toolchain/` leaves, written into the manifest.

**What came out.** Both numbers exist now, and both qualify the thing they
measure. The ladder's cost is startup, not search — the bundled rung is the right
call on every instance this rig currently produces. And the deadlock dividend is
real, reproduces across engines, and **evaporates the moment an admissible
heuristic is switched on**: it is a substitute for a heuristic, not an addition to
one.

Artifacts: `LADDER.md` / `ladder.json`, `DIVIDEND.md` / `dividend.json`,
`toolchain.json`, `MANIFEST.json`. Raw Fast Downward output for every measurement
is in `logs/`; the instances are in `instances/`; the theorem-compiled tasks are
in `guarded/`.

```bash
cd engine-rig
export FAST_DOWNWARD=".../.toolchain/downward/fast-downward.py"
python -m bench --out runs/20260728T072633Z-E2-fd-ladder-bench
python -m bench.verify runs/20260728T072633Z-E2-fd-ladder-bench
```

---

## 1. The ladder's real cost is the driver, not the search

Wall clock, milliseconds, fastest of three (full table in `LADDER.md`):

| instance | stub-bfs | fd/lmcut *search* | fd/lmcut end-to-end | fd/ipdb end-to-end | fd/lama end-to-end |
|---|---|---|---|---|---|
| `gripper-05` | 11.6 | 2.9 | 153.1 | 160.0 | 152.5 |
| `gripper-07` | 100.8 | 24.1 | 175.2 | 170.1 | 150.0 |
| `gripper-08` | 270.4 | 64.5 | **218.5** | 181.8 | 158.3 |
| `gripper-10` | 1953.9 | 507.2 | 692.5 | 263.1 | 161.9 |
| `sokoban-far6` | 246.7 | 4.1 | 183.2 | **1774.1** | 182.9 |

Three readings:

* **Fast Downward's search is microseconds and its process is ~150 ms.** Every FD
  row on this batch sits between 140 and 260 ms almost regardless of the
  instance, because what the caller waits for is the Python driver starting, the
  translator running, and a 280 MB binary loading. On `sokoban-far6` the search
  itself is **4.1 ms out of 183 ms** — 2% of the bill.
* **The crossover is at `gripper-08`**, around 10⁴ stub expansions. Below it the
  bundled rung wins end to end; above it FD pulls away hard (at `gripper-10` the
  stub takes 2.0 s and LAMA takes 162 ms). Every instance the engines in this rig
  currently generate is below that line, which means **D-025 — pinning `run()` to
  `stub-bfs` for determinism — costs nothing in speed today.** That was argued as
  a determinism trade-off; it turns out not to be a trade-off at all yet.
* **`ipdb`'s cost profile is the opposite of `lmcut`'s, and on this batch it never
  pays.** `sokoban-far6`: ipdb expands 18 states to lmcut's 47 and takes **10×
  longer end to end** (1774 ms vs 183 ms), because it builds pattern databases
  before it searches. `backends.py` says ipdb is selectable because its profile
  is the opposite of lmcut's; this is that sentence with a number on it.

## 2. Optimality: the rungs agree, and the satisficing rung is genuinely not optimal

All 17 instances, four configurations, and every plan replayed by the rig's own
validator against the domain it was produced from:

* **Both optimal rungs hit the gripper closed form on all ten instances**, and
  agree with the bundled rung everywhere. The oracle is arithmetic
  (`2m + 2⌈m/2⌉ − 1`) and shares no code with any planner.
* **LAMA's first plan is up to 3.4× the optimum**: `sokoban-open4far`, optimal 11,
  LAMA 37. On the gripper family it happens to hit the optimum every time — while
  expanding **43 states at `gripper-10` where lmcut expands 66,176**. So
  `plan.optimal = False` on that rung is not a formality, and neither is the
  reason to keep it: it is the only rung that scales here, and its answer is not
  a length anyone may quote as an optimum.
* **`sokoban-ringstuck` / `fd-satisficing` reads *not entitled*, not *unsolvable*
  and not *error*.** LAMA exhausted its space and said so; D-024 refuses to let a
  satisficing rung read exit 12 as a proof. An earlier draft of this bench filed
  that as a run failure. It is a policy outcome and now renders as one.

## 3. The deadlock dividend — and the qualification that is the actual finding

### 3a. On a blind search, the dividend is real and reproduces across engines

| instance | search | before | after | saved |
|---|---|---|---|---|
| `far4` | stub-bfs (Python) | 808 | 571 | −29% |
| `far4` | `astar(blind())` (FD) | 837 | 574 | **−31%** |
| `far6` | stub-bfs | 3152 | 2788 | −12% |
| `far6` | `astar(blind())` | 3070 | 2706 | −12% |
| `ringstuck4` | stub-bfs | 44 | 22 | −50% |
| `ringstuck8` | stub-bfs | 216 | 162 | −25% |

The FD rows here use the **`full` guard**, because that is what makes them
comparable to the stub rows beside them: the Python pruner receives every theorem
the carver proved, so the only fair FD comparator is the guard that also carries
every one. §3b holds the guard fixed instead, for a different question.

The `far4` / blind row is **837 → 574**, which is exactly what
`tools/p13_fd_dividend.py` recorded for `open4far` and STATUS.md quotes. That
tool and `bench/compile_theorems.py` were written independently and encode the
theorems differently; they agree to the state. The dividend is not an artefact of
the bundled search's node ordering.

Two things the ladder of sizes adds that a single board could not:

* **The dividend shrinks as the board grows.** On the unsolvable ring family it
  falls from 50% at 12 cells to 25% at 28. The theorems cut a region of roughly
  fixed size — 2 corner theorems, whatever the board — so their share of a growing
  space falls. On the solvable family it settles at a flat 12% from `far5` up.
* **Carving is not free, and on this batch it costs more than it saves.** `far7`
  takes **1.44 s** to carve and saves **0.08 s** of blind search (0.878 → 0.797).
  Every row in the stub table is like that. The expansion dividend is real; the
  wall-clock dividend, once the carving is on the invoice, is negative
  everywhere here. It would turn positive on an instance large enough for the
  saved fraction of a much longer search to exceed a carve whose cost grows with
  the board rather than with the search — which this batch does not contain (G5).

### 3b. On an admissible heuristic, the dividend is zero

The comparison below is **singleton guard against singleton guard** on every row.
That matters: the `full` guard is refused by the two admissible heuristics (§3c),
so quoting blind's `full` number beside lmcut's `singleton` number would compare
16 theorems against 8 and the difference could be theorem count rather than
heuristic. Holding the guard fixed removes that reading. Same instances, same 8
theorems, same compilation — only the heuristic changes:

| instance | configuration | guard | before | after | dividend |
|---|---|---|---|---|---|
| `far4` | `astar(blind())` | singleton | 837 | 610 | **−27%** |
| `far4` | `astar(lmcut())` | singleton | 23 | 22 | −4% |
| `far4` | `astar(ipdb())` | singleton | 12 | 12 | **0** |
| `far6` | `astar(blind())` | singleton | 3070 | 2762 | **−10%** |
| `far6` | `astar(lmcut())` | singleton | 47 | 47 | **0** |
| `far6` | `astar(ipdb())` | singleton | 18 | 18 | **0** |
| `far7` | `astar(blind())` | singleton | 7196 | 6365 | **−12%** |
| `far7` | `astar(lmcut())` | singleton | 69 | 68 | −1% |
| `far7` | `astar(ipdb())` | singleton | 21 | 21 | **0** |

The same 8 corner theorems that buy a blind search 10–27% buy an admissible
heuristic between nothing and 4%. Adding the 8–32 pair theorems on top moves
blind a little further (`far4` 610 → 574, `far6` 2762 → 2706) and cannot be given
to the other two at all.

**This is the finding.** Theoria 1.9's promise — every deadlock proved, the
planner speeds up at the same time — holds against a search that has no other way
of knowing a region is dead, and does not hold against one that does. The
magnitudes are not close: on `far6`, lmcut expands **47 where blind expands
3070** (65× better) and the same theorems' contribution to blind is 1.11×. A
proved deadlock is a *substitute* for a heuristic, not an addition to one.

That does not make the theorems worthless — they are still the object the LLM
adjudicates into the playbook as a `prune` clause, and 1.9's argument that
deadlocks turn the test machine from a Sunday exam into a day job stands on
their *frequency*, not on their speed-up. What it does is remove the speed-up
half of the claim wherever a real planner is reachable, and this rig can now
say by how much rather than in principle.

### 3c. Pair deadlocks cannot reach the admissible rungs at all

Fast Downward has no pruning hook (`choose_tier` clause 3), so the theorems are
compiled into the task. Corner deadlocks compile to a negative precondition and
stay in STRIPS. Pair deadlocks need a universally quantified negated conjunction,
hence `:adl` — and FD's translator turns that into an **axiom**:

```
This configuration does not support axioms!
Terminating. Tried to use unsupported feature.        (driver exit 34)
```

`astar(lmcut())` and `astar(ipdb())` both refuse. `astar(blind())` accepts it and
runs. So the encoding is sound and usable, and it is closed off on exactly the two
rungs whose numbers anyone would want — which, given 3b, costs nothing measurable,
but is a real limit and is pinned by a test
(`test_the_full_guard_is_refused_by_the_optimal_rung_for_the_reason_recorded`) so
that a later FD build lifting it fails the suite rather than passing unnoticed.

### 3d. On unsolvable instances the translator settles it before any search

Every `ringstuck*` instance, every FD rung: **0 expansions before and after**, and
the translator's task size collapses to 4. FD proves unsolvability by relaxed
reachability and the search never starts. The bundled rung's 44 → 22 is a fact
about the bundled rung, which has no such check. STATUS.md already recorded this
for the single `ringstuck` fixture; it now holds across a five-size ladder.

**Soundness held everywhere.** Plan length is unchanged on every optimal
comparison, on both engines, under both guards, across all nine instances — and
every plan produced from a theorem-compiled task was replayed against the
*original* domain by the rig's own validator. `MANIFEST.json`'s
`soundness_problems` is empty.

## 4. The reproducibility gap `.toolchain/` leaves

Recorded in `MANIFEST.json` under `toolchain`, and re-derived from the live binary
at run time rather than quoted from P-13:

| | |
|---|---|
| Driver | `.worktrees/p13/engine-rig/.toolchain/downward/fast-downward.py` |
| Reported | `Fast Downward 24.06+`, revision `7120aa0` |
| Binary sha256 | `645671ae40d825478a043a9f94c856dc6130a11c166b3393837c153c5020aee1` |
| Matches P-13 manifest | **yes** — hash, commit and version all checked, not assumed |
| Build | `cmake -G Ninja -S src -B builds/release -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=<mingw64>/bin/gcc.exe -DCMAKE_CXX_COMPILER=<mingw64>/bin/g++.exe -DCMAKE_EXE_LINKER_FLAGS="-static" && cmake --build builds/release` |
| Compiler | winlibs mingw-w64 GCC 16.1.0 (UCRT, posix, SEH, r3) |
| Full recipe | `runs/p13-fd-real/TOOLCHAIN_MANIFEST.md` |

**The gap, stated plainly:** every Fast Downward number in this run came from a
binary that is not tracked by git and cannot be rebuilt from this repository
alone. The repo's byte-reproducibility requirement does not reach them. What
stands in for it is the hash, the commit and the build command above — weaker than
a committed artifact, and not pretending otherwise. What it buys is
falsifiability: a rebuild that hashes differently is a question a reader can
raise, where an unrecorded toolchain leaves nothing to ask about.

The bundled rung's half of every table **is** reproducible and `bench.verify`
checks it on a machine with no planner at all.

## 5. Verification

```
python -m bench.verify runs/20260728T072633Z-E2-fd-ladder-bench
```

1. every file the manifest lists still hashes to what it said;
2. no recorded soundness problems;
3. the three clocks are present and correctly nested (FD search ⊆ FD total ⊆
   subprocess wall) — **ordering only, never equality**;
4. this machine's planner binary is the one the run used, by hash;
5. five instances re-measured and their *structural* fields compared exactly.

Timings are deliberately excluded from (5). Node counts, plan lengths, task sizes
and exit codes are a function of the instance and the configuration and are
compared for equality; wall clock is a function of this machine on this afternoon
and is not. On a machine without `.toolchain/`, checks 4 and the FD half of 5 skip
with a stated reason and the rest still runs.

`tests/test_bench.py` — 26 tests, all offline-safe. The FD log parser, the one
part that depends on Fast Downward's exact wording, is tested against **committed**
FD output (`runs/p13-fd-real/work/lmcut/run.log`): the assertion is the "A* expands
8 states" that P-13's manifest quotes, recovered from the log it quoted it from.

## 6. Gaps — what this run does not establish

* **G1 — Two domains.** Gripper and sokoban. The dividend result generalises as
  far as sokoban-like geometry and no further; nothing here says what a proved
  deadlock is worth in a domain whose dead regions are not positional.
* **G2 — One planner build.** FD 24.06+ rev `7120aa0`, one machine, one compiler.
  The axiom refusal in 3c is a property of *these* heuristic implementations.
* **G3 — Pair deadlocks are unmeasured on the admissible rungs**, and cannot be
  measured without either a different encoding that avoids axioms or a
  heuristic that accepts them. Given 3b the expected value is zero, but that is a
  prediction, not a measurement, and it is not recorded as one.
* **G4 — Timings are not reproducible**, by nature. Every wall-clock figure here
  is one machine's afternoon. The orderings and the crossover point are robust;
  the individual milliseconds are not.
* **G5 — The dividend was measured on instances small enough for a blind search
  to finish.** Whether the ratio holds at sizes where blind search cannot run is
  exactly the regime where it would matter most, and is untested.
* **G6 — `.toolchain/` remains out of git** (§4). This run documents the hole; it
  does not close it, and closing it was not in scope.
