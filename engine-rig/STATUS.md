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
| `engine-rig-m6-fd` | `fd_adapter` | done (stub backend — see below) |
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

218 passed, 1 skipped (`test_fast_downward_agrees_with_the_stub`, which starts
running the moment a Fast Downward executable is reachable).

## Convergence interface (post-M8)

`engine-rig/interop/` exports LP-solved pagoda certificates for the
theory-compiler track, which asked for them in its M8 note. Headline finding:
their peg fixture's stated goal (`count(Peg, alive=true) = 1`) admits **no** linear
pagoda certificate, although the unsolvability claim itself is true and two
narrowed goals (target cell 1 or 3) do get certificates. See
`interop/README.md`.

## Blockers

None. Two standing deviations, both recorded rather than worked around: the Fast
Downward stub (below, sanctioned by the M6 ticket) and the frozen `engine` enum
(D-018), which the new engines emit inside rather than edit.

## Fast Downward

**FD is not connected; the stub is in use.** This is the outcome the ticket
allows after two reasonable attempts. Both attempts, verbatim:

1. **Discovery.** Searched PATH for `fast-downward`, `fast-downward.py`,
   `downward`, `fd`, `planner`; checked `FAST_DOWNWARD`, `FAST_DOWNWARD_HOME`,
   `DOWNWARD_ROOT` and any `*downward*` environment variable; checked
   `C:\Program Files\fast-downward`, `C:\fast-downward`, `~/fast-downward`,
   `~/downward`, `/opt/fast-downward`, `/usr/local/lib/fast-downward`; checked
   for importable `downward`, `fast_downward`, `pyperplan`, `unified_planning`
   packages. Nothing found.
2. **Install.** `pip install downward` and `pip download fast-downward` both
   fail with "No matching distribution found" — Fast Downward is a C++ project
   distributed as source, not on PyPI. Building it from source would need a
   repository clone plus a C++ toolchain and CMake, which is outside both "two
   reasonable attempts" and this sprint's offline constraint.

**Substitute.** `engines/fd_adapter/search.py` is a breadth-first search over
grounded STRIPS behind the same `solve(domain, problem)` interface. BFS is
length-optimal for unit costs, exactly like the `astar(blind())` configuration
the FD path would use, so the acceptance criterion ("plan length equals the
hand-verified optimum") means the same thing under either backend. Each plan
records which backend produced it in `payload.backend`.

The Fast Downward code path (discovery, invocation, `sas_plan` parsing) is
implemented and **unexercised**. `test_fast_downward_agrees_with_the_stub` is
skipped here and starts running the moment an FD executable is reachable.
