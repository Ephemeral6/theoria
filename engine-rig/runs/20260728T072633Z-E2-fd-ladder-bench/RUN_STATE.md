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
`tools/p13_fd_dividend.py` recorded for `open4far` and STATUS.md quotes. Two
things that agreement does and does not establish, since an earlier draft of this
document overstated it:

* It **does** show the dividend is not an artefact of the bundled search's node
  ordering — a Python BFS over frozensets and Fast Downward over SAS+ variables
  are genuinely different searches, and they cut the same fraction.
* It does **not** show two independent encodings agreeing. P-13's guard is
  `(safe1 ?b ?to)` plus a `forall`-`or` over `safe2`; this module's is
  `(not (dead1 ?b ?to))` plus a `forall`-`or` over `not deadpair`. Same shape,
  same schema, opposite polarity — a De Morgan dual of one encoding, not two.
  Agreement to the state is close to forced and was quoted as though it were
  corroboration. The `indexed` guard in §3c *is* a structurally different
  encoding, and its agreement with the `:adl` one (574 either way on `far4`
  blind) is the corroboration this paragraph originally claimed.

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

### 3c. Pair deadlocks *can* reach the admissible rungs — and make them worse

Fast Downward has no pruning hook (`choose_tier` clause 3), so the theorems are
compiled into the task. Corner deadlocks compile to a negative precondition and
stay in STRIPS. The obvious pair encoding needs a universally quantified negated
conjunction, hence `:adl` — and FD's `normalize.py` turns *any* `forall`
precondition into an **axiom**:

```
This configuration does not support axioms!
Terminating. Tried to use unsupported feature.        (driver exit 34)
```

`astar(lmcut())` and `astar(ipdb())` both refuse; `astar(blind())` accepts it.

**An earlier version of this document concluded from that that pair deadlocks
"cannot reach" the admissible rungs. That was wrong, and an adversarial review of
this run refuted it by building the encoding that does.** Nothing about a pair
deadlock needs quantification — only the schema's ignorance of how many dead
partners a position has. Number them: a static `npair<k> ?b ?to` gives the count,
static `deadpair<i> ?b ?to ?ob ?oc` names the i-th, and one `push-pair<k>` schema
per arity binds them and adds one ground `(not (at ?ob_i ?oc_i))` each. Pure
`:strips :typing :negative-preconditions`. It is the `indexed` guard in
`compile_theorems.py`, and it agrees with the `:adl` guard to the state on the one
configuration that accepts both (`far4` blind: 574 either way).

The optimal rungs take it. What they do with it is the finding:

| instance | rung | unguarded | + pair theorems (`indexed`) | task size |
|---|---|---|---|---|
| `far4` | `astar(lmcut())` | 23 | **34** | 1029 → 4101 |
| `far4` | `astar(ipdb())` | 12 | 12 | 1029 → 4101 |
| `far6` | `astar(lmcut())` | 47 | **66** | 2813 → 26253 |
| `far6` | `astar(ipdb())` | 18 | 18 | 2813 → 26253 |

Optimal length is unchanged on every row (soundness holds) and every plan was
mapped back to the original vocabulary and replayed. But `lmcut` expands **more**
states with the pair theorems than without them, and the task grows by roughly an
order of magnitude: FD compiles a negative precondition on a fluent into one
operator copy per other value of that variable, so the guard that was supposed to
cost only grounding costs the search a much larger operator set.

So the honest statement is not "cannot reach" but: **the theorems reach the
admissible rungs, and giving them to those rungs is a net loss.** That is a
stronger result than the one it replaces, and it only exists because the claim
was attacked. Both halves are pinned by tests
(`test_the_full_guard_is_refused_by_the_optimal_rung_for_the_reason_recorded`,
`test_the_indexed_guard_gets_the_pair_deadlocks_through_the_optimal_rung`).

### 3d. On unsolvable instances the translator settles it before any search

Every `ringstuck*` instance, every FD rung: **0 expansions before and after**, and
the translator's task size collapses to 4. FD proves unsolvability by relaxed
reachability and the search never starts. The bundled rung's 44 → 22 is a fact
about the bundled rung, which has no such check. STATUS.md already recorded this
for the single `ringstuck` fixture; it now holds across a five-size ladder.

**Soundness held everywhere.** Plan length is unchanged on every optimal
comparison, on both engines, under all three guards, across all nine instances —
and every plan produced from a theorem-compiled task was replayed against the
*original* domain by the rig's own validator. `MANIFEST.json`'s
`soundness_problems` is empty.

### 3e. A latent unsoundness the review found in the compiler itself

No number above is affected, but the compiler had a hole and it is worth the
record. The pair guard reads `at(?ob,?oc)` in the **pre-state**, where the pushed
box still holds its *old* position. For a pattern naming one box twice, the guard
therefore blocks transitions that *leave* the pattern rather than enter it —
strictly stronger than the theorem, and stronger is the direction that destroys
optimality. Measured with a deliberately vacuous same-box pattern, `far4`'s
optimal length went **11 → 25** and `guardable()` raised nothing.

Why no reported number moved: `carve()` cannot emit such a pattern, because two
positions of one box are mutex and `prove()` rejects patterns no reachable state
satisfies. Verified — 0 same-box pairs across all four `far` instances. But that
is a property of a *different module*, and `compile_theorems.py`'s own docstring
claimed its assumptions were "checked rather than assumed" while contemplating
only the direction that costs a dividend, never the one that costs correctness.
`tools/p13_fd_dividend.py` had this check and said why; this module had dropped
it. `guardable()` clause 3 restores it, with a test.

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

`tests/test_bench.py` — 34 tests, offline-safe apart from six that need a
planner. The FD log parser, the one part that depends on Fast Downward's exact
wording, is tested against **committed** FD output
(`runs/p13-fd-real/work/lmcut/run.log`): the assertion is the "A* expands 8
states" that P-13's manifest quotes, recovered from the log it quoted it from.

Four of those tests exist because an adversarial review of this run put them
there: the same-box guard hole (§3e), the hand-copied domain text nothing else
pinned, the indexed encoding reaching the optimal rungs (§3c), and the two pair
encodings agreeing on the one configuration that accepts both.

## 6. Gaps — what this run does not establish

* **G1 — Two domains.** Gripper and sokoban. The dividend result generalises as
  far as sokoban-like geometry and no further; nothing here says what a proved
  deadlock is worth in a domain whose dead regions are not positional.
* **G2 — One planner build.** FD 24.06+ rev `7120aa0`, one machine, one compiler.
  The axiom refusal in 3c is a property of *these* heuristic implementations.
* **G3 — closed, and the prediction it contained was wrong.** This gap used to
  read "pair deadlocks are unmeasured on the admissible rungs and cannot be
  measured without a different encoding … given 3b the expected value is zero."
  The adversarial review built that encoding (§3c). The measured value is not
  zero but *negative*: `lmcut` 23 → 34 on `far4`, 47 → 66 on `far6`. Recorded
  here rather than deleted, because a gap that turned out to be hiding a wrong
  guess is worth more on the record than a gap that quietly vanished.
* **G7 — absolute blind-search expansion counts carry an unstated tie-break
  dependence.** `astar(blind())` has a huge g-layer and its expansion count moves
  with FD's operator ordering: under a different f-tie-break the `far5` baseline
  goes 958 → 1479, a swing of +54%. The **ratios** are stable (−9%/−12% became
  −13%/−15%), and shuffling `:objects` / `:init` does not perturb anything since
  FD canonicalises — so the run is still deterministic and the dividend
  percentages hold. But the absolute blind numbers in `DIVIDEND.md` should be
  read as one tie-break's, not as a property of the instance. Found by the
  adversarial review; not currently measured by the bench itself.
* **G4 — Timings are not reproducible**, by nature. Every wall-clock figure here
  is one machine's afternoon. The orderings and the crossover point are robust;
  the individual milliseconds are not.
* **G5 — The dividend was measured on instances small enough for a blind search
  to finish.** Whether the ratio holds at sizes where blind search cannot run is
  exactly the regime where it would matter most, and is untested.
* **G6 — `.toolchain/` remains out of git** (§4). This run documents the hole; it
  does not close it, and closing it was not in scope.
