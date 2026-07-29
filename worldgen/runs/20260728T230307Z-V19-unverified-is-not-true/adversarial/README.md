# adversarial/ — the review's own instruments

Everything the adversarial review of V19 ran, so its numbers can be re-derived
rather than believed. The report is `../ADVERSARIAL-VERBATIM.md`.

Nothing here is imported by `worldgen/`, runs in the test suite, or writes
inside the checkout: every mutant is applied to a throwaway copy of the package
under a temp root, and the copy is deleted afterwards.

## The mutation campaign — 80 mutants, 30 escapees

| file | what it is |
|---|---|
| `harness.py` | the runner. One package copy per mutant; applies the edits, runs `python -m pytest worldgen -q` and `python -m worldgen.build --into <tmp> --quiet` inside the copy, records both exit codes. Refuses to run a mutant whose anchor does not occur **exactly once** — a patch that silently no-ops is a green result for the wrong reason, which is the failure `invariant_sandbox.py` is built against and this file inherits. |
| `gen_mutants.py` | emits `mutants.json` — the 72 mutants of batch 1 |
| `batch2.py` | emits `mutants2.json` — the 8 mutants of batch 2 (the `edge_check → False` probes and the sampling mutants) |
| `mutants.json`, `mutants2.json` | the mutant definitions, as `(file, anchor, replacement)` triples |
| `results.json`, `results2.json` | raw results including the failing test names and build tails |
| `run.log`, `run2.log` | one line per mutant, in submission order |

```bash
cd <worktree root>
python gen_mutants.py > mutants.json
python harness.py mutants.json results.json 4     # ~4 workers; the full batch is slow
```

`harness.py` and `drift.py` carry absolute paths to the worktree and to the
scratch root they were run from; edit `SRC` / `SCRATCH` before re-running.

## Standalone probes

| file | the question it answers | reads |
|---|---|---|
| `probe_edge_check_is_exercised.py` | (c) Are the three new `edge_check`s exercised, or vacuously green? Counts the transitions on which each guarded quantity actually moves. | working tree |
| `probe_c12_exception_swallowed.py` | (b/F1) With mutant C12 applied, does a `check` that raises on every state report `holds`? At `23ec179`, it does. | `git show 23ec179:` — pass `--worktree` to re-ask against current code |
| `probe_weakening_is_a_noop.py` | (F7) Is any `WEAKENINGS` entry observationally identical to its own control? At `23ec179`, `boolean_default` was. | working tree |
| `drift.py` | (F2) Does `python -m worldgen.build --check` pin the *committed* artefacts, or only determinism? Only determinism — it exits 0 while rewriting `transitions_checked: 104` to `0`. | package copy |

**On anchors and moving code.** The review examined commit `23ec179`; repairs
began landing while this directory was being written, and `probe_c12`'s anchor
stopped matching the working tree within the hour. That probe therefore reads
the reviewed blob out of git rather than the checkout, and refuses to re-anchor
itself — a mutant applied at a different site is a different experiment, and
silently becoming one is the failure mode the whole review is about. The two
probes that read the working tree say so in the table above, and their quoted
results are labelled with the commit they were taken at. A repaired tree is
*expected* to change what they print.

The three `probe_*.py` files write nothing and run from anywhere:

```bash
python worldgen/runs/20260728T230307Z-V19-unverified-is-not-true/adversarial/probe_edge_check_is_exercised.py
```
