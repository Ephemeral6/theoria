"""E8 — where IC3's boundary is.

M9 got IC3/PDR one non-linear inductive invariant, on peg `0111`. One point is
not a line. This package measures the boundary along the axes the item names:
state-space size, predicate count, and mechanism composition.

Module layout, fixed up front so the pieces do not collide:

    harness.py          the per-step runner: subprocess timeout, the record
                        schema, and the deterministic/timing split
    axis_size.py        axis A -- peg-N, which contains the M9 anchor
    emit.py             Invariant -> recheck `certificate-v1`, so that
                        "an independent checker accepts it" is a real column
    recheck_column.py   that column, per rung, with recheck/'s own exit codes
    worldgen_system.py  worldgen world -> boolean System, with the gate that
                        proves the derived relation is the world's relation
    axis_compose.py     axis C -- mechanism composition at held-fixed size
    reencode.py         one world, said in more or fewer booleans -- and the
                        rewriting that gives a padded certificate a native form
    axis_predicates.py  axis B -- predicate count at a state space held
                        EXACTLY fixed, which is what axis A cannot do
    __main__.py         the one entry point: `python -m ic3bounds --axis ...`

The three axes are not three benchmarks that share a directory.  They run one
runner (`harness.measure_in_process`), one six-verdict taxonomy and one record
schema; an axis contributes only *which world* and *which columns beyond the
shared ones*.  Where an axis needs a different `System` builder or a different
gate it substitutes those two module-level names in `harness` and restores them
-- it does not write a second runner.

Two rules the whole package is built on, both from `bench/README.md` and
`recheck/README.md`:

* **Deterministic fields are re-derived exactly; timings are checked for
  presence and ordering, never equality.** A wall clock is a statement about
  one machine on one afternoon.
* **Two transcriptions, never one.** The module that builds the `System` IC3
  solves must not be the module that builds the rule set the rechecker reads.
  A shared adapter makes "the independent checker agreed" mean nothing, which
  is the failure `recheck/README.md` opens by naming.
"""
