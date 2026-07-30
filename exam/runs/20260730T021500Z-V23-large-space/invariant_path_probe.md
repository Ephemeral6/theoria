# Can any shipped engine walk the class (ii) path?

`exam/runs/20260730T021500Z-V23-large-space/invariant_path_probe.md`
Scripts: `probe_lp_interface.py`, `probe_lp_soundness.py`, `probe_answer_key.py`
Data: `probe_lp_interface.json`, `probe_lp_soundness.json`, `probe_answer_key.json`

The class (ii) items of `exam/papers/verdict.py` are advertised as *"enumeration
out of reach; only invariant reasoning answers"* (`verdict.py:1350`, the paper's
own `notes.classes` map). This run asks whether the repo ships an engine that can
actually produce a machine-checkable unsolvability certificate on such a level,
and what the shipped answer key does instead.

Everything below is split into **MEASURED** (a number this run produced on this
machine) and **DERIVED** (extrapolation or reading of code). Nothing outside this
directory was modified; `engine-rig` and `worldgen` were read only.

**Working-tree note.** `exam/papers/verdict.py` was edited by a concurrent track
*during* this run: D-EX-028 landed, renaming `state_space.exhaustive_feasible` to
`naive_enumeration_feasible` and adding `enumeration_attempted` /
`enumeration_refused_because` (`verdict.py:805-832`). All line cites below are
against the **post-D-EX-028 working tree** (`exam/papers/verdict.py` modified,
uncommitted; last commit touching it `a95f7b32`). D-EX-028's own comment states
*"every shipped class (ii) item is settled by an exhaustive computation over at
most 600 nodes in at most 5 ms"* — §5.4 below measures exactly that, independently,
and confirms it (600 nodes max, 3.1 ms max). It does **not** change any finding
here about the engines.

---

## 1. LP_POTENTIAL INTERFACE

### 1.1 The signature

`engine-rig/engines/lp_potential/potential.py:270`

```python
def solve(graph: Dict[str, object], initial: str,
          goal_states: Optional[Sequence[str]] = None,
          margin: int = 1, bound: int = 10,
          solver_options: Optional[Dict[str, object]] = None) -> LpOutcome:
```

`initial` and every element of `goal_states` are **bitstrings over board
positions** — `Certificate.potential` (`potential.py:135-139`) sums `w[i]` over
indices `i` where `state[i] == "1"`.

### 1.2 What it reads off `graph` — MEASURED (probe A)

Deleting one key at a time from a fully built `interop.peg1d.build_graph(6, ...)`
dict and re-calling `solve`:

| key | removed → |
|---|---|
| `edges` | **KeyError — REQUIRED** |
| `n_pos` | **KeyError — REQUIRED** |
| `goal_states` | ok (only read when the `goal_states` argument is `None`, `potential.py:296`) |
| `states`, `distance_to_goal`, `reachable`, `solvable`, `goal`, `initial_configs`, `move_instances` | ok — never touched by `solve` |

So the prior read's claim — *"it reads `graph["states"]` and `graph["edges"]`"* —
is **half right and the wrong half matters**. `solve` never touches
`graph["states"]`. It touches `graph["edges"]` (`potential.py:258`, inside
`moves_from_graph`) and `graph["n_pos"]` (`potential.py:298`).

`graph["states"]` *is* read by the neighbouring engine `ic3_pdr`
(`engines/ic3_pdr/system.py:117`) and by `admissibility_report`
(`potential.py:614`, via `distance_to_goal`), but not by the certificate path.

### 1.3 Granularity — MEASURED (probe A) + code

Three different granularities are in play and they are not the same:

| object | granularity | count at `n_pos=6` (MEASURED) |
|---|---|---|
| `graph["edges"]` — the required input | **per (state, move) instance** | 64 |
| `moves_from_graph` output — what the LP sees | **per distinct `(src, over, dst)` geometry**, de-duplicated at `potential.py:255-263` | 8 |
| LP variables | **per board cell**, `2*n_pos` (`w` plus L1 slacks `t`) | 12 |
| LP rows | 1 per geometry + 1 per goal state + `2*n_pos` box rows | 8 + 1 + 12 = 21 |

**The LP itself is per-cell. The required input is per-edge.** That gap is the
whole finding: the engine demands an object of size *O(states × moves)* in order
to extract an object of size *O(geometries)*.

### 1.4 Is the materialisation *necessary*? — MEASURED (probe C)

No, not for peg solitaire. `moves_from_graph` de-duplicates, so a graph carrying
exactly one edge per geometry produces a byte-identical LP. Handing `solve` such
a "geometry-only" graph:

| `n_pos` | geometries | status | seconds (MEASURED) |
|---|---|---|---|
| 6 | 8 | `no_linear_pagoda` | 0.001 |
| 50 | 96 | `no_linear_pagoda` | 0.003 |
| 100 | 196 | `no_linear_pagoda` | 0.009 |
| 250 | 496 | `no_linear_pagoda` | 0.038 |
| 500 | 996 | `no_linear_pagoda` | 0.159 |
| 1000 | 1996 | `no_linear_pagoda` | 0.610 |

Cross-check at `n_pos=8`: fully materialised graph → `no_linear_pagoda`;
geometry-only graph → `no_linear_pagoda`. **Agree.**

So the "requires a materialised state graph" claim is **true of the shipped
interface and false of the shipped mathematics**. `solve` will happily run on a
2^1000-state peg board in 0.6 s *if the caller already knows the move geometries*
— which for peg solitaire `interop.peg1d.move_instances(n)` computes without any
enumeration at all. There is no shipped call site that does this; every caller in
the rig passes a `build_graph` dict.

### 1.5 The blocker that is *not* removable — MEASURED (probe D)

`solve` builds one LP row per move as (`potential.py:304-309`):

```python
row[move.dst] += 1.0
row[move.src] -= 1.0
row[move.over] -= 1.0
```

and `Move.delta` (`potential.py:121-123`) is `w[dst] - w[src] - w[over]`.

MEASURED, exhaustively over all 5³ = 125 role assignments at `n_pos=5`: the
coefficient vector of an `lp_potential` move **always sums to −1**, including
under index collisions (`src == over`, `over == dst`, …). That is peg solitaire's
signature: every jump removes exactly one peg.

An A2 comb transition changes the occupancy vector with coefficient sum

* **0** for a plain cart move (cart leaves `c`, enters `c'`),
* **+1** for a move that also latches a switch,
* **0** for a blocked move.

−1 is none of these. **No assignment of `(src, over, dst)` expresses an A2
transition**, at any board size, with any weights. The obstruction is the move
algebra, not the graph size.

---

## 2. SMALL-K RESULT — MEASURED (probes E and `probe_lp_soundness.py`)

A shipped-shape comb level (`comb_open` geometry: corridor, `s` alcove above and
below every corridor cell, `require_all_switches`), encoded as the most faithful
bitstring available (bits `0..C-1` = "cart is here", bits `C..C+S-1` = "switch j
latched"), fully materialised, `LEFT` forbidden, handed to `lp.solve`:

| corridor | `n_pos` | reachable states | edges | build s | solve s | `solve()` status |
|---|---|---|---|---|---|---|
| 2 | 10 | 40 | 68 | 0.000 | 0.035 | `certified` |
| 3 | 15 | 168 | 292 | 0.001 | 0.002 | `certified` |
| 4 | 20 | 680 | 1 188 | 0.003 | 0.003 | `certified` |
| 5 | 25 | 2 728 | 4 772 | 0.013 | 0.009 | `certified` |
| 6 | 30 | 10 920 | 19 108 | 0.088 | 0.034 | `certified` |
| 7 | 35 | 43 688 | 76 452 | 0.356 | 0.136 | `certified` |
| 8 | 40 | 174 760 | 305 828 | 1.762 | 0.610 | `certified` |
| 9 | 45 | 699 048 | 1 223 332 | 9.036 | 2.696 | `certified` |
| 10 | 50 | 2 796 200 | 4 893 348 | 37.483 | 11.536 | `certified` |

**It certifies. The certificate is false.** At corridor 4:

* MEASURED: the goal state (cart on `G`, all 8 switches latched) **is in the
  forward closure from the start** — the level is **SOLVABLE**.
* MEASURED: `solve()` returns `status="certified"`, weights
  `[0,…,0,1,0,…,0]`, `claim: "goal unreachable from 00001000000000000000"`.
* MEASURED: `certificate.holds = True`; `conditions = {inv_init: True,
  inv_closed: True, goal_break: True}`.
* MEASURED: `premises_against_graph(...).sound_over_graph = True`,
  `move_list_complete = True`, `moves_raising_potential = 0`.
* MEASURED: `heuristic_from(cert).entitlement(None)["admissible"] = True`.
* MEASURED: on **1 188 of 1 188** edges, the delta `lp_potential` models
  (`w[dst]-w[src]-w[over]`) differs from the true potential delta
  (`Φ(dst_state) − Φ(src_state)`).
* MEASURED: on **10 of 1 188** edges the *real* potential rises;
  `Φ(start) = 0`, `Φ(goal) = 1`.

Every one of the engine's four self-checks passes because all four are computed
from the same `Move` list, i.e. from the same wrong algebra. `solve` has
`edge["src_state"]` and `edge["dst_state"]` in hand at `potential.py:258` and
never compares them to `edge["positions"]`.

**Reading, stated carefully.** This is *misuse* — the graph is not a peg1d graph
and `lp_potential`'s docstrings say it is about peg jumps throughout. The finding
is not "lp_potential is unsound on its own domain". It is:

> There is no adapter from an A2/worldgen level to `lp_potential`'s input
> anywhere in the repo (grep for `peg1d` / `build_graph` outside `engine-rig`
> returns only `fuzzlab/worlds/jumpgraph.py` and this run's scratch script), and
> the naive adapter a reader would write does not fail loudly — it mints a
> full-marks certificate for a solvable level.

That is the practical content of "sound but incomplete": the soundness is
relative to an input contract the engine does not check and no shipped code
satisfies for this world.

**Interpretation of `certified` vs `no_linear_pagoda`.** Note that on its *own*
domain (probe C) `lp_potential` returns `no_linear_pagoda` for full-board peg
solitaire at every size tried — i.e. even where it can run, on the natural
"unsolvable" family it declines. That is the documented incompleteness
(CLAUDE.md; `potential.py:283-289`), not a defect.

---

## 3. SHIPPED-K RESULT

**DERIVED** (from §2's measured curve plus the interface). No large run was
attempted; nothing here exhausted RAM.

The shipped class (ii) levels are `comb_room("gantry", 60, None)` and
`comb_room("lattice", 60, 2)` (120 switches), `comb_open("spindle", 200, 1, 200)`
(400 switches, budget 150), `comb_open("orchard", 60, 2, 1)` (120 switches).

* MEASURED growth in §2: reachable states multiply by exactly **4.0** per added
  corridor cell (2 796 200 / 699 048 = 4.000), edges ≈ 1.75 × states.
* DERIVED at corridor 60: `2.796e6 × 4^50 ≈ 3.5e36` states, `≈ 6e36` edges.
  The shipped truth records agree in order of magnitude — MEASURED from the
  artifact: `lower_bound = 1.329e36` (2^120) for gantry/lattice.
* DERIVED build time at corridor 60, taking 37.5 s at corridor 10 and the
  measured ×4: `37.5 × 4^50 ≈ 4.8e31` seconds ≈ **1.5e24 years**.
* DERIVED memory: at ≥1 byte per edge (the actual Python dict-of-strings
  encoding is ~300 bytes), ≥ 6e36 bytes.

So at shipped `k` the honest answer to *"does it raise, hang, or OOM"* is: **the
input cannot be constructed**. `solve` would never be entered. There is no
timeout or budget in `moves_from_graph` — it is a bare `for edge in
graph["edges"]` (`potential.py:258`) — so the failure mode is the caller's
enumerator dying, not an engine-side refusal.

**And the geometry-only shortcut of §1.4 does not rescue it**, for two
independent reasons:

1. DERIVED: even given the geometries for free, §1.5 shows no A2 transition is
   representable as an `lp_potential` `Move`.
2. DERIVED: "distinct move geometry" is well defined only because peg
   solitaire's transition relation is position-uniform. An A2 latching move's
   effect depends on the latch mask, so there is no finite geometry set to hand
   over.

---

## 4. ENGINE SURVEY

Question per engine: *what input does it need, and does that input scale to a
class (ii) level?*

| engine | entry | input it needs | scales to 2^120? | can it emit an unsolvability certificate? |
|---|---|---|---|---|
| `mdl_segmenter` | `segment_trajectory(frames, …)` (`segmenter.py:243`) | a sequence of raster frames | yes (linear in frames) | **no** — perception; emits segmentations/events, never a verdict |
| `cegis_miner` | `mine(transitions, …)` (`miner.py:302`) | observed `Transition` records | yes (linear in samples) | **no** — synthesises guarded rules from a sample; `status` is always `"candidate"` per `CONTRACTS/candidates_schema.md` |
| `zero_space` | `analyse(states, colors)` (`zerospace.py:278`) | a **list of states** (a trajectory) | only as far as you can list states | **no** — GF(2) laws that hold *on the sample*; `verify` (`zerospace.py:326`) re-checks against the same states, so there is no closure proof over the transition relation |
| `lp_potential` | `solve(graph, …)` (`potential.py:270`) | `graph["edges"]` (per state-move instance) + `n_pos`; bitstring states; **peg-jump move algebra** | **no** (§3) | in principle yes, in practice no: no A2 adapter, and §1.5 shows none can exist |
| `fd_adapter` | `search(domain, problem, …)` (`search.py:139`), `solve_parsed` | grounded PDDL `Domain` + `Problem` | **no** — `search` is BFS with `max_expansions=500000` (`search.py:140`) and *raises* `RuntimeError` past it (`search.py:165-166`) | FD *can* prove unsolvability (`backends.proves_unsolvable`, `backends.py:239`, exit 10/11/12-on-optimal). MEASURED on this machine: `find_fast_downward() → None`, no `engine-rig/.toolchain/` → **stub-bfs fallback**, expected per CLAUDE.md, not a defect. Also: **no A2→PDDL compiler exists anywhere in the repo** (grep for `pddl` under `exam/` and `worldgen/`: zero hits) |
| `probe_frontier` | `reach(domain, base, goal_atoms, …)` (`reach.py:118`) | same grounded PDDL, then delegates to `fd_adapter` | **no** — inherits the BFS budget; refuses to say `unreachable` unless the search was exhaustive (`UnprovenUnreachability`, `reach.py:38`) | only via `fd_adapter`; same two blockers |
| *(extra)* `ic3_pdr` | `ic3(system, …)` (`pdr.py:229`); `peg_system(graph, …)` (`system.py:102`) | a **fully enumerated** `System` — its own docstring: *"the states, the labelled transitions, the initial and bad sets are all enumerated up front"* (`system.py:5-9`); reads `graph["states"]` at `system.py:117` | **no** — strictly worse than `lp_potential`, it needs `states` too | yes on enumerable systems (inductive clause invariant); the docstring already names the fix ("a system with more than a few dozen variables wants a real solver behind `states_where`") |
| *(extra)* `deadlock_carver` | `carve(Task.build(domain, problem))` (`carve.py:254`) | grounded PDDL + h² mutexes — **no state enumeration** | the only genuinely symbolic engine in the rig; DERIVED cost ≈ O(atoms² × actions) | **not for these items.** It proves *conditional* theorems `pattern ∧ ¬goal ⇒ dead`, capped at `MAX_PATTERN = 2` atoms (`carve.py:59`). A pattern containing `at(cart, start)` is not closed — the cart can move — so it cannot certify whole-level unsolvability here. Also needs the PDDL compiler that does not exist |

**Answer to question 3: no.** No shipped engine can produce a machine-checkable
unsolvability certificate for a class (ii) level at shipped size. Two engines
(`deadlock_carver`, and `fd_adapter` on the FD rungs) are architecturally capable
of symbolic unsolvability reasoning; both are blocked at the front door by the
absence of any A2/worldgen → PDDL compiler, and `deadlock_carver` is additionally
blocked by its theorem shape.

---

## 5. WHAT THE SHIPPED ANSWER KEY ACTUALLY IS

Read from `exam/artifacts/truth/p15-verdict-a2.truth.json` (the shipped
artifact — `verdict.build()` was **not** re-run, to avoid rewriting
`exam/artifacts/variant_specs/`).

### 5.1 The verdict word is a literal

For all four class (ii) items the string `"unsolvable"` is passed as a positional
argument to `_make_item` at the call site:

* `verdict.py:1064` (ii1 gantry), `:1086` (ii2 lattice), `:1111` (ii3 spindle),
  `:1136` (ii4 orchard).

`_make_item` (`verdict.py:696`) copies it into `truth["claim"]` unchanged. **No
search, no engine, no BFS produces the verdict.** What is machine-checked is the
*reference certificate*, by `_self_check` (`verdict.py:1396`) calling the
rubric's own `check_certificate`.

### 5.2 The certificates, verbatim — MEASURED from the artifact

| item id | variant | board | switches | certificate |
|---|---|---|---|---|
| `vq-721d09813c` | `a2var-ii1-gantry-sealed` | 8×62 | 120 | `{"kind":"invariant","invariant":"cart_region","initial_value":[1,1],"goal_value":[5,1]}` |
| `vq-6150a6eeb7` | `a2var-ii2-lattice-bridge` | 8×62 | 120 | `{"kind":"cut_set","cells":[[4,2]]}` |
| `vq-ee54166153` | `a2var-ii3-spindle-budget` | 5×202 | 400 | `{"kind":"counting","bound":199,"limit":150}` |
| `vq-2986ed8ffc` | `a2var-ii4-orchard-noleft` | 5×62 | 120 | `{"kind":"invariant","invariant":"cart_col","initial_value":2,"goal_value":1}` |

All four: `witness = null`, `witness_source = null`, `search_credible = false`,
`state_space.naive_enumeration_feasible = false`,
`state_space.enumeration_attempted = false`, `state_space.enumerated = null`,
`state_space.truncated = null` (post-D-EX-028 spelling;
`search_credible` is derived from it at `verdict.py:720`).

### 5.3 The quotient — MEASURED, and the prior read is confirmed with one correction

| item | `truth.state_space.lower_bound` | `truth…positional_states` | MEASURED `positional_states` | MEASURED relaxed-graph nodes | undirected edges | components |
|---|---|---|---|---|---|---|
| ii1 gantry | 1.329e36 (2^120) | 180 | **180** | **300** | 475 | **2** |
| ii2 lattice | 1.329e36 (2^120) | 180 | **180** | **301** | 477 | 1 |
| ii3 spindle | 1.153e18 (2^60) | 600 | **600** | **600** | 997 | 1 |
| ii4 orchard | 3.323e35 (2^118) | 177 | **177** | **180** | 297 | 1 |

**Prior read: "the answer key is produced by BFS over a ~180-node positional
quotient (`_region_rep`, ~verdict.py:1330)".**

*Confirmed in scale, corrected in three details:*

1. `_region_rep` is at **`verdict.py:1382`**, not 1330. (`_large_space` is at
   **`verdict.py:795`**, not 767; `subset_lower_bound` at `379` is correct;
   `lp_potential.solve` at `270` is correct.)
2. `_region_rep` does not produce *the answer*; it produces the **`initial_value`
   / `goal_value` fields of ii1's certificate**. It calls the rubric's own
   `components(relaxed_edges(level))` (`verdict.py:1388-1392`) — a DFS/BFS over
   the **300-node** relaxed positional graph, not 180. The 180 is
   `positional_states` (`verdict.py:579`), a *different* BFS over the reachable
   `(cart, button)` pairs, recorded in `state_space` and used by nothing else.
3. Only **two of four** class (ii) certificates involve a search at build time:
   * ii1 — `_region_rep`, DFS/BFS over 300 nodes;
   * ii3 — `relaxed_distance(Level(long_comb), (2,1), (2,200))` at
     `verdict.py:1093`, BFS over 600 nodes, MEASURED result **199**;
   * ii2 — `cells: [[4,2]]` is a hand-written literal at `verdict.py:1087`;
   * ii4 — `initial_value: 2, goal_value: 1` are hand-written literals at
     `verdict.py:1138`. Its checker path (`row_col_deltas`,
     `rubrics_verdict.py:524`) does **no** search at all — MEASURED
     `check_certificate` time **0.0000 s**.

### 5.4 What the checker costs, at shipped size — MEASURED

| item | `relaxed_edges` | `components` | `check_certificate` | verdict |
|---|---|---|---|---|
| ii1 | 0.0006 s | 0.0001 s | **0.0007 s** | `ok=True` |
| ii2 | 0.0007 s | 0.0001 s | **0.0015 s** | `ok=True` |
| ii3 | 0.0014 s | 0.0002 s | **0.0031 s** | `ok=True` |
| ii4 | 0.0003 s | 0.0001 s | **0.0000 s** | `ok=True` |

`subset_lower_bound` (which demonstrates 2^m without searching) runs in
0.0012–0.0047 s and returns `m = 120, 120, 60, 118`.

### 5.5 Is the check sound?

Yes, and this is the part worth defending. `relaxed_edges`
(`rubrics_verdict.py:439`) is an explicitly *undirected over-approximation* whose
node set is a closure under `Level.step`; its docstring states the soundness
direction ("taking the undirected closure only adds edges, so a separation in
this graph is a separation in the real one"). It ignores latch state entirely,
which is exactly why it is *sound for separation* and — as
`_large_space`'s own `quotient_note` (`verdict.py:807-816`) says — **not** a
sound abstraction for the positive direction. `_make_item` (`verdict.py:697-720`)
records the withdrawn D-EX-022 attempt to derive `search_credible` from the
quotient and why it was wrong; the `quotient_note` at `verdict.py:840-856`
carries D-EX-028's amendment that the unsoundness is **one-sided** — an
over-approximation yields false `solvable`, never false `unsolvable`, so a goal
in a different component is a sound separation.

So the exam **does** ship a machine-checkable invariant certificate for class (ii),
verified in ≤ 3.1 ms at 2^120 states. It lives in
`exam/grading/rubrics_verdict.py`, is written for this world only, and has no
connection to `engine-rig` whatsoever.

---

## 6. BOTTOM LINE

The sentence *"enumeration out of reach; only invariant reasoning answers"*
(`verdict.py:1350`) is **true as a statement about the levels and false as a
statement about the framework's engines**, and the paper's own instructions
already imply the second half without saying it. The levels really are past
enumeration — MEASURED 2^120, 2^120, 2^60, 2^118 by a construction that needs no
search — and there really is a cheap machine-checkable invariant path: the
closed-grammar certificates of `rubrics_verdict.check_certificate`, verified in
under 3.1 ms per item over positional graphs of 180–600 nodes. What does *not*
exist is any engine-side ability to *find* such a certificate at that size.
`lp_potential`, the repo's designated invariant engine, is blocked twice over:
its shipped interface demands an edge list of size *O(states × moves)*
(`potential.py:255-263, 298`), which at shipped `k` is ~6e36 entries and simply
cannot be built; and even given the geometries for free, its move algebra fixes
every transition's coefficient sum at −1 (MEASURED over all 125 role assignments),
so no A2 cart move — sum 0, or +1 when it latches — is expressible at all. The
five other shipped engines are worse or orthogonal: `ic3_pdr` needs
`graph["states"]` outright, `fd_adapter`/`probe_frontier`/`deadlock_carver` need
a PDDL compiler for this world that does not exist anywhere in the repo, and
`zero_space`/`cegis_miner`/`mdl_segmenter` mine from samples and emit candidates,
never verdicts. The honest wording is therefore: *the answer key is a
construction, checked by a purpose-built O(cells × actions) rubric; no engine in
`engine-rig` is on this path, and the one that claims the invariant role cannot
be pointed at these levels at all.* The sharpest evidence that this gap needs
documenting rather than assuming: when this run wrote the obvious adapter and
handed a **solvable** comb level to `lp_potential.solve`, it returned
`status="certified"`, `holds=True`, `sound_over_graph=True`, `admissible=True` —
a clean unreachability proof for a reachable goal, with all four of the engine's
self-checks agreeing, because all four read the same wrong move algebra.

**Residual wording gap.** D-EX-028 has already narrowed the *truth record*
(`exhaustive_feasible` → `naive_enumeration_feasible`, `verdict.py:805-812`) so
that the paper no longer claims no exhaustive method is feasible. The paper's
`notes.classes["large_unsolvable"]` still reads *"enumeration out of reach; only
invariant reasoning answers"* (`verdict.py:1350`), which is the sentence this
report is about. On the evidence here it should say something like: *the naive
forward enumeration class (i) is graded on cannot terminate; the answer comes
from a construction and is checked by an O(cells × actions) certificate over a
180–600-node positional relaxation. No engine in `engine-rig` participates.*
