# A0_REPORT — did the cold start actually work?

**Short answer: yes, and the interesting part is where it did not.**

The loop closed. Perception → engine proposals → adjudication → certify (both
layers) → plan → win, and then the same manual carried to an unsolvable variant
and produced a machine-checked impossibility theorem with an empty axiom list.
That is the A0 acceptance criterion in Theoria Phase 1, met.

It also produced a manual that is **wrong about the world in a way full-history
replay cannot see**, which is the failure mode Theoria 1.3 predicts and the
reason the framework exists. That the miss was written down *before* it was
measured is the most useful thing in this report.

Everything below is reproducible with `python run_all.py` (≈6 s) and
`python -m pytest` (26 tests).

---

## 1 · What was built

| milestone | artefact | state |
|---|---|---|
| M1 | `world/` — 9×9 Cart/Button/Door/Portal world, 59 reachable states; deterministic explorer; 276-frame `raw_trace.jsonl` | green |
| M2 | `pipeline/` — board extraction → `mdl_segmenter` → multi-track CEGIS → `zero_space` → `probe_frontier`; **29** schema-valid candidates | green |
| M3 | `theory/theory.dsl` + `THEORIZE_LOG.md` — 3 objects, 7 rules, 2 invariants, 1 pending theorem; every candidate adjudicated | green |
| M4 | four co-derived forms; cheap certify 22 356/22 356 pixels; Lean `inv_all`, 0 axioms; plan SAT, 12 steps, world agrees frame-for-frame | green |
| M5 | `theory_no_button.dsl`; plan UNSAT; `unsolvable`, 0 axioms; explanation in the manual's own vocabulary | green |
| M6 | this report + `artifacts/score_vs_truth.json` | — |

---

## 2 · Accuracy against the ground truth

Measured once, at M6, after M4 and M5 were green
(`certify/score_vs_truth.py`; seal discipline in `THEORIZE_LOG.md`).

| measurement | result |
|---|---|
| full-history replay (what certify sees) | **276/276 frames, 22 356/22 356 pixels, 0 anomalies** |
| every reachable (state, action) pair, base world | **233/236 = 98.73 %** |
| the 3 pairs the trajectory could never contain | **0/3 = 0 %** |
| every reachable (state, action) pair, variant | **92/92 = 100 %** |
| Lean obligations discharged | **2/2**, axiom lists empty in both |

The three misses:

```
cart (2,2) pressed=false  DOWN   world: Button pressed   manual: nothing happens
cart (3,1) pressed=false  RIGHT  world: Button pressed   manual: nothing happens
cart (4,2) pressed=false  UP     world: Button pressed   manual: nothing happens
```

They are the Button pressed from above, below and the right. `THEORIZE_LOG`
R-05 rejected the direction generalisation of `press_left` for want of evidence,
predicted that the manual would therefore be wrong in exactly these three
places, and predicted that replay would never notice. All three held.

**This is a scale model of DC22.** The manual is not *wrong*; it is *missing a
rule*, and a missing rule makes the modelled world smaller than the real one
while leaving the replay score untouched. 100 % on the past, 98.73 % on the
whole, and the gap sits precisely where no observation could ever have landed.

The one thing that could have exposed it — a probe — could not be run, and the
reason is structural rather than incidental: the Button's latch is
**irreversible**, so once the trajectory presses it from the left the other
three approaches are permanently unobservable. A0's own design made the decisive
experiment impossible. That is a lesson about how to build the *next* self-made
world, and it is written up in §6.

---

## 3 · Where the engines earned their keep

Three results that a hand-filled candidate box would not have produced.

**`zero_space` found the Button→Door dependency as a conservation law.**
Handed 152 anonymous indicator bits and told nothing about buttons or doors, it
returned

```
[cell (3,2) shows 8]  +  [cell (4,5) shows 5]   ≡  1   (mod 2)
```

— *the Door exists if and only if the Button is unpressed*, with 275
transitions of support, against the single witness the rule miner had. The rule
says when it happens; the law says that it always holds. This is the clause the
whole A0 world was built to test, and an engine produced it unprompted.

**CEGIS produced a semantically right guard on one witness.** `act==LEFT ∧
tcolor(LEFT)==7` — "push into a cell showing colour 7" — with a frontier of size
1, i.e. the vocabulary pinned it exactly. Also `act==DOWN ∧ tcolor(DOWN)==3` for
the Portal, on two witnesses, with a frontier of size 2 that the adjudication had
to break by argument.

**MDL adjudicated the segmentation.** The colour-agnostic connected-components
operator fragmented the trajectory into 90 tracks with 88 vanishes and 87
appears, because the Cart is constantly adjacent to the Button. The
uniform-colour operator gave 3 tracks and 216 events. Script bits: 6511 vs 4423.
The framework's own criterion picked the right operator with no thumb on the
scale.

---

## 4 · Where the framework's own criteria collided

**Concept-admission by compression says the Button and the Door should not
exist.** Per-object accounts, from the engine's own cost model:

| object | script bits | pixel baseline | account |
|---|---|---|---|
| Cart | 2169 | 5136 | **+2967** |
| Button | 29 | 12 | **−17** |
| Door | 25 | 12 | **−13** |

Theoria 1.8 makes shortening the manual a concept's ticket of admission, and
constraint 5 forbids an entry with no gain. By that rule both should have been
rejected — each has one event in 275 transitions and costs 21 bits to declare.
They were admitted anyway, on constraint 2: cells (3,2) and (4,5) change, so
they cannot be board, and if they are not objects either then two pixels of every
frame are unexplained and the cheap layer fails at frame 0.

The compression account is not wrong, it is comparing against the wrong
alternative. The alternative to "the Button is an object" is not "encode its
pixel edits"; it is "leave the cell unexplained forever", which this accounting
prices at zero. **Recommendation for the framework: the compression account
should be computed against the shortest *responsibility-complete* description,
not against a per-object pixel baseline.** Otherwise every rarely-moving object
in every world will look like a bad concept.

**The manual's most important semantic fact is not in the DSL.** `step`'s frame
axiom — *if no rule fires for an object, that object is unchanged* — has no
sentence form in `dsl_grammar_v0.1`. It lives in a comment at the top of
`theory.dsl` and is hard-coded in all three backends. Eleven mined `*_still_*`
rules (up to 74/74 coverage) were rejected as entailed by it, which is the right
call and shortens the manual by eleven clauses; but a manual whose default
behaviour is a comment is not a manual, and a second reader compiling
`theory.dsl` would get a different world. **This is the single expressivity gap
to close first.** Full ledger: `THEORIZE_LOG.md` §E.

---

## 5 · Failure-taxonomy diagnosis

Against Theoria Phase 3's table. Scored on this spike only; A0 is one
self-built world and none of these numbers generalise.

| failure class | verdict on A0 | evidence |
|---|---|---|
| **概念不成形** | **hit, and instructive** | not vocabulary thrash — the vocabulary was right first time — but the *admission criterion* misfired: compression said reject, responsibility said admit (§4). The segmentation operator space also had to be widened before objects were recoverable at all (D-A0-007) |
| **机制归纳错** | **clear** | zero replay mismatches; every mined guard that was accepted is exactly right against the truth. CEGIS did not hallucinate once |
| **调度失误** | **clear** | no arithmetic or enumeration was done by hand. Every number in `theory.dsl` traces to an engine payload. The one hand-computation — the per-object compression accounts — is derived from the engine's own `CostModel` |
| **表达力不够** | **hit, five times** | frame axiom (E-03, serious), direction lifting (E-02), guard negation (E-01), board landmarks (E-04), weight vectors (E-05). None blocked the spike; E-03 compromises handover |
| **证明打不动** | **clear** | both obligations discharged by `decide` in under 2 s, axiom lists empty, no `sorry`, no Mathlib. The Lean layer was the easiest part of the sprint, which was not the expectation |
| **搜索爆炸** | **clear** | the stub BFS solved a 38-cell instance in well under a second. Untested at scale: Fast Downward is still not connected |
| **戳探设计差** | **hit, hard** | **zero executable probes were emitted.** Every frontier ambiguity was either extensionally undecidable in this world (`free` / `clear` / `tcolor==0` are the same predicate here) or decidable only in a configuration the world cannot be driven into. The one ambiguity that mattered — was the press direction-free? — could not be probed *at all*, because the latch is irreversible |
| **修订抖动** | **not applicable, and that is the problem** | the manual was revised **zero** times by certify. Both layers went green on the first run. The inner loop was not exercised; see §6 |

Two classes were hit hard (表达力, 戳探), one was hit in an unexpected form
(概念), and four came back clean. The clean ones are weak evidence: A0 is small,
deterministic, and built by the same instance that theorized it.

---

## 6 · What this spike does *not* show

Listed plainly, because a green A0 is worth exactly as much as its caveats.

1. **The theorize→certify inner loop never ran.** One pass over the candidate
   stream produced a manual that passed both certify layers immediately. So A0
   demonstrates that a manual *can* be induced; it demonstrates nothing about
   *repair*, which is the loop's actual job and the thing Phase 3 will spend its
   budget on. The revision count is 0, and a revision count of 0 is not a
   success metric.

2. **The probe machinery got no exercise.** Zero executable probes. A0's
   ambiguities are the wrong kind: identical predicates, or an irreversible
   latch. A second self-built world should be designed so that (a) every rule
   can be re-witnessed — no monotone latches, or a reset — and (b) at least one
   frontier is separable by an action the agent can actually take.

3. **The seal is imperfect.** The same instance built the world and adjudicated
   it. No ground-truth file was read before M6, and every verdict in
   `THEORIZE_LOG.md` is written to be re-derivable from the candidate stream
   alone — but that is a weaker guarantee than a genuine blind. The
   framework-level fix is the one Phase 3 already specifies: prompt iteration on
   self-built worlds, ARC only as validation.

4. **Two of the three real bugs were in the compiler, not the theory.** The
   simultaneous-rule-semantics bug made the Door never open; the PDDL subtype bug
   made a solvable instance report UNSAT. A wrong backend is
   indistinguishable, from inside the loop, from a wrong manual — and one of
   these bugs manufactured a *false* UNSAT, which under constraint 6 would have
   triggered a certificate obligation for a theorem that is false. The
   four-co-derived-forms design is supposed to make drift visible; here it took a
   human reading the plan output. `plan_stage.py` now cross-checks the planner
   against the manual and the world, which is the check that was missing.

5. **Scale is untested.** 59 states, 38 arena cells, 275 transitions. Lean's
   `decide` is affordable at 152 states and will not be at 10⁶. Fast Downward is
   still not connected.

6. **`cart_unique` was proved by the representation, not by Lean.** Encoding the
   state as *the Cart's cell* assumes there is exactly one Cart. The invariant is
   real and is checked — per frame, by the responsibility pass — but the Lean
   file does not prove it and says so. Any state encoding that makes an invariant
   unstateable is quietly deciding it.

---

## 7 · Verdict

**A0 is证活, not判死.** The framework's central bet — that an LLM can cold-start
a world theory from engine proposals, and that the theory can be compiled,
certified, planned with, and used to prove an impossibility — held on the first
world it was tried on, end to end, in about six seconds of compute.

The bet that was *not* tested is the one Phase 3 rides on: that when the theory
is wrong, the loop repairs it. A0 produced a manual with a known, predicted,
replay-invisible hole and had no mechanism available to close it. The next spike
should be built to make that hole probeable, and should be scored on revisions,
not on first-pass accuracy.

Recommended before the next spike, in order:

1. give the DSL a frame-axiom sentence form (E-03) — cheapest, highest value;
2. build A0′ with reversible mechanics and a probe-separable frontier, and
   report revision count as the primary metric;
3. change the concept-admission account to price against a
   responsibility-complete baseline (§4);
4. connect Fast Downward, and re-run M4 to confirm the adapter is a no-op change.
