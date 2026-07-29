# E11 · Deadlock and unsolvability claims, adjudicated by reachability

Ticket: **E11-engine-crosscheck-deep**, lane RES-3 (verify). Worktree
`.worktrees/e11-engine-crosscheck-deep/`. Read-only against `engine-rig/`,
`cold-start-*`, `a0-spike/`, `fuzzlab/`, `theory-compiler/`, `worldgen/`; no
network; sealed pile untouched (every fixture adjudicated here is synthetic and
lives in `engine-rig/fixtures/`, `worldgen/out/`, or a track's own `theory/`).

**Headline.** 50 machine-readable deadlock / unsolvability claims were
adjudicated by exhaustive reachability. **50 CONFIRMED, 0 refuted.** No engine
in this rig has issued an unsound deadlock theorem or a false unsolvability
certificate. Two negative controls were independently re-rejected, and the one
known-false theorem in the repo (`cold-start-a2`'s `right_room_locked`) was
re-refuted with its break localised to a single transition.

**The one genuine cross-source contradiction is not in the theorems.** It is in
the *decision procedure* two tracks use to decide when a planner has proved
unsolvability at all: `cold-start-a0/certify/fd_unsat.py` and
`engine-rig/engines/fd_adapter/backends.py` assign Fast Downward's exit codes
names that are **one apart**, and `cold-start-a0`'s reading is the unsafe one.
Both tracks' suites are green on their own; only the crossing exposes it (§4).

---

## 1 · Claim inventory

Nothing like this existed in the repo. "Deadlock" (a conditional theorem about a
state *region*) and "unsolvable" (a categorical claim about a start state) are
kept apart, per the ticket.

### 1a · Deadlock claims — `conditional_unsolvability`

Producer `engine-rig/engines/deadlock_carver`. Form: `<pattern> AND not-goal =>
dead`. Harvested by running `deadlock_carver.carve` on all four sokoban
instances — the defendant stating its own case; the verdict is mine.

| # | Instance | Pattern | Closure | Where the claim is on disk |
|---|---|---|---|---|
| 1–8 | `sokoban-open4far` | `at(b1,c11)`, `at(b1,c14)`, `at(b1,c41)`, `at(b1,c44)`, `at(b2,c11)`, `at(b2,c14)`, `at(b2,c41)`, `at(b2,c44)` | `no_deleting_action` | `engine-rig/artifacts/candidates.jsonl` lines 25–32; `engine-rig/recheck/cases/sokoban-open4far-dead-*.cert.json` |
| 9–16 | `sokoban-open4far` | `at(b1,c12)&at(b2,c13)`, `at(b1,c13)&at(b2,c12)`, `at(b1,c21)&at(b2,c31)`, `at(b1,c24)&at(b2,c34)`, `at(b1,c31)&at(b2,c21)`, `at(b1,c34)&at(b2,c24)`, `at(b1,c42)&at(b2,c43)`, `at(b1,c43)&at(b2,c42)` | `deleting_actions_blocked` | same, lines 33–40 |
| 17–32 | `sokoban-open4` | the same 16 patterns, against a **different goal** | both kinds | `carve()` only — **no `.cert.json` exists** |
| 33–34 | `sokoban-ringstuck` | `at(b1,c11)`, `at(b1,c14)` | `no_deleting_action` | `engine-rig/recheck/cases/sokoban-ringstuck-dead-b1-1{1,4}.cert.json` (not in `candidates.jsonl`) |
| 35–36 | `sokoban-ring` | `at(b1,c11)`, `at(b1,c14)` | `no_deleting_action` | `carve()` only — **no `.cert.json` exists** |

Two of these are additionally carried as machine-checked Lean, by the *other*
track, from the same candidate stream —
`theory-compiler/runs/20260728T080019Z-C4-deadlock-lean/`:

| Claim | File | Recorded status |
|---|---|---|
| `at(b1,c11) AND not-goal => dead` | `corner.lean` = `verify/Deadlock_corner.lean` | `#print axioms` empty, no `sorry`, no `native_decide`; 28672 leaf goals |
| `at(b1,c12) AND at(b2,c13) AND not-goal => dead` | `pair.lean` = `verify/Deadlock_pair.lean` | axiom set empty; 1792 leaf goals |
| negative controls `at(b1,c22)`, `at(b1,c22)&at(b2,c23)` | `verify/Control_*.lean` | **must fail**; `verify/EVIDENCE.json` records `rejected: true, failed_on_closure: true` |

Scope note carried by the producer itself, and honoured below —
`engine-rig/STATUS.md:194`: the pair deadlocks are *false* over the raw
Cartesian product, where the player may stand on a box; the carver reasons over
h²-consistent states. §6a judges over **reachable** states, all of which are
well-formed, so this qualifier is respected rather than sidestepped.

### 1b · Unsolvability claims — categorical

| # | Claim | Producer / where | Kind |
|---|---|---|---|
| U1 | goal unreachable from peg4 `1110` | `engine-rig/engines/lp_potential`; `artifacts/candidates.jsonl:21` | LP pagoda |
| U2 | goal unreachable from peg4 `1011` | `lp_potential.solve_certificate` (certificate exists; **not** in the committed stream) | LP pagoda |
| U3 | goal unreachable from peg4 `0111` | `engine-rig/engines/ic3_pdr`; `candidates.jsonl:42`; `recheck/cases/peg4-0111-ic3.cert.json`; Lean `verify/Ic3_{computational,algebraic}.lean` | inductive invariant |
| U4 | `sokoban-ringstuck` has no plan | `fd_adapter.solve_parsed` → `None`; `fixtures/sokoban.py:276-280`; `tests/test_sokoban_fixture.py:117`; `runs/…E2-fd-ladder-bench/ladder.json` | BFS exhaustion |
| U5 | peg-5 `11011` cannot reach `01000` | `engine-rig/interop/certificates/pagoda_5_11011_to_01000.json` | pagoda certificate |
| U6 | peg-5 `11011` cannot reach `00010` | `engine-rig/interop/certificates/pagoda_5_11011_to_00010.json` | pagoda certificate |
| U7 | probe `p_side` is UNREACHABLE — the box cannot reach `c31` on `sokoban-ring` | `engine-rig/engines/probe_frontier`; `tests/test_probe_reach.py:94`; `tests/test_integration.py:151` | reach verdict |
| U8 | A0 spike `mismatch` unsolvable — box never reaches `(3,2)`; `I(s) := (br+bc) % 2 = 0` | `a0-spike/artifacts/A0.lean:92`; `a0-spike/theory/theory.dsl:75` | Lean parity invariant |
| U9 | the Cart can never reach the goal, under the *no-button* manual | `cold-start-a0/theory/generated_no_button/theory.lean:321`; `artifacts/unsolvable_report.json` | Lean `w`-potential |
| U10 | `right_room_locked` — "the Cart can never occupy (2,7)" | `cold-start-a2/theory/generated_holed/theory.lean`; `engine-rig/recheck/cases/a2-right-room-locked.cert.json` | Lean `w`-potential |
| U11–U14 | four worldgen worlds are unsolvable, each with an `exhaustive_reachability` certificate | `worldgen/out/worlds/{t2-unsolvable-nodoor, v-707a64ad, v-d2c2b1b9, v-ce732813}/ground_truth.json` | exhaustive reachability |

### 1c · Explicitly *not* claims — the false-positive trap

| Non-claim | Why it is not a claim |
|---|---|
| `lp_potential` returns `None` on peg4 `0111` | **Silence, not a verdict.** `lp_potential` is sound but incomplete (`CLAUDE.md`; `engine-rig/DECISIONS.md` D-014 asserts this *as a test*). `0111` is genuinely unsolvable and no linear pagoda proves it. Reading the `None` as "solvable" manufactures a contradiction with U3 that does not exist. `fuzzlab/props/lp_potential.py:6-13` already encodes the same discipline: only a certificate issued for a *solvable* configuration is a finding. |
| `lp_potential` returns `None` on peg4 `1101` | Same silence — and here the configuration really is solvable, so the silence is correct. `ic3_pdr` returns a `Counterexample`, not an invariant. No disagreement. |
| `deadlock_carver` emitting no theorem for a dead state | Incompleteness of a 2-atom pattern language, quantified in §6a. Not a claim of liveness. |
| `cold-start-a3`'s two-portal UNSAT | A compiler artefact: with two portals `(portal-exit ?dest)` is unsatisfiable, so `fd_adapter.solve` reports a confident UNSAT **for a correct manual** (`cold-start-a3/a3pipeline/compile_a3.py:256`, `DECISIONS.md:129`). Recorded by that track as a known defect, not an unsolvability claim. |
| `cold-start-a2`'s `c7-4` UNSAT | Same category. |

---

## 2 · The link, and where independence is real

Every verdict below comes from code I wrote in this session: `indep_ground.py`
(an s-expression reader, a STRIPS grounder, forward BFS, backward alive-closure)
plus four small purpose-written drivers. Step by step, whose code ran:

| Step | Whose code |
|---|---|
| Parse `sokoban_domain.pddl` / `sokoban_*.pddl` | **mine** — fresh s-expression reader |
| Ground actions; derive static predicates; drop instances with false static preconditions | **mine** — re-derived from PDDL semantics, *not* `engines/fd_adapter/pddl.ground_actions` |
| Forward reachable set; backward alive-closure; optimal plan length | **mine** |
| peg-4 and peg-5 successor relation | **mine** — re-implemented from the prose in `fixtures/peg4.py`'s docstring; `peg4.successors` was not called on the adjudicating path |
| a2 rule-set evaluation (`and`/`or`/`=`/`!=`/`if`/`lit`/`var`/`param`/`table`/`call`) | **mine**; `engine-rig/recheck/expr.py` was **not** imported |
| A0 spike world (push2 and push1) | **mine** — `step` re-implemented from `A0.lean`'s own definition |
| `no_button` manual | **mine** — `step` table extracted from the Lean file, then BFS |
| worldgen grid reachability | **mine** — 4-connected BFS over the `layout` literal |

**No adjudicated party's decision procedure appears anywhere in that column.**
Not `fd_adapter.search`, not `deadlock_carver.carve`, not
`mutex.reachable_pairs`, not `lp_potential.solve_certificate`, not
`ic3_pdr.check`, not `probe_frontier`, not `recheck.verify`, not
`worldgen`'s own solver.

`fuzzlab/oracles/search.py` was read and is genuinely engine-independent
(`optimal_plan_length` / `distance_to_any` return `(None, exhausted)` so a budget
blowout cannot be read as "unreachable"). In the end it was **not used**: its
`optimal_plan_length` wants an already-grounded action dict, and grounding is the
step most at risk of circularity, so I grounded myself and kept the BFS in the
same file. Stated plainly because the ticket named that oracle.

---

## 3 · Shared dependencies — complete, not abridged

Independence here is partial and the residue is real.

1. **`engine-rig/fixtures/data/sokoban_*.pddl`** — the world description itself,
   emitted by `engine-rig/fixtures/sokoban.py`. If the generator misrendered a
   board, the engines and I inherit the same wrong world and agree wrongly. Not
   eliminable from inside the repo. *Partially mitigated*: the C4 Lean encoding
   was transcribed on the theory-compiler track through a different path
   (`spike_encoding.py`; one cell per moving thing, `clear` derived rather than
   stored) and lands on the same numbers — §7.2.
2. **`engine-rig/artifacts/candidates.jsonl`, `engine-rig/recheck/cases/*.json`,
   `engine-rig/interop/certificates/*.json`, `worldgen/out/worlds/*/spec.json`**
   — the claims themselves, read as the defendant's statement. A claim missing
   from these files is a claim I did not adjudicate.
3. **Claim harvest only**: I imported `engines.fd_adapter.pddl.parse_{domain,problem}`,
   `engines.deadlock_carver.carve`, `engines.lp_potential`, `engines.ic3_pdr`,
   `fixtures.peg4.generate` to *enumerate what is claimed*. None ran on an
   adjudicating path. If `carve` under-reports its own theorems I would not
   notice — I would simply have judged fewer claims.
4. **`engine-rig/recheck/cases/a2-{world,holed}.rules.json`** — `recheck`'s
   transcription of `cold-start-a2`'s manual and world. A mistranscription there
   is invisible to me. Only the data was used, never `recheck`'s evaluator.
5. **`a0-spike/artifacts/A0.lean`** — for U8 I re-executed the `step` and `I`
   written in that file. A `theory.dsl` → `A0.lean` transcription error would not
   be caught; I verified the theorem is true *of the encoding*, the same scope
   the Lean proof has.
6. **`engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md`** — the measured Fast
   Downward exit codes in §4 are read from that manifest. `.toolchain/` is
   gitignored and no FD build is present here, so I could not re-run the planner.
   The finding does not depend on it (§4).
7. **`worldgen`'s door/switch semantics** were not modelled; §6c uses a
   relaxation instead, which is why that gap does not propagate.
8. Python 3.13 standard library only (`re`, `collections`, `itertools`, `json`).
   No numpy, no scipy, no LP solver — certificates were never re-solved, only
   re-checked against enumeration.

---

## 4 · The contradiction

**Two files disagree about which Fast Downward exit code means "proved
unsolvable", and they disagree by exactly one.**

`engine-rig/engines/fd_adapter/backends.py:70-74`, whose own comment says the
values were "read off `driver/returncodes.py` in the build this rig installs --
not from memory, which had them one apart":

```
FD_TRANSLATE_UNSOLVABLE = 10
FD_SEARCH_UNSOLVABLE = 11
FD_SEARCH_UNSOLVED_INCOMPLETE = 12
```

`cold-start-a0/certify/fd_unsat.py:26-36` sets `FD_UNSOLVABLE_EXIT = 12`, with
the docstring `"12 SEARCH_UNSOLVABLE — proved, not merely unfound — 13
SEARCH_UNSOLVED_INCOMPLETE, which is not a proof and is deliberately not treated
as UNSAT here."` The same wording is in `cold-start-a0/DECISIONS.md` D-A0-020 and
`cold-start-a0/BLOCKER_FAST_DOWNWARD.md:105-125`.

The tie-break is measured, on a real build, in this repo.
`engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md:229-241` (FD 24.06+, rev
`7120aa0`) records `astar(lmcut())` and `--alias lama-first` both exiting **12**
on an unsolvable instance, states that 12 is `SEARCH_UNSOLVED_INCOMPLETE` and not
11, and says a caller "should treat 11 and 12 together as 'no plan found' and not
read 12 as a hard proof." `engine-rig`'s naming is right; `cold-start-a0`'s is
one off.

**Why it matters, independent of who has the names right.** Compare the two
predicates as written:

* `backends.proves_unsolvable(tier, returncode, log)` accepts exit 12 only when
  the rung is `fd-optimal` **and** the log contains FD's phrase `Completely
  explored state space`. It refuses exit 12 on the satisficing rung outright,
  because LAMA searches under a cost bound.
* `fd_unsat.is_unsat(exc)` accepts exit 12 from a message string alone. It sees
  neither the rung nor the log.

So on the FD path `cold-start-a0` will file "the planner **proved** there is no
plan" — the branch that under its constraint 6 triggers the certificate
obligation and all of M5 — on a run where FD merely stopped. That is precisely
the "裸 UNSAT" laundering `fd_unsat.py`'s own docstring says it exists to
prevent, and the error runs in the unsafe direction.

**Why no test caught it.** `cold-start-a0/tests/test_followups.py:241-251`
asserts `is_unsat(… exit 12 …)` is true and `is_unsat(… exit 13 …)` is false —
the test encodes the same wrong mapping as the module, so the suite is green.
`engine-rig`'s tests exercise `proves_unsolvable` against the right mapping and
are also green. Each track is internally consistent. **Only reading them against
each other exposes it.**

**Blast radius — latent, not currently firing.** `is_unsat` is live at
`cold-start-a0/pipeline/plan_stage.py:64` and
`cold-start-a0/certify/fd_conformance.py:176`, but `cold-start-a0/DECISIONS.md`
D-A0-021 records that `run_all.py` and `prime.run_prime` call
`solve(..., prefer="stub")` unconditionally, so the committed artefacts ride on
the BFS stub and the FD branch is not taken. No published artefact is known to be
wrong today; the defect is a trap armed for whoever first routes that pipeline
through a real planner. Note also that `fd_unsat`'s exit-13 guard is dead code —
FD does not use 13 for this.

Corroborating detail: `cold-start-a0/artifacts/fd_real.json` and
`BLOCKER_FAST_DOWNWARD.md:16` record `a0-no-button` as UNSAT under FD with the
log line *"Completely explored state space — no solution!"*. That verdict is
**correct** — U9 confirms it below — but it is correct because the log said so,
which is the condition `is_unsat` does not check. The right answer was reached by
the wrong predicate.

Per the ticket this is written up, not fixed. Suggested minimal repair, for the
`cold-start-a0` track to take or leave: set `FD_UNSOLVABLE_EXIT = 11`, and treat
12 as a proof only under the two side conditions `proves_unsolvable` imposes
(optimal rung **and** `Completely explored state space` in the log) — which means
`is_unsat` needs the rung and the log, not just the exception string.

---

## 5 · Method and scale

Exhaustive forward BFS from the initial state, then a backward closure from the
goal states over the reachable subgraph. A state is **alive** if some goal state
is reachable from it, **dead** otherwise. Every run exhausted its space — no
budget was hit, so every "unreachable" here is a proof and not a timeout.

| Instance | Ground actions | Reachable states | Edges | Goal states reachable | Alive | Dead | Solvable | Optimal plan |
|---|---|---|---|---|---|---|---|---|
| `sokoban-open4` | 112 | 3352 | 9552 | 14 | 448 | 2904 | yes | **6** |
| `sokoban-open4far` | 112 | 3352 | 9552 | 14 | 448 | 2904 | yes | **11** |
| `sokoban-ring` | 40 | 44 | 84 | 11 | 22 | 22 | yes | **1** |
| `sokoban-ringstuck` | 40 | 44 | 84 | **0** | **0** | 44 | **no** | — |
| `a2-world` (rule set) | 4 actions over a 148-state product | 55 | — | yes | — | — | **yes** | **18** |
| `a2-holed` (rule set) | same | 41 | — | **no** | — | — | **no** | — |
| A0 spike `mismatch`, push2 | 4 dirs | 315 | — | **no** | — | — | **no** | — |
| A0 spike `mismatch`, push1 variant | 4 dirs | 2070 | — | **yes** | — | — | **yes** | — |
| `no_button` manual | 148 step entries | 23 cells | — | **no** | — | — | **no** | — |

peg-4 and peg-5, from my own re-implementation of the jump rule:

| Start | Reachable set | Goal | Distance | Solvable |
|---|---|---|---|---|
| `1110` | `{1110, 1001}` | `0100` | — | no |
| `0111` | `{0111, 1001}` | `0100` | — | no |
| `1011` | `{1011, 1100, 0010}` | `0100` | — | no |
| `1101` | `{1101, 0011, 0100}` | `0100` | **2** | yes |
| `11011` | `{11011, 00111, 01001, 10010, 11100}` | `01000` / `00010` | — | no to both |

---

## 6 · Verdicts

### 6a · Deadlock claims — 36 of 36 CONFIRMED, 0 refuted

For each pattern: enumerate every **reachable** state containing it, and check
none is alive. This is the payload's own wording — `"claim": "every reachable
state containing at(b1,c11) is dead"` — so it is the claim being judged, not a
weaker one.

| Instance | Theorems | Refuted | Vacuous over reachable | Reachable states covered | Of the instance's dead states |
|---|---|---|---|---|---|
| `sokoban-open4` | 16 | **0** | 0 | 1624 | 1624 / 2904 = **55.9 %** |
| `sokoban-open4far` | 16 | **0** | 0 | 1624 | 1624 / 2904 = **55.9 %** |
| `sokoban-ring` | 2 | **0** | 0 | 22 | 22 / 22 = **100 %** |
| `sokoban-ringstuck` | 2 | **0** | 0 | 22 | 22 / 44 = **50 %** |

Per-pattern match counts (all with 0 alive): each single-atom corner on
`open4far` matches **210** reachable states; each two-atom wall pair matches
**14**; each corner on `ringstuck` matches **11**.

The 18 patterns carrying a `.cert.json` were adjudicated a second time from the
certificate JSON rather than from `carve()`, decoding
`["=", ["var","b1"], ["lit","1,1"]]` → `at(b1,c11)`. Same 18 verdicts. **The
recheck encoding and the PDDL encoding agree.**

Negative controls, independently re-judged — they must **not** be dead:

| Control pattern | Reachable matches | Of those, alive | My verdict |
|---|---|---|---|
| `at(b1,c22)` | 210 | **70** | not dead — control correctly rejected |
| `at(b1,c22) & at(b2,c23)` | 14 | **14** | not dead — control correctly rejected |

Two cases worth naming: `at(b1,c42) & at(b2,c43)` is dead on `open4far` even
though **c42 is b1's own goal cell** — b1 is home and the level is still lost.
`at(b1,c12) & at(b2,c13)` is dead on `open4` where **c12 is b1's goal**. Neither
is a corner; both need the h² mutex facts. Both confirmed dead.

### 6b · Unsolvability claims U1–U10

| Claim | Reachability says | Verdict |
|---|---|---|
| U1 `1110` (LP) | reachable `{1110,1001}`, goal `0100` absent | **CONFIRMED** |
| U2 `1011` (LP) | reachable `{1011,1100,0010}`, goal absent | **CONFIRMED** |
| U3 `0111` (IC3) | reachable `{0111,1001}`, goal absent | **CONFIRMED** |
| U4 `ringstuck` (fd_adapter) | 44 reachable states, **0** goal states, exhausted | **CONFIRMED** |
| U5 peg-5 `11011` ↛ `01000` | 5 reachable states, `01000` absent | **CONFIRMED** |
| U6 peg-5 `11011` ↛ `00010` | same 5 states, `00010` absent | **CONFIRMED** |
| U7 `p_side` unreachable | on `sokoban-ring` the box reaches exactly `{c11,c12,c13,c14}`; `c31` absent | **CONFIRMED** |
| U8 A0 `mismatch` unsolvable | 315 reachable states; box reaches only `{(1,1),(1,3),(3,1),(3,3),(3,5),(5,1),(5,3)}`; `(3,2)` absent; every reachable state satisfies `I` | **CONFIRMED** |
| U9 `no_button` manual unsolvable | 23 reachable cells from `c24`; goal `c11` absent — and 23 matches the comment's "23 cells the Cart was ever observed on" | **CONFIRMED of the manual** |
| U10 `right_room_locked` | see below | **CONFIRMED of the holed manual, REFUTED of the world — as already recorded** |

The IC3 invariant on `0111` was re-checked from the CNF alone against my own
successor relation over all 16 states: 8 satisfying states, holds at `0111`,
closed under every jump from every satisfying state (not merely reachable ones),
excludes the goal, contains the reachable set. All four hold.

`lp_potential` and `ic3_pdr` **never disagree** on peg-4. On `0111` the LP is
silent and IC3 speaks; that is incompleteness meeting completeness, not a
conflict (§1c).

**U8's documented flip, reproduced.** `a0-spike/artifacts/adaptation.json:48`
records `mismatch_still_unsolvable: false` for the `push1` world variant, with
`invalidated_theorems: ["unsolvable_mismatch"]`. Re-running my BFS with the box
sliding one cell instead of two: the space grows from 315 to **2070** states, the
box reaches **both** parities, and `(3,2)` **is** reached. The parity invariant
genuinely stops holding — the theorem was true of the world it was proved about
and false of the variant, exactly as recorded. Adjudicated as a correct
retraction, not as a defect.

**U10 in detail.** Running my own rule-set evaluator over both a2 manuals:

* `a2-holed`: 41 of 148 states reachable, goal **not** reachable. The
  certificate's three conditions all hold — `inv_init` ✓, `inv_closed` ✓,
  `goal_break` ✓. The Lean theorem is **true of this manual**.
* `a2-world`: 55 states reachable, goal reachable at distance **exactly 18** —
  matching the 18-action refutation episode in
  `cold-start-a2/artifacts/refutation.json` to the move. `inv_closed` **fails**,
  and my BFS names the witness without being told where to look:

  ```
  {button: 7, cart: "6,4", door: "no"} --down--> {button: 7, cart: "7,6", door: "no"}
  ```

  That edge is the `teleport_down` rule, which `a2-world.rules.json`'s own
  provenance block names as the single rule the holed manual is missing. So the
  contradiction between "Lean proves `unsolvable`, axiom-free" and "an 18-action
  episode wins" is real, is **already documented** as `refuted: true`, and its
  cause is now independently localised to one transition by a method that never
  read the refutation.

### 6c · The four worldgen worlds — U11–U14, CONFIRMED by relaxation

The door/switch/latch/toggle semantics are `worldgen`'s own and I did not model
them; modelling them from the spec would have risked reproducing whatever the
generator believes. Instead: **treat every door that any switch could ever drive
as permanently OPEN.** That is a relaxation of the real world — it can only add
reachable states — so if the goal is unreachable in the relaxation it is
unreachable in the world. This needs nothing but the `layout` literal, the
`entities` list, and 4-connected BFS.

| World | Doors on an undriven net | Doors a switch could drive | Reachable cells (relaxed) | Goal | Verdict |
|---|---|---|---|---|---|
| `t2-unsolvable-nodoor` | `(3,4)`, `(4,2)` | — | **11** | `(4,5)` unreachable | **CONFIRMED** |
| `v-707a64ad` | `(3,4)` on net **b** | `(4,2)` on net a | 12 | `(4,5)` unreachable | **CONFIRMED** |
| `v-d2c2b1b9` | `(3,4)` on net **b** | `(4,2)` on net a | 12 | `(4,5)` unreachable | **CONFIRMED** |
| `v-ce732813` | — (no entities; `forbidden_action: DOWN`) | — | **3** | `(5,7)` unreachable | **CONFIRMED** |

The structural reason the two `v-*` worlds are unsolvable is now explicit and was
not stated in their certificates: door `(3,4)` sits on net **b**, the only switch
drives net **a**, so nothing in the world can ever open the one cell joining the
start region to the goal region. The switch is a red herring.

Two counts match the certificates exactly — `t2-unsolvable-nodoor`'s 11
(`agent_cells: 11`, "the reachable set has 11 states") and `v-ce732813`'s 3. For
the two `v-*` worlds the certificate counts 21 *states* (cell × net) where I
count 12 *cells*; these are different units and I did not reproduce the 21. Not a
discrepancy, and not a match either — stated rather than glossed.

---

## 7 · What only the crossing exposes

1. **The FD exit-code contradiction (§4).** Neither track can see it alone; both
   suites are green; the disagreement is a single integer in two files that never
   import each other.
2. **Three independent encodings of `sokoban-open4far` agree numerically.** The
   grounded STRIPS task (with `clear` atoms), the C4 Lean structure (one cell per
   moving thing, `clear` derived), and my own grounder:

   | Quantity | C4 `verify/EVIDENCE.json` | My BFS |
   |---|---|---|
   | ground actions | 112 | 112 |
   | reachable states | 3352 | 3352 |
   | well-formed states | 3360 (`encodable_states`) | 3360 |
   | reachable states covered by `at(b1,c11)` | 210 | 210 |
   | reachable states covered by `at(b1,c12)&at(b2,c13)` | 14 | 14 |
   | plan length | 11 | 11 |

   The 8-state gap (3360 − 3352) is the player boxed into a corner, e.g.
   `player=c11, b1=c12, b2=c21` — well-formed but never reachable. Each track's
   tests only check its own encoding; nothing in the repo compared them.
3. **The C4 Lean `level_is_winnable` witness is exactly optimal.** Its explicit
   `ReachFrom` chain is 11 steps; my BFS optimum is 11. A hand-written witness
   that happened to be longer would have gone unnoticed, since Lean needs only
   *some* path.
4. **`deadlock_carver`'s node account is reproduced from outside.** Its README
   reports `ringstuck` pruning 44 expansions to 22. My reachability graph
   independently gives 44 reachable states and exactly 22 covered by the two
   theorems. The account is not self-reported bookkeeping.
5. **`recheck` never evaluates the `ring` or `open4` goals.** Both ship a
   `.rules.json` but no `.cert.json`. The *patterns* are shared with
   `ringstuck`/`open4far`, so the gap is smaller than the 36-vs-18 count suggests
   — but `goal_break` is goal-dependent, and `ring`'s goal (`b1@c13`) differs
   from `ringstuck`'s (`b1@c31`). The obligation "`at(b1,c11)` excludes `ring`'s
   goal" is checked by no rechecker in the repo. §6a checks it: it holds.
6. **`fd_adapter`'s committed unsolvability verdicts ride on the BFS stub —
   structurally, not incidentally.** `solve_parsed(domain, problem)` with no
   `domain_path`/`problem_path` sets `on_disk=False`, and `choose_tier` rule 3
   forces `stub-bfs`; likewise any call with `prune=`. Every call in
   `fuzzlab/props/fd_adapter.py` is of that shape, and `deadlock_carver`'s
   pruning report passes `prune=`. The ticket's caveat is confirmed — **and its
   consequence for U4 is benign**: the stub is a complete BFS over a 44-state
   space, which my own exhaustion reproduces exactly. U4's "no plan" is a genuine
   exhaustion proof, not a planner shrug.
7. **`probe_frontier` and `fd_adapter` agree for the same underlying reason, and
   neither knows it.** U7 (`p_side` unreachable, on `ring`) and U4 (`ringstuck`
   has no plan) are the same geometric fact — the box never leaves row 1 of the
   ring — reached by two engines through two different interfaces on two
   different instances. My single BFS produces both from one reachable set:
   box cells `{c11,c12,c13,c14}` on *both* problems.
8. **The one certificate that is FALSE of the world (U10) and the one theorem
   that got RETRACTED (U8/push1) are both correctly labelled.** A crosscheck that
   only looked for false positives would have flagged them; reading each against
   its own recorded status shows the repo already knows. Both are negative
   controls in effect, and both behaved.

---

## 8 · Where this could not reach a verdict

Stated rather than papered over.

* **No Fast Downward on this machine.** `.toolchain/` is gitignored by design, so
  §4's exit codes are read from `runs/p13-fd-real/TOOLCHAIN_MANIFEST.md` rather
  than re-measured. The *contradiction* between the two files is verifiable
  without any planner; only the question of which naming matches upstream leans
  on that manifest.
* **The world descriptions are a common ancestor.** Shared dependency 1. Nothing
  inside the repo can rule out a systematic error in
  `engine-rig/fixtures/sokoban.py`; §7.2's three-encoding agreement is evidence
  against it, not a proof.
* **U8 and U9 are judged against their own Lean encodings.** I re-executed the
  `step` written in the Lean file. A DSL→Lean transcription error is out of reach
  — that is a compiler-conformance question and belongs to whatever checks
  `theory.dsl` against `theory.lean`, not here.
* **U9 is a claim about a manual, not about the world.** `no_button` is a variant
  manual by construction; I confirmed the theorem is true of it and did not touch
  whether the world has a button.
* **`deadlock_carver` completeness is measured, not adjudicated.** 44.1 % of
  `open4far`'s dead reachable states, and half of `ringstuck`'s, are dead for
  reasons no 2-atom pattern can state. That is the documented ceiling of h²
  (`mutex.py`: "Raising the cap needs h^m, not a bigger loop"), not a defect. No
  claim was made about them, so none was refuted.
* **Not adjudicated at all, and why:**
  * `exam/artifacts/truth/p15-verdict-a2.truth.json` — **9** unsolvable exam
    items with certificates. The 5 `small_unsolvable` ones carry
    `exhaustive_feasible: true` with 7–31 enumerated states and *are* brute-
    forceable; the 4 `large_unsolvable` ones bound their spaces at 2^60–2^120 and
    are not. Out of budget for this pass; the small five are the obvious next
    target for anyone continuing this lane.
  * `proxy/variants/v00{1,2,3}.json` — 3 unsolvable ARC-variant claims. The
    underlying board is not in-repo; adjudicating them needs the live game, and
    this lane does not touch the network.
  * `cold-start-a3`'s `a3-l2-oneway` negative control — asserted unsolvable by
    that track's own `solve()`; re-deriving A3's portal semantics was out of
    budget.
  * `ablation-arm/artifacts/{a0-no-button,a2-holed}/run_report.json` — replicas of
    U9 and U10; the originals are adjudicated above, the replicas were not
    separately re-derived.
  * `worldgen`'s retracted `t1-tokens-lock`-with-`LEFT`-forbidden claim
    (`worldgen/RUN_STATE.md:396`) — declared unsolvable, is not, and never
    entered the corpus. No live claim to judge.
* **`zero_space`, `cegis_miner`, `mdl_segmenter`** emit no deadlock or
  unsolvability claim. The one `zero_space` product that became one is U10, via
  `cold-start-a2`'s adjudication, and is judged above.
* **`engine-rig/recheck/` was not re-run.** Its verdicts were used only as a
  source of machine-readable claims. Whether `recheck` itself is correct is E5's
  question, not this one.
* **The speed-up half of the deadlock story was not re-measured.**
  `engine-rig/STATUS.md:130-141` already records that a proved deadlock is a
  substitute for a heuristic and not an addition to one (`lmcut` 47→47, `ipdb`
  18→18). That is E7's audit; this lane judged truth, not dividend.

---

*Adjudicating code: `indep_ground.py`, `adjudicate.py`, `adj2.py`, `adj_a2.py`
and three inline drivers, written this session in the session scratchpad, not
committed. Every number in §5 and §6 is reproducible from the four `.pddl` files,
the `recheck/cases/*.json` rule sets, `interop/certificates/pagoda_5_*.json`, the
four `worldgen/out/worlds/*/spec.json`, and the Lean files named in §1.*
