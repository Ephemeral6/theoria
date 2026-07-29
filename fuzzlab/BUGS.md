# BUGS — what the battery found, and what it did not

`fuzzlab` may not modify `engine-rig`. Everything here is a report; nothing here
was fixed in place. Reproduce any row with the command beside it.

## Verdict: no engine defect found

500 worlds per engine, six engines, **3000 worlds, 23 invariants, 0 violations,
0 unexplained raises, 80 skipped** (all one documented cause, B1 below).
Campaign seed `0x00005eedc1e4f002`, engine-rig at `0b01f29`. That is a real
result and it is also a weak one, and both halves need saying.

It is real because the invariants are judged by independent oracles, not by the
engines' own checkers — `fuzzlab/oracles/gf2.py` is a separate GF(2) elimination,
`fuzzlab/oracles/search.py` a separate BFS and STRIPS replay — and because the
house rule in `oracles/__init__.py` is that **an oracle may not call the engine
it judges**. Checking `zero_space` with `zero_space.verify` would establish that
the module agrees with itself and nothing more.

It is weak because absence of evidence over one corpus is not a proof, because
three of five generators had to be repaired before the corpus was worth anything
at all (below), and because 23 invariants over six engines is thin. What the run
licenses is: *these particular claims held on these 3000 worlds*.

## The findings are about the generators, not the engines

The first campaign was green too — and it was worthless. An adversarial audit of
the inherited generators (full text in
`runs/20260728T085448Z-E4-property-fuzz/GENERATOR_AUDIT.md`) measured what the
corpus actually contained:

| id | what was wrong | measured before | after repair |
|---|---|---|---|
| **G1** | **`gridworld` could never produce an obstacle.** `_place_obstacles` required that no reachable mover placement land in the obstacle's halo — but the mover is stopped exactly when it is adjacent, so the condition reduced to "the obstacle is unreachable", which a ≤4-cell obstacle in a ≥5×5 grid cannot arrange. | **0 obstacles in 3200 worlds** across five campaign seeds; `mdl_segmenter` saw only single-component frames; `cegis_miner`'s `clear(strip(D))` conjunct was never load-bearing, so only the bounds half of any guard was ever needed | 136/200 worlds carry obstacles, 0 dropped; the segmenter now sees **1–23 tracks** |
| **G2** | **`jumpgraph` was mostly degenerate.** `initial` and `goal_states` were drawn uniformly from all 2ⁿ bit strings with no conditioning on peg count or reachability. | 52.5 % of initial states had **no legal move**; 87.5 % had ≤4 reachable states; only 3 % genuinely solvable; of 70 certificates `lp_potential` issued, **43 were over a one-state reachable set** | 0 single-state worlds, 44/200 solvable, median 4 and mean 7.4 reachable states with a tail past 32 |
| **G3** | `blockworld` drew goals independently of the initial state | 14.7 % of worlds already satisfied at step 0 | goals drawn from unmet literals / unoccupied floors |
| **G4** | `hypset` spent a quarter of the budget on flavours where no action splits anything | 28.5 % undiscriminating, 11 % single-action | reweighted to ~10 %; minimum two actions |

**So the honest reading of the first green run is that it certified nothing**,
and it is recorded that way rather than quietly superseded. The numbers quoted
above are from after the repair.

Ground truth, by contrast, was **honest everywhere** — every carried truth was
independently recomputed with 0 mismatches across all five families, including
`jumpgraph`'s `distance_to_goal` table, which `lp_potential.admissibility_report`
consumes and which would otherwise have validated the engine against itself.

## Capability boundaries observed — reported, not filed as defects

Neither of these is a bug. Both are documented behaviour meeting a corpus that
now actually exercises it, and both are worth the other tracks knowing.

### B1 · the mover merges with an obstacle it touches

`transitions_from_segmentation` raises `ValueError: transition N narrates
['vanish']; only move/none are mined on this fixture`. Cause: the colour-agnostic
component operator merges the mover with an obstacle the instant they are
adjacent, so the merged component narrates as `vanish`+`appear` rather than
`move`. This is the **touching-objects gap** the A0 family has now reported
upstream three times.

Once `gridworld` started producing reachable obstacles this stopped being rare:
it fired on **179 of 500 worlds** (716 raises across four invariants). Retrying
with `split_by_color=True` — the operator that exists for exactly this — recovers
almost all of them, leaving **20 of 500 (4 %)** that neither operator can narrate
as move/none. `fuzzlab/props/cegis_miner.py` therefore tries both operators and
records which one worked, and the residue is the campaign's entire `skipped`
count (80 = 20 worlds × 4 invariants), carrying its reason rather than appearing
as an unexplained raise.

Worth stating plainly: **the default operator cannot mine a world in which the
mover ever touches another object.** For a segmenter aimed at ARC that is a
sharp limit, and it is invisible on any corpus of single-object worlds — which
is what the rig's own fixtures and, until this run, this battery both were.

```bash
python -m fuzzlab.minimize --engine cegis_miner --invariant frontier_guards_are_consistent --kind skipped
```

### B2 · `NoSeparatingGuard` on a coarse vocabulary

Documented and deliberate (`test_contradictory_evidence_is_reported_not_papered_over`):
the fixed five-predicate vocabulary cannot always separate a positive from a
negative. Recorded as `skipped`, never as a violation.

## Two false accusations the battery made about itself

Recorded because a fuzz battery's most likely output is a **false accusation**,
and the only defence is checking the oracle before filing. Both were caught by
reading the first finding rather than the count.

| | reported | actually |
|---|---|---|
| `probe_frontier.entropy_matches_bruteforce` | 120 violations in 120 worlds | the oracle summed class **sizes**; the engine sums `Hypothesis.weight`, and `hypset` draws non-uniform weights. The engine was right every time. |
| `fd_adapter.plan_replays_to_the_goal` | 13 plans "do not execute" | the oracle keyed its action table on `GroundAction.text`, which is a bound method, not a property — so it recognised no action at all. The engine was right every time. |

`fuzzlab/tests/test_oracles.py` now pins both against closed forms.

## What was deliberately not asserted

Writing an invariant against a guarantee nobody made produces a confident, wrong
bug report. These were considered and rejected, each with its source:

* **no frame round-trip from a `Segmentation`.** There is no replay function in
  the rig and a `Segmentation` could not support one — `Track` carries a single
  `color` and no per-frame per-cell colours, and an `appear` event carries only
  `{"at": [r,c]}`. The script is a bit-accounting scheme, not a decodable
  encoding. The strongest true statement is about **occupancy**, and that is
  `masks_partition_the_foreground`;
* **no `script_bits < baseline_bits`.** D-005's threshold is stated against
  Fixture A specifically; on random worlds the script is routinely longer. The
  structural claim is the bit *identity*, and that is what is checked;
* **no completeness for `lp_potential`.** The engine is sound and *explicitly*
  incomplete — D-014 makes the incompleteness a test so it cannot be quietly
  "fixed". The invariant is one-directional: a certificate implies unreachable,
  never the converse. Nor is sharpness asserted: D-008 says `M` is a worst case
  and "admissibility is the requirement, sharpness is not";
* **no optimality for `fd-satisficing`**, which documents itself as
  non-optimal via `Plan.optimal is False`; the check runs only where the plan
  claims optimality;
* **no cegis frontier completeness beyond `rule.frontier_max_size`**, which is
  `min(max(len(cegis_guard), 1), max_frontier_size)` and often 1 — two-literal
  minimal guards are then legitimately absent;
* **no global optimality for `probe_frontier`'s greedy argmax**, which is
  documented as greedy, one bit at a time.

## Standing caveats on this run

1. **Fast Downward is not installed on this machine.** `fd_adapter` fell back to
   `stub-bfs` on every world, so `fd-optimal` and `fd-satisficing` were never
   exercised and the ladder's cross-rung invariant is untested here. Expected,
   not a defect — but it means `fd_adapter`'s coverage is one rung of three.
2. **`blockworld` plans stay short.** The deepest plan seen before the G3 repair
   was 8 actions. Short plans cannot distinguish an optimal planner from a
   satisficing one even when both rungs are available.
3. **`fuzzlab`'s STRIPS parser is the engine's.** Re-implementing a PDDL parser
   would test a parser, not a planner, so `parse_domain`/`parse_problem`/
   `ground_actions` are shared and everything downstream of them is not. If the
   parser is wrong, these three properties inherit the error and report a pass.
4. **One instance wrote the generators, the oracles and the invariants.** The
   adversarial audits were independent agents with no stake in the code, which
   is better than nothing and is not independence.

---

# V-13 supersede · the coverage numbers above are wrong, and here are the right ones

**Appended, not edited.** Everything above this line is the E-4 / V-10 rounds'
report and stays as written; this section supersedes the parts of it that quote
per-invariant coverage. Nothing about any engine's correctness changed — the
campaign was green before and is green now. What changed is that the battery
stopped overstating how much of itself it had run.

Run: `runs/20260728T161127Z-V13-audit-the-published-surface/`, campaign seed
`0x00005eedc1e4f002`, 500 worlds per engine, engine-rig `68a8365`.

## S1 · `lp_potential` claimed 500 worlds per invariant and evaluated 267

All four invariants in `props/lp_potential.py` opened with a bare
`if cert is None: return []` (or `if heuristic is None`). `campaign.py` counts a
world as evaluated by an invariant unless that invariant files a `skipped`, so
"I checked this world and found nothing" and "I could not check this world at
all" were the same empty list, and the report credited the full 500.

| | before (E-4/V-10) | after (V-13) |
|---|---|---|
| `certificate_implies_unreachable` | 500 / 500 | **267 / 500** |
| `three_conditions_hold` | 500 / 500 | **267 / 500** |
| `heuristic_is_admissible` | 500 / 500 | **267 / 500** |
| `infinite_means_unreachable` | 500 / 500 | **267 / 500** |
| `lp_potential` skipped findings | 0 | **932** (233 worlds × 4) |
| campaign-wide skipped | 80 | **1142** |

**Why the two numbers differ:** on 233 of 500 `jumpgraph` worlds (46.6%) the
engine issues no certificate. Every invariant in that module is conditional on
one existing, so on those worlds all four cost a `linprog` call and report
nothing. The 233 are now four `skipped` findings each, carrying
`cause: "no_certificate"` and the reason. The engine is unchanged, the four
invariants are unchanged, and no new claim is checked — only the denominator is
now the one that was earned.

**The negative control, and it is sharper than the argument.** Due to a parallel
cross-check (E-11): replace `engines.lp_potential.run` with
`return None, None` — the engine **entirely disabled** — and against the old
code the four invariants produced byte-identical findings while `campaign.json`
went on reporting `evaluated: 500, skipped: 0`. A battery that cannot tell a
working engine from a deleted one is not measuring the engine, and the coverage
column was the only place that could have said so. That experiment is now
`tests/test_battery.py:test_a_dead_lp_potential_shows_up_as_lost_coverage`. It
was confirmed to **fail** against the pre-V-13 code
(`certificate_implies_unreachable still reports 25 worlds evaluated with the
engine disabled`) and to pass after — a regression test nobody has watched fail
is a regression test nobody has tested.

**Two numbers that must not be mixed.** 267/500 is a fact about *this battery*:
the worlds on which these invariants evaluate anything. It is **not** the
engine's incompleteness rate. Most certificate-less worlds are worlds where a
goal is genuinely reachable, and declining to certify there is the engine being
*sound* — the opposite of a gap. E-11's exhaustive measurement puts the real
incompleteness at 639/2189 = 29.2% of certificate-less cases, 21.3% of all
worlds, roughly half the figure a reader would infer from 46.6%. Quoting the
coverage number as an engine defect rate would be wrong in the engine's favour
nowhere and against it everywhere.

## S2 · `cegis_miner` was mining a static obstacle in 37% of its worlds

Not an engine defect — a corpus defect, and the second of its kind in this
battery. `transitions_from_segmentation` takes the track to mine as a parameter
and falls back to `seg.tracks[0]`, the segmenter's first component in raster
order. `props/cegis_miner.py:_mine` had always taken that fallback, and on the
campaign seed's first 60 gridworlds **21 of the 57 minable ones mined a rock**.

A rock produces one `blocked_<D>` rule per action with `effect: none`, guards
that are trivially mutually exclusive and trivially complete. All four guard
invariants pass. The rules are *true of the rock*, so nothing was wrong with the
engine; what was wrong is that in 37% of its worlds the engine was not being
tested. This is the same failure `worlds/gridworld.py:_place_obstacles` records
— an acceptance test that produced 0 obstacles in 3200 worlds, and a green
campaign that certified neither engine.

`_mine` now picks the track whose anchors match the pixel-derived mover
trajectory from `oracles/motion.py`, **and prefers the operator that keeps the
mover in one piece** rather than the first that mines anything at all — the
second half of the same defect, found while acting on the review. Over the
standing 500-world campaign: subject-unknown **54 → 15**, unminable **unchanged
at 20**, all six invariants at a uniform **465/500**. The residue is § S5.

Two checks that this is a repair and not fuzzlab flattering the engine:

* **the default is used by nobody real.** `theoria-arm/world/adapt.py:mine`
  loops `for track in seg.tracks` and passes `track` explicitly, keeping
  `track_id` beside every result; `engine-rig/tools/run_all.py` and the fixture
  tests take the default because they run one-object fixtures where
  `tracks[0]` *is* the mover. fuzzlab was the only caller taking a
  `tracks[0]` that could be a rock, so selecting the mover moves it **towards**
  real use, not away from it;
* **the engine got no easier input.** The unminable count did not move (3 → 3
  on 60 worlds, 20 → 20 on 500), so the repair did not quietly route the
  battery around the worlds the segmenter cannot narrate — it changed which
  object is mined, not which worlds are attempted.

A note for whoever reads the parallel E-11 report: it counts 1209 published rows
as **false** on the strength of this, judging `blocked_*` rules with
`effect: none` against the *mover's* motion. This round's reading is different
and is stated so it can be argued with: the payload
(`miner.py:Rule.as_json()`) carries **no object identifier**, so a rule mined
off a rock is a true statement whose subject is unnamed. The defect that is
certainly real is therefore the **contract** one — a `rule_hypothesis` cannot
say which object it is about — and the caller-side one repaired here. Both
readings agree the situation is bad; they disagree on which line to file it
under, and this battery does not file a violation against an engine for a track
its own caller chose.

## S3 · what V-13 added, and the coverage it earned

| engine | invariants | evaluated / 500 |
|---|---|---|
| `cegis_miner` | 4 → **6** | 480 → **465**, uniform across all six (see § S7) |
| `probe_frontier` | 4 → **5** | **500** (`costs_are_the_world's`) |
| `lp_potential` | 4 (unchanged) | 500 → **267**, as above |

Campaign totals: **26 invariants, 3000 worlds, 0 violated, 0 raised, 1142
skipped**, `generator_errors: 0`. The green is the same green; the skipped
column is the part that is new, and it is the honest part.

## S4 · still not asserted, and why — the V-10 ranking, unfinished

V-10 ranked three invariants by value. Two are done. The third is not, and the
reasons are recorded rather than the omission being silent:

* **`mdl_segmenter.mdl_accounting_is_closed` (V-10's rank 3) — not done.**
  `baseline_bits` is the denominator of the compression ratio the manual uses to
  decide whether an object hypothesis is worth writing down, and `gain_bits` /
  `ratio` derive from it; `script_bits_identity` locks only the other end of the
  equation. Deferred because it is the only one of the three that needs a
  re-implementation of the engine's `CostModel` pricing to be an *independent*
  oracle — reusing `CostModel` would test the aggregation and not the pricing,
  which is exactly the trap `engine-rig`'s own
  `test_baseline_is_computed_from_the_actual_pixel_diffs` falls into. Ranked
  below the two that were done because it defends an accounting identity, where
  those two defend claims the manual consumes as causal law.
* **`segment_operator` — a repair, not an audit, and it is not fuzzlab's to
  make.** `mdl_segmenter/__init__.py:to_payload` writes the string
  `"connected_components(4)+bipartite_common_fate"` unconditionally while
  `Segmentation` does not record which operator ran; the same world segmented
  with `split_by_color=True` and `False` yields 23 versus 6 tracks under a
  byte-identical payload string. V-10 proved this false; it remains the only
  published field this battery can prove false. **fuzzlab may not edit
  `engine-rig`** (`fuzzlab/README.md`; this round changed 0 bytes there), and an
  invariant asserting it would fire on every world forever, converting a known
  one-line defect into permanent campaign noise. It belongs in `PARTNER_SYNC.md`
  as a one-line engine fix, not here.
* **`probe_frontier`'s 12 executable fields** (`tier`, `verdict`,
  `reach.status/.plan/.length/.expansions/.backend`, …) remain at **zero
  fuzzlab coverage**: `hypset` has no planner, so `design()` and
  `run_with_planner()` are never called. `engine-rig`'s
  `test_probe_reach.py` is the only defence and it is one fixed sokoban board.
  Unchanged from V-10, and still an order of magnitude more expensive than
  anything done this round.
* **`lifted` guards are still unaudited.** `lift()` substitutes the direction
  variable into the template's guard without re-verifying it, so `act==DOWN`
  becomes `act==?dir`, which is vacuously true. The two new invariants read
  lifted rules' `effect`, `action` and `support`; neither evaluates a lifted
  **guard**, because evaluating `act==?dir` against a concrete action is not a
  question `atoms.evaluate` answers. A parallel cross-check (E-11) reports 104
  of 149 lifted rules carrying exactly `["act==?dir"]` — a guard that constrains
  nothing. That claim is not adjudicated here and is not repeated as fact; it is
  named as the next thing to aim an invariant at, and it needs a `?dir`-aware
  evaluator this battery does not have.
* **`admissibility_report` is unaudited but not broken** — E-11 checked 505312
  rows exhaustively with no disagreement. Recorded as a blank rather than a
  defect, and ranked below everything above for that reason.

## S5 · `mdl_segmenter` loses the mover mid-trajectory: `Track.anchors` carries `None`

**Another engine's territory. Observation with numbers, not an adjudicated
defect.** Found by the adversarial review of V-13 asking why `_mover_track`
still falls back, and re-measured independently before being written down.

**The first explanation was wrong, and it had leaked into a user-visible
message.** `props/cegis_miner.py:_mined_subject`'s docstring said the fallback
happened because "the segmenter did not list the mover first" — a raster-order
accident — and that sentence had been copied verbatim into the `skipped`
finding, so whoever triaged it would have been sent to the wrong engine. Both
are corrected; the message now points at `mdl_segmenter` and at this section.

Measured over 500 `gridworld` worlds, seed `0x00005eedc1e4f002`, shipped code:

| | worlds |
|---|---|
| mined track **is** the mover | 465 |
| unminable (documented touching-objects refusal) | 20 |
| **fallback: no track matches the mover** | **15** |

Of those 15:

| | worlds |
|---|---|
| a track with the mover's **exact bounding box exists**, but its `anchors` contain `None` | **14** |
| right bounding box, anchors simply wrong, no `None` | 1 |

So in 14 of 15 the segmenter **found** the object and then **lost track of it on
some frames**. The track is not missing and its shape is not wrong; its
trajectory has holes.

```
world 12   mover shape (1,3), moves 19 times over 23 frames
           pixel anchors[:8]  [(3,3),(3,3),(2,3),(1,3),(1,4),(1,3),(0,3),(1,3)]
           track anchors[:8]  [None, None, (2,3),(1,3),(1,4),(1,3),(0,3),(1,3)]
           -> None on 2 of 23 frames
world 19   mover shape (3,1), 16 frames
           -> None on 15 of 16 frames: the track exists and is nearly empty of positions
world 55   mover shape (1,1), 34 frames
           -> no None at all; the anchors are just not the mover's (the 1 of 15)
```

The pixel anchors come from `oracles/motion.py`, which reads rendered frames and
imports nothing from `engines`, and are cross-checked against
`gridworld.Rules.step` over 4455 transitions in
`tests/test_oracles.py:test_motion_agrees_with_the_generator_across_the_corpus`.
"The mover was at (3,3) on frame 0" is therefore not this battery's opinion.

**Why it reaches further than fuzzlab.** `Track.anchors` is what
`cegis_miner.transitions_from_segmentation` reads to build `State.anchor`, which
is what every guard atom (`at(r,c)`, `free(strip(D))`) is evaluated against. A
`None` anchor makes the engine raise `ValueError("object absent at frame %d")` —
an honest refusal, but it means a world that is segmentable in principle yields
nothing minable in practice. `first_frame` and `events[].at` in the
`mdl_segmenter` payload come off the same anchors.

**Not claimed:** a parallel lane reports a separate `mdl_segmenter` issue about
object-id bit-width computed per-frame while tracks span frames. **Whether these
are two symptoms of one defect is unverified and is not asserted here.** They
are plausibly related — both sit on the frame/track boundary — but nothing in
this run tested it, and a guess filed next to measurements gets quoted as one.

Reproduce:

```bash
python - <<'EOF'
from fuzzlab import prng
from fuzzlab.worlds.gridworld import generate
from fuzzlab.oracles import motion
from engines import mdl_segmenter
w = generate(prng.derive(0x5EED_C1_E4_F0_02, "gridworld", 12))
seg = mdl_segmenter.segment_trajectory(w.frames, background=0, split_by_color=True)
shape, colour, bg = motion.mover_spec(w)
print("pixel:", motion.mover_anchors(w)[:8])
for t in seg.tracks:
    if tuple(t.shape) == shape:
        print("track:", t.anchors[:8])
EOF
```

## S6 · `Rule.as_json()` names no subject — the contract gap behind the "1209 false rows" dispute

E-11 counted 1209 published `rule_hypothesis` rows as **false** because they
carry `effect: none` while the world's mover demonstrably moved. This round read
the same fact differently. The coordinator has adjudicated it; recorded here is
the reasoning, and the third argument is the reviewer's and the strongest:

1. **The rules are true of their subject.** Mined off a static obstacle,
   "nothing happens when you press DOWN" describes a rock correctly. Measured:
   on every world where the mined track could not be established as the mover,
   *all* rules had `effect: none` and there were *no* lifted rules.
2. **The caller chose the subject.** `transitions_from_segmentation` takes
   `track` as a parameter, and `theoria-arm/world/adapt.py:mine` loops every
   track passing it explicitly, keeping `track_id` beside each result. `fuzzlab`
   was taking the `seg.tracks[0]` default — a caller defect, repaired here.
3. **Nothing was published.** `props/cegis_miner.py:_mine` calls
   `engine.mine(transitions)` and **never passes `out_path=`**, the only
   argument that makes `cegis_miner.run()` emit candidates; `fuzzlab` has no
   writer to `candidates.jsonl` anywhere. So "1209 **published** rows" has no
   referent in this battery's output — those rows live in memory inside a
   property run and nowhere else. This holds regardless of how one reads 1 and 2.

**The contract defect the episode exposes stands, and it is the part worth
keeping:** `miner.py:Rule.as_json()` emits `name, action, guard,
guard_cost_bits, effect, frontier, …` and **no object identifier**. A
`rule_hypothesis` in `candidates.jsonl` cannot say which object it describes.
Harmless on a one-object fixture; on any board with two movable things it makes
two contradictory rules indistinguishable from one wrong one.
`CONTRACTS/candidates_schema.md` is frozen and says nothing about payload
internals, so this is `cegis_miner`'s README to change, not a schema question.

## S7 · corrections this round made to itself, after review

An adversarial reviewer was run against V-13 before delivery. It found five
things. All are fixed; none is silently fixed, because a report that reads as
though it was right the first time is worth less than one that shows where it
was not.

| # | what the reviewer found | disposition |
|---|---|---|
| R1 | `costs_are_the_world's` shipped an `if expected > 0` guard that **excluded the zero-cost branch its own docstring twice claimed to check** (`props/probe_frontier.py:52`, `:214` "which is checked below"). `hypset` gives 27.6% of worlds a zero-cost action **on purpose** (`worlds/hypset.py:21`, "Zero is not a hypothetical"). An engine returning `0.0` instead of `inf` passed silently. | **Guard fixed**, not the docstring — leaving a false "checked" inside the invariant written to separate *not checked* from *checked and clean* is this round's own defect one level up. New mutant `pf-zero-cost-value-is-zero`: **survives** the old guard, **killed 11/11** by the new one (11 of 40 worlds carry a free action; 29 inert). |
| R2 | `_mined_subject`'s docstring was present-tense and false (said 21, actual 15) and named the wrong cause — and the wrong cause had been **copied into the user-visible `skipped` message**. | Docstring and message rewritten with the true cause, which is § S5 above. Triage now starts at `mdl_segmenter`. |
| R3 | `MUTATION.md` cited "4455 transitions over 200 worlds"; the shipped test swept **five worlds, 93 transitions**. The measurement was real but lived only in a scratch script, so the repository could not reproduce the number it published. | The sweep **is** the test now: `test_motion_agrees_with_the_generator_across_the_corpus` runs 200 worlds and asserts `checked == 4455`, so the published figure cannot drift from the code without a failure. |
| R4 | `cm-freeze-lifted-direction` was described as closing the lifted-rule gap. The engine **never emits a concrete `effect.direction`** — a census of 357 rules found only `{None, "?dir"}` — so the mutant only reaches `_claimed_delta`'s `if direction in DELTA` branch, which nothing else reaches. It measures tolerance of a malformed field, not `?dir` semantics. | Claim struck from the mutant's own description. Reproduced the reviewer's decisive experiment: **delete those two lines and `cm-freeze-lifted-direction` survives at eval=34, killed=0.** New mutant `cm-lift-admits-a-wrong-direction` tests the real path (`?dir` → `DELTA[witness action]`) by widening a lifted rule's support to a transition where nothing moved: **killed 32/32**, and it still dies with the branch deleted. |
| R5 | `RUN_STATE.md` and `MANIFEST.json` referenced an `ADVERSARIAL-1.md` that did not exist. | Archived; the references are live. |

**A sixth correction is this round's own**, not the reviewer's, and it is the
one that changes a published number. `_mine` committed to the **first
segmentation operator that mined at all**, rather than the first that mined *the
mover* — so a world where only `split_by_color=True` keeps the mover in one
piece was silently mined off a rock under the default operator. Fixed:
subject-unknown worlds fall **54 → 15** of 500, and all six `cegis_miner`
invariants now report a uniform **465/500**.

That number is *lower* than the 480/500 the four guard invariants claimed before
V-13, and the drop is the point: those 480 included worlds whose entire rule set
was `blocked_<D>` rules saying nothing ever happens. Reporting them as evaluated
was the same confusion this round removed from `props/lp_potential.py`, and
applying the rule to one module and not the other would have been the harder
thing to explain.
