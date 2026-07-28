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

309 passed, 9 skipped on a machine with no Fast Downward build. The skips are
all FD's: the cross-rung agreement checks and the ladder bench rows, which need
a real planner by definition. Everything else — including the whole driver
protocol and the certificate rechecker — runs on any machine.

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

## The certificates, rechecked by something that never met the engines (E5)

`recheck/` is a second, independent route to "is this certificate the right
object" — the first being Lean, which answers a different question. It takes a
**rule set** and a **certificate** as two files and derives everything else: the
state space is the full product of the declared variable domains, and every edge
is computed by grounding the rules. It reads no edge list, takes no state space
from the certificate, and imports nothing from `engines/` (D-028; a test
enforces the import ban).

```bash
python -m recheck <rules.json> <cert.json>       # 0 ACCEPT 1 REJECT 3 INCONSISTENT
python -m recheck.verify_all --out runs/<id>     # the whole thing, expectations included
```

**The two runs it exists for.**

| rule set | certificate | verdict | |
|---|---|---|---|
| `peg4-0111` | `ic3_pdr`'s invariant | **ACCEPT** | 16 states, three conditions green |
| `a2-holed` | A2's `right_room_locked` | **ACCEPT** | 148 states — agrees with Lean, which is the only thing that makes the next row mean anything |
| `a2-world` | the same certificate | **REJECT** | `inv_closed`, witness `{cart=6,4} -down-> {cart=7,6}` |

The A2 pair is one certificate — the 0/1 pagoda weight
`cold-start-a2/theory/generated_holed/theory.lean` proves closed by `decide`,
`#print axioms unsolvable` = `[]` — against two rule sets one rule apart.
Against the manual it was written for it verifies. Against the world's own rules
it fails, and an independent breadth-first search over the same derived relation
reaches the goal in **18 actions**, the same length as A2's own recorded
refutation. A rechecker that passed that would not be lenient; it would be wrong.

All **18** `deadlock_carver` theorems recheck green as `dead_region`
certificates — 16 on `open4far`, 2 on `ringstuck` — against multi-valued rule
sets nobody grounded for them.

**The state space had to be restricted, so the restriction is proved** (D-029).
The pair deadlocks are false over the raw product, where the player may stand on
a box; the carver reasons over h²-consistent states. A rule set may therefore
declare a constraint, and the rechecker refuses to use it until it has shown the
constraint holds at init and is closed under every action. That closes the
cheapest attack there is: add `constraint: cart != "6,4"` to A2's world and the
false theorem verifies — except `constraint_closed` fails.

**The rule sets are transcriptions, and that is where the risk actually is**
(D-030). Every case is anchored to something published elsewhere, and an
adversarial audit ran the differentials rather than reading the code:

| anchor | measured |
|---|---|
| A2's recorded 18-action refutation replayed through `a2-world`, compared on the rendered 9×9 | 19/19 frames, 0/1539 pixels wrong |
| the derived step vs `cold-start-a2`'s compiled predictors, whole product | 592/592 both worlds, and 0/592 differences in *which rules fire* |
| Lean's explicit 592-row `step` table vs `a2-holed` | 592/592 |
| the pagoda table vs Lean's `def w` | 37/37 cells, exactly 21 zeros |
| the sokoban encoding vs the generated PDDL, independently grounded | 26 880/26 880 `open4far`, 1 056/1 056 `ringstuck` |
| optima the fixtures state by hand: ring 1, open4 6, ringstuck unsolvable, open4far 11; peg 1110/0111/1011 unsolvable, 1101 in 2 | 8/8 |

The differential was itself checked for the ability to fail: `a2-world`'s rules
against the *holed* predictor give exactly 4 disagreements, all of them the
teleport.

**25 forgeries, 24 refused and one that works.** `forgeries.py` catalogues ways
to lie to this rechecker — an invariant no state satisfies, one every state
satisfies, a certificate bringing its own goal or edge list, a shrunken variable
domain, a constraint that excludes the witness, a rule set edited under the same
name — each with the condition that must be the one to fail. The one that works
is **`delete-the-rule`**: hand it a rule set with a rule missing and a
certificate true of it, and it accepts, correctly. That is Theoria §1.3 entire
and no certificate checker can see it; it is carried as `expect: NOT-CAUGHT` and
the suite fails if it ever starts being caught.

Two anchors need `cold-start-a2/` on the machine. This package reads that
directory and writes nothing to it; when it is absent the anchors are reported
**unavailable**, never as passes.

## What an engine is worth, assembled for the paper (E6)

`ENGINE_DIVIDEND.md`, built by `python -m tools.engine_dividend_table` from three
artefacts, with `--check` to fail if it goes stale. Measurements in
`runs/20260728T191530Z-E6-engine-dividend/`.

Two thirds of E6's brief was already done and is **cited, not re-run**: E2
measured the deadlock dividend and the three-rung ladder, E7 audited the
dividend to destruction. What E6 added:

* **Pagoda certificates are no longer unrechecked.** E5 left `lp_potential`
  uncovered and said so; the only checker for those certificates imported the
  producing engine and trusted the producer's own witness list. `recheck/` now
  has a fourth condition shape that grounds the move set from the declared
  geometry and **refuses** an `obligations` key as input. 4 certificates, all
  ACCEPT; 3 have producer documents and all 3 differentials agree; 11 new
  forgeries, all as declared. The fourth case, `keyed-gate`, exists because a
  naive checker false-rejects it -- its only potential-raising move needs two
  keys and every two-key state is already outside the region.
* **The zero row.** `open4`: 16 true theorems, **47 expansions before and 47
  after**, pruner fired 0 times. D-020 argued this row is the informative one and
  it existed in no regenerable artefact. The theorems are sound and the hook is
  connected; there is no dead region on the path this search takes.
* Wall clock charged against `search_seconds` rather than the ~150 ms driver
  clock, with carving on the invoice -- **0 of 6 rows that ran a search repay the
  carve** -- and a tie-break sweep closing E2's gap G7.

**The rule the assembler now states, and why** (D-033): it reads verdicts rather
than re-deriving them. A draft that recomputed section C's optimality agreement
scored "no known optimum" as "disagreement" and rendered **no** against three
admissible planners. Three further defects had one shape -- a column reading a
key that does not exist and rendering as a valid table full of `--`. A
re-render-and-diff `--check` catches none of them; only a test pinning a real
number does, and the suite now pins several plus perturbation tests.

**Do not quote the §A table on its own.** Both its columns are heuristic-free
controls, the `ipdb` column is E7-demoted to *measured, not evidence*, and the
guard is a choice with a sign -- the `indexed` encoding makes `far5` blind go
958 -> 1159, a 21% loss.

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
