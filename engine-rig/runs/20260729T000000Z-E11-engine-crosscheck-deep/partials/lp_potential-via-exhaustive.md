# lp_potential, cross-checked against exhaustive enumeration

**Ticket** E11-engine-crosscheck-deep (RES-3 / verify lane) · **worktree**
`.worktrees/e11-engine-crosscheck-deep` · **tree** `ed592a6` on
`agent/e11-engine-crosscheck-deep` · Python 3.13.13, scipy 1.17.1, numpy 2.4.4 ·
2026-07-29.

Nothing under `engine-rig/` or `fuzzlab/` was modified. The harness lived in the
session scratchpad; the one in-process monkeypatch (§6.1) patched a module
attribute in my own interpreter and wrote no file.

**Headline: no unsoundness.** Zero false certificates, zero inadmissible
heuristic values, zero missing moves, zero exact-arithmetic condition failures,
over 3000 worlds and 42090 state-level admissibility comparisons. The three
things worth reporting are all about what nobody is *checking*, not about a
wrong answer.

---

## 1. The chain, and who wrote each link

The whole point of this pass is that the judge and the judged do not share
plumbing. Every step is named with its owner.

| # | Step | Code used | Owner | Independent of engine? |
|---|---|---|---|---|
| 1 | draw a world from a seed | `fuzzlab/worlds/jumpgraph.py::generate` | fuzzlab | yes (shared — see §2) |
| 2 | world **definition** = `spec.triples`, `spec.initial`, `spec.goal_states` | `JumpSpec` dataclass | fuzzlab | yes |
| 3 | successor relation | written in the harness, driven by `spec.triples` alone | **me** | yes |
| 4 | reachable set / distances | `fuzzlab/oracles/search.py::bfs_distances`, `distance_to_any` | fuzzlab oracles | yes (no engine import) |
| 5 | the engine's answer | `engines.lp_potential.run` | engine-rig | — (this is the subject) |
| 6 | recompute the 3 conditions | written in the harness, `Fraction`, iterating **`spec.triples`** | **me** | yes |
| 7 | admissibility | harness loop, `heuristic.value(s)` vs step 4 distance | me + engine's `value()` | partly (see §2.4) |
| 8 | LP-status / parameter probe | LP rebuilt from scratch in the harness, `scipy.linprog` | **me** | yes |

Step 3 is the deliberate deviation from `fuzzlab/props/lp_potential.py`. That
property rebuilds successors from `graph["edges"]` — **the same table
`moves_from_graph` reads**. I rebuilt them from `spec.triples`, the field the
generator was told to build the world from, so a divergence between the
definition and the rendered `edges` would show up here and cannot show up there.
It did not (0/3000), but the check was previously not being made by anyone.

## 2. Shared dependencies — the full list, nothing dropped

1. **The world generator.** `jumpgraph.generate` produces both my truth and the
   engine's input. Unavoidable — I have no second source of peg worlds — and it
   means a generator that only ever emits easy geometries would make both of us
   look good. Partially mitigated: I check the generator's own `solvable` flag
   and its `distance_to_goal` table against my forward BFS (0 mismatches over
   3000 worlds / 505 312 states), so at least the generator's *asserted* truth is
   no longer taken on faith.
2. **The peg-jump rule itself.** `(src,over,dst)` semantics is hard-coded in
   `Move.delta`, in `jumpgraph.apply`, in `fuzzlab/props`, and in my harness —
   four copies of one convention. If the convention is wrong relative to real peg
   solitaire, all four are wrong together. Not checkable from inside this repo.
3. **`fuzzlab/oracles/search.py`.** My BFS. It imports no engine and the ticket
   licenses it, but it is one implementation, not two.
4. **`Heuristic.value()`.** Admissibility is `h(s) <= d(s)` and only `d(s)` is
   independent; `h(s)` must come from the engine because it *is* the engine's
   claim. So §5 tests the number the engine reports, not the formula that
   produced it — a sign error inside `value()` that happened to stay below the
   true distance would pass.
5. **`scipy.optimize.linprog` / HiGHS.** The engine solves with it and my §7
   probe re-solves with it. A HiGHS bug reporting spurious infeasibility would
   be invisible to both. This is the weakest link in the silence analysis and
   the reason §7 leans on exact rational re-verification of the one positive
   result rather than on the solver's word.
6. **`spec.triples` itself.** My step-3 successors and the engine's constraint
   set both bottom out here. Independent of `edges`, not independent of the spec.

## 3. Method and scale

Worlds are `jumpgraph`, drawn with the campaign's own seed
`0x00005EEDC1E4F002` via `prng.derive(seed, "jumpgraph", i)` for
`i = 0 … 2999` — so index `i < 500` is exactly the world the E4 campaign saw,
and the numbers below are comparable to `fuzzlab/out/campaign.json`.

* **3000 worlds.** `n_pos` 4–9 (roughly uniform), state space `2^n_pos`, so at
  most **512 states per world**; 505 312 states enumerated in total.
* **Fully exhaustive.** Every BFS ran to completion — no world hit
  `search.STATE_BUDGET`, so every "unreachable" below is a proof, not a timeout.
* Truth per world: forward BFS from `initial`; and, for admissibility, a
  separate forward BFS from **every** state of the space (not the generator's
  backward-BFS table).
* Replay: `prng.derive` is a pure function of the seed and `generate` is a pure
  function of that, so every row replays from its `seed` field alone.

## 4. Results

### 4.1 Base rates (3000 worlds)

| | count | share |
|---|---|---|
| goal genuinely **unreachable** (exhaustive) | 2189 | 73.0 % |
| goal genuinely reachable | 811 | 27.0 % |
| certificate issued | 1550 | 51.7 % |
| `(None, None)` — no certificate | 1450 | 48.3 % |
| `CertificateError` (rational snap failed) | **0** | 0 % |

### 4.2 Soundness — nothing found, and that is the result

| check | scope | violations |
|---|---|---|
| certificate issued on a **reachable** world | 1550 certificates | **0** |
| `inv_closed` re-derived over `spec.triples` in `Fraction` | 1550 × all triples | **0** |
| `goal_break` re-derived over `spec.triples` in `Fraction` | 1550 | **0** |
| `cert.moves` misses a triple the world defines | 1550 | **0** |
| `cert.moves` contains a triple the world does not define | 1550 | **0** |
| `h(s) > true distance(s)` | 42 090 comparisons | **0** |
| `h(s) = inf` on a state that can reach a goal | 343 504 states swept | **0** |
| generator's `solvable` flag vs my BFS | 3000 | **0** |
| generator's `distance_to_goal` vs my per-state BFS | 505 312 entries | **0** |

No false certificate exists in this corpus. The certificates are also not
trivial: **0 of 1550** are the constant weight vector (the counting pagoda),
which cannot certify anything here — every jump removes exactly one peg and the
generator only draws goals with *fewer* pegs than the start, so `w ≡ 1` gives
`potential(goal) < potential(initial)` and `goal_break` fails by construction.
824 certificates use a negative weight and 556 use a non-integer one.

### 4.3 Incompleteness — the size

The circulating figure is **"~46 % of `jumpgraph` worlds get no certificate."**
It reproduces exactly: at the campaign's own N = 500 I get **46.6 %**. But it is
being read as an incompleteness rate, and it is not one.

| at N = 500 (campaign scale) | share of all worlds |
|---|---|
| no certificate, because the goal **is reachable** — *correct* | 24.0 % |
| no certificate on a genuinely unreachable world — *incompleteness* | 22.6 % |
| **total "no certificate"** | **46.6 %** |

At N = 3000 the incompleteness rate is **639 / 2189 = 29.2 % of truly
unreachable worlds** (21.3 % of all worlds). Roughly half of the headline 46 %
is the engine correctly declining to prove a false statement. Quoting 46 % as
the incompleteness number overstates it by about 2×.

### 4.4 Incompleteness — the shape

Silence is **not** a fact about the puzzle; it is a fact about the LP's degrees
of freedom. It tracks constraints-per-variable monotonically:

| (distinct triples + goals) / `n_pos` | worlds (unreachable only) | silent |
|---|---|---|
| ~1.0 | 230 | 19.6 % |
| ~1.5 | 577 | 23.7 % |
| ~2.0 | 549 | 27.0 % |
| ~2.5 | 247 | 28.7 % |
| ~3.0 | 277 | 39.4 % |
| ~3.5 | 152 | 38.2 % |
| ~4.0 | 149 | 44.3 % |

The clearest single driver is board size, in the **counter-intuitive**
direction — the LP has one variable per position, so a small board is a
*cramped* LP, not an easy one:

| `n_pos` | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|
| silent | **63.2 %** | 41.2 % | 35.3 % | 21.5 % | 13.9 % | **14.7 %** |

Two more, both consistent with "more constraints, less room":

* **number of goals**: 1 goal → 23.0 % silent; 2 goals → 36.7 % (one weight
  vector must clear *every* goal by the margin simultaneously).
* **peg drop** `pegs(initial) − max pegs(goal)`: 1 → 27.3 %, 2 → 34.1 %,
  3 → 35.8 %, 4 → 40.0 % (n=30).

What does **not** predict silence: reachable-set size. Silence is 31.2 % at
|reach| = 2, dips to 23.4 % in the 17–32 band, and rises again to 36.6 % at
|reach| ≥ 65. There is no "only small instances" story and no trivial-instance
artifact — after the generator's `movable` fix, **0** worlds in either group have
|reach| = 1.

This is the documented boundary from `CLAUDE.md`, now with a number and a
mechanism. It is **not** a defect, and §7 is the only part of it that is.

### 4.5 Heuristic

Admissibility: **0 violations in 42 090 comparisons**, plus 0 cases of
`h = inf` on a reachable state. The claim holds.

Sharpness is not claimed (D-008), and it is worth recording how much is being
given up: across the 1550 worlds with a heuristic, **65.1 %** of the states with
a finite `h` and a genuinely finite distance get `h = 0`, and in **579 / 1550
(37.4 %)** of those worlds `h` is 0 on *every* such state — an admissible bound
that never once says anything. Nobody currently measures this.

## 5. What only the cross-check can expose

Four things. The first is the one that matters.

### 5.1 The battery cannot tell a working engine from a dead one

All four invariants in `fuzzlab/props/lp_potential.py` return `[]` — not
`violated`, not `skipped`, *nothing* — when `cert is None` or
`heuristic is None`. So on the 48.3 % of worlds where the engine answers
`(None, None)` the battery makes no assertion and records no trace of having
declined to.

Demonstrated, in-process, no files touched:

```
real engine                    findings: {}   (all four invariants returned nothing)
engine stubbed to (None,None)  findings: {}   (all four invariants returned nothing)
```

Replacing `lp_potential.run` with `return None, None` passes the entire
`lp_potential` property battery with byte-identical output. Meanwhile
`fuzzlab/out/campaign.json` records, for this engine,
`invariant_worlds_evaluated: 500` on each of the four invariants and
`"skipped": 0` — a coverage number that counts *invocations*, not *claims*, and
therefore reports full coverage on ~46 % of worlds where no claim was made. The
engine's own suite cannot see this either: it asserts silence on exactly two
hand-picked configurations of one 16-state fixture (`SOLVABLE`, `0111`).

Neither side is wrong. The gap is that the *rate* of silence is a first-class
property of a sound-but-incomplete engine, and it is the one quantity nothing in
the repo observes.

### 5.2 A missing move geometry would be invisible to `three_conditions_hold`

`fuzzlab`'s `three_conditions_hold` iterates `cert.moves` — the engine's own
move list, produced by `moves_from_graph`. If that function ever dropped a
triple, the certificate would be unsound *and* the property would confirm the
weights are non-increasing on the (short) list it was handed. The engine's
`check_exactly` iterates the same list, so both re-checks would agree.

Worse, the property's fallback oracle would agree too: its `_successors` reads
`graph["edges"]`, the same table `moves_from_graph` reads, so a defect in
`build_graph`'s edge emission corrupts the engine and its judge identically.

I checked from `spec.triples` instead: **0 missing, 0 extra, over 1550
certificates.** Clean today, structurally unobservable from where `fuzzlab`
stands.

### 5.3 `admissibility_report` is published and verified by nobody

`lp_potential.candidates()` embeds `admissibility_report(...)` into the
`heuristic` candidate that goes to `candidates.jsonl`, and `Heuristic.as_json()`
hard-codes `"admissible": True`. That report's `true_distance` column comes from
`graph["distance_to_goal"]` — the *generator's* backward BFS. `fuzzlab` never
looks at `admissibility_report`; it recomputes `h` against its own oracle. The
engine's own test (`test_the_report_marks_every_checked_state_admissible`) reads
the same fixture table it is meant to be checking. So a wrong backward BFS would
propagate a wrong `true_distance` straight into the frozen candidate stream that
the adjudicating LLM reads.

I compared it to 505 312 independent forward-BFS distances: **0 mismatches**.
The table is correct; it just had nothing checking it.

### 5.4 The heuristic exists only where it is useless

`run()` returns `(None, None)` whenever no certificate is found, and
`heuristic_from` needs a `Certificate`. There is therefore **no path through the
public API that yields a heuristic for a solvable configuration** — on all 811
genuinely reachable worlds (27 %) the engine hands back no bound at all.
Admissibility is consequently only ever exercised on states inside worlds already
proved unwinnable. "Certificate and heuristic are the same object"
(Theoria 1.9) is being honoured literally, and the cost is that the search bound
is unavailable in precisely the case where a search would be run. Whether that
is intended is a design question for the engine-rig track, not a defect call I
can make.

## 6. One real finding: 1 silence in 639 is the weight box, not the mathematics

`solve_certificate(..., margin: int = 1, bound: int = 10)` boxes every weight to
`[-10, 10]`. That bound is not part of the "linear pagoda" concept, and the
constraint system is homogeneous apart from the margin, so a world admitting a
pagoda only at larger weights is reported identically to a world admitting none.

Rebuilding the LP myself for all 639 silent-but-unreachable worlds:

| | count |
|---|---|
| HiGHS status 2 (infeasible) at `bound=10` | 639 / 639 |
| still infeasible at `bound = 100`, `10⁴`, `10⁶` | 638 |
| **feasible once the box is widened** | **1** |
| feasible with `margin = 1/1000` instead of 1 | 1 (the same world) |

The one world, verified in exact `Fraction` arithmetic and not on the solver's
word:

```
seed        17475932563032345095   (campaign index 2302)
n_pos 8, initial 00100011, goals {00000010, 10000010}, |reach| = 4
independent BFS: goal unreachable, search exhausted
engine:  solve_certificate -> None
weights at bound=100:  [12, 9, 3, 7, -1, 11, 10, -4]
  exact inv_closed over all 17 defined triples: holds
  goal gaps above initial potential: +1 and +13   (margin 1 required)
  -> a valid linear pagoda.  max |w| = 12 > 10.
```

So `CLAUDE.md`'s "some genuinely unsolvable ones admit no linear pagoda" is
right for 638 of 639, and for one it is `bound=10` doing the refusing. Scale:
**0.16 % of silences, 0.046 % of unreachable worlds** — small, real, and
currently indistinguishable from the documented boundary. Corroborating: exactly
1 of the 1550 issued certificates sits at the box edge (`|w| = 10`), so the box
is nearly-but-not-quite non-binding. Reporting only; per the ticket I have not
touched the engine.

## 7. Where I could not reach a conclusion

* **"No linear pagoda exists" rests on HiGHS.** For the 638 worlds I call
  genuinely incomplete, the evidence is `linprog` returning status 2 in floating
  point. I verified the one *positive* result exactly, but I did not produce an
  exact rational infeasibility certificate (Farkas dual) for the negatives, so
  "no linear pagoda exists" is a solver claim, not a proof. Confidence is
  moderate: the pattern is smooth in `n_pos` and constraint density rather than
  scattered, which is not what solver flakiness looks like.
* **`n_pos ≤ 9` is the whole corpus.** `MAX_POSITIONS = 9` is a generator
  constant, and exhaustive enumeration is what buys the truth here. Nothing above
  512 states was examined, and the silence-vs-`n_pos` trend is *decreasing* over
  4–9, so extrapolating it past 9 is unjustified in either direction.
* **The 27 % reachable worlds are barely tested.** The engine returns
  `(None, None)`, my only assertion is "no certificate", and there is no
  heuristic to check (§5.4). Cross-checking has almost nothing to bite on there.
* **Only the `jumpgraph` family.** `lp_potential` hard-codes peg-jump semantics,
  so there is no second family to try, and shared dependency #2 stays unresolved.
* **I did not vary `DENOMINATOR_LIMIT`.** With 0 `CertificateError`s in 3000
  worlds the rational snap never failed, so I have no evidence about its
  behaviour under stress — only that it is not currently firing.
* **Sharpness has no baseline.** I can report `h = 0` on 65 % of useful states
  but not whether that is good, because no alternative admissible heuristic was
  computed to compare against.
