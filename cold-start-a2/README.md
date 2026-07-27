# cold-start-a2 — the DC22-isomorphic world, and the theorem that is false

A2's two acceptance sentences, from [Theoria.md](../Theoria.md) Phase 1:

> **仪器造得出展品，回路转得起来。**

This directory does both on a self-built world. It exists instead of the
literal A2 ("port the upstream DC22 model into the DSL") because that item
collided with the pile cut; the owner ruled on 2026-07-28 that A2 is fulfilled
by a self-built world isomorphic to DC22's failure structure. See
[`arc-recon/data/incidents.jsonl`](../arc-recon/data/incidents.jsonl) **INC-004**
and [`A2_REPORT.md`](A2_REPORT.md) §1.

**No upstream DC22 artifact was read.** The isomorphism argument cites only the
structural description already printed in Theoria §1.3. Zero API calls, zero
network, zero contact with the sealed pile.

## The exhibit, in one paragraph

A 9×9 pushing world whose goal room is sealed behind a solid wall and reachable
only by a teleport. The pipeline induces the complete manual from a full sweep;
one rule — the teleport — is then deleted by hand. The holed manual replays the
play record at **184/184 frames, zero anomalies**, its planner returns **UNSAT**,
and Lean signs `unsolvable` with an **empty axiom list**. The world solves the
same goal in 18 actions. Every gate is green and the theorem is false.

Then the loop turns: 打脸 → 定位 → 戳探 → 修订 → 重证 → 解出, each beat leaving an
artefact behind. The repaired manual proves a theorem of *exactly the same
shape* — same generator, same `decide`-only tactic, same empty axiom list —
about the sealed pocket at (7,1), and that one is true. The pair of Lean files
is the two-layer truth regime you can diff.

## Run it

```bash
cd cold-start-a2 && python run_all.py              # ~17s, all steps green
cd cold-start-a2 && python -m pytest               # 44 tests
cd cold-start-a2 && python -m tools.verify_readonly # 258 files hashed, 0 changed
```

Artefacts are byte-reproducible for a fixed seed: two clean runs produce
identical `artifacts/` and identical generated forms.

## Layout

| path | what |
|---|---|
| `a2world/a2_world.py` | the world. Geometry, transition function, and `step_holed` — the referee's copy of what the holed manual claims |
| `a2world/explorer.py` | the sweep, its three monotone strata, and the cut that defines the play record |
| `a2world/ground_truth.py` | M1: both traces, plus the referee's copy. Not opened while theorizing |
| `theory/theory.dsl` | the complete manual (control) |
| `theory/theory_holed.dsl` | **the exhibit's input** — the control minus one rule |
| `theory/theory_repaired.dsl` | the manual after the loop, written from `probes.jsonl` |
| `theory/generated_holed/theory.lean` | the theorem that type-checks and is false |
| `theory/generated_repaired/theory.lean` | the theorem of the same shape that is true |
| `theory/generated_repaired_stale/` | a **red** artefact, kept on purpose: the refuted certificate regenerated against the repaired step |
| `a2pipeline/` | the stages. Engines, compile, certify, plan, exhibit, and the six loop beats |
| `artifacts/loop_ledger.json` | the eight beats, each with the file that settles it |

## What is reused, and where reuse stops

The engines are `engine-rig`'s, the parser is the frozen v0.1 contract's, and
the compile backends and certify layer are `cold-start-a0`'s — imported
unmodified. A2 writes no engine and no generator, which is the point: an exhibit
produced by a compiler written for the exhibit would prove nothing about the
instrument.

Reuse is **read-only**. `cold-start-a0` belongs to the theory-compiler track.
Where reusing a function would have meant writing into that tree — A0's
`plan_stage` reports into its own `artifacts/` — A2 rewrites the driver and
keeps the logic. `artifacts/upstream_pin.json` hashes every upstream file A2
imports, because that tree had work in flight while this was built.

## Two findings about the reused code

Both are in [`DECISIONS.md`](DECISIONS.md) and on `PARTNER_SYNC.md`; neither was
fixed in place, because that is not this track's directory.

* **D-A2-006 — the PDDL backend cannot ground a teleport.** `gen_pddl_a0` emits
  a cell object only for cells in the derived arena, and a static coloured cell
  like a Portal entry is not in it, so `teleport-down`'s `?p - markedcell`
  parameter has no inhabitant and the planner returns UNSAT on a manual that
  *has* the teleport rule. A0 could not see this — its goal was reachable
  through the Door. A2's goal is reachable only through the teleport, which
  turns a latent bug into a wrong answer. Worked around in
  `a2pipeline/compile_a2.py::pddl_addressable`.
* **D-A2-007 — `lean_check` loses the diagnostic when there is one.** It decodes
  the toolchain's output with the process locale; Lean's error messages contain
  U+2019, this box is GBK, and the subprocess reader raises exactly when a proof
  fails. A0 never had a red Lean file. A2 has one on purpose.
