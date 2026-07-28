# engine-rig · STATUS

Live status of the engine rig track. Milestones are git tags; each one also
appends a paragraph to `/PARTNER_SYNC.md`.

## Milestones

| Tag | Scope | State |
|---|---|---|
| `engine-rig-m1-fixtures` | Fixtures A/B/C, deterministic generators | done |
| `engine-rig-m2-mdl` | `mdl_segmenter` | done |
| `engine-rig-m3-cegis` | `cegis_miner` | done |
| `engine-rig-m4-zerospace` | `zero_space` | done |
| `engine-rig-m5-lp` | `lp_potential` | done |
| `engine-rig-m6-fd` | `fd_adapter` | done (real Fast Downward — see below) |
| `engine-rig-m7-probe` | `probe_frontier` | done |
| `engine-rig-m8-integration` | all six engines + schema validator | done |
| `engine-rig-m9-deadlock-ic3-probe` | `deadlock_carver`, `ic3_pdr`, probes on the planner | done |

All nine milestones are reached. `python -m tools.run_all --force` runs the eight
engines end to end and emits 44 candidates, every line of which passes the frozen
schema validator. That stream is committed at `artifacts/candidates.jsonl`
(deterministic mode, so it is byte-stable and cannot drift unnoticed).

## M9 — the three gaps Theoria 1.9 and the A0 cold start named

**`deadlock_carver`** — conditional mini unsolvability theorems, `pattern AND
not-goal => dead`, proved by localised enumeration over the grounded task plus
h² mutexes derived from the action set. Theoria 1.9's own example is produced
literally (`at(b1,c11) AND not-goal => dead`, a box in a dead corner), alongside
the wall-pair deadlocks that actually need the mutexes. The same theorem is a
candidate and a planner pruner:

| Instance | Theorems | Expansions before → after | Plan |
|---|---|---|---|
| `open4far` (solvable) | 16 | 808 → **571** (−29.3%) | 11 either way |
| `ringstuck` (unsolvable) | 2 | 44 → **22** (−50.0%) | none either way |
| `open4` (shallow) | 16 | 47 → 47 (−0%) | 6 either way |

The zero row stays on the record (D-020): true theorems buy nothing when the
answer lies shallower than any deadlock. Soundness is checked by a referee that
exhausts the state space and shares nothing with the proof.

**`ic3_pdr`** — the fallback inductive-invariant engine. Acceptance line met:
Fixture C's `0111` is unsolvable, `lp_potential` is infeasible on it (D-014), and
IC3 returns `I(s) = (!pos1 | pos2) & (pos1 | !pos2)` — "positions 1 and 2 always
hold the same thing" — with `inv_init`/`inv_closed`/`goal_break` all true and
re-verified by an independent checker that does not import the search. The
solvable configuration `1101` correctly gets a replayed counterexample rather
than an invariant.

**Probes on the planner** — `probe_frontier` hypothetical configurations are
compiled into PDDL problems and handed to `fd_adapter`. SAT promotes the probe to
executable and charges the reach plan's length to its path cost; UNSAT returns an
`unreachable` verdict. On the sokoban ring: `p_row1` executable at 1.000 bits for
a path cost of 11 (a 10-move reach plan), `p_side` a full bit that cannot be
bought. This answers A0's "zero executable probes" (THEORIZE_LOG P-01..P-03) and
reproduces R-05's shape as machinery.

Fixture D (`fixtures/sokoban.py`) was added for the first and third: one
generated PDDL domain, four levels. All of it is offline and byte-reproducible.

Two engines were added after `CONTRACTS/candidates_schema.md` was frozen. The
contract and its validator are untouched; the new engines emit under the enum
member whose work they extend and name themselves in `payload.producer`
(D-018). **This is contract pressure worth a v0.2 conversation** and is flagged
in `PARTNER_SYNC.md`.

## Test suite

255 passed with Fast Downward reachable; 252 passed, 3 skipped without. The
three that skip are the cross-rung agreement checks, which need a real planner
by definition; everything else — including the whole driver protocol — runs on
any machine.

## The dividend, re-measured on a planner that knows nothing about this rig

M9's deadlock numbers were taken with the theorems as a Python pruner inside the
bundled BFS, so they only ever said something about the stub. `tools/p13_fd_dividend.py`
compiles the same theorems into PDDL as static guards on `push` (FD reads files
and has no pruning hook) and lets Fast Downward take the node account. All 16
`open4far` theorems and both `ringstuck` ones encode, none skipped.

| Instance | FD before → after | FD saved | Stub before → after (M9) | Same answer |
|---|---|---|---|---|
| `open4` | 49 → 49 | 0 | 47 → 47 | yes |
| `open4far` | 837 → **574** | −31.4% | 808 → 571 (−29.3%) | yes, 11 steps |
| `ringstuck` | 0 → 0 | n/a | 44 → 22 | yes, UNSAT |

Three readings, and the third is the one that costs us something:

* **`open4far`: the dividend survives the change of engine** — 31.4% against the
  stub's 29.3%, same 11-step plan. The saving was not an artefact of the stub's
  node ordering.
* **`open4`: the zero replicates.** D-020's negative result holds on FD too.
* **`ringstuck`: the theorems buy nothing a real planner needed.** FD's
  translator settles the instance by relaxed reachability before search begins
  (`No relaxed solution! Generating unsolvable task...`) and expands 0 states
  either way. M9's 44 → 22 is a fact about the bundled search, which has no such
  check — not a dividend a real planner would ever have collected. It stays on
  the record next to D-020's zero.

Second half of the same tool: every generated cold-start domain solved by both
backends. `a0-spike` (match / mismatch), `cold-start-a0` (base / no-button),
`cold-start-a2` (base / holed / repaired) — **7 of 7 agree**, on plan length and
on unsolvability, including three instances where FD independently proves the
UNSAT the bundled search found. `runs/p13-fd-real/DIVIDEND.md`.

## What the ladder is worth (E2, 2026-07-28)

`bench/` prices the three rungs on one batch — a gripper size ladder with a
closed-form optimum and the sokoban fixtures extended by size. Full numbers in
`runs/20260728T072633Z-E2-fd-ladder-bench/`.

* **Fast Downward's cost here is startup, not search.** Every FD row on the batch
  sits between 140 and 260 ms almost regardless of instance; on `sokoban-far6`
  the search itself is 4.1 ms of a 181 ms bill. The crossover against the bundled
  rung is at `gripper-08`, ~10^4 stub expansions. Every instance this rig
  currently generates is below it, so **D-025's determinism pin costs nothing in
  speed today.**
* **`ipdb` never pays on this batch**: `sokoban-far6` 1794 ms end to end against
  `lmcut`'s 181 ms, for 18 expansions against 47. Its pattern databases are built
  before it searches.
* **LAMA's first plan reaches 3.4x the optimum** (`open4far`: 37 against 11) while
  being the only rung that scales — 43 expansions at `gripper-10` where `lmcut`
  expands 66,176. `plan.optimal = False` there is load-bearing.
* **Node counts are reported per rung and never divided across rungs** (D-026):
  the stub expands grounded STRIPS states, FD expands SAS+ states.

**The deadlock dividend, and the qualification.** The M9 numbers were taken
against a blind search, and they replicate: `far4` blind 837 -> 574 (-31%) on FD,
matching `tools/p13_fd_dividend.py`'s `open4far` figure to the state, through an
independently written compilation (D-027). But switch the heuristic on and the
dividend goes to zero. Holding the guard fixed at the 8 corner theorems both
sides can take, `far6`: `blind` 3070 -> 2762 (-10%), `lmcut` 47 -> 47, `ipdb`
18 -> 18. **A proved deadlock is a substitute for a heuristic, not an addition to
one.** 1.9's frequency argument stands; its speed-up half does not survive a real
planner. Soundness held everywhere: plan length unchanged on every optimal
comparison, every guarded plan replayed against the original domain.

Pair deadlocks reach the admissible rungs only through a second encoding, and
doing so is a net loss. The obvious guard needs `:adl`, FD turns the `forall`
into an axiom, and `lmcut` / `ipdb` refuse a task with axioms (exit 34). Dropping
the quantifier for indexed static selectors (`indexed` guard) is pure STRIPS and
they accept it -- but `lmcut` then expands *more*: `far4` 23 -> 34, `far6`
47 -> 66, with the task an order of magnitude larger, because FD compiles a
negative precondition on a fluent into one operator copy per other value. Optimal
length unchanged throughout. Both halves pinned by tests.

An adversarial review of the run also found a latent unsoundness in the compiler:
the pair guard reads the pre-state, so a pattern naming one box twice blocks
transitions that *leave* it (measured: `far4` optimal 11 -> 25). No reported
number is affected -- `carve()` cannot emit such a pattern, two positions of one
box being mutex -- but that was a property of another module being trusted, and
`guardable()` now checks it. `tools/p13_fd_dividend.py` had the check; `bench/`
had dropped it.

## What a proved deadlock is worth to a planner, and what the claim should say (E7)

E2 found that Theoria 1.9's *每证一个死锁，规划器同时提速* fails on a real
planner. E7 audits that finding: replicates it, attacks it, and answers the
question it left open. Full account, with a suggested wording for the design
document, in [`DEADLOCK_CLAIM.md`](DEADLOCK_CLAIM.md); measurements in
`runs/20260728T150713Z-E7-deadlock-claim-audit/`; `python -m audit --out <dir>`
to re-run, `python -m audit.verify <dir>` to check.

**All nine of E2's rows replicate to the expansion**, and the ladder extends to
`far10`: blind saves 1279 / 1918 / 2415 expansions at far8/9/10, `lmcut` saves 1
at each. The `ipdb` column is reported and is evidence for nothing -- see below.
The blind dividend is steady only on this family (8.7%-27.1% across far4..far10);
across instances generally it runs 0% (`stub-wall`, `rnd0013`) to 100%
(`rnd0021`), so an earlier draft's "steady 10-27%" was wrong at both ends.

**The pruner is connected and the prize was not small.** The guard takes far6
from 312 ground actions to 296 at both the rig's grounder and FD's own
translator, 16 removed and 0 added; 69 firings and 237 states cut on `far4`, plan
unchanged; an independent walk that never consults the pruner puts 17-49% of the
reachable space in the dead region.

**The mechanism.** Three sets over the whole reachable space:

| | reachable | truly dead | **delete-relaxation dead** | theorem dead | theorems the relaxation misses |
|---|---|---|---|---|---|
| `far4` | 3342 | 2904 | **2904** | 1624 | **0** |
| `far5` | 13774 | 10687 | **10687** | 4508 | **0** |
| `far6` | 42803 | 29776 | **29776** | 9928 | **0** |

On this family the delete relaxation FD computes *before search begins* is
exactly the true dead set, and the theorems are a strict subset of it. far4 is
verified exhaustively against the real planner -- 0 disagreements in 3342 states
-- and the one-state crosscheck of the Python relaxation against FD's translator
stands at 116/116 across five geometries and two encodings.

**Three things the adversarial pass broke, all of which improved the result.**

* *"Not one state, at any size"* is false: `rnd0021` has eleven, verified against
  FD, and there `astar(lmcut())` goes 33 -> 0. But a width-1 theorem can escape
  the relaxation only if its pattern atom is a goal atom, which forces the
  instance to be unsolvable -- so for the 8 **singleton** theorems the guard
  carries, the zero on `far{N}` was a **theorem about that family, not a
  measurement**. `far{N}` is majority width-2 and that half remains a measurement
  at far4/5/6. The real boundary is **h^2 (the carver's mutexes) versus h^1 (FD's
  pre-search test)**.
* *"The dividend is zero because the information is redundant, not because it is
  unused"* is withdrawn as a false exclusive. `astar(lmcut())` does save
  expansions -- up to 153, tie-break-invariantly -- and where containment holds
  it is not by pruning: every state the guard removes was already an lmcut dead
  end. Deleting the dead push operators makes the relaxation *harder*, raising h
  on **live** states -- but that mechanism is isolated on one instance
  (`hunt0021` h(init) 15 -> 18) and merely consistent with the other three, whose
  h(init) does not move. A third mechanism nobody had named, exhibited once.
* *`ipdb` is not a usable instrument* at this effect size. `far9` 78 -> 30 dies
  under 2 of 8 seeds and under a bigger PDB budget; `swap-passage` 454 -> 0 is a
  `pdb_max_size` artefact. An earlier draft quoted far8's 27 -> 24 as a dividend.

**What this moves.** The boundary is not "which search you use" and not merely
"whether the relaxation covers the region", but **whether the theorems prove more
than the planner's own pre-search relaxation** -- cheap to test in advance.
§1.9's frequency argument and the theorems' role as proof obligations are
untouched; the unconditional speed clause is what needs conditioning.

## Convergence interface (post-M8)

`engine-rig/interop/` exports LP-solved pagoda certificates for the
theory-compiler track, which asked for them in its M8 note. Headline finding:
their peg fixture's stated goal (`count(Peg, alive=true) = 1`) admits **no** linear
pagoda certificate, although the unsolvability claim itself is true and two
narrowed goals (target cell 1 or 3) do get certificates. See
`interop/README.md`.

## Blockers

None. **The Fast Downward stub is no longer one of them** — FD is built and
connected (below), and the stub is now the ladder's bottom rung by design rather
than a substitute for a missing one. One standing deviation remains, recorded
rather than worked around: the frozen `engine` enum (D-018), which the newer
engines emit inside rather than edit.

## Fast Downward — connected (P-13)

**FD is built from source and connected.** The blocker recorded above is
cleared. Fast Downward 24.06+ (`7120aa01`), compiled with winlibs GCC 16.1.0,
235 targets, no patches. Provenance for every fetched artifact — URL, version,
size, sha256, build command, tool versions — is in
`runs/p13-fd-real/TOOLCHAIN_MANIFEST.md`; the toolchain itself lives in the
gitignored `.toolchain/` and is not committed.

```bash
export FAST_DOWNWARD="<repo>/engine-rig/.toolchain/downward/fast-downward.py"
```

Point it at the **driver**, not `downward.exe`: only the driver understands
`--alias`, which is how the satisficing rung asks for LAMA.

Setting that variable is the whole integration — no caller changes. With it set
the suite is **255 passed**; without it, **252 passed, 3 skipped**.

### The three-rung ladder (Theoria 1.10b)

| tier | who answers | length-optimal |
|---|---|---|
| `stub-bfs` | the bundled grounded-STRIPS BFS | yes |
| `fd-optimal` | Fast Downward, `astar(lmcut())`, `astar(ipdb())` selectable | yes |
| `fd-satisficing` | Fast Downward, LAMA's first pass | no |

`backends.choose_tier` picks the rung by a written rule, tested clause by clause
with an injected discovery function so it is verifiable on a machine with no
planner. `prefer="stub"` still wins unconditionally, and `run()` is pinned to
the bundled rung (D-025) so `artifacts/candidates.jsonl` is byte-identical
whether or not this machine has a planner. All three rungs return the same
optimal length on the rig's own instance, and the same plan.

### The one thing that will bite a rebuild

The plain build produced a binary that segfaulted while writing the plan file,
15/15, invisible under gdb. Cause: the dynamic binary imports `libstdc++-6.dll`
and Git Bash puts Git-for-Windows' own older GCC runtime first on `PATH`; the
ABI-incompatible library survived inlined code and died on the first
out-of-line call. Fixed with `-DCMAKE_EXE_LINKER_FLAGS="-static"`. **Do not drop
`-static`.** Two further limits: no LP solver is present (CPLEX not found), so
LP-based configurations are unavailable; and FD's driver cannot enforce
time/memory limits on Windows (it uses `preexec_fn`), which is the sole cause of
4 failures in FD's own `test-exitcodes.py` — budget planner runs with an
external `subprocess` timeout instead.

### What a real planner corrected in this rig

**Exit codes do not tell a proof from a shrug.** The adapter used to read a
missing plan file as a crash, which the cold-start-a0 track reported as a defect
(it cannot tell "proved unsolvable" — which triggers the certificate obligation
— from "the planner fell over", which is an incident). Fixing it turned up that
the obvious fix is wrong. FD's `driver/returncodes.py` has `TRANSLATE_UNSOLVABLE
= 10`, `SEARCH_UNSOLVABLE = 11`, `SEARCH_UNSOLVED_INCOMPLETE = 12` — and
measurement shows `SEARCH_UNSOLVABLE` is reserved for algorithms that detect
unsolvability structurally. **A complete `astar(blind())` that exhausts the
state space of a provably unsolvable instance exits 12**, the same code an
incomplete search that gave up returns. `backends.proves_unsolvable` therefore
decides on FD's own log line plus the completeness of the configuration we
chose, and refuses the claim on the satisficing rung even when the log says the
space was exhausted (D-024).
