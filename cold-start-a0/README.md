# cold-start-a0

The A0 cold-start spike from [Theoria.md](../Theoria.md) Phase 1: a self-built,
truth-known micro-world, run through the whole inner loop for the first time —
perception → engine proposals → adjudication → certify → plan → win, plus a
constructed unsolvable variant and its impossibility theorem.

Nothing here touches the ARC API. `engine-rig` and `theory-compiler` are used as
libraries and are never modified.

```bash
cd cold-start-a0
python run_all.py                  # A0, the whole loop, ~6 s
python -m prime.run_prime          # A0-prime: cold start + seeded repair control
python -m pytest                   # 44 tests
python -m certify.score_vs_truth   # scoring against the referee's copy
python -m pipeline.concept_account # concept accounts, responsibility-complete
python -m certify.fd_conformance   # the Fast Downward code path
```

**Read [A0_REPORT.md](A0_REPORT.md) first**, then
[prime/A0P_REPORT.md](prime/A0P_REPORT.md). A0's loop closed and its manual came
out 233/236 correct — wrong in three places that full-history replay cannot see,
exactly where [THEORIZE_LOG.md](THEORIZE_LOG.md) said it would be. A0-prime then
answers the two questions A0 left open, and finds that **reversibility beats
coverage**: half the state-action coverage, and a perfect manual.

## Layout

| path | what |
|---|---|
| `world/` | the A0 world, the systematic explorer, the referee's ground truth |
| `pipeline/` | board extraction, the segmentation operator space, the multi-track CEGIS driver, the engine stage, plan/commit, the unsolvable variant |
| `theory/` | **hand-written**: `theory.dsl`, `theory_no_button.dsl`, `playbook.dsl`. `generated*/` is compiler output and is never hand-edited |
| `compile/` | the four backends and the derived problem instance |
| `certify/` | cheap layer (replay ∧ responsibility), expensive layer (Lean), M6 scoring |
| `artifacts/` | traces, `candidates.jsonl`, reports — all byte-reproducible |
| `prime/` | **A0-prime** — the follow-up world, its probe machinery and the seeded repair control |
| `proposals/` | the `semantics:` extension request for `dsl_grammar` v0.2 |
| `THEORIZE_LOG.md` | every candidate, and why it was accepted, rejected or left to a probe |
| `DECISIONS.md` | design calls, upstream gaps and the one upstream defect found |

## The world

```
      c0 c1 c2 c3 c4 c5 c6 c7 c8
 r0    #  #  #  #  #  #  #  #  #
 r1    #  .  .  .  .  #  .  .  #
 r2    #  .  .  .  .  #  .  *  #     * goal (not rendered)
 r3    #  .  B  .  .  #  .  .  #     B Button, 7 -> 8 when pushed into
 r4    #  .  .  .  .  D  .  .  #     D Door, vanishes when the Button is pressed
 r5    #  C  .  .  .  #  .  .  #     C Cart
 r6    #  .  .  .  #  #  .  .  #
 r7    #  #  #  P  #  #  .  .  #     P Portal -> (1,1)
 r8    #  #  #  #  #  #  #  #  #
```

59 reachable states. The Door is the only opening in the divider, and it only
opens once the Button is pressed — so no account of the Cart's motion alone can
explain the trajectory. That is the property the spike exists to test.

## What determinism means here

Fixed seed, no clock, no randomness. `raw_trace.jsonl` is byte-identical across
runs (`test_trace_is_byte_stable`), and `candidates.jsonl` is byte-stable under
`THEORIA_DETERMINISTIC_IDS=1` + `THEORIA_FIXED_TIME`, which `run_all.py` sets.

## Lean

`certify/lean_check.py` looks for `lean` in `$LEAN`, then
`.toolchain/lean-*/bin/`, then `PATH`. The toolchain is gitignored; fetch it with

```bash
curl -sSL -o lean.zip https://github.com/leanprover/lean4/releases/download/v4.9.0/lean-4.9.0-windows.zip
```

and unzip into `.toolchain/`. The generated Lean uses **no Mathlib** and
**`decide`, never `native_decide`** — `native_decide` would put
`Lean.ofReduceBool` in the axiom list, and the acceptance test is that the list
is empty.
