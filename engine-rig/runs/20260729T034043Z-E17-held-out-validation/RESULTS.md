# E17 · results — the two numbers, and what they are not

Splits, metrics, predictions and validity criteria were fixed in
`PREREGISTRATION.md` and committed in `ef382c9` before the harness existed and
before any of the numbers below did. `git merge-base --is-ancestor ef382c9 HEAD`
is the check.

Reproduce: `cd engine-rig && python -m heldout.run --out
runs/20260729T034043Z-E17-held-out-validation/results.json`. Raw console output
in `measured/heldout-run.txt`; every count here is a field of `results.json`.

---

## Validity

| criterion | result |
|---|---|
| `fit()` reproduces `zerospace.analyse().basis` with nothing withheld | **120 / 120 worlds** |
| `heldout/peg.py` reproduces committed Fixture C field by field | **ok** |
| two consecutive runs byte-identical | **yes** (`results.json` carries no clock) |
| every miss carries a concrete witness | yes — `misses[]`, `witnesses{}` |
| `python -m pytest engine-rig -q` | **504 passed, 27 skipped, exit 0** (`measured/pytest.txt`) |

The run is valid. Per §5 of the pre-registration, no hit rate could have made it
invalid, and none did.

---

## `zero_space` — 120 `parityworld` worlds, 60 transitions each

`delta_hit` = the law's `a · d = 0` holds on **every** withheld difference.
`value_hit` = the constant survives too. They came out identical everywhere, so
only `delta_hit` is quoted below; both are in `results.json`.

| split | scope | laws | `delta_hit` |
|---|---|---|---|
| **Z-S1** random 70 / 30 transition split | global | 180 | **100.0 %** |
| Z-S1 | cell_local | 960 | 100.0 % |
| **Z-S2** leave-one-operation-out | global | 1680 | **13.1 %** |
| Z-S2 | cell_local | 6800 | **92.9 %** |
| Z-S2, `k = 2` (pooled over n) | global | 720 | **0.0 %** |
| Z-S2, `k = 3` (pooled over n) | global | 960 | **22.9 %** |

1940 laws miss in total. Every one is emitted with the world id, the law's
support, the offending transition index and the operation that caused it.

**Read this as D-003, not as a defect.** The engine's declared quantifier is the
*observed* difference space. Withhold an operation and the observed difference
space shrinks, the null space grows, and the extra laws are true of everything
that was seen and false of the thing that was not. That is the documented
behaviour working, reported honestly. `rank_loss` makes the mechanism explicit:
the train difference rank is below the full rank in **780 / 780** Z-S2 splits and
in **0 / 120** Z-S1 splits — which is the entire explanation of the gap between
100.0 % and 13.1 %.

**And that gap is the finding.** Two cuts of the same evidence, both defensible,
both registered in advance, differing by 87 points. A single held-out number for
this engine is not a property of the engine; quoting Z-S1 alone would read as
"verified and it extrapolates", and quoting Z-S2 alone as "the laws do not
hold". Neither sentence is true on its own.

### Predictions: two held, one falsified, one falsified in its stated form

* **1 (Z-S1 ≈ 100 %) — held**, exactly.
* **2 (Z-S2 below 100 %, *lower for small `|ops|`*) — half falsified.** It is
  below 100 %, but the driver is not `|ops|`: it is the operation *width* `k`.
  At `k = 2` the rate is 0.0 % at every `n`; at `k = 3` it is 20.0 / 25.0 /
  22.7 % at `n` = 6 / 8 / 10. `|ops| = n - k + 1` varies from 4 to 9 across those
  cells and does not order them. Recorded as written, not rewritten.
* **3 (`cell_local` at 100 % under both splits) — falsified. 92.9 %.**
  This is the run's one real surprise and it is not D-003's mechanism. A
  cell-local law is supposed to be a fact about the *encoding* ("this cell holds
  exactly one colour"), which no amount of withheld dynamics can touch. What
  happens instead is that a larger null space contains more vectors whose support
  happens to sit inside a single cell, and `local_laws` classifies them as
  encoding laws. So thinner evidence does not only add global laws — it
  **manufactures encoding-local ones that are not there**. That is the same
  `scope`-over-assertion E11 found from the opposite direction (world facts filed
  as encoding artefacts); this is encoding artefacts invented out of missing
  evidence. Smallest witness: `pw-n6-k2-se17a1838` with operation 0 (cells 0,1)
  withheld yields a `cell_local` law of support `["B@0"]` and value 0 — "cell 0
  never holds B", i.e. cell 0 is permanently R — beside its partner `["R@0"]`
  value 1. Both are filed as facts about the encoding. Both are false, and the
  first withheld transition refutes them: operation 0 is the only operation that
  touches cell 0, so removing it makes cell 0 look constant.

---

## `lp_potential` — 289 `pegN` instances, n ∈ {4,5,6,7}

What this engine fits on is the **move list**: `solve_certificate` writes one LP
row per geometry and `check_exactly`'s `inv_closed` then quantifies over that
same list. So the geometry is the hold-out.

### L-L1 · one geometry withheld — 2422 cases

| | |
|---|---|
| silent (`solve_certificate` → `None`) | **1014** — D-014 incompleteness answering; **not** a miss |
| errors (`LpUnavailable` / `CertificateError`) | 0 |
| certificates produced | **1408** |
| `inv_closed` still holds on the withheld geometry | **372 — 26.4 %** |
| **claim false** against BFS over the complete move set | **58 — 4.1 %** |
| held-out states where `h(s) > true distance` | **1778** (742 cases) |
| reached `candidates.jsonl` | **0** |

**Smallest witness, checkable by hand.** `peg4`, goal `0100`, start `0011`,
geometry `jump(3,2,1)` withheld. The LP returns `w = [0, 1/2, -1/2, 0]`; all
three conditions are exactly true in the rationals; the certificate reads *"goal
unreachable from 0011"*. `0100` is one move from `0011` — by `jump(3,2,1)`, the
withheld geometry — and Fixture C's own docstring records the containing path
`1101 -> 0011 -> 0100 SOLVABLE in 2 moves`. The certificate is false and its own re-check cannot
see it, because the move that refutes it is not in the list the re-check
iterates.

### The half that passes, and it must not be buried

* **The emit gate holds: 0 of 1408 got out.** `premises_against_graph`
  re-derives the move list from the graph rather than from the certificate and
  withheld every single one. The hole is in `check_exactly`, at the boundary
  between the LP and its own re-check — **not** at the boundary between the
  engine and the shared candidate stream.
* Those two are kept apart in `results.json` on purpose. The gate fails a
  certificate for two different reasons and only the second is evidence the
  *weights* are wrong: a short move list is caught by counting, a raised
  potential is caught by arithmetic. Counting caught all 1408; arithmetic
  independently caught **1036**, which is exactly the 1408 − 372 that fail
  `inv_closed`. The two detectors agreeing to the unit is a consistency check on
  this run, not a second piece of evidence.
* **L-L2, and prediction 6 held: `lp_potential` already had a held-out check
  nobody had labelled as one.** The LP constrains exactly two state sets —
  `initial` and the goals — so every other state is held out by construction.
  Over the 105 certificates fitted on complete graphs: **0 admissibility
  violations in 506 held-out states**. Alone among the eight rows of
  `ENGINE_TABLE.md`, this engine's re-check was never circular. Under L-L1 the
  same measurement gives 1778 violations, which is the difference between an
  argument standing on complete evidence and the same argument standing on
  partial evidence.
* 105 certificates against 184 silences, 0 false, on the complete graph. Sound
  and incomplete, exactly as documented.

---

## Corrections to the pre-registration, recorded rather than applied

`PREREGISTRATION.md` cites **D-008** twice for `lp_potential`'s incompleteness.
The correct decision is **D-014** ("Pagoda incompleteness is asserted by a test,
not hidden"); D-008 is the heuristic's max-single-step rule. The pre-registration
is left exactly as committed — its value is that it did not change — and the
correction lives here and in the code comments. Nothing about the split, the
metric or the criterion depended on the number.

## What changed in `ENGINE_TABLE.md`

The boundary column of rows 3 and 4 now carries these numbers, and the file
gained a standing rule under **「已验证」**:

> Where no held-out validation exists, a cell may say 「在观测证据上自洽」 and may
> not say 「已验证」.

Two of the eight rows now have the other half. Six do not, and their re-check
columns are to be read with that sentence attached. Every numeral above enters
the table through a probe against `results.json`; none is typed into the prose,
which is E9's rule and is enforced by `tests/test_engine_table.py`.

### One incidental fix, flagged rather than absorbed

Regenerating the table required updating three expectations that were already
stale on this branch before E17 touched anything — they are `fuzzlab`'s, not
`engine-rig`'s, and they had been corrected downward by the fuzzlab track in
`eb61aa9` / `404e136` after E9 pinned them:

| fact | E9 expected | artifact on this branch |
|---|---|---|
| `rig.campaign_worlds` | 500 | **60** |
| `rig.mutants` | 55 | **64** |
| `rig.survivors` | 15 | **14** |

All three were re-read directly out of `fuzzlab/out/*.json` before the literals
were changed, not taken from the generator's error message. E9's tripwire was
working; this is what it is for. Anyone quoting "500 worlds per engine" from an
earlier draft of the table should stop.
