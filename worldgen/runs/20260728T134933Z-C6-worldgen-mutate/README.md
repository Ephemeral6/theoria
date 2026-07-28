# run 20260728T134933Z-C6-worldgen-mutate

Worker `W-1251`. Branch `agent/c6-worldgen-mutate`, base commit `0d28e99`.

The narrative lives in **`worldgen/RUN_STATE.md` § RUN_STATE — C6-worldgen-mutate**
rather than here, because it is the territory's standing record and the item
asked for the interface to be written there. This directory is the evidence.

| file | what it is |
|---|---|
| `MANIFEST.json` | provenance; `files[]` carries sha256 for the 15 mutants' 90 artefacts and every source file this run changed |
| `PLAN.md` | written **before** any code, including the decision not to retrofit a second parameter system and the reason |
| `verify.txt` | `python -m worldgen.verify`, full output: green, with both QC stages recorded as measured misses |
| `diagnose_t2-switch-push.txt` | `qc/diagnose_miner.py` on the *base* world, localising its `NoSeparatingGuard` to vocabulary shortness — the evidence that `v-efe43df1`'s QC failure is inherited and not caused by mutation |
| `diagnose_v-efe43df1.txt` | the same on the mutant, for the comparison |
| `summarise.py` | one line per mutation off `MUTATIONS.json`; how the corpus was inspected while it was being chosen |
| `manifest_files.py` | fills `MANIFEST.json`'s `files[]` |
| `lint_unused.py` | crude unused-import sweep over the files this run touched |
| `adversarial/` | the probes the measurement-code reviewer wrote. **They were run against the pre-fix code and several will no longer reproduce** — `a2b_noop.py` demonstrates a no-op edit being accepted, which is now refused; `a5b_stall.py` demonstrates the greedy walk stalling silently, which now empties the budget; `a6_family.py` demonstrates a guard change passing as a reversibility change, which now fails the gate. Kept as the record of what was wrong, not as a live suite; the live forms are in `worldgen/tests/test_mutate.py` |

## The two gate catches worth keeping

The first gated build refused two of the twelve edits I had written, both on
predictions I had made from reading the geometry:

```
BUILD GATE FAILED:
  v-df73c526   a world's measured solvability contradicts the spec's `intended_solvable`
  v-df73c526   a declared primary rule never fires, or a fired tag is undeclared
  v-fdcdd355   a declared primary rule never fires, or a fired tag is undeclared
```

`t1-tokens-lock` with `LEFT` forbidden: I claimed it unsolvable because the third
token becomes unreachable, and the goal never needed the lock — it is reachable
along the top row. The same edit also left `walk_through_lock` dormant.
`t2-cycler-lock` with `open_phase=0`: the cycler starts open, so `advance_cycler`
never fires anywhere.

Both were replaced rather than exempted. Neither id survives into the corpus,
which is why they are recorded here — a gate that has never refused anything is
indistinguishable from one that cannot.

## The adversarial pass

Two review agents, no stake in the code, one on the measurement functions and
one on the read licence. Between them they found nine defects in shipped
artefacts or in claims `worldgen/RUN_STATE.md` made — including one that broke
five tests in `exam/` while every test in `worldgen/` stayed green, and one
(`seed` copied from the base) that identified the base of all fifteen mutants
exactly. The table is in `RUN_STATE.md § what the adversarial pass changed`.

They also **refuted** two things worth as much as the defects: the product-BFS
detection latency was cross-checked against two independent oracles over the
fifteen mutants and seventy fuzzed edits with zero disagreements, and the
claim→rule graph's suspected cross-mechanism blind spot does not exist — no
mechanism paints over another's cells in any reachable state of any of the
twenty, verified by rendering each in isolation and diffing.
