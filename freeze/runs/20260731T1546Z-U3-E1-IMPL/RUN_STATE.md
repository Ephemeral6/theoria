# U3-E1-IMPL — the first computation code for 主终点一 (U3 达成率)

**What this run delivers.** `freeze/u3.py` + `freeze/tests/test_u3.py`:
the evaluator whose absence STATS_RULES.md §9.14 registers as a launch
precondition ("U3 达成率本身没有任何计算代码 … 未实现不得开跑"), together with
the §9.2 non-vacuity check to its executable extent, its frozen negative
control, and a sweep over every existing theoria-arm run plus the A0 material.

## The frozen judgment implemented (verbatim anchors)

Per-game attainment = the arm produced **至少一条机器可查的定理** with
(a) the theory-compiler Lean form **compiles**;
(b) `#print axioms` reports only whitelisted axioms —
    allow {`propext`, `Quot.sound`}; never {`sorryAx`, `Lean.ofReduceBool`};
    anything else (incl. `Classical.choice`) fails (b), and `Classical.choice`
    additionally sets `flags.classical_choice_needed` for §1.2's preregistered
    sensitivity listing;
(c) the statement is **non-vacuous** (§1.2.1) — the D-A3-007 `I := true` class
    must be caught.
U3 = 证得动 (Theoria.md:262), not winning: the cheap layer's replay and the
episode outcome are reported but are **not criteria** (§5.7.5: U3 从产出物裁).

## Design decisions taken strictly, with the ambiguity recorded

1. **Declared refusal** (`expensive.detail` beginning `not attempted:` — the
   enumerative development too big): the frozen sentence requires the arm to
   *produce* a theorem; a refusal produced none → **not attained**, never
   excluded. On the generous reading it would be a 缺格 (§1.2.1) — but §1.2.1
   rules 缺格局留在分母、计为未达成, so **the verdict is identical on both
   readings**; only the failure-attribution label differs (whether the game
   enters g in §1.4's inconclusive arithmetic). Strictly it is NOT a 缺格:
   §1.2.1 defines 缺格 as a produced theorem the hashed checker cannot run,
   and §9.20 bars g from adjudication arithmetic until its game-level, prior
   criterion is frozen. `u3.py` therefore emits `label=declared_refusal`,
   `flags.gap_candidate_g=true` — a flag for the freeze territory to rule on,
   never arithmetic. **Ambiguity registered for freeze**: whether "定理写成了
   查不了的形状 → (c) 未达成" (§1.2.1's arm-caused branch) should swallow the
   refusal case too; the strict implementation here reads a refusal as simply
   "no theorem produced".
2. **Undischarged / unreported fails closed.** A Lean file never run, or run
   green with no `#print axioms` evidence, is not 机器可查 — labels
   `undischarged` / `axioms_unreported`, both not-attained. `--probe`
   re-runs Lean live to recover honest cases.
3. **(c) executable extent + confessed residual.** Implemented: static
   constant scan of `def I`/`def Goal`; definitional-constancy probes in Lean
   itself (`fun _ => rfl` / `trivial`) under `--probe`; §1.2.1-unsolvable
   sub-checks (a)(b) via co-theorems, (c)(d) via recorded run evidence with
   provenance strings. Not implemented: the full two-witness predicate for a
   *syntactically disguised* constant, and the prune-kind checks — a theorem
   kind with no implemented check **fails closed**, and every judgment carries
   `criteria.c_residuals` naming what was deferred (§9.2 stays open until the
   freeze territory accepts this extent or extends it).

## Gate outputs (verbatim)

```
$ python -m pytest freeze/tests/test_u3.py -q
29 passed in 14.00s
```

Negative controls inside that suite:
* frozen §9.2 control `cold-start-a3/theory/generated_l1_vacuous` →
  `not_attained / vacuous` (caught **both** lean-free via static scan and
  live via constancy probe);
* failing obligation (recorded rc=1, and live `theorem bad : 1 = 2 := rfl`)
  → `not_attained / failing_obligation`;
* live `sorry` → sorryAx rejected; live `Classical.em` tautology (the G1
  counterexample from §1.2) → `axiom_violation` + `classical_choice_needed`;
* positive: `a0-spike`, `cold-start-a0`, `generated_l1` → `attained /
  discharged` (recorded and live-probe paths agree).

## Sweep — every existing theoria-arm run + A0 (u3_table.md / u3_table.json)

```
$ python freeze/u3.py sweep <main-tree theoria-arm/runs> a0-spike cold-start-a0 \
      cold-start-a3/theory/generated_l1{,_vacuous} --probe
3 / 60 directories attained U3
labels: no_evidence 49, declared_refusal 4, no_proof_layer 3, discharged 3, vacuous 1
```

Per-game rollup over live-arm material (best record per run, dev pile only):

| game | runs seen | best label | U3 |
|---|---|---|---|
| g50t-5849a774 | 12 | declared_refusal | **not attained** |
| sk48-d8078629 | 3 | declared_refusal | **not attained** |
| ar25 / tn36 | 0 runs with certify evidence | — | not attained (no evidence) |

**Reading for Phase 3's exit condition (U3 达成 ≥k 局): today the count is 0.**
No live arm run has ever reached the proof layer — every certify record either
left no evidence, recorded the proof layer unavailable, or declared the
enumerative-development refusal. The three attained directories are the A0/A3
cold-start material (synthetic worlds, discharged Lean proofs) — they prove the
evaluator's positive path, not a dev-pile game. The blocker E1 now measures is
therefore the arm's Lean-form refusal on grid worlds, which is exactly the gap
`certify.py`'s expensive layer already names.

Sweep caveat: the sweep read the MAIN tree's `theoria-arm/runs` read-only while
two live legs were running; any mid-write artefact would have been labelled
`unreadable` (none was). Re-run after the legs finish before quoting the table
as final.

## What this unblocks / what it does not

* §9.14 (U3 has no computation code): **implementation now exists** with CLI +
  tests; the freeze territory must still countersign it and hash it into the
  freeze kit before 开跑.
* §9.2 ((c) executable check): implemented to the extent above, negative
  control passing; residuals named in-code and here, not hidden.
* Untouched: STATS_RULES.md, CLAIMS_TEXT.md (frozen texts, corrections there
  are the freeze track's to append), the live legs' run dirs, .env, sealed
  pile (zero contact — all材料 are dev-pile games or synthetic worlds).
