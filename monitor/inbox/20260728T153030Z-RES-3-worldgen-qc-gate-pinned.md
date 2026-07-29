# V12-worldgen-gate-deaf — the QC gate is connected, and two things belong to other territories

From: RES-3 executor, worker on `agent/v12-worldgen-gate-deaf`
Provenance: `worldgen/runs/20260728T153030Z-V12-worldgen-gate-deaf/`
Date: 2026-07-28T15:30:30Z · zero network, zero API, zero sealed-pile contact

## What the item found, in one paragraph

`gating=False` on `worldgen/verify.py`'s two QC stages **was deliberate** — it is
stated in the file's own docstring, it was there in the first commit (`66493f6`),
and C6 (`9a37d8a`) deliberately rewrote the paragraph into the plural when it
added the mutants stage. Both QC reds are **upstream**: `a0_relational_v1`'s
vocabulary raises `NoSeparatingGuard` on `t2-lock-fragile` and on
`t2-switch-push`, and the fix is an atom in `cold-start-a0/pipeline/atoms_a0.py`,
which `worldgen/` may not edit. So gating on `pass` was **refused** — it would
leave the world factory permanently red for a file it is forbidden to repair.

What was defective was different, and worth naming because it is a *class*:
`verify` judged each QC stage by `proc.returncode` alone, and `run_qc` returns 1
for an honest miss exactly as Python returns 1 for an uncaught `ImportError`. **A
QC layer that had stopped executing altogether was indistinguishable from one
that measured a miss**, and both printed `[miss]` and exited 0. Nothing pinned
the verdict either, so "neither stage gates" was implemented as "any QC outcome
exits 0". The repair: `worldgen/qc/KNOWN_MISS.json` transcribes the published
verdict by hand with each red's owner beside it, and the stages now gate on
**deviation from the pin** and on failure to write a verdict. No pre-registered
bar was touched; both artifacts still say `pass: false`; `verify` still exits 0,
but its last line is no longer the bare token `green`.

Negative control mutation-tested: with the pre-V12 semantics restored, 6 of 7
implanted reds exited 0. Restored, 7 of 7 behave.
(`runs/…-V12-…/mutation_check.txt`.)

## Two items for other territories — I did not act on either

### 1. `exam/` almost certainly has the same three defects

`exam/verify.py:25` says, of itself:

> Same shape as `worldgen/verify.py`, and for the same reason stated there

That reason no longer holds unqualified, and the shape it copied includes the
part that was wrong: judging a non-gating stage by its exit code makes a dead
stage and a measured miss the same signal. Worth someone checking whether
`exam/verify.py` can tell a crashed stage from a missed bar, and whether anything
pins what it currently reports. **Not mine to touch** — different territory.

### 2. `python -m worldgen.verify` dirties ten committed artifacts, and they are
### the other track's outputs

On a clean tree, one `verify` run leaves ten files modified under
`worldgen/out/qc/*/`: `candidates.jsonl` and `engines_report.json` for six worlds
and mutants (e.g. `frontier_size` 32 → 57). Identical on every run, so this is
**drift between the `cold-start-a0` code state that produced the committed copies
and the one on disk now**, not nondeterminism. `QC.json` and `QC_MUTANTS.json`
themselves are byte-stable.

Two consequences for whoever owns the release manifest:

* anyone who runs the territory's own verify command leaves an uncommitted diff
  behind, and will either commit upstream's drift into `worldgen/`'s history or
  `git checkout` it away without noticing what it was;
* those committed artifacts no longer describe the pipeline that exists.

The diff is kept at
`worldgen/runs/20260728T153030Z-V12-worldgen-gate-deaf/out_dirtied_by_verify.diff`;
the tree was restored with `git checkout -- worldgen/out/`. I did not regenerate
them — `worldgen/out/` is generator-only and the generator in question belongs to
the other track.

## Status of the branch

Uncommitted, in `.worktrees/v12-worldgen-gate-deaf/`, for RES-3 to collect.
Files touched: `worldgen/verify.py`, `worldgen/qc/gate.py` (new),
`worldgen/qc/KNOWN_MISS.json` (new), `worldgen/tests/test_verify_qc_gate.py`
(new), `worldgen/README.md`, `worldgen/RUN_STATE.md` (append-only), and the run
directory. Nothing outside `worldgen/` except this note.
`python -m pytest worldgen/ -q` → 425 passed, 13 skipped, exit 0.
