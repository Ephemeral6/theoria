# E15 P2 — the 639, re-issued and reconciled against E11

**Item** E15-solver-status-bit, P2 only (`PREREGISTRATION.md` §"P2 — the 639
re-issued, readable off the artifact"). **Branch** `agent/e15-solver-status-bit`,
**commit at run time** `99204472a77320bfb37dd142141ddc20e63cc3fe`. Python
3.13.13, scipy 1.17.1, numpy 2.4.4. Zero API calls, zero network, nothing
written outside `engine-rig/`.

Authority rule, fixed before the run and honoured below: **where this census and
E11's hand derivation disagree, E11 wins, the census keeps its own number, and
the divergence is named here.** Nothing was tuned to reproduce an expected
integer.

## 1. What was run

```bash
cd engine-rig
python runs/20260729T044500Z-E15-solver-status-bit/census.py      # writes census.jsonl, SUMMARY.json
python runs/20260729T044500Z-E15-solver-status-bit/reconcile.py   # writes reconciliation.jsonl, RECONCILIATION.json
```

Corpus, identical to E11's by construction rather than by description: campaign
seed `0x00005EEDC1E4F002`, `fuzzlab.prng.derive(seed, "jumpgraph", i)` for
`i = 0…2999`, worlds from `fuzzlab.worlds.jumpgraph.generate`. 3000 distinct
seeds, indices contiguous `0…2999`, `n_pos` spanning 4–9.

**Byte-stability.** Two consecutive full runs produce identical files:

| file | sha256 |
|---|---|
| `census.jsonl` | `22f180b5d0d6389c4af95f4a3062ffbd8ea4bcc56cee41027015174148ef4bd3` |
| `SUMMARY.json` | `98c9bc38b6cd7672de5916b7cdf5a40141737e4f5dcb579263b04f8f326d3ed7` |
| `reconciliation.jsonl` | `a2ccf5053c404fd4bdb0bcfed6c741be6eb659a012fcfbc62ee71659918d2e09` |
| `RECONCILIATION.json` | `0a1a3d2d8b1bcd01ea3f0b2c6ea3514ea218e4ee890c7812795393d0fa915a19` |

## 2. Who owns each column, and where the LP is not re-solved

The pre-registered constraint is that no column of `census.jsonl` is computed by
re-solving the LP outside the engine. `census.py` imports `json`, `os`, `sys`,
`time`, `collections`, `fractions`, `engines.lp_potential`, `fuzzlab.prng`,
`fuzzlab.worlds.jumpgraph`. It does not import `scipy` and contains no second
LP.

| column | source | independent of the engine? |
|---|---|---|
| `seed`, `initial`, `goal_states`, `n_pos`, `n_triples` | `fuzzlab` world draw | shared with E11 by design |
| `reachable_size`, `goal_truly_unreachable` | forward BFS written in the harness, driven by `spec.triples` | yes |
| `generator_solvable_flag` | the generator, recorded only as a cross-check | yes |
| `engine.status`, `engine.solver_status`, `engine.decided`, `engine.bound`, `engine.margin`, `engine.solver_message` | `LpOutcome.as_json()`, verbatim | no — this is the subject |
| `silent` | `outcome.status != CERTIFIED` — the **status word** | no |
| `wider_box[*]` | the same engine, called again with a different `bound` | no |
| `wider_box[*].exact_recheck` | `Fraction` arithmetic over `spec.triples` in the harness | yes |

Ground truth is BFS over `spec.triples`, not `graph["edges"]` — the engine's
move list is built from `edges`, so an oracle reading `edges` would share a
failure with the subject. E11 made the same choice for the same reason. The
generator's own `solvable` flag agrees with the harness BFS on **3000 / 3000**
worlds; it is recorded, not relied on.

**`silent` is read off the status word, not off `certificate is None`.** The
inherited draft of `census.py` derived it from the certificate being absent, and
that is the exact reconstruction this item exists to forbid: it is also true
under an iteration limit. The two expressions agree on this corpus — which is
why writing the wrong one here would have been invisible — and `census.jsonl` is
byte-identical before and after the change. It is corrected anyway, because the
census is the artifact that is supposed to model the reading discipline.

## 3. Pre-registered table versus measured

Every count below is a tally of the engine's own `status` strings in
`census.jsonl` (`census.py::summarise`).

| quantity | pre-registered (E11 §4.1, §4.3) | measured | verdict |
|---|---|---|---|
| worlds | 3000 | **3000** | match |
| goal genuinely unreachable | 2189 | **2189** | match |
| certificate issued (`status == certified`) | 1550 | **1550** | match |
| no certificate | 1450 | **1450** | match |
| silent **and** genuinely unreachable | 639 | **639** | match |
| incompleteness rate | 639 / 2189 = 29.2 % | **639 / 2189 = 29.1914 % → 29.2 %** | match |
| `CertificateError` | 0 | **0** | match |
| outcomes not decided (HiGHS 1 / 3 / 4) | 0 | **0** | match |

Supporting counts, none of them pre-registered but all of them checkable:

* status histogram: `certified` 1550, `no_linear_pagoda` 1450, nothing else.
* solver-status histogram: `0` ×1550, `2` ×1450. No row carries HiGHS 1, 3 or 4,
  so the new `budget` / `unbounded` / `numerical` words are unexercised by this
  corpus — they are covered by P4's negative controls, not by the census.
* `status == certified` implies `solver_status == 0` on all 1550 rows;
  `status == no_linear_pagoda` implies `solver_status == 2` on all 1450. The
  word and the integer never disagree.
* `bound == 10` and `margin == 1` on all 3000 census rows. **The default box is
  not changed anywhere.**
* certificates issued on a genuinely *reachable* world: **0** (soundness, not
  claimed here but worth the line).
* goal genuinely reachable: 811 — the complement, matching E11 §4.1.

## 4. The 639, row by row (P2.3)

`reconcile.py` compares **all 639** silent-and-genuinely-unreachable worlds
against E11 §6, one row each; `reconciliation.jsonl` is that table, 639 lines,
one JSON object per world carrying `index`, `seed`, `n_pos`, `engine_status`,
`engine_solver_status`, `engine_bound`, the three widened-box statuses,
`feasible_when_widened`, E11's expectation for that row, and `agree`.

Rows compared **639**. Rows agreeing **639**. Rows disagreeing **0**.

Only two row signatures occur, so the 639-line table collapses without loss:

| signature | HiGHS at `bound=10` | `bound=100` | `bound=1e4` | `bound=1e6` | worlds |
|---|---|---|---|---|---|
| still incomplete | 2 (infeasible) | `no_linear_pagoda` | `no_linear_pagoda` | `no_linear_pagoda` | **638** |
| box-limited | 2 (infeasible) | `certified` | `certified` | `certified` | **1** |

| E11 §6 line | E11 | census | verdict |
|---|---|---|---|
| HiGHS status 2 at `bound=10` | 639 / 639 | **639 / 639** | match |
| still infeasible at 100 / 1e4 / 1e6 | 638 | **638** | match |
| feasible once the box is widened | 1 | **1** | match |

### The one box-limited world

E11's individual claim, and the census row for it, agree field by field:

| field | E11 §6 | census (`census.jsonl` index 2302) |
|---|---|---|
| seed | 17475932563032345095 | 17475932563032345095 |
| campaign index | 2302 | 2302 |
| `n_pos` | 8 | 8 |
| `initial` | `00100011` | `00100011` |
| goals | `{00000010, 10000010}` | `["00000010", "10000010"]` |
| `|reach|` | 4 | 4 |
| independent BFS | goal unreachable | goal unreachable |
| engine at `bound=10` | no certificate | `no_linear_pagoda`, `solver_status` 2 |
| weights at `bound=100` | `[12, 9, 3, 7, -1, 11, 10, -4]` | `[12, 9, 3, 7, -1, 11, 10, -4]` |
| exact `inv_closed` over all 17 triples | holds | holds |
| goal gaps above the initial potential | +1, +13 | `+1`, `+13` (initial potential 9) |
| `max |w|` | 12 > 10 | 12.0 |

The weight vector is re-checked in exact `Fraction` arithmetic over
`spec.triples` — not on HiGHS's word — by `census.py::exact_pagoda_holds`, and
`holds` is true. This is the one *positive* result in the widened box, and it is
the one that does not rest on the solver.

### The widened box is a diagnostic, kept apart

`bound` 100 / 1e4 / 1e6 is never touched by the census proper. It appears only
under the `wider_box` key, only on the 639 rows that are both silent and
genuinely unreachable (0 rows outside that set carry it), and no quantity in
§3 is computed from it. It is a second question — "is this silence the
mathematics or the box?" — asked of the same engine with `bound` moved, which
`LpOutcome` now carries on the verdict. `engines/lp_potential/potential.py`'s
`bound: int = 10` default is unchanged, per the pre-registration's out-of-scope
list.

## 5. Divergences

**Against E11's hand derivation: none.** Every line of §3 and §4 matches, and
`RECONCILIATION.json` records `totals_agree: true`, `rows_disagreeing: 0`. The
authority rule was never triggered; had it been, the census number would have
stood here with the divergence named.

Three things did diverge, none of them from E11, all recorded because a clean
reconciliation is only worth reading if the near-misses are in it too:

1. **The ticket prose is wrong; E11 §6 is right.** The ticket says "638 of the
   639 silences were status 2, the other was the hard-coded `bound=10`". The
   census finds **639 / 639** are HiGHS status 2 *at* `bound=10`, and that 1 of
   those 639 is additionally feasible at a wider box — which is E11 §6's actual
   wording. The two are not the same claim: status 2 is the solver's verdict
   *inside* the box, so the box-limited world is status 2 **and** widenable, not
   status 2 **or** widenable. The pre-registration anticipated this discrepancy
   and specified that the census tests E11, the primary source. It does, and E11
   holds.

2. **`silent` was being reconstructed from `certificate is None`** in the
   inherited draft. Corrected to branch on the status word (§2). `census.jsonl`
   is byte-identical either way, so this changed no number — it removes a
   latent instance of the defect the item is about.

3. **`SUMMARY.json` carried a `wall_seconds` field**, which made the artifact
   differ between otherwise identical runs. Timing moved to stdout; the artifact
   is now byte-stable across runs. No count changed.

## 6. What this does not establish

* **"No linear pagoda exists" is still a HiGHS claim.** For the 638 genuinely
  incomplete worlds the evidence is `linprog` returning status 2 in floating
  point. No exact rational infeasibility certificate (Farkas dual) is produced,
  and P2 does not upgrade that — E11 §7 says the same. Distinguishing status 2
  from status 1 makes the claim *attributable*, not *proved*.
* **The corpus exercises two of the six status words.** `budget`, `unbounded`,
  `numerical` and `undecided` appear 0 times in 3000 worlds. The census is
  evidence that they do not fire here, and no evidence at all that they are
  handled correctly when they do; that is P4's job.
* **`jumpgraph` only, `n_pos ≤ 9` only.** `MAX_POSITIONS = 9` is a generator
  constant and exhaustive BFS is what buys the ground truth. Nothing above 512
  states was examined, and the silence-versus-`n_pos` trend is decreasing over
  4–9, so extrapolating past 9 is unjustified in either direction.
* **29.2 % is an incompleteness rate for this corpus at `bound=10`, margin 1.**
  Both parameters travel with it on every row of `census.jsonl`, which is the
  point: before E15 neither was readable off any artifact.
